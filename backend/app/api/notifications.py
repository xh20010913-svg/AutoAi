from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Total count
    count_stmt = select(func.count()).select_from(Notification).where(Notification.user_id == user.id)
    total = (await session.execute(count_stmt)).scalar_one()

    # Paginated items, newest first
    stmt = (
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    items = result.scalars().all()

    return NotificationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    notification = await session.get(Notification, notification_id)
    if not notification or notification.user_id != user.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    await session.commit()
    await session.refresh(notification)
    return notification


@router.post("/read-all")
async def mark_all_read(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        update(Notification)
        .where(Notification.user_id == user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await session.execute(stmt)
    await session.commit()
    return {"message": "All notifications marked as read"}


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user.id, Notification.is_read == False)
    )
    count = (await session.execute(stmt)).scalar_one()
    return UnreadCountResponse(unread_count=count)
