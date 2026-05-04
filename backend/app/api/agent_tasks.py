from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.project import Agent, AgentTask, Task
from app.schemas.agent_task import (
    AgentStatusOverview,
    AgentStatusResponse,
    AgentTaskResponse,
    TaskAssign,
)

router = APIRouter(prefix="/agents", tags=["agents"])


def _compute_agent_status(agent_tasks: List[AgentTask], tasks: Dict[str, Task]) -> str:
    if not agent_tasks:
        return "idle"
    for at in agent_tasks:
        task = tasks.get(at.task_id)
        if task and task.status == "blocked":
            return "blocked"
    return "working"


@router.post("/{agent_id}/assign", response_model=AgentTaskResponse, status_code=201)
async def assign_task(
    agent_id: int,
    body: TaskAssign,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    task = await session.get(Task, body.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    assignment = AgentTask(agent_id=agent_id, task_id=body.task_id)
    session.add(assignment)
    await session.commit()
    await session.refresh(assignment)
    return assignment


@router.delete("/{agent_id}/assign/{task_id}", status_code=204)
async def unassign_task(
    agent_id: int,
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(AgentTask).where(
        AgentTask.agent_id == agent_id, AgentTask.task_id == task_id
    )
    result = await session.execute(stmt)
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await session.delete(assignment)
    await session.commit()


@router.get("/{agent_id}/tasks", response_model=List[AgentTaskResponse])
async def get_agent_tasks(
    agent_id: int,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    stmt = select(AgentTask).where(AgentTask.agent_id == agent_id)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/status/all", response_model=AgentStatusOverview)
async def get_all_agent_status(
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Agent))
    agents = list(result.scalars().all())
    statuses: list = []
    for agent in agents:
        stmt = select(AgentTask).where(AgentTask.agent_id == agent.id)
        at_result = await session.execute(stmt)
        agent_tasks = list(at_result.scalars().all())
        task_ids = [at.task_id for at in agent_tasks]
        tasks_map = {}
        if task_ids:
            for tid in task_ids:
                t = await session.get(Task, tid)
                if t:
                    tasks_map[tid] = t
        status = _compute_agent_status(agent_tasks, tasks_map)
        current_task_id = agent_tasks[0].task_id if agent_tasks else None
        statuses.append(
            AgentStatusResponse(
                agent_id=agent.id,
                agent_name=agent.name,
                status=status,
                current_task_id=current_task_id,
                active_task_count=len(agent_tasks),
            )
        )
    return AgentStatusOverview(agents=statuses)


@router.get("/{agent_id}/status", response_model=AgentStatusResponse)
async def get_agent_status(
    agent_id: int,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    stmt = select(AgentTask).where(AgentTask.agent_id == agent_id)
    result = await session.execute(stmt)
    agent_tasks = list(result.scalars().all())
    task_ids = [at.task_id for at in agent_tasks]
    tasks_map = {}
    if task_ids:
        for tid in task_ids:
            t = await session.get(Task, tid)
            if t:
                tasks_map[tid] = t
    status = _compute_agent_status(agent_tasks, tasks_map)
    current_task_id = agent_tasks[0].task_id if agent_tasks else None
    return AgentStatusResponse(
        agent_id=agent.id,
        agent_name=agent.name,
        status=status,
        current_task_id=current_task_id,
        active_task_count=len(agent_tasks),
    )
