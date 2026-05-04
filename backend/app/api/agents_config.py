from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.agent import AgentConfig, AgentRole, RoleTemplate
from app.models.project import Agent
from app.schemas.agent import (
    AgentConfigResponse,
    AgentConfigUpdate,
    AgentRoleBind,
    AgentRoleResponse,
    RoleTemplateCreate,
    RoleTemplateResponse,
)

router = APIRouter(prefix="/agents", tags=["agents"])


# --- Agent Config ---

@router.get("/{agent_id}/config", response_model=AgentConfigResponse)
async def get_agent_config(agent_id: str, session: AsyncSession = Depends(get_session)):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    stmt = select(AgentConfig).where(AgentConfig.agent_id == agent_id)
    result = await session.execute(stmt)
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")
    return config


@router.put("/{agent_id}/config", response_model=AgentConfigResponse)
async def update_agent_config(
    agent_id: str,
    body: AgentConfigUpdate,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    stmt = select(AgentConfig).where(AgentConfig.agent_id == agent_id)
    result = await session.execute(stmt)
    config = result.scalar_one_or_none()
    if not config:
        config = AgentConfig(agent_id=agent_id)
        session.add(config)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    await session.commit()
    await session.refresh(config)
    return config


# --- Role Templates ---

roles_router = APIRouter(prefix="/roles", tags=["roles"])


@roles_router.get("", response_model=list[RoleTemplateResponse])
async def list_roles(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(RoleTemplate))
    return result.scalars().all()


@roles_router.post("", response_model=RoleTemplateResponse, status_code=201)
async def create_role(body: RoleTemplateCreate, session: AsyncSession = Depends(get_session)):
    role = RoleTemplate(**body.model_dump())
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role


@roles_router.get("/{role_id}", response_model=RoleTemplateResponse)
async def get_role(role_id: str, session: AsyncSession = Depends(get_session)):
    role = await session.get(RoleTemplate, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role template not found")
    return role


@roles_router.put("/{role_id}", response_model=RoleTemplateResponse)
async def update_role(
    role_id: str,
    body: RoleTemplateCreate,
    session: AsyncSession = Depends(get_session),
):
    role = await session.get(RoleTemplate, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role template not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    await session.commit()
    await session.refresh(role)
    return role


@roles_router.delete("/{role_id}", status_code=204)
async def delete_role(role_id: str, session: AsyncSession = Depends(get_session)):
    role = await session.get(RoleTemplate, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role template not found")
    await session.delete(role)
    await session.commit()


# --- Agent Role Binding ---

@router.get("/{agent_id}/role", response_model=AgentRoleResponse)
async def get_agent_role(agent_id: str, session: AsyncSession = Depends(get_session)):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    stmt = select(AgentRole).where(AgentRole.agent_id == agent_id).options(selectinload(AgentRole.role))
    result = await session.execute(stmt)
    agent_role = result.scalar_one_or_none()
    if not agent_role:
        raise HTTPException(status_code=404, detail="Agent has no bound role")
    return agent_role


@router.put("/{agent_id}/role", response_model=AgentRoleResponse)
async def bind_agent_role(
    agent_id: str,
    body: AgentRoleBind,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    role = await session.get(RoleTemplate, body.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role template not found")
    stmt = select(AgentRole).where(AgentRole.agent_id == agent_id)
    result = await session.execute(stmt)
    agent_role = result.scalar_one_or_none()
    if not agent_role:
        agent_role = AgentRole(agent_id=agent_id, role_id=body.role_id)
        session.add(agent_role)
    else:
        agent_role.role_id = body.role_id
    await session.commit()
    stmt = select(AgentRole).where(AgentRole.agent_id == agent_id).options(selectinload(AgentRole.role))
    result = await session.execute(stmt)
    return result.scalar_one()
