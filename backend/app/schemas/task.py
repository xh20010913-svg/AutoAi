from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "todo"
    priority: str = "medium"
    assignee: str = ""
    position: int = 0


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    position: Optional[int] = None


class TaskStatusUpdate(BaseModel):
    status: str
    position: Optional[int] = None


class TaskReorder(BaseModel):
    task_ids: list[str]


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    priority: str
    assignee: str
    project_id: Optional[str]
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
