from datetime import datetime

from pydantic import BaseModel


class ProviderCreate(BaseModel):
    name: str
    type: str
    base_url: str
    api_key: str = ""


class ProviderUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    base_url: str | None = None
    api_key: str | None = None


class ProviderResponse(BaseModel):
    id: str
    name: str
    type: str
    base_url: str
    api_key: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HealthCheckResponse(BaseModel):
    provider_id: str
    provider_name: str
    status: str
    detail: str = ""
