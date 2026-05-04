import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.database import get_session
from app.models.agent import AgentConfig, AgentRole, RoleTemplate  # noqa: F401
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


async def _create_agent(client: AsyncClient, name="Test Agent"):
    """Create an agent via direct DB insertion helper."""
    async with TestingSession() as session:
        from app.models.project import Agent
        agent = Agent(name=name)
        session.add(agent)
        await session.commit()
        await session.refresh(agent)
        return agent.id


async def _create_role(client: AsyncClient, **overrides):
    payload = {"name": "Researcher", "budget_level": "low", "authority": "read", "allowed_paths": "/data", **overrides}
    resp = await client.post("/api/v1/roles", json=payload)
    assert resp.status_code == 201
    return resp.json()


# --- Agent Config Tests ---

@pytest.mark.asyncio
async def test_get_agent_config_not_found(client: AsyncClient):
    agent_id = await _create_agent(client)
    resp = await client.get(f"/api/v1/agents/{agent_id}/config")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_agent_config_creates_new(client: AsyncClient):
    agent_id = await _create_agent(client)
    resp = await client.put(f"/api/v1/agents/{agent_id}/config", json={"model": "gpt-4o", "provider": "openai"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "gpt-4o"
    assert data["provider"] == "openai"
    assert data["agent_id"] == agent_id


@pytest.mark.asyncio
async def test_get_agent_config(client: AsyncClient):
    agent_id = await _create_agent(client)
    await client.put(f"/api/v1/agents/{agent_id}/config", json={"model": "claude-3", "provider": "anthropic"})
    resp = await client.get(f"/api/v1/agents/{agent_id}/config")
    assert resp.status_code == 200
    assert resp.json()["model"] == "claude-3"


@pytest.mark.asyncio
async def test_update_agent_config_partial(client: AsyncClient):
    agent_id = await _create_agent(client)
    await client.put(f"/api/v1/agents/{agent_id}/config", json={"model": "gpt-4", "provider": "openai"})
    resp = await client.put(f"/api/v1/agents/{agent_id}/config", json={"model": "gpt-4o"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "gpt-4o"
    assert data["provider"] == "openai"


@pytest.mark.asyncio
async def test_agent_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/agents/nonexistent/config")
    assert resp.status_code == 404


# --- Role Template Tests ---

@pytest.mark.asyncio
async def test_create_role(client: AsyncClient):
    resp = await client.post("/api/v1/roles", json={"name": "Admin", "budget_level": "high"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Admin"
    assert data["budget_level"] == "high"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_roles(client: AsyncClient):
    await _create_role(client, name="Role A")
    await _create_role(client, name="Role B")
    resp = await client.get("/api/v1/roles")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_role(client: AsyncClient):
    role = await _create_role(client)
    resp = await client.get(f"/api/v1/roles/{role['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == role["id"]


@pytest.mark.asyncio
async def test_update_role(client: AsyncClient):
    role = await _create_role(client)
    resp = await client.put(f"/api/v1/roles/{role['id']}", json={"name": "Updated", "budget_level": "high"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_role(client: AsyncClient):
    role = await _create_role(client)
    resp = await client.delete(f"/api/v1/roles/{role['id']}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/roles/{role['id']}")
    assert resp.status_code == 404


# --- Agent Role Binding Tests ---

@pytest.mark.asyncio
async def test_get_agent_role_not_found(client: AsyncClient):
    agent_id = await _create_agent(client)
    resp = await client.get(f"/api/v1/agents/{agent_id}/role")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_bind_agent_role(client: AsyncClient):
    agent_id = await _create_agent(client)
    role = await _create_role(client, name="Analyst")
    resp = await client.put(f"/api/v1/agents/{agent_id}/role", json={"role_id": role["id"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == agent_id
    assert data["role_id"] == role["id"]
    assert data["role"]["name"] == "Analyst"


@pytest.mark.asyncio
async def test_switch_agent_role(client: AsyncClient):
    agent_id = await _create_agent(client)
    role1 = await _create_role(client, name="Role1")
    role2 = await _create_role(client, name="Role2")
    await client.put(f"/api/v1/agents/{agent_id}/role", json={"role_id": role1["id"]})
    resp = await client.put(f"/api/v1/agents/{agent_id}/role", json={"role_id": role2["id"]})
    assert resp.status_code == 200
    assert resp.json()["role_id"] == role2["id"]


@pytest.mark.asyncio
async def test_bind_role_invalid(client: AsyncClient):
    agent_id = await _create_agent(client)
    resp = await client.put(f"/api/v1/agents/{agent_id}/role", json={"role_id": "nonexistent"})
    assert resp.status_code == 404
