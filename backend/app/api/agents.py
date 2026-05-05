from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.websocket import manager
from app.database import get_session
from app.models.project import Agent
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Agent).order_by(Agent.created_at))
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
    await manager.broadcast("agent_status_change", AgentResponse.model_validate(agent).model_dump())
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
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
    await manager.broadcast("agent_status_change", AgentResponse.model_validate(agent).model_dump())
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent_data = AgentResponse.model_validate(agent).model_dump()
    await session.delete(agent)
    await session.commit()
    await manager.broadcast("agent_status_change", {**agent_data, "status": "deleted"})
