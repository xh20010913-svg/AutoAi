from datetime import datetime

from pydantic import BaseModel


class AgentConfigResponse(BaseModel):
    id: str
    agent_id: str
    model: str
    provider: str
    api_key_env: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentConfigUpdate(BaseModel):
    model: str | None = None
    provider: str | None = None
    api_key_env: str | None = None


class RoleTemplateCreate(BaseModel):
    name: str
    description: str = ""
    budget_level: str = "medium"
    authority: str = ""
    allowed_paths: str = ""


class RoleTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    budget_level: str | None = None
    authority: str | None = None
    allowed_paths: str | None = None


class RoleTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    budget_level: str
    authority: str
    allowed_paths: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentRoleBind(BaseModel):
    role_id: str


class AgentRoleResponse(BaseModel):
    id: str
    agent_id: str
    role_id: str
    bound_at: datetime
    role: RoleTemplateResponse | None = None

    model_config = {"from_attributes": True}
