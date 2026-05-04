from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.project import Task
from app.schemas.task import (
    TaskCreate,
    TaskReorder,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.services.notification import create_notification, find_user_id_by_username

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    status: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Task)
    if status:
        stmt = stmt.where(Task.status == status)
    stmt = stmt.order_by(Task.position)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    body: TaskCreate,
    session: AsyncSession = Depends(get_session),
):
    task = Task(**body.model_dump())
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # Notify assignee if task is created with an assignee
    if task.assignee:
        user_id = await find_user_id_by_username(session, task.assignee)
        if user_id:
            await create_notification(
                session, user_id, "task_assigned",
                "New task assigned",
                f"You have been assigned to task: {task.title}",
            )

    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    body: TaskUpdate,
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_assignee = task.assignee
    old_status = task.status

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    await session.commit()
    await session.refresh(task)

    # Notify new assignee if assignee changed
    if body.assignee is not None and body.assignee != old_assignee and body.assignee:
        user_id = await find_user_id_by_username(session, body.assignee)
        if user_id:
            await create_notification(
                session, user_id, "task_assigned",
                "Task assigned to you",
                f"You have been assigned to task: {task.title}",
            )

    # Notify assignee if task completed via update
    if body.status == "done" and old_status != "done" and task.assignee:
        user_id = await find_user_id_by_username(session, task.assignee)
        if user_id:
            await create_notification(
                session, user_id, "task_completed",
                "Task completed",
                f"Task completed: {task.title}",
            )

    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await session.delete(task)
    await session.commit()


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    body: TaskStatusUpdate,
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = task.status
    task.status = body.status
    if body.position is not None:
        task.position = body.position

    await session.commit()
    await session.refresh(task)

    # Notify assignee when task is completed
    if body.status == "done" and old_status != "done" and task.assignee:
        user_id = await find_user_id_by_username(session, task.assignee)
        if user_id:
            await create_notification(
                session, user_id, "task_completed",
                "Task completed",
                f"Task completed: {task.title}",
            )

    return task


@router.post("/reorder", response_model=list[TaskResponse])
async def reorder_tasks(
    body: TaskReorder,
    session: AsyncSession = Depends(get_session),
):
    tasks = []
    for position, task_id in enumerate(body.task_ids):
        task = await session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        task.position = position
        tasks.append(task)
    await session.commit()
    for task in tasks:
        await session.refresh(task)
    return tasks
