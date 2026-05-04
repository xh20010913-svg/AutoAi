from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.project import Agent, Task
from app.schemas.agent import (
    AgentCreate,
    AgentResponse,
    AgentUpdate,
    TaskAssign,
    TaskUnassign,
)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Agent).order_by(Agent.id))
    return result.scalars().all()


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(
    body: AgentCreate,
    session: AsyncSession = Depends(get_session),
):
    agent = Agent(**body.model_dump())
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    body: AgentUpdate,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)
    await session.commit()
    await session.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: int,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    # Unassign all tasks assigned to this agent
    stmt = select(Task).where(Task.assignee_id == agent_id)
    result = await session.execute(stmt)
    for task in result.scalars().all():
        task.assignee_id = None
        task.assignee = ""
    await session.delete(agent)
    await session.commit()


@router.post("/assign", response_model=dict)
async def assign_task(
    body: TaskAssign,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, body.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    task = await session.get(Task, body.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check if already assigned to this agent
    if task.assignee_id == body.agent_id:
        return {"message": "Task already assigned to this agent", "task_id": task.id, "agent_id": agent.id}

    # If task was previously assigned to another agent, decrement their count
    if task.assignee_id is not None:
        prev_agent = await session.get(Agent, task.assignee_id)
        if prev_agent and prev_agent.active_tasks > 0:
            prev_agent.active_tasks -= 1
            if prev_agent.active_tasks == 0:
                prev_agent.status = "idle"

    task.assignee_id = agent.id
    task.assignee = agent.name
    agent.active_tasks += 1
    agent.status = "working"

    await session.commit()
    return {"message": "Task assigned", "task_id": task.id, "agent_id": agent.id}


@router.post("/unassign", response_model=dict)
async def unassign_task(
    body: TaskUnassign,
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(Task, body.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.assignee_id is None:
        return {"message": "Task is not assigned", "task_id": task.id}

    agent = await session.get(Agent, task.assignee_id)
    if agent and agent.active_tasks > 0:
        agent.active_tasks -= 1
        if agent.active_tasks == 0:
            agent.status = "idle"

    task.assignee_id = None
    task.assignee = ""

    await session.commit()
    return {"message": "Task unassigned", "task_id": task.id}
