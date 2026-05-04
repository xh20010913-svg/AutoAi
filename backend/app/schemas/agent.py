from pydantic import BaseModel


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    status: str
    model: str
    completed_tasks: int
    current_task_id: str | None
    active_tasks: int

    model_config = {"from_attributes": True}
