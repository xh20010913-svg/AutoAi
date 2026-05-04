from datetime import datetime

from pydantic import BaseModel


class RunCreate(BaseModel):
    agent_id: str
    task_id: str | None = None
    command: str
    timeout: int = 600


class RunResponse(BaseModel):
    id: str
    agent_id: str
    task_id: str | None
    command: str
    status: str
    exit_code: int | None
    timeout: int
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RunLogResponse(BaseModel):
    id: int
    run_id: str
    seq: int
    stream: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RunListResponse(BaseModel):
    items: list[RunResponse]
    total: int
