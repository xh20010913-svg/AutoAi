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


async def _register(client: AsyncClient, **overrides):
    payload = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "secret123",
        **overrides,
    }
    return await client.post("/api/v1/auth/register", json=payload)


async def _register_and_login(client: AsyncClient, **overrides):
    await _register(client, **overrides)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": overrides.get("email", "test@example.com"), "password": overrides.get("password", "secret123")},
    )
    return resp.json()["access_token"]


# ── POST /api/v1/auth/register ──


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await _register(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await _register(client)
    resp = await _register(client)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_register_missing_fields(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={"email": "a@b.com"})
    assert resp.status_code == 422


# ── POST /api/v1/auth/login ──


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await _register(client)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "secret123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await _register(client)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "secret123"},
    )
    assert resp.status_code == 401


# ── GET /api/v1/auth/me ──


@pytest.mark.asyncio
async def test_me_with_token(client: AsyncClient):
    token = await _register_and_login(client)
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"


@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token(client: AsyncClient):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401
