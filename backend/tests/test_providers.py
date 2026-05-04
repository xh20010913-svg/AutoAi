import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.database import get_session
from app.models.project import Base
from app.models.provider import Model, Provider  # noqa: F401

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
    payload = {"name": "Test Provider", "api_type": "openai", **overrides}
    resp = await client.post("/api/v1/providers", json=payload)
    assert resp.status_code == 201
    return resp.json()


async def _create_model(client: AsyncClient, provider_id: str, **overrides):
    payload = {"name": "Test Model", "model_id": "test-model-1", **overrides}
    resp = await client.post(f"/api/v1/providers/{provider_id}/models", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ── Provider tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_provider(client: AsyncClient):
    resp = await client.post(
        "/api/v1/providers",
        json={"name": "OpenAI", "base_url": "https://api.openai.com", "api_type": "openai"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "OpenAI"
    assert data["api_type"] == "openai"
    assert data["enabled"] is True
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
        json={"name": "Updated Provider", "enabled": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Provider"
    assert data["enabled"] is False


@pytest.mark.asyncio
async def test_delete_provider(client: AsyncClient):
    provider = await _create_provider(client)
    resp = await client.delete(f"/api/v1/providers/{provider['id']}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/providers/{provider['id']}")
    assert resp.status_code == 404


# ── Model tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_model(client: AsyncClient):
    provider = await _create_provider(client)
    resp = await client.post(
        f"/api/v1/providers/{provider['id']}/models",
        json={"name": "GPT-4", "model_id": "gpt-4", "context_window": 8192, "max_tokens": 4096},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "GPT-4"
    assert data["model_id"] == "gpt-4"
    assert data["context_window"] == 8192
    assert data["provider_id"] == provider["id"]


@pytest.mark.asyncio
async def test_create_model_provider_not_found(client: AsyncClient):
    resp = await client.post(
        "/api/v1/providers/nonexistent/models",
        json={"name": "Model", "model_id": "m1"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_models(client: AsyncClient):
    provider = await _create_provider(client)
    await _create_model(client, provider["id"], name="Model A", model_id="ma")
    await _create_model(client, provider["id"], name="Model B", model_id="mb")
    resp = await client.get(f"/api/v1/providers/{provider['id']}/models")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_models_provider_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/providers/nonexistent/models")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_model(client: AsyncClient):
    provider = await _create_provider(client)
    model = await _create_model(client, provider["id"])
    resp = await client.delete(f"/api/v1/providers/{provider['id']}/models/{model['id']}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/providers/{provider['id']}/models")
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_delete_model_not_found(client: AsyncClient):
    provider = await _create_provider(client)
    resp = await client.delete(f"/api/v1/providers/{provider['id']}/models/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_model_wrong_provider(client: AsyncClient):
    p1 = await _create_provider(client, name="P1")
    p2 = await _create_provider(client, name="P2")
    model = await _create_model(client, p1["id"])
    resp = await client.delete(f"/api/v1/providers/{p2['id']}/models/{model['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cascade_delete_provider_deletes_models(client: AsyncClient):
    provider = await _create_provider(client)
    await _create_model(client, provider["id"])
    await client.delete(f"/api/v1/providers/{provider['id']}")
    resp = await client.get(f"/api/v1/providers/{provider['id']}/models")
    assert resp.status_code == 404
