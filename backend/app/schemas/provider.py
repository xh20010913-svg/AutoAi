from datetime import datetime

from pydantic import BaseModel


# ── Provider ────────────────────────────────────────────────────────────

class ProviderCreate(BaseModel):
    name: str
    base_url: str = ""
    api_type: str = "openai"
    enabled: bool = True


class ProviderUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    api_type: str | None = None
    enabled: bool | None = None


class ProviderResponse(BaseModel):
    id: str
    name: str
    base_url: str
    api_type: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Model ───────────────────────────────────────────────────────────────

class ModelCreate(BaseModel):
    name: str
    model_id: str
    context_window: int = 4096
    max_tokens: int = 4096
    enabled: bool = True


class ModelResponse(BaseModel):
    id: str
    provider_id: str
    name: str
    model_id: str
    context_window: int
    max_tokens: int
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}
