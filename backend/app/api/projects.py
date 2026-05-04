from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project))
    return result.scalars().all()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(body: ProjectCreate, session: AsyncSession = Depends(get_session)):
    project = Project(name=body.name)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, session: AsyncSession = Depends(get_session)):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, body: ProjectUpdate, session: AsyncSession = Depends(get_session)):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.name = body.name
    await session.commit()
    await session.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, session: AsyncSession = Depends(get_session)):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.delete(project)
    await session.commit()
