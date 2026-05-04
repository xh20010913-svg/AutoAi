import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.database import get_session
from app.models.project import Base
from app.models.user import User  # noqa: F401 — ensure table is created

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


# --- Auth helpers ---


async def register_user(client: AsyncClient, **overrides):
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "secret123",
        **overrides,
    }
    return await client.post("/api/v1/auth/register", json=payload)


async def login_user(client: AsyncClient, username="testuser", password="secret123"):
    return await client.post("/api/v1/auth/login", json={"username": username, "password": password})


async def get_auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register + login, return Authorization header dict."""
    await register_user(client)
    resp = await login_user(client)
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
