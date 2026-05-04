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
