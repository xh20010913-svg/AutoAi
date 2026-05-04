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


async def _create_provider(client: AsyncClient, **overrides):
    payload = {
        "name": "OpenAI",
        "type": "openai",
        "base_url": "https://api.openai.com",
        "api_key": "sk-test",
        **overrides,
    }
    resp = await client.post("/api/v1/providers", json=payload)
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_create_provider(client: AsyncClient):
    resp = await client.post(
        "/api/v1/providers",
        json={"name": "OpenAI", "type": "openai", "base_url": "https://api.openai.com", "api_key": "sk-test"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "OpenAI"
    assert data["type"] == "openai"
    assert data["base_url"] == "https://api.openai.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_providers(client: AsyncClient):
    await _create_provider(client, name="Provider A")
    await _create_provider(client, name="Provider B")
    resp = await client.get("/api/v1/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_provider(client: AsyncClient):
    provider = await _create_provider(client)
    resp = await client.get(f"/api/v1/providers/{provider['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == provider["id"]


@pytest.mark.asyncio
async def test_get_provider_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/providers/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_provider(client: AsyncClient):
    provider = await _create_provider(client)
    resp = await client.put(
        f"/api/v1/providers/{provider['id']}",
        json={"name": "Updated Name", "api_key": "sk-new"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Name"
    assert data["api_key"] == "sk-new"
    assert data["type"] == "openai"


@pytest.mark.asyncio
async def test_delete_provider(client: AsyncClient):
    provider = await _create_provider(client)
    resp = await client.delete(f"/api/v1/providers/{provider['id']}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/providers/{provider['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_provider_without_api_key(client: AsyncClient):
    resp = await client.post(
        "/api/v1/providers",
        json={"name": "Local LLM", "type": "openai_compatible", "base_url": "http://localhost:8080"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["api_key"] == ""


@pytest.mark.asyncio
async def test_health_check_healthy(client: AsyncClient, monkeypatch):
    provider = await _create_provider(client)

    class MockResponse:
        status_code = 200

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            return MockResponse()

    import app.api.providers as providers_mod
    monkeypatch.setattr(providers_mod.httpx, "AsyncClient", lambda **kw: MockClient())

    resp = await client.post(f"/api/v1/providers/{provider['id']}/health-check")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["provider_id"] == provider["id"]


@pytest.mark.asyncio
async def test_health_check_unreachable(client: AsyncClient, monkeypatch):
    provider = await _create_provider(client, base_url="http://localhost:1")

    import httpx

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            raise httpx.RequestError("Connection refused")

    import app.api.providers as providers_mod
    monkeypatch.setattr(providers_mod.httpx, "AsyncClient", lambda **kw: MockClient())

    resp = await client.post(f"/api/v1/providers/{provider['id']}/health-check")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_health_check_not_found(client: AsyncClient):
    resp = await client.post("/api/v1/providers/nonexistent/health-check")
    assert resp.status_code == 404
