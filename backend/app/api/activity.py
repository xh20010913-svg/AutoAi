from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.activity import ActivityLog
from app.schemas.activity import ActivityLogResponse

router = APIRouter(prefix="/activity", tags=["activity"])


async def log_activity(
    session: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: str,
    user_id: str | None = None,
    detail: dict | None = None,
):
    entry = ActivityLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        detail=detail,
    )
    session.add(entry)


@router.get("", response_model=list[ActivityLogResponse])
async def list_activity(
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(ActivityLog)
    if action:
        stmt = stmt.where(ActivityLog.action == action)
    if resource_type:
        stmt = stmt.where(ActivityLog.resource_type == resource_type)
    stmt = stmt.order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()
