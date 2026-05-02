from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="todo")
    priority: Mapped[str] = mapped_column(String(16), default="medium")
    assignee: Mapped[str] = mapped_column(String(128), default="")
    created_at: Mapped[str] = mapped_column(String(64), default=_utc_now)
    updated_at: Mapped[str] = mapped_column(String(64), default=_utc_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "assignee": self.assignee,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class HelpRequest(Base):
    __tablename__ = "help_requests"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="open")
    severity: Mapped[str] = mapped_column(String(16), default="blocking")
    task_id: Mapped[str] = mapped_column(String(32), default="")
    role_id: Mapped[str] = mapped_column(String(64), default="")
    session_id: Mapped[str] = mapped_column(String(128), default="")
    answer: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String(64), default=_utc_now)
    updated_at: Mapped[str] = mapped_column(String(64), default=_utc_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "detail": self.detail,
            "status": self.status,
            "severity": self.severity,
            "task_id": self.task_id,
            "role_id": self.role_id,
            "session_id": self.session_id,
            "answer": self.answer,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(128), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    provider: Mapped[str] = mapped_column(String(64), default="default")
    model: Mapped[str] = mapped_column(String(128), default="")
    model_tier: Mapped[str] = mapped_column(String(16), default="medium")
    cost_tier: Mapped[str] = mapped_column(String(16), default="medium")
    api_key_env: Mapped[str] = mapped_column(String(128), default="")
    token_budget_json: Mapped[str] = mapped_column(Text, default="{}")
    task_types_json: Mapped[str] = mapped_column(Text, default="[]")
    tools_json: Mapped[str] = mapped_column(Text, default="[]")
    authority_json: Mapped[str] = mapped_column(Text, default="{}")
    scope_json: Mapped[str] = mapped_column(Text, default="{}")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "description": self.description,
            "provider": self.provider,
            "model": self.model,
            "model_tier": self.model_tier,
            "cost_tier": self.cost_tier,
            "api_key_env": self.api_key_env,
            "token_budget": json.loads(self.token_budget_json),
            "task_types": json.loads(self.task_types_json),
            "tools": json.loads(self.tools_json),
            "authority": json.loads(self.authority_json),
            "scope": json.loads(self.scope_json),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Role:
        return cls(
            id=data["id"],
            display_name=data.get("display_name", ""),
            description=data.get("description", ""),
            provider=data.get("provider", "default"),
            model=data.get("model", ""),
            model_tier=data.get("model_tier", "medium"),
            cost_tier=data.get("cost_tier", "medium"),
            api_key_env=data.get("api_key_env", ""),
            token_budget_json=json.dumps(data.get("token_budget", {}), ensure_ascii=False),
            task_types_json=json.dumps(data.get("task_types", []), ensure_ascii=False),
            tools_json=json.dumps(data.get("tools", []), ensure_ascii=False),
            authority_json=json.dumps(data.get("authority", {}), ensure_ascii=False),
            scope_json=json.dumps(data.get("scope", {}), ensure_ascii=False),
        )


class RoleSecret(Base):
    __tablename__ = "role_secrets"

    role_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    api_key: Mapped[str] = mapped_column(Text, default="")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    time: Mapped[str] = mapped_column(String(64), default=_utc_now)
    type: Mapped[str] = mapped_column(String(32), default="")
    sender: Mapped[str] = mapped_column(String(64), default="")
    recipient: Mapped[str] = mapped_column(String(64), default="")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "time": self.time,
            "type": self.type,
            "from": self.sender,
            "to": self.recipient,
            "payload": json.loads(self.payload_json),
        }


class ConfigKV(Base):
    __tablename__ = "config"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")


class RunStateRow(Base):
    __tablename__ = "run_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    next_session: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[str] = mapped_column(String(64), default=_utc_now)
    updated_at: Mapped[str] = mapped_column(String(64), default=_utc_now)
    last_status: Mapped[str] = mapped_column(String(32), default="never-run")
    last_session_id: Mapped[str] = mapped_column(String(128), default="")
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
