from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.project import Base


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("agents.id"), unique=True, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False, default="gpt-4")
    provider: Mapped[str] = mapped_column(String, nullable=False, default="openai")
    api_key_env: Mapped[str] = mapped_column(String, nullable=False, default="OPENAI_API_KEY")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent: Mapped["Agent"] = relationship("Agent", back_populates="config")


class RoleTemplate(Base):
    __tablename__ = "role_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    budget_level: Mapped[str] = mapped_column(String, nullable=False, default="medium")
    authority: Mapped[str] = mapped_column(String, nullable=False, default="")
    allowed_paths: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent_roles: Mapped[list["AgentRole"]] = relationship("AgentRole", back_populates="role")


class AgentRole(Base):
    __tablename__ = "agent_roles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("agents.id"), unique=True, nullable=False)
    role_id: Mapped[str] = mapped_column(String, ForeignKey("role_templates.id"), nullable=False)
    bound_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    role: Mapped["RoleTemplate"] = relationship("RoleTemplate", back_populates="agent_roles")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="agent_role")
