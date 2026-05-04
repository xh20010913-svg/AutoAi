from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.project import Agent
from app.schemas.agent import AgentResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/status/all", response_model=list[AgentResponse])
async def list_agents_status(
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Agent))
    return result.scalars().all()


@router.get("/{agent_id}/status", response_model=AgentResponse)
async def get_agent_status(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
