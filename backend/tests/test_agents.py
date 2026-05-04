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
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient):
    resp = await client.post("/api/v1/agents", json={"name": "My Agent"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Agent"
    assert data["role"] == "backend"
    assert data["status"] == "idle"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient):
    await _create_agent(client, name="Agent A")
    await _create_agent(client, name="Agent B")
    resp = await client.get("/api/v1/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


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
    resp = await client.patch(f"/api/v1/agents/{agent['id']}", json={"name": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"


@pytest.mark.asyncio
async def test_update_agent_status(client: AsyncClient):
    agent = await _create_agent(client)
    resp = await client.patch(f"/api/v1/agents/{agent['id']}", json={"status": "running"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"


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
async def test_create_agent_with_all_fields(client: AsyncClient):
    resp = await client.post("/api/v1/agents", json={
        "name": "Full Agent",
        "role": "tester",
        "model": "claude-sonnet-4-6",
        "system_prompt": "You are a tester.",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Full Agent"
    assert data["role"] == "tester"
    assert data["model"] == "claude-sonnet-4-6"
    assert data["system_prompt"] == "You are a tester."
