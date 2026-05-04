import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.database import get_session
from app.models.activity import ActivityLog
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
async def test_activity_logged_on_create(client: AsyncClient):
    await _create_task(client, title="My Task")
    resp = await client.get("/api/v1/activity")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["action"] == "task_created"
    assert data[0]["resource_type"] == "task"
    assert data[0]["detail"]["title"] == "My Task"


@pytest.mark.asyncio
async def test_activity_logged_on_update(client: AsyncClient):
    task = await _create_task(client)
    await client.put(f"/api/v1/tasks/{task['id']}", json={"title": "Updated"})
    resp = await client.get("/api/v1/activity", params={"action": "task_updated"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["action"] == "task_updated"
    assert data[0]["detail"]["title"] == "Updated"


@pytest.mark.asyncio
async def test_activity_logged_on_delete(client: AsyncClient):
    task = await _create_task(client)
    await client.delete(f"/api/v1/tasks/{task['id']}")
    resp = await client.get("/api/v1/activity", params={"action": "task_deleted"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["action"] == "task_deleted"


@pytest.mark.asyncio
async def test_activity_filter_by_action(client: AsyncClient):
    await _create_task(client, title="Task A")
    await _create_task(client, title="Task B")
    resp = await client.get("/api/v1/activity", params={"action": "task_created"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(e["action"] == "task_created" for e in data)


@pytest.mark.asyncio
async def test_activity_filter_by_resource_type(client: AsyncClient):
    await _create_task(client)
    resp = await client.get("/api/v1/activity", params={"resource_type": "task"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert all(e["resource_type"] == "task" for e in data)


@pytest.mark.asyncio
async def test_activity_pagination(client: AsyncClient):
    for i in range(3):
        await _create_task(client, title=f"Task {i}")
    resp = await client.get("/api/v1/activity", params={"limit": 2, "offset": 0})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_activity_ordered_by_newest(client: AsyncClient):
    await _create_task(client, title="First")
    await _create_task(client, title="Second")
    resp = await client.get("/api/v1/activity")
    data = resp.json()
    assert data[0]["detail"]["title"] == "Second"
    assert data[1]["detail"]["title"] == "First"


@pytest.mark.asyncio
async def test_activity_empty(client: AsyncClient):
    resp = await client.get("/api/v1/activity")
    assert resp.status_code == 200
    assert resp.json() == []
