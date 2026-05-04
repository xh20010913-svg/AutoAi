from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.project import Agent
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    role: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Agent)
    if role:
        stmt = stmt.where(Agent.role == role)
    result = await session.execute(stmt)
    agents = result.scalars().all()
    return [_agent_to_response(a) for a in agents]


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(
    body: AgentCreate,
    session: AsyncSession = Depends(get_session),
):
    agent = Agent(
        name=body.name,
        role=body.role,
        skills=json.dumps(body.skills),
        max_concurrent_tasks=body.max_concurrent_tasks,
        success_rate=body.success_rate,
        model=body.model,
    )
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return _agent_to_response(agent)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _agent_to_response(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    body: AgentUpdate,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "skills" and value is not None:
            value = json.dumps(value)
        setattr(agent, field, value)
    await session.commit()
    await session.refresh(agent)
    return _agent_to_response(agent)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await session.delete(agent)
    await session.commit()


def _agent_to_response(agent: Agent) -> AgentResponse:
    """Convert Agent ORM model to response, parsing skills JSON."""
    skills = []
    try:
        skills = json.loads(agent.skills)
    except (json.JSONDecodeError, TypeError):
        pass
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        skills=skills,
        status=agent.status,
        max_concurrent_tasks=agent.max_concurrent_tasks,
        success_rate=agent.success_rate,
        model=agent.model,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )
