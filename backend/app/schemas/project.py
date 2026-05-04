from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str


class ProjectUpdate(BaseModel):
    name: str


class ProjectResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class AgentCreate(BaseModel):
    name: str


class AgentUpdate(BaseModel):
    name: str


class AgentResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
