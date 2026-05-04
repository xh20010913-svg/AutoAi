from datetime import datetime

from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str
    role: str = "assistant"
    model: str = ""
    provider: str = ""


class AgentUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    model: str | None = None
    provider: str | None = None
    status: str | None = None


class AgentResponse(BaseModel):
    id: int
    name: str
    role: str
    model: str
    provider: str
    status: str
    active_tasks: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskAssign(BaseModel):
    task_id: str
    agent_id: int


class TaskUnassign(BaseModel):
    task_id: str
