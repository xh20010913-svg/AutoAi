from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TaskAssign(BaseModel):
    task_id: str


class AgentTaskResponse(BaseModel):
    id: str
    agent_id: int
    task_id: str
    assigned_at: datetime

    model_config = {"from_attributes": True}


class AgentStatusResponse(BaseModel):
    agent_id: int
    agent_name: str
    status: str
    current_task_id: Optional[str]
    active_task_count: int


class AgentStatusOverview(BaseModel):
    agents: List[AgentStatusResponse]
