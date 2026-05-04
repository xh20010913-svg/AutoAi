import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.config import settings
from app.main import app


# ── App-level tests (exercises lifespan + real app) ────


@pytest.mark.asyncio
async def test_app_lifespan():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
