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
    blocked_reason: str = ""
    depends_on_ids: list[str] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    position: Optional[int] = None
    blocked_reason: Optional[str] = None


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
    blocked_reason: str = ""
    created_at: datetime
    updated_at: datetime
    depends_on_ids: list[str] = []
    depended_by_ids: list[str] = []

    model_config = {"from_attributes": True}


class DependencyAdd(BaseModel):
    depends_on_id: str


class DependencyRemove(BaseModel):
    depends_on_id: str


class GraphNode(BaseModel):
    id: str
    title: str
    status: str


class GraphEdge(BaseModel):
    source: str
    target: str


class DependencyGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
