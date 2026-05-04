from pydantic import BaseModel


class TaskStats(BaseModel):
    total: int
    by_status: dict[str, int]


class RuntimeResponse(BaseModel):
    active_agents: int
    total_tasks: TaskStats
    cpu_usage: float
    memory_usage: float
    uptime: float
