from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.user import User
from app.ws import notification_manager


async def create_notification(
    session: AsyncSession,
    user_id: str,
    notification_type: str,
    title: str,
    content: str,
) -> Notification:
    """Create a notification and push it via WebSocket."""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        content=content,
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)

    # Push via WebSocket (fire-and-forget)
    try:
        await notification_manager.send_to_user(user_id, {
            "id": notification.id,
            "type": notification.type,
            "title": notification.title,
            "content": notification.content,
            "is_read": notification.is_read,
            "created_at": str(notification.created_at),
        })
    except Exception:
        pass

    return notification


async def find_user_id_by_username(session: AsyncSession, username: str) -> str | None:
    """Look up a user ID by username."""
    from sqlalchemy import select
    stmt = select(User.id).where(User.username == username)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
