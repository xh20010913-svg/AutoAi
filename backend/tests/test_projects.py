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


async def _create_project(client: AsyncClient, **overrides):
    payload = {"name": "Test Project", **overrides}
    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ── POST /api/v1/projects ──


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    resp = await client.post("/api/v1/projects", json={"name": "My Project"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Project"
    assert data["description"] == ""
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_project_with_description(client: AsyncClient):
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "Full Project", "description": "A detailed project"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Full Project"
    assert data["description"] == "A detailed project"


@pytest.mark.asyncio
async def test_create_project_missing_name(client: AsyncClient):
    resp = await client.post("/api/v1/projects", json={})
    assert resp.status_code == 422


# ── GET /api/v1/projects ──


@pytest.mark.asyncio
async def test_list_projects_empty(client: AsyncClient):
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    await _create_project(client, name="Project A")
    await _create_project(client, name="Project B")
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


# ── GET /api/v1/projects/:id ──


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    project = await _create_project(client)
    resp = await client.get(f"/api/v1/projects/{project['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == project["id"]
    assert resp.json()["name"] == project["name"]


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/projects/nonexistent-id")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Project not found"


# ── PUT /api/v1/projects/:id ──


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient):
    project = await _create_project(client)
    resp = await client.put(
        f"/api/v1/projects/{project['id']}",
        json={"name": "Updated Name"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_project_description(client: AsyncClient):
    project = await _create_project(client)
    resp = await client.put(
        f"/api/v1/projects/{project['id']}",
        json={"description": "New description"},
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "New description"
    assert resp.json()["name"] == "Test Project"


@pytest.mark.asyncio
async def test_update_project_not_found(client: AsyncClient):
    resp = await client.put(
        "/api/v1/projects/nonexistent-id",
        json={"name": "X"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_project_partial(client: AsyncClient):
    project = await _create_project(client, name="Original", description="Desc")
    resp = await client.put(
        f"/api/v1/projects/{project['id']}",
        json={"name": "New Name"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Desc"


# ── DELETE /api/v1/projects/:id ──


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    project = await _create_project(client)
    resp = await client.delete(f"/api/v1/projects/{project['id']}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/projects/{project['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_found(client: AsyncClient):
    resp = await client.delete("/api/v1/projects/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_verify_removed(client: AsyncClient):
    p1 = await _create_project(client, name="Keep")
    p2 = await _create_project(client, name="Delete")
    await client.delete(f"/api/v1/projects/{p2['id']}")
    resp = await client.get("/api/v1/projects")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == p1["id"]
