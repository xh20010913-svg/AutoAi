from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.project import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    theme: Mapped[str] = mapped_column(String, nullable=False, default="auto")
    language: Mapped[str] = mapped_column(String, nullable=False, default="zh")
    notification_enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    dashboard_layout: Mapped[Optional[str]] = mapped_column(String, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
