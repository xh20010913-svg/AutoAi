from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    owner_id: str
    status: str = "active"


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    owner_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
