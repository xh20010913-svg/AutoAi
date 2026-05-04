from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.project import Agent, Project, Task

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def global_search(
    q: str = Query(..., min_length=1),
    type: str | None = Query(None, alias="type"),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    results: list[dict] = []
    remaining = limit

    if type is None or type == "task":
        stmt = select(Task).where(Task.title.ilike(pattern)).limit(remaining)
        rows = (await session.execute(stmt)).scalars().all()
        results.extend(
            {"id": t.id, "title": t.title, "type": "task", "status": t.status}
            for t in rows
        )
        remaining = limit - len(results)

    if remaining > 0 and (type is None or type == "project"):
        stmt = select(Project).where(Project.name.ilike(pattern)).limit(remaining)
        rows = (await session.execute(stmt)).scalars().all()
        results.extend(
            {"id": p.id, "name": p.name, "type": "project"} for p in rows
        )
        remaining = limit - len(results)

    if remaining > 0 and (type is None or type == "agent"):
        stmt = select(Agent).where(Agent.name.ilike(pattern)).limit(remaining)
        rows = (await session.execute(stmt)).scalars().all()
        results.extend(
            {"id": a.id, "name": a.name, "type": "agent"} for a in rows
        )

    return {"query": q, "results": results}
