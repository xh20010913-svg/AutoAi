from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    notification_enabled: Optional[bool] = None
    dashboard_layout: Optional[str] = None


class SettingsResponse(BaseModel):
    user_id: str
    theme: str
    language: str
    notification_enabled: bool
    dashboard_layout: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
