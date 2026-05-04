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


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "My Project", "description": "A test project"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Project"
    assert data["description"] == "A test project"
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_project_minimal(client: AsyncClient):
    resp = await client.post("/api/v1/projects", json={"name": "Minimal"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Minimal"
    assert data["description"] == ""
    assert data["owner_id"] is None
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    await _create_project(client, name="Project A")
    await _create_project(client, name="Project B")
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["size"] == 20


@pytest.mark.asyncio
async def test_list_projects_pagination(client: AsyncClient):
    await _create_project(client, name="P1")
    await _create_project(client, name="P2")
    await _create_project(client, name="P3")
    resp = await client.get("/api/v1/projects", params={"page": 1, "size": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1

    resp = await client.get("/api/v1/projects", params={"page": 2, "size": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["page"] == 2


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    project = await _create_project(client)
    resp = await client.get(f"/api/v1/projects/{project['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == project["id"]


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/projects/nonexistent")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Project not found"


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient):
    project = await _create_project(client)
    resp = await client.put(
        f"/api/v1/projects/{project['id']}",
        json={"name": "Updated", "description": "New desc", "status": "archived"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated"
    assert data["description"] == "New desc"
    assert data["status"] == "archived"


@pytest.mark.asyncio
async def test_update_project_partial(client: AsyncClient):
    project = await _create_project(client, description="Original")
    resp = await client.put(
        f"/api/v1/projects/{project['id']}",
        json={"name": "Only Name Changed"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Only Name Changed"
    assert data["description"] == "Original"


@pytest.mark.asyncio
async def test_update_project_not_found(client: AsyncClient):
    resp = await client.put(
        "/api/v1/projects/nonexistent",
        json={"name": "Nope"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    project = await _create_project(client)
    resp = await client.delete(f"/api/v1/projects/{project['id']}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/projects/{project['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_found(client: AsyncClient):
    resp = await client.delete("/api/v1/projects/nonexistent")
    assert resp.status_code == 404
