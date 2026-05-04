from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "todo"
    priority: str = "medium"
    assignee: str = ""
    position: int = 0


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assignee: str | None = None
    position: int | None = None


class TaskStatusUpdate(BaseModel):
    status: str
    position: int | None = None


class TaskReorder(BaseModel):
    task_ids: list[str]


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    priority: str
    assignee: str
    project_id: str | None
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
