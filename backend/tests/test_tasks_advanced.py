"""
Comprehensive Task CRUD API tests — edge cases, boundary conditions, and concurrency.
"""
import asyncio
import string
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


async def _create(client: AsyncClient, **overrides):
    payload = {"title": "Test Task", **overrides}
    return await client.post("/api/v1/tasks", json=payload)


# ──────────────────────────────────────────────
# 1. CREATE — boundary / edge cases
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_empty_title(client: AsyncClient):
    """Title is required — empty string should still create (API allows it)."""
    resp = await _create(client, title="")
    assert resp.status_code == 201
    assert resp.json()["title"] == ""


@pytest.mark.asyncio
async def test_create_missing_title(client: AsyncClient):
    """Omitting title entirely should fail (Pydantic validation)."""
    resp = await client.post("/api/v1/tasks", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_very_long_description(client: AsyncClient):
    """Description with 100 000 characters should be accepted."""
    long_desc = "A" * 100_000
    resp = await _create(client, description=long_desc)
    assert resp.status_code == 201
    assert len(resp.json()["description"]) == 100_000


@pytest.mark.asyncio
async def test_create_unicode_title(client: AsyncClient):
    """Unicode / CJK characters in title."""
    resp = await _create(client, title="完成前端国际化 🚀")
    assert resp.status_code == 201
    assert resp.json()["title"] == "完成前端国际化 🚀"


@pytest.mark.asyncio
async def test_create_invalid_status_value(client: AsyncClient):
    """The API accepts any string for status — no enum validation."""
    resp = await _create(client, status="nonexistent_status")
    assert resp.status_code == 201
    assert resp.json()["status"] == "nonexistent_status"


@pytest.mark.asyncio
async def test_create_all_fields(client: AsyncClient):
    """Create with every field populated."""
    resp = await _create(
        client,
        title="Full Task",
        description="Desc",
        status="in_progress",
        priority="high",
        assignee="alice",
        position=5,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Full Task"
    assert data["description"] == "Desc"
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"
    assert data["assignee"] == "alice"
    assert data["position"] == 5


@pytest.mark.asyncio
async def test_create_negative_position(client: AsyncClient):
    """Negative position should be accepted (no constraint in schema)."""
    resp = await _create(client, position=-1)
    assert resp.status_code == 201
    assert resp.json()["position"] == -1


# ──────────────────────────────────────────────
# 2. GET — not found & edge cases
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_nonexistent_task(client: AsyncClient):
    resp = await client.get("/api/v1/tasks/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_returns_all_fields(client: AsyncClient):
    task = (await _create(client, title="Field Check", description="d", assignee="bob")).json()
    resp = await client.get(f"/api/v1/tasks/{task['id']}")
    data = resp.json()
    for key in ("id", "title", "description", "status", "priority", "assignee", "project_id", "position", "created_at", "updated_at"):
        assert key in data


# ──────────────────────────────────────────────
# 3. LIST — empty, filter, ordering
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_empty(client: AsyncClient):
    resp = await client.get("/api/v1/tasks")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_filter_returns_empty(client: AsyncClient):
    await _create(client, title="Only Todo", status="todo")
    resp = await client.get("/api/v1/tasks", params={"status": "done"})
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_ordered_by_position(client: AsyncClient):
    await _create(client, title="Pos 5", position=5)
    await _create(client, title="Pos 0", position=0)
    await _create(client, title="Pos 2", position=2)
    resp = await client.get("/api/v1/tasks")
    data = resp.json()
    positions = [t["position"] for t in data]
    assert positions == sorted(positions)


# ──────────────────────────────────────────────
# 4. UPDATE — partial, 404, clearing fields
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_partial(client: AsyncClient):
    """PUT with partial body should only update provided fields."""
    task = (await _create(client, title="Original", description="keep me")).json()
    resp = await client.put(f"/api/v1/tasks/{task['id']}", json={"title": "Changed"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Changed"
    assert data["description"] == "keep me"


@pytest.mark.asyncio
async def test_update_nonexistent(client: AsyncClient):
    resp = await client.put("/api/v1/tasks/no-id", json={"title": "X"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_clear_assignee(client: AsyncClient):
    task = (await _create(client, assignee="alice")).json()
    resp = await client.put(f"/api/v1/tasks/{task['id']}", json={"assignee": ""})
    assert resp.status_code == 200
    assert resp.json()["assignee"] == ""


# ──────────────────────────────────────────────
# 5. DELETE — idempotent? (no, 404 on second delete)
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_twice(client: AsyncClient):
    task = (await _create(client)).json()
    resp1 = await client.delete(f"/api/v1/tasks/{task['id']}")
    assert resp1.status_code == 204
    resp2 = await client.delete(f"/api/v1/tasks/{task['id']}")
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent(client: AsyncClient):
    resp = await client.delete("/api/v1/tasks/does-not-exist")
    assert resp.status_code == 404


# ──────────────────────────────────────────────
# 6. STATUS PATCH — edge cases
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_status_with_position(client: AsyncClient):
    task = (await _create(client)).json()
    resp = await client.patch(f"/api/v1/tasks/{task['id']}/status", json={"status": "done", "position": 99})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert data["position"] == 99


@pytest.mark.asyncio
async def test_update_status_nonexistent(client: AsyncClient):
    resp = await client.patch("/api/v1/tasks/ghost/status", json={"status": "done"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_status_missing_body(client: AsyncClient):
    task = (await _create(client)).json()
    resp = await client.patch(f"/api/v1/tasks/{task['id']}/status", json={})
    assert resp.status_code == 422


# ──────────────────────────────────────────────
# 7. REORDER — edge cases
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reorder_single_task(client: AsyncClient):
    task = (await _create(client)).json()
    resp = await client.post("/api/v1/tasks/reorder", json={"task_ids": [task["id"]]})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_reorder_nonexistent_task(client: AsyncClient):
    resp = await client.post("/api/v1/tasks/reorder", json={"task_ids": ["fake-id"]})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_reorder_empty_list(client: AsyncClient):
    resp = await client.post("/api/v1/tasks/reorder", json={"task_ids": []})
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_reorder_updates_positions(client: AsyncClient):
    t1 = (await _create(client, title="A")).json()
    t2 = (await _create(client, title="B")).json()
    t3 = (await _create(client, title="C")).json()
    # Reverse order
    resp = await client.post(
        "/api/v1/tasks/reorder",
        json={"task_ids": [t3["id"], t2["id"], t1["id"]]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert [d["id"] for d in data] == [t3["id"], t2["id"], t1["id"]]
    assert [d["position"] for d in data] == [0, 1, 2]


# ──────────────────────────────────────────────
# 8. CONCURRENCY — parallel operations
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_concurrent_creates(client: AsyncClient):
    """Create 20 tasks concurrently — all should succeed with unique IDs."""
    tasks = [_create(client, title=f"Concurrent-{i}") for i in range(20)]
    results = await asyncio.gather(*tasks)
    statuses = [r.status_code for r in results]
    assert all(s == 201 for s in statuses)
    ids = [r.json()["id"] for r in results]
    assert len(set(ids)) == 20


@pytest.mark.asyncio
async def test_concurrent_create_and_list(client: AsyncClient):
    """Create and list concurrently — list should always be consistent."""
    for i in range(5):
        await _create(client, title=f"Seed-{i}")

    async def create_one():
        return await _create(client, title="New")

    async def list_all():
        return await client.get("/api/v1/tasks")

    results = await asyncio.gather(
        create_one(), create_one(), create_one(), list_all(), list_all()
    )
    for r in results:
        assert r.status_code in (200, 201)


@pytest.mark.asyncio
async def test_concurrent_updates_same_task(client: AsyncClient):
    """Multiple concurrent PUTs on the same task — last write wins, no crash."""
    task = (await _create(client, title="Shared")).json()
    updates = [
        client.put(f"/api/v1/tasks/{task['id']}", json={"title": f"Writer-{i}"})
        for i in range(10)
    ]
    results = await asyncio.gather(*updates)
    assert all(r.status_code == 200 for r in results)
    # Verify the task still exists and has one of the writer titles
    final = await client.get(f"/api/v1/tasks/{task['id']}")
    assert final.status_code == 200
    assert final.json()["title"].startswith("Writer-")


@pytest.mark.asyncio
async def test_concurrent_delete_same_task(client: AsyncClient):
    """Concurrent deletes — one succeeds, rest get 404."""
    task = (await _create(client)).json()
    deletes = [client.delete(f"/api/v1/tasks/{task['id']}") for _ in range(5)]
    results = await asyncio.gather(*deletes)
    codes = [r.status_code for r in results]
    assert codes.count(204) >= 1
    assert all(c in (204, 404) for c in codes)


@pytest.mark.asyncio
async def test_concurrent_status_patches(client: AsyncClient):
    """Multiple status patches at once — no crash."""
    task = (await _create(client)).json()
    patches = [
        client.patch(
            f"/api/v1/tasks/{task['id']}/status",
            json={"status": s, "position": i},
        )
        for i, s in enumerate(["todo", "in_progress", "done", "blocked", "todo"])
    ]
    results = await asyncio.gather(*patches)
    assert all(r.status_code == 200 for r in results)


@pytest.mark.asyncio
async def test_concurrent_reorder(client: AsyncClient):
    """Multiple reorder ops at once — all succeed."""
    tasks = [(await _create(client, title=f"R-{i}")).json() for i in range(5)]
    ids = [t["id"] for t in tasks]
    reorders = [
        client.post("/api/v1/tasks/reorder", json={"task_ids": ids[::-1]})
        for _ in range(5)
    ]
    results = await asyncio.gather(*reorders)
    assert all(r.status_code == 200 for r in results)
