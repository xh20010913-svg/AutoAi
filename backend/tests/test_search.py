import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.database import get_session
from app.models.project import Agent, Base, Project, Task

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


async def _seed_data(session: AsyncSession):
    session.add_all([
        Task(id="t1", title="Design API", status="todo", position=0),
        Task(id="t2", title="Build frontend", status="in_progress", position=1),
        Task(id="t3", title="Write tests", status="done", position=2),
        Project(name="AutoAi"),
        Project(name="MultiCa"),
        Agent(name="CodeBot"),
        Agent(name="ReviewBot"),
    ])
    await session.commit()


@pytest.mark.asyncio
async def test_search_by_keyword(client: AsyncClient):
    async with TestingSession() as session:
        await _seed_data(session)

    resp = await client.get("/api/v1/search", params={"q": "API"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "API"
    results = data["results"]
    assert len(results) == 1
    assert results[0]["title"] == "Design API"


@pytest.mark.asyncio
async def test_search_by_type_filter(client: AsyncClient):
    async with TestingSession() as session:
        await _seed_data(session)

    resp = await client.get("/api/v1/search", params={"q": "Auto", "type": "project"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "AutoAi"
    assert data["results"][0]["type"] == "project"


@pytest.mark.asyncio
async def test_search_agent(client: AsyncClient):
    async with TestingSession() as session:
        await _seed_data(session)

    resp = await client.get("/api/v1/search", params={"q": "Bot", "type": "agent"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 2


@pytest.mark.asyncio
async def test_search_no_results(client: AsyncClient):
    async with TestingSession() as session:
        await _seed_data(session)

    resp = await client.get("/api/v1/search", params={"q": "nonexistent"})
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 0


@pytest.mark.asyncio
async def test_search_empty_query(client: AsyncClient):
    resp = await client.get("/api/v1/search", params={"q": ""})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_limit(client: AsyncClient):
    async with TestingSession() as session:
        await _seed_data(session)

    resp = await client.get("/api/v1/search", params={"q": "e", "limit": 2})
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 2
