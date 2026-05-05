import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_not_found_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/nonexistent")
    assert resp.status_code == 404
