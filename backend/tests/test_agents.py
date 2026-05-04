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


async def _create_agent(client: AsyncClient, **overrides):
    payload = {"name": "Test Agent", **overrides}
    resp = await client.post("/api/v1/agents", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient):
    resp = await client.post("/api/v1/agents", json={"name": "Backend Agent"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Backend Agent"
    assert data["role"] == "backend"
    assert data["status"] == "idle"
    assert data["model"] == ""
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_agent_with_fields(client: AsyncClient):
    resp = await client.post("/api/v1/agents", json={
        "name": "GPT Agent",
        "role": "pm",
        "model": "gpt-4",
        "provider": "openai",
        "api_key_env": "OPENAI_API_KEY",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "GPT Agent"
    assert data["role"] == "pm"
    assert data["model"] == "gpt-4"
    assert data["provider"] == "openai"
    assert data["api_key_env"] == "OPENAI_API_KEY"


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient):
    await _create_agent(client, name="Agent A")
    await _create_agent(client, name="Agent B")
    resp = await client.get("/api/v1/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_agents_filter_by_status(client: AsyncClient):
    agent_a = await _create_agent(client, name="Idle Agent")
    agent_b = await _create_agent(client, name="Working Agent")
    await client.patch(f"/api/v1/agents/{agent_b['id']}/status", json={"status": "working"})
    resp = await client.get("/api/v1/agents", params={"status": "working"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "working"


@pytest.mark.asyncio
async def test_list_agents_filter_by_role(client: AsyncClient):
    await _create_agent(client, name="Backend", role="backend")
    await _create_agent(client, name="Frontend", role="frontend")
    resp = await client.get("/api/v1/agents", params={"role": "frontend"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["role"] == "frontend"


@pytest.mark.asyncio
async def test_get_agent(client: AsyncClient):
    agent = await _create_agent(client)
    resp = await client.get(f"/api/v1/agents/{agent['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == agent["id"]


@pytest.mark.asyncio
async def test_get_agent_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/agents/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_agent(client: AsyncClient):
    agent = await _create_agent(client)
    resp = await client.put(f"/api/v1/agents/{agent['id']}", json={
        "name": "Updated Agent",
        "model": "gpt-4",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Agent"
    assert data["model"] == "gpt-4"
    assert data["role"] == "backend"  # unchanged


@pytest.mark.asyncio
async def test_update_agent_not_found(client: AsyncClient):
    resp = await client.put("/api/v1/agents/nonexistent", json={"name": "X"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_agent(client: AsyncClient):
    agent = await _create_agent(client)
    resp = await client.delete(f"/api/v1/agents/{agent['id']}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/agents/{agent['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_agent_not_found(client: AsyncClient):
    resp = await client.delete("/api/v1/agents/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_agent_status(client: AsyncClient):
    agent = await _create_agent(client)
    resp = await client.get(f"/api/v1/agents/{agent['id']}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "idle"
    assert data["current_task_id"] is None


@pytest.mark.asyncio
async def test_update_agent_status(client: AsyncClient):
    agent = await _create_agent(client)
    resp = await client.patch(f"/api/v1/agents/{agent['id']}/status", json={
        "status": "working",
        "current_task_id": "task-123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "working"
    assert data["current_task_id"] == "task-123"


@pytest.mark.asyncio
async def test_update_agent_status_clear_task(client: AsyncClient):
    agent = await _create_agent(client)
    await client.patch(f"/api/v1/agents/{agent['id']}/status", json={
        "status": "working",
        "current_task_id": "task-123",
    })
    resp = await client.patch(f"/api/v1/agents/{agent['id']}/status", json={
        "status": "idle",
        "current_task_id": None,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "idle"
    assert data["current_task_id"] is None


@pytest.mark.asyncio
async def test_update_agent_status_not_found(client: AsyncClient):
    resp = await client.patch("/api/v1/agents/nonexistent/status", json={"status": "working"})
    assert resp.status_code == 404
