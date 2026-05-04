import asyncio
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.api.runs import _active_processes
from app.database import get_session
from app.models.project import Base

engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    with patch("app.api.runs._bg_session_factory", TestingSession):
        yield
    # Wait for any background processes to finish before dropping tables
    for proc in list(_active_processes.values()):
        try:
            proc.kill()
        except Exception:
            pass
    for proc in list(_active_processes.values()):
        try:
            await proc.wait()
        except Exception:
            pass
    await asyncio.sleep(0.2)
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


async def _start_run(client: AsyncClient, **overrides):
    payload = {"agent_id": "agent-1", "command": "echo hello", **overrides}
    resp = await client.post("/api/v1/runs", json=payload)
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_create_run(client: AsyncClient):
    resp = await client.post(
        "/api/v1/runs",
        json={"agent_id": "agent-1", "command": "echo hello"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["agent_id"] == "agent-1"
    assert data["command"] == "echo hello"
    assert data["status"] == "pending"
    assert data["exit_code"] is None
    assert "id" in data


@pytest.mark.asyncio
async def test_get_run(client: AsyncClient):
    run = await _start_run(client)
    resp = await client.get(f"/api/v1/runs/{run['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == run["id"]


@pytest.mark.asyncio
async def test_get_run_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/runs/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_runs(client: AsyncClient):
    await _start_run(client, agent_id="a1")
    await _start_run(client, agent_id="a2")
    resp = await client.get("/api/v1/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_runs_filter_by_agent(client: AsyncClient):
    await _start_run(client, agent_id="a1")
    await _start_run(client, agent_id="a2")
    resp = await client.get("/api/v1/runs", params={"agent_id": "a1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["agent_id"] == "a1"


@pytest.mark.asyncio
async def test_list_runs_filter_by_status(client: AsyncClient):
    await _start_run(client, command="echo hello")
    await asyncio.sleep(2)
    resp = await client.get("/api/v1/runs", params={"status": "succeeded"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "succeeded"


@pytest.mark.asyncio
async def test_stop_run(client: AsyncClient):
    run = await _start_run(client, command="ping -n 60 127.0.0.1")
    await asyncio.sleep(0.5)
    resp = await client.post(f"/api/v1/runs/{run['id']}/stop")
    assert resp.status_code == 200
    assert resp.json()["status"] == "stopped"
    assert resp.json()["finished_at"] is not None


@pytest.mark.asyncio
async def test_stop_run_not_found(client: AsyncClient):
    resp = await client.post("/api/v1/runs/nonexistent/stop")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_stop_already_finished_run(client: AsyncClient):
    await _start_run(client, command="echo done")
    await asyncio.sleep(2)
    # Need to get the run id to stop it
    resp = await client.get("/api/v1/runs")
    run_id = resp.json()["items"][0]["id"]
    resp = await client.post(f"/api/v1/runs/{run_id}/stop")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_run_logs(client: AsyncClient):
    run = await _start_run(client, command="echo hello")
    await asyncio.sleep(2)
    resp = await client.get(f"/api/v1/runs/{run['id']}/logs")
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) >= 1
    assert logs[0]["stream"] == "stdout"
    assert "hello" in logs[0]["content"]


@pytest.mark.asyncio
async def test_get_run_logs_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/runs/nonexistent/logs")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_run_completes_with_exit_code(client: AsyncClient):
    run = await _start_run(client, command="echo test")
    await asyncio.sleep(2)
    resp = await client.get(f"/api/v1/runs/{run['id']}")
    data = resp.json()
    assert data["status"] == "succeeded"
    assert data["exit_code"] == 0
    assert data["started_at"] is not None
    assert data["finished_at"] is not None


@pytest.mark.asyncio
async def test_run_with_task_id(client: AsyncClient):
    resp = await client.post(
        "/api/v1/runs",
        json={"agent_id": "agent-1", "command": "echo hi", "task_id": "task-123"},
    )
    assert resp.status_code == 201
    assert resp.json()["task_id"] == "task-123"
