import pytest
from httpx import AsyncClient


async def _create_agent(client: AsyncClient, **overrides):
    payload = {"name": "Test Agent", **overrides}
    resp = await client.post("/api/v1/agents", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ── Create ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient):
    resp = await client.post("/api/v1/agents", json={"name": "My Agent"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Agent"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_agent_missing_name(client: AsyncClient):
    resp = await client.post("/api/v1/agents", json={})
    assert resp.status_code == 422


# ── List ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_agents_empty(client: AsyncClient):
    resp = await client.get("/api/v1/agents")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient):
    await _create_agent(client, name="A1")
    await _create_agent(client, name="A2")
    resp = await client.get("/api/v1/agents")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# ── Get ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_agent(client: AsyncClient):
    agent = await _create_agent(client)
    resp = await client.get(f"/api/v1/agents/{agent['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == agent["id"]


@pytest.mark.asyncio
async def test_get_agent_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/agents/99999")
    assert resp.status_code == 404


# ── Update ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_agent(client: AsyncClient):
    agent = await _create_agent(client)
    resp = await client.put(f"/api/v1/agents/{agent['id']}", json={"name": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"


@pytest.mark.asyncio
async def test_update_agent_not_found(client: AsyncClient):
    resp = await client.put("/api/v1/agents/99999", json={"name": "X"})
    assert resp.status_code == 404


# ── Delete ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_agent(client: AsyncClient):
    agent = await _create_agent(client)
    resp = await client.delete(f"/api/v1/agents/{agent['id']}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/agents/{agent['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_agent_not_found(client: AsyncClient):
    resp = await client.delete("/api/v1/agents/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_agent_missing_name(client: AsyncClient):
    agent = await _create_agent(client)
    resp = await client.put(f"/api/v1/agents/{agent['id']}", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_agent_empty_name(client: AsyncClient):
    resp = await client.post("/api/v1/agents", json={"name": ""})
    assert resp.status_code == 201
