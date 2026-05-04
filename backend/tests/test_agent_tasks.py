import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.database import get_session
from app.models.project import Agent, Base

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


async def _create_agent(session: AsyncSession, name: str = "Agent-1") -> int:
    agent = Agent(name=name)
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return agent.id


async def _create_task(client: AsyncClient, title: str = "Task", status: str = "todo") -> dict:
    resp = await client.post("/api/v1/tasks", json={"title": title, "status": status})
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_assign_task(client: AsyncClient):
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    task = await _create_task(client)
    resp = await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task["id"]})
    assert resp.status_code == 201
    data = resp.json()
    assert data["agent_id"] == agent_id
    assert data["task_id"] == task["id"]


@pytest.mark.asyncio
async def test_assign_task_agent_not_found(client: AsyncClient):
    task = await _create_task(client)
    resp = await client.post("/api/v1/agents/9999/assign", json={"task_id": task["id"]})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_assign_task_task_not_found(client: AsyncClient):
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    resp = await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": "nonexistent"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unassign_task(client: AsyncClient):
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    task = await _create_task(client)
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task["id"]})
    resp = await client.delete(f"/api/v1/agents/{agent_id}/assign/{task['id']}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_unassign_task_not_found(client: AsyncClient):
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    resp = await client.delete(f"/api/v1/agents/{agent_id}/assign/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_agent_tasks(client: AsyncClient):
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    t1 = await _create_task(client, title="T1")
    t2 = await _create_task(client, title="T2")
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": t1["id"]})
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": t2["id"]})
    resp = await client.get(f"/api/v1/agents/{agent_id}/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_agent_tasks_agent_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/agents/9999/tasks")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_agent_status_idle(client: AsyncClient):
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "idle"
    assert data["active_task_count"] == 0
    assert data["current_task_id"] is None


@pytest.mark.asyncio
async def test_agent_status_working(client: AsyncClient):
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    task = await _create_task(client)
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task["id"]})
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "working"
    assert data["active_task_count"] == 1
    assert data["current_task_id"] == task["id"]


@pytest.mark.asyncio
async def test_agent_status_blocked(client: AsyncClient):
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    task = await _create_task(client, status="blocked")
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task["id"]})
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "blocked"


@pytest.mark.asyncio
async def test_agent_status_blocked_after_unassign(client: AsyncClient):
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    blocked_task = await _create_task(client, status="blocked")
    working_task = await _create_task(client)
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": blocked_task["id"]})
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": working_task["id"]})
    # Unassign the blocked task
    await client.delete(f"/api/v1/agents/{agent_id}/assign/{blocked_task['id']}")
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "working"


@pytest.mark.asyncio
async def test_agent_status_all_empty(client: AsyncClient):
    resp = await client.get("/api/v1/agents/status/all")
    assert resp.status_code == 200
    assert resp.json()["agents"] == []


@pytest.mark.asyncio
async def test_agent_status_all(client: AsyncClient):
    async with TestingSession() as session:
        a1 = await _create_agent(session, "Agent-A")
        a2 = await _create_agent(session, "Agent-B")
    task = await _create_task(client)
    await client.post(f"/api/v1/agents/{a1}/assign", json={"task_id": task["id"]})
    resp = await client.get("/api/v1/agents/status/all")
    assert resp.status_code == 200
    agents = resp.json()["agents"]
    assert len(agents) == 2
    agent_a = next(a for a in agents if a["agent_id"] == a1)
    agent_b = next(a for a in agents if a["agent_id"] == a2)
    assert agent_a["status"] == "working"
    assert agent_b["status"] == "idle"
