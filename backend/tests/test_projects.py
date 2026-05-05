import pytest
from httpx import AsyncClient


async def _create_project(client: AsyncClient, **overrides):
    payload = {"name": "Test Project", **overrides}
    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ── Create ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    resp = await client.post("/api/v1/projects", json={"name": "My Project"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Project"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_project_missing_name(client: AsyncClient):
    resp = await client.post("/api/v1/projects", json={})
    assert resp.status_code == 422


# ── List ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_projects_empty(client: AsyncClient):
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    await _create_project(client, name="P1")
    await _create_project(client, name="P2")
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# ── Get ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    proj = await _create_project(client)
    resp = await client.get(f"/api/v1/projects/{proj['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == proj["id"]


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/projects/99999")
    assert resp.status_code == 404


# ── Update ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient):
    proj = await _create_project(client)
    resp = await client.put(f"/api/v1/projects/{proj['id']}", json={"name": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"


@pytest.mark.asyncio
async def test_update_project_not_found(client: AsyncClient):
    resp = await client.put("/api/v1/projects/99999", json={"name": "X"})
    assert resp.status_code == 404


# ── Delete ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    proj = await _create_project(client)
    resp = await client.delete(f"/api/v1/projects/{proj['id']}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/projects/{proj['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_found(client: AsyncClient):
    resp = await client.delete("/api/v1/projects/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_project_missing_name(client: AsyncClient):
    proj = await _create_project(client)
    resp = await client.put(f"/api/v1/projects/{proj['id']}", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_project_empty_name(client: AsyncClient):
    resp = await client.post("/api/v1/projects", json={"name": ""})
    assert resp.status_code == 201
