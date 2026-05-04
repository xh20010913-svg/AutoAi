from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str
    role: str = "backend"
    model: str = ""
    provider: str = ""
    api_key_env: str = ""


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    api_key_env: Optional[str] = None
    status: Optional[str] = None
    current_task_id: Optional[str] = None


class AgentStatusUpdate(BaseModel):
    status: str
    current_task_id: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    model: str
    provider: str
    api_key_env: str
    status: str
    current_task_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
