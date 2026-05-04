import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.database import get_session
from app.models.project import Base
from app.models.settings import UserSettings  # noqa: F401
from app.models.user import User  # noqa: F401

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


async def _register(client: AsyncClient, **overrides):
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "secret123",
        **overrides,
    }
    return await client.post("/api/v1/auth/register", json=payload)


async def _login(client: AsyncClient):
    return await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "secret123"},
    )


async def _auth_header(client: AsyncClient) -> dict:
    await _register(client)
    resp = await _login(client)
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_settings_creates_defaults(client: AsyncClient):
    headers = await _auth_header(client)
    resp = await client.get("/api/v1/settings", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["theme"] == "auto"
    assert data["language"] == "zh"
    assert data["notification_enabled"] is True
    assert data["dashboard_layout"] is None


@pytest.mark.asyncio
async def test_get_settings_returns_existing(client: AsyncClient):
    headers = await _auth_header(client)
    await client.put("/api/v1/settings", json={"theme": "dark"}, headers=headers)
    resp = await client.get("/api/v1/settings", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["theme"] == "dark"


@pytest.mark.asyncio
async def test_update_settings_partial(client: AsyncClient):
    headers = await _auth_header(client)
    resp = await client.put(
        "/api/v1/settings",
        json={"theme": "light", "language": "en"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["theme"] == "light"
    assert data["language"] == "en"
    assert data["notification_enabled"] is True


@pytest.mark.asyncio
async def test_update_settings_creates_if_missing(client: AsyncClient):
    headers = await _auth_header(client)
    resp = await client.put(
        "/api/v1/settings",
        json={"dashboard_layout": '{"cols":2}'},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["dashboard_layout"] == '{"cols":2}'
    assert data["theme"] == "auto"


@pytest.mark.asyncio
async def test_get_settings_unauthorized(client: AsyncClient):
    resp = await client.get("/api/v1/settings")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_settings_unauthorized(client: AsyncClient):
    resp = await client.put("/api/v1/settings", json={"theme": "dark"})
    assert resp.status_code == 401
