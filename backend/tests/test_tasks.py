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
async def test_list_tasks(client: AsyncClient):
    await _create_task(client, title="Task A")
    await _create_task(client, title="Task B")
    resp = await client.get("/api/v1/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.get(f"/api/v1/tasks/{task['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == task["id"]


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.put(f"/api/v1/tasks/{task['id']}", json={"title": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.delete(f"/api/v1/tasks/{task['id']}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/tasks/{task['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_filter_by_status(client: AsyncClient):
    await _create_task(client, title="Todo", status="todo")
    await _create_task(client, title="In Progress", status="in_progress")
    resp = await client.get("/api/v1/tasks", params={"status": "in_progress"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "in_progress"


@pytest.mark.asyncio
async def test_update_status(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.patch(f"/api/v1/tasks/{task['id']}/status", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


@pytest.mark.asyncio
async def test_reorder_tasks(client: AsyncClient):
    t1 = await _create_task(client, title="A")
    t2 = await _create_task(client, title="B")
    resp = await client.post("/api/v1/tasks/reorder", json={"task_ids": [t2["id"], t1["id"]]})
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["id"] == t2["id"]
    assert data[1]["id"] == t1["id"]


# ── DAG / Dependency tests ──


@pytest.mark.asyncio
async def test_create_task_with_dependencies(client: AsyncClient):
    t1 = await _create_task(client, title="Dep A")
    t2 = await _create_task(client, title="Dep B", depends_on_ids=[t1["id"]])
    assert t2["status"] == "blocked"
    assert t1["id"] in t2["depends_on_ids"]
    # Re-fetch t1 to get updated depended_by_ids
    resp = await client.get(f"/api/v1/tasks/{t1['id']}")
    t1_refreshed = resp.json()
    assert t2["id"] in t1_refreshed["depended_by_ids"]


@pytest.mark.asyncio
async def test_dependency_graph(client: AsyncClient):
    t1 = await _create_task(client, title="A")
    t2 = await _create_task(client, title="B", depends_on_ids=[t1["id"]])
    resp = await client.get("/api/v1/tasks/dependency-graph")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    edge = data["edges"][0]
    assert edge["source"] == t1["id"]
    assert edge["target"] == t2["id"]


@pytest.mark.asyncio
async def test_cycle_detection(client: AsyncClient):
    t1 = await _create_task(client, title="A")
    t2 = await _create_task(client, title="B", depends_on_ids=[t1["id"]])
    # A -> B, trying B -> A should fail
    resp = await client.post(f"/api/v1/tasks/{t1['id']}/dependencies", json={"depends_on_id": t2["id"]})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_self_dependency_rejected(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.post(f"/api/v1/tasks/{task['id']}/dependencies", json={"depends_on_id": task["id"]})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_duplicate_dependency_rejected(client: AsyncClient):
    t1 = await _create_task(client, title="A")
    t2 = await _create_task(client, title="B", depends_on_ids=[t1["id"]])
    resp = await client.post(f"/api/v1/tasks/{t2['id']}/dependencies", json={"depends_on_id": t1["id"]})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_add_dependency_blocks_task(client: AsyncClient):
    t1 = await _create_task(client, title="A")
    t2 = await _create_task(client, title="B")
    assert t2["status"] == "todo"
    resp = await client.post(f"/api/v1/tasks/{t2['id']}/dependencies", json={"depends_on_id": t1["id"]})
    assert resp.status_code == 201
    updated = resp.json()
    assert updated["status"] == "blocked"
    assert updated["blocked_reason"] != ""


@pytest.mark.asyncio
async def test_auto_unblock_on_dependency_completion(client: AsyncClient):
    t1 = await _create_task(client, title="A")
    t2 = await _create_task(client, title="B", depends_on_ids=[t1["id"]])
    assert t2["status"] == "blocked"
    # Complete t1
    resp = await client.patch(f"/api/v1/tasks/{t1['id']}/status", json={"status": "done"})
    assert resp.status_code == 200
    # t2 should now be unblocked
    resp = await client.get(f"/api/v1/tasks/{t2['id']}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "todo"
    assert resp.json()["blocked_reason"] == ""


@pytest.mark.asyncio
async def test_remove_dependency_unblocks_task(client: AsyncClient):
    t1 = await _create_task(client, title="A")
    t2 = await _create_task(client, title="B", depends_on_ids=[t1["id"]])
    assert t2["status"] == "blocked"
    resp = await client.delete(f"/api/v1/tasks/{t2['id']}/dependencies/{t1['id']}")
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["status"] == "todo"
    assert updated["blocked_reason"] == ""


@pytest.mark.asyncio
async def test_blocked_status_guards_activation(client: AsyncClient):
    t1 = await _create_task(client, title="A")
    t2 = await _create_task(client, title="B", depends_on_ids=[t1["id"]])
    assert t2["status"] == "blocked"
    # Try to move blocked task to in_progress
    resp = await client.patch(f"/api/v1/tasks/{t2['id']}/status", json={"status": "in_progress"})
    assert resp.status_code == 200
    # Should stay blocked because dependencies are not done
    assert resp.json()["status"] == "blocked"


@pytest.mark.asyncio
async def test_parallel_dependencies(client: AsyncClient):
    t1 = await _create_task(client, title="A")
    t2 = await _create_task(client, title="B")
    # C depends on both A and B
    resp = await client.post("/api/v1/tasks", json={
        "title": "C", "depends_on_ids": [t1["id"], t2["id"]]
    })
    assert resp.status_code == 201
    t3 = resp.json()
    assert t3["status"] == "blocked"
    assert len(t3["depends_on_ids"]) == 2
    # Complete only A
    await client.patch(f"/api/v1/tasks/{t1['id']}/status", json={"status": "done"})
    resp = await client.get(f"/api/v1/tasks/{t3['id']}")
    assert resp.json()["status"] == "blocked"  # Still blocked by B
    # Complete B
    await client.patch(f"/api/v1/tasks/{t2['id']}/status", json={"status": "done"})
    resp = await client.get(f"/api/v1/tasks/{t3['id']}")
    assert resp.json()["status"] == "todo"


@pytest.mark.asyncio
async def test_dependency_nonexistent_task(client: AsyncClient):
    resp = await client.post("/api/v1/tasks", json={
        "title": "Task", "depends_on_ids": ["nonexistent-id"]
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_blocked_reason_on_status_attempt(client: AsyncClient):
    t1 = await _create_task(client, title="Blocker")
    t2 = await _create_task(client, title="Blocked Task", depends_on_ids=[t1["id"]])
    assert t2["blocked_reason"] != ""
    # Try to move to in_progress — should stay blocked with reason
    resp = await client.patch(f"/api/v1/tasks/{t2['id']}/status", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "blocked"
    assert "Blocker" in resp.json()["blocked_reason"]


@pytest.mark.asyncio
async def test_done_task_can_have_incomplete_deps(client: AsyncClient):
    t1 = await _create_task(client, title="A")
    # B is done and depends on A (which is todo) — should remain done
    resp = await client.post("/api/v1/tasks", json={
        "title": "B", "status": "done", "depends_on_ids": [t1["id"]]
    })
    assert resp.status_code == 201
    t2 = resp.json()
    assert t2["status"] == "done"  # Already done, should not be blocked
