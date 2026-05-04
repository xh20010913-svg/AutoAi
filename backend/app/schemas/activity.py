from datetime import datetime

from pydantic import BaseModel


class ActivityLogResponse(BaseModel):
    id: str
    user_id: str | None
    action: str
    resource_type: str
    resource_id: str
    detail: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
