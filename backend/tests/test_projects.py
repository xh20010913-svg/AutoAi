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


async def _register_user(client: AsyncClient, username="testuser"):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": f"{username}@test.com", "password": "pass123"},
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_project(client: AsyncClient, owner_id: str, **overrides):
    payload = {"name": "Test Project", "owner_id": owner_id, **overrides}
    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    user = await _register_user(client)
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "My Project", "owner_id": user["id"]},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Project"
    assert data["owner_id"] == user["id"]
    assert data["status"] == "active"
    assert data["description"] == ""
    assert "id" in data


@pytest.mark.asyncio
async def test_create_project_with_description(client: AsyncClient):
    user = await _register_user(client)
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "Desc Proj", "owner_id": user["id"], "description": "A test project"},
    )
    assert resp.status_code == 201
    assert resp.json()["description"] == "A test project"


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    user = await _register_user(client)
    await _create_project(client, user["id"], name="Project A")
    await _create_project(client, user["id"], name="Project B")
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    user = await _register_user(client)
    project = await _create_project(client, user["id"])
    resp = await client.get(f"/api/v1/projects/{project['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == project["id"]


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/projects/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient):
    user = await _register_user(client)
    project = await _create_project(client, user["id"])
    resp = await client.put(
        f"/api/v1/projects/{project['id']}",
        json={"name": "Updated Name"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"
    # description unchanged
    assert resp.json()["description"] == project["description"]


@pytest.mark.asyncio
async def test_update_project_not_found(client: AsyncClient):
    resp = await client.put("/api/v1/projects/nonexistent", json={"name": "X"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    user = await _register_user(client)
    project = await _create_project(client, user["id"])
    resp = await client.delete(f"/api/v1/projects/{project['id']}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/projects/{project['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_found(client: AsyncClient):
    resp = await client.delete("/api/v1/projects/nonexistent")
    assert resp.status_code == 404
