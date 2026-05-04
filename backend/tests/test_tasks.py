import pytest
from httpx import AsyncClient


async def _create_task(client: AsyncClient, **overrides):
    payload = {"title": "Test Task", **overrides}
    resp = await client.post("/api/v1/tasks", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ── Create ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient):
    resp = await client.post("/api/v1/tasks", json={"title": "My Task"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "My Task"
    assert data["status"] == "todo"
    assert data["priority"] == "medium"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_task_full_fields(client: AsyncClient):
    resp = await client.post("/api/v1/tasks", json={
        "title": "Full Task",
        "description": "A description",
        "status": "in_progress",
        "priority": "high",
        "assignee": "alice",
        "position": 5,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["description"] == "A description"
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"
    assert data["assignee"] == "alice"
    assert data["position"] == 5


@pytest.mark.asyncio
async def test_create_task_missing_title(client: AsyncClient):
    resp = await client.post("/api/v1/tasks", json={})
    assert resp.status_code == 422


# ── List ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_tasks_empty(client: AsyncClient):
    resp = await client.get("/api/v1/tasks")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient):
    await _create_task(client, title="Task A")
    await _create_task(client, title="Task B")
    resp = await client.get("/api/v1/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_filter_by_status(client: AsyncClient):
    await _create_task(client, title="Todo", status="todo")
    await _create_task(client, title="Done", status="done")
    resp = await client.get("/api/v1/tasks", params={"status": "done"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "done"


@pytest.mark.asyncio
async def test_filter_by_status_no_match(client: AsyncClient):
    await _create_task(client)
    resp = await client.get("/api/v1/tasks", params={"status": "nonexistent"})
    assert resp.status_code == 200
    assert resp.json() == []


# ── Get ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.get(f"/api/v1/tasks/{task['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == task["id"]


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/tasks/nonexistent-id")
    assert resp.status_code == 404


# ── Update ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.put(f"/api/v1/tasks/{task['id']}", json={"title": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_update_task_partial(client: AsyncClient):
    task = await _create_task(client, title="Original", description="Desc")
    resp = await client.put(f"/api/v1/tasks/{task['id']}", json={"priority": "high"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["priority"] == "high"
    assert data["title"] == "Original"


@pytest.mark.asyncio
async def test_update_task_not_found(client: AsyncClient):
    resp = await client.put("/api/v1/tasks/nonexistent-id", json={"title": "X"})
    assert resp.status_code == 404


# ── Delete ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.delete(f"/api/v1/tasks/{task['id']}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/tasks/{task['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_not_found(client: AsyncClient):
    resp = await client.delete("/api/v1/tasks/nonexistent-id")
    assert resp.status_code == 404


# ── Status patch ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_status(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.patch(f"/api/v1/tasks/{task['id']}/status", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


@pytest.mark.asyncio
async def test_update_status_with_position(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.patch(f"/api/v1/tasks/{task['id']}/status", json={"status": "done", "position": 99})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert data["position"] == 99


@pytest.mark.asyncio
async def test_update_status_not_found(client: AsyncClient):
    resp = await client.patch("/api/v1/tasks/nonexistent-id/status", json={"status": "done"})
    assert resp.status_code == 404


# ── Reorder ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reorder_tasks(client: AsyncClient):
    t1 = await _create_task(client, title="A")
    t2 = await _create_task(client, title="B")
    resp = await client.post("/api/v1/tasks/reorder", json={"task_ids": [t2["id"], t1["id"]]})
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["id"] == t2["id"]
    assert data[1]["id"] == t1["id"]


@pytest.mark.asyncio
async def test_reorder_tasks_not_found(client: AsyncClient):
    resp = await client.post("/api/v1/tasks/reorder", json={"task_ids": ["nonexistent-id"]})
    assert resp.status_code == 404
