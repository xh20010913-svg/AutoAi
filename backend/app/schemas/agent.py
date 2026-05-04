from datetime import datetime

from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str
    role: str = "backend"
    model: str = ""
    provider_id: str | None = None
    system_prompt: str = ""


class AgentUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    model: str | None = None
    provider_id: str | None = None
    status: str | None = None
    system_prompt: str | None = None


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    model: str
    provider_id: str | None
    status: str
    system_prompt: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
