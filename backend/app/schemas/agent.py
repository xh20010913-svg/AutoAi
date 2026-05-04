from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    name: str
    role: str = "backend"
    skills: list[str] = []
    max_concurrent_tasks: int = 3
    success_rate: float = 1.0
    model: str = ""


class AgentUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    skills: list[str] | None = None
    status: str | None = None
    max_concurrent_tasks: int | None = None
    success_rate: float | None = None
    model: str | None = None


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    skills: list[str]
    status: str
    max_concurrent_tasks: int
    success_rate: float
    model: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
