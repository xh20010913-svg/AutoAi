import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.database import get_session
from app.models.project import Base

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
TestingSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    from fastapi import FastAPI

    test_app = FastAPI()

    async def override_get_session():
        async with TestingSession() as session:
            yield session

    test_app.include_router(api_router)
    test_app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as c:
        yield c


async def _create_task(client: AsyncClient, **overrides):
    payload = {"title": "Test Task", **overrides}
    resp = await client.post("/api/v1/tasks", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ── POST /api/v1/tasks ──


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient):
    resp = await client.post("/api/v1/tasks", json={"title": "My Task"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "My Task"
    assert data["status"] == "todo"
    assert data["priority"] == "medium"
    assert data["description"] == ""
    assert data["position"] == 0
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_task_with_all_fields(client: AsyncClient):
    payload = {
        "title": "Full Task",
        "description": "Detailed description",
        "status": "in_progress",
        "priority": "high",
        "assignee": "agent-1",
        "position": 5,
    }
    resp = await client.post("/api/v1/tasks", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Full Task"
    assert data["description"] == "Detailed description"
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"
    assert data["assignee"] == "agent-1"
    assert data["position"] == 5


@pytest.mark.asyncio
async def test_create_task_missing_title(client: AsyncClient):
    resp = await client.post("/api/v1/tasks", json={})
    assert resp.status_code == 422


# ── GET /api/v1/tasks ──


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
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_tasks_filter_by_status(client: AsyncClient):
    await _create_task(client, title="Todo", status="todo")
    await _create_task(client, title="In Progress", status="in_progress")
    await _create_task(client, title="Done", status="done")
    resp = await client.get("/api/v1/tasks", params={"status": "in_progress"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "in_progress"
    assert data[0]["title"] == "In Progress"


@pytest.mark.asyncio
async def test_list_tasks_filter_no_match(client: AsyncClient):
    await _create_task(client, title="Todo", status="todo")
    resp = await client.get("/api/v1/tasks", params={"status": "blocked"})
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_tasks_ordered_by_position(client: AsyncClient):
    await _create_task(client, title="Third", position=2)
    await _create_task(client, title="First", position=0)
    await _create_task(client, title="Second", position=1)
    resp = await client.get("/api/v1/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert [t["title"] for t in data] == ["First", "Second", "Third"]


# ── GET /api/v1/tasks/:id ──


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.get(f"/api/v1/tasks/{task['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == task["id"]
    assert resp.json()["title"] == task["title"]


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/tasks/nonexistent-id")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Task not found"


# ── PUT /api/v1/tasks/:id ──


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.put(f"/api/v1/tasks/{task['id']}", json={"title": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_update_task_multiple_fields(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.put(
        f"/api/v1/tasks/{task['id']}",
        json={"title": "New Title", "priority": "high", "description": "New desc"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "New Title"
    assert data["priority"] == "high"
    assert data["description"] == "New desc"


@pytest.mark.asyncio
async def test_update_task_not_found(client: AsyncClient):
    resp = await client.put("/api/v1/tasks/nonexistent-id", json={"title": "X"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_task_partial(client: AsyncClient):
    task = await _create_task(client, title="Original", priority="low")
    resp = await client.put(f"/api/v1/tasks/{task['id']}", json={"priority": "high"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Original"
    assert data["priority"] == "high"


# ── DELETE /api/v1/tasks/:id ──


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


@pytest.mark.asyncio
async def test_delete_task_verify_removed_from_list(client: AsyncClient):
    t1 = await _create_task(client, title="Keep")
    t2 = await _create_task(client, title="Delete")
    await client.delete(f"/api/v1/tasks/{t2['id']}")
    resp = await client.get("/api/v1/tasks")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == t1["id"]


# ── PATCH /api/v1/tasks/:id/status ──


@pytest.mark.asyncio
async def test_update_status(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.patch(f"/api/v1/tasks/{task['id']}/status", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


@pytest.mark.asyncio
async def test_update_status_with_position(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.patch(
        f"/api/v1/tasks/{task['id']}/status",
        json={"status": "in_progress", "position": 3},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "in_progress"
    assert data["position"] == 3


@pytest.mark.asyncio
async def test_update_status_not_found(client: AsyncClient):
    resp = await client.patch("/api/v1/tasks/nonexistent-id/status", json={"status": "done"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_drag_status_transition(client: AsyncClient):
    task = await _create_task(client)
    # todo -> in_progress -> in_review -> done
    for status in ["in_progress", "in_review", "done"]:
        resp = await client.patch(f"/api/v1/tasks/{task['id']}/status", json={"status": status})
        assert resp.status_code == 200
        assert resp.json()["status"] == status


# ── POST /api/v1/tasks/reorder ──


@pytest.mark.asyncio
async def test_reorder_tasks(client: AsyncClient):
    t1 = await _create_task(client, title="A")
    t2 = await _create_task(client, title="B")
    t3 = await _create_task(client, title="C")
    resp = await client.post(
        "/api/v1/tasks/reorder",
        json={"task_ids": [t3["id"], t1["id"], t2["id"]]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["id"] == t3["id"]
    assert data[0]["position"] == 0
    assert data[1]["id"] == t1["id"]
    assert data[1]["position"] == 1
    assert data[2]["id"] == t2["id"]
    assert data[2]["position"] == 2


@pytest.mark.asyncio
async def test_reorder_tasks_not_found(client: AsyncClient):
    t1 = await _create_task(client, title="A")
    resp = await client.post(
        "/api/v1/tasks/reorder",
        json={"task_ids": [t1["id"], "nonexistent-id"]},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_reorder_single_task(client: AsyncClient):
    t1 = await _create_task(client, title="Solo")
    resp = await client.post("/api/v1/tasks/reorder", json={"task_ids": [t1["id"]]})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_reorder_empty_list(client: AsyncClient):
    resp = await client.post("/api/v1/tasks/reorder", json={"task_ids": []})
    assert resp.status_code == 200
    assert resp.json() == []
