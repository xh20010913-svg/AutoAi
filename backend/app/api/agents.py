from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.project import Agent
from app.schemas.project import AgentCreate, AgentResponse, AgentUpdate

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentResponse])
async def list_agents(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Agent))
    return result.scalars().all()


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(body: AgentCreate, session: AsyncSession = Depends(get_session)):
    agent = Agent(name=body.name)
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, session: AsyncSession = Depends(get_session)):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: int, body: AgentUpdate, session: AsyncSession = Depends(get_session)):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.name = body.name
    await session.commit()
    await session.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: int, session: AsyncSession = Depends(get_session)):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await session.delete(agent)
    await session.commit()
