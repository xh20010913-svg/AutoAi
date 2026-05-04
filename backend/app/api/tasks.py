from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.project import Task, task_dependencies
from app.schemas.task import (
    DependencyAdd,
    DependencyGraph,
    DependencyRemove,
    GraphEdge,
    GraphNode,
    TaskCreate,
    TaskReorder,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

DONE_STATUSES = {"done", "cancelled"}


def task_to_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        assignee=task.assignee,
        project_id=task.project_id,
        position=task.position,
        created_at=task.created_at,
        updated_at=task.updated_at,
        depends_on_ids=[d.id for d in task.depends_on],
        depended_by_ids=[d.id for d in task.depended_by],
    )


async def _load_task(session: AsyncSession, task_id: str) -> Optional[Task]:
    stmt = (
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.depends_on), selectinload(Task.depended_by))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _has_cycle(session: AsyncSession, task_id: str, target_id: str) -> bool:
    visited: set[str] = set()
    queue = [target_id]
    while queue:
        current_id = queue.pop(0)
        if current_id == task_id:
            return True
        if current_id in visited:
            continue
        visited.add(current_id)
        stmt = select(task_dependencies.c.depends_on_id).where(
            task_dependencies.c.task_id == current_id
        )
        result = await session.execute(stmt)
        for (dep_id,) in result:
            queue.append(dep_id)
    return False


async def _check_and_update_blocked(session: AsyncSession, task: Task) -> None:
    if task.status != "blocked":
        return
    dep_task = await _load_task(session, task.id)
    if not dep_task:
        return
    all_done = all(d.status in DONE_STATUSES for d in dep_task.depends_on)
    if all_done and dep_task.depends_on:
        task.status = "todo"


async def _check_dependents_on_completion(session: AsyncSession, task: Task) -> None:
    if task.status not in DONE_STATUSES:
        return
    # Query for tasks that depend on this one
    stmt = (
        select(Task)
        .join(task_dependencies, Task.id == task_dependencies.c.task_id)
        .where(task_dependencies.c.depends_on_id == task.id)
        .options(selectinload(Task.depends_on))
    )
    result = await session.execute(stmt)
    for dependent in result.scalars().all():
        await _check_and_update_blocked(session, dependent)


async def _enforce_blocking_on_dependency_add(
    session: AsyncSession, task: Task, dep: Task
) -> None:
    if dep.status not in DONE_STATUSES and task.status not in DONE_STATUSES:
        task.status = "blocked"


# — Literal-path routes first (before /{task_id}) —

@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    status: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Task).options(selectinload(Task.depends_on), selectinload(Task.depended_by))
    if status:
        stmt = stmt.where(Task.status == status)
    stmt = stmt.order_by(Task.position)
    result = await session.execute(stmt)
    return [task_to_response(t) for t in result.scalars().all()]


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    body: TaskCreate,
    session: AsyncSession = Depends(get_session),
):
    data = body.model_dump(exclude={"depends_on_ids"})
    task = Task(**data)
    session.add(task)
    await session.flush()

    for dep_id in body.depends_on_ids:
        dep = await _load_task(session, dep_id)
        if not dep:
            await session.rollback()
            raise HTTPException(status_code=404, detail=f"Dependency task {dep_id} not found")
        if await _has_cycle(session, task.id, dep_id):
            await session.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Adding dependency {dep_id} would create a cycle",
            )
        task.depends_on.append(dep)
        await _enforce_blocking_on_dependency_add(session, task, dep)

    await session.commit()
    await session.refresh(task)
    task = await _load_task(session, task.id)
    return task_to_response(task)


@router.get("/dependency-graph", response_model=DependencyGraph)
async def get_dependency_graph(session: AsyncSession = Depends(get_session)):
    stmt = select(Task).options(selectinload(Task.depends_on))
    result = await session.execute(stmt)
    tasks = result.scalars().all()

    nodes = [GraphNode(id=t.id, title=t.title, status=t.status) for t in tasks]
    edges: list[GraphEdge] = []
    seen_edges: set[tuple[str, str]] = set()
    for t in tasks:
        for dep in t.depends_on:
            edge_key = (dep.id, t.id)
            if edge_key not in seen_edges:
                edges.append(GraphEdge(source=dep.id, target=t.id))
                seen_edges.add(edge_key)

    return DependencyGraph(nodes=nodes, edges=edges)


@router.post("/reorder", response_model=list[TaskResponse])
async def reorder_tasks(
    body: TaskReorder,
    session: AsyncSession = Depends(get_session),
):
    tasks = []
    for position, task_id in enumerate(body.task_ids):
        task = await _load_task(session, task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        task.position = position
        tasks.append(task)
    await session.commit()
    for task in tasks:
        await session.refresh(task)
    return [task_to_response(t) for t in tasks]


# — Parameterized routes (/{task_id}...) —

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    task = await _load_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_to_response(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    body: TaskUpdate,
    session: AsyncSession = Depends(get_session),
):
    task = await _load_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await session.commit()
    await session.refresh(task)
    task = await _load_task(session, task.id)
    return task_to_response(task)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    task = await _load_task(session, task_id)
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
    task = await _load_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Block starting a task if dependencies are not done
    if body.status not in DONE_STATUSES and task.status in {"blocked", "todo"}:
        incomplete = [d for d in task.depends_on if d.status not in DONE_STATUSES]
        if incomplete:
            task.status = "blocked"
            if body.position is not None:
                task.position = body.position
            await session.commit()
            await session.refresh(task)
            task = await _load_task(session, task.id)
            return task_to_response(task)

    task.status = body.status
    if body.position is not None:
        task.position = body.position

    await session.flush()
    await _check_dependents_on_completion(session, task)
    await session.commit()
    await session.refresh(task)
    task = await _load_task(session, task.id)
    return task_to_response(task)


@router.post("/{task_id}/dependencies", response_model=TaskResponse, status_code=201)
async def add_dependency(
    task_id: str,
    body: DependencyAdd,
    session: AsyncSession = Depends(get_session),
):
    task = await _load_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    dep = await _load_task(session, body.depends_on_id)
    if not dep:
        raise HTTPException(status_code=404, detail=f"Dependency task {body.depends_on_id} not found")

    if task_id == body.depends_on_id:
        raise HTTPException(status_code=400, detail="A task cannot depend on itself")

    if any(d.id == body.depends_on_id for d in task.depends_on):
        raise HTTPException(status_code=400, detail="Dependency already exists")

    if await _has_cycle(session, task_id, body.depends_on_id):
        raise HTTPException(
            status_code=400,
            detail=f"Adding dependency {body.depends_on_id} would create a cycle",
        )

    task.depends_on.append(dep)
    await _enforce_blocking_on_dependency_add(session, task, dep)
    await session.commit()
    await session.refresh(task)
    task = await _load_task(session, task.id)
    return task_to_response(task)


@router.delete("/{task_id}/dependencies/{depends_on_id}", response_model=TaskResponse)
async def remove_dependency(
    task_id: str,
    depends_on_id: str,
    session: AsyncSession = Depends(get_session),
):
    task = await _load_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    dep = next((d for d in task.depends_on if d.id == depends_on_id), None)
    if not dep:
        raise HTTPException(status_code=404, detail="Dependency not found")

    task.depends_on.remove(dep)
    await _check_and_update_blocked(session, task)
    await session.commit()
    await session.refresh(task)
    task = await _load_task(session, task.id)
    return task_to_response(task)
