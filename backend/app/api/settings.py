from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.settings import UserSettings
from app.models.user import User
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


DEFAULTS = {
    "theme": "auto",
    "language": "zh",
    "notification_enabled": True,
    "dashboard_layout": None,
}


@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    settings = await session.get(UserSettings, current_user.id)
    if not settings:
        settings = UserSettings(user_id=current_user.id, **DEFAULTS)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    return settings


@router.put("", response_model=SettingsResponse)
async def update_settings(
    body: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    settings = await session.get(UserSettings, current_user.id)
    if not settings:
        settings = UserSettings(user_id=current_user.id, **DEFAULTS)
        session.add(settings)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)

    settings.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(settings)
    return settings
