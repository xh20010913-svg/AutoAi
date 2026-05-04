import json
import pytest
from pathlib import Path
from app.dispatcher import Dispatcher, TaskNode, RoleConfig


# ─── Unit tests: pure logic, no file I/O ────────────────────────────────────


class TestDispatcherCore:
    """Tests for dispatcher logic using in-memory data."""

    def _make_dispatcher(self, tasks: list[dict], roles: list[dict] | None = None) -> Dispatcher:
        d = Dispatcher()
        d.set_tasks(tasks)
        if roles:
            d.set_roles(roles)
        return d

    def test_get_ready_tasks_no_deps(self):
        d = self._make_dispatcher([
            {"id": "t1", "title": "Task 1", "status": "todo", "dependencies": []},
            {"id": "t2", "title": "Task 2", "status": "todo", "dependencies": []},
        ])
        ready = d.get_ready_tasks()
        assert len(ready) == 2

    def test_get_ready_tasks_with_deps(self):
        d = self._make_dispatcher([
            {"id": "t1", "title": "Task 1", "status": "todo", "dependencies": []},
            {"id": "t2", "title": "Task 2", "status": "todo", "dependencies": ["t1"]},
        ])
        ready = d.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "t1"

    def test_deps_become_ready_when_dependency_done(self):
        d = self._make_dispatcher([
            {"id": "t1", "title": "Task 1", "status": "done", "dependencies": []},
            {"id": "t2", "title": "Task 2", "status": "todo", "dependencies": ["t1"]},
        ])
        ready = d.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "t2"

    def test_blocked_tasks(self):
        d = self._make_dispatcher([
            {"id": "t1", "title": "Task 1", "status": "todo", "dependencies": []},
            {"id": "t2", "title": "Task 2", "status": "todo", "dependencies": ["t1"]},
            {"id": "t3", "title": "Task 3", "status": "todo", "dependencies": ["t1", "t2"]},
        ])
        blocked = d.get_blocked_tasks()
        assert len(blocked) == 2
        blocked_ids = {t.id for t in blocked}
        assert blocked_ids == {"t2", "t3"}

    def test_dispatch_one_returns_highest_priority(self):
        d = self._make_dispatcher([
            {"id": "t1", "title": "Low task", "status": "todo", "priority": "low", "dependencies": []},
            {"id": "t2", "title": "High task", "status": "todo", "priority": "high", "dependencies": []},
            {"id": "t3", "title": "Med task", "status": "todo", "priority": "medium", "dependencies": []},
        ])
        result = d.dispatch_one()
        assert result is not None
        assert result["task_id"] == "t2"
        assert result["priority"] == "high"

    def test_dispatch_one_returns_none_when_no_ready(self):
        d = self._make_dispatcher([
            {"id": "t1", "title": "Task 1", "status": "todo", "dependencies": ["missing"]},
        ])
        result = d.dispatch_one()
        assert result is None

    def test_dispatch_one_respects_role_load(self):
        d = self._make_dispatcher([
            {"id": "t1", "title": "T1", "status": "in_progress", "suggested_role": "backend", "dependencies": []},
            {"id": "t2", "title": "T2", "status": "in_progress", "suggested_role": "backend", "dependencies": []},
            {"id": "t3", "title": "T3", "status": "todo", "suggested_role": "backend", "dependencies": []},
        ], roles=[
            {"name": "backend", "max_concurrent": 2},
        ])
        result = d.dispatch_one()
        assert result is None  # backend is at max capacity

    def test_dispatch_one_with_role_filter(self):
        d = self._make_dispatcher([
            {"id": "t1", "title": "FE task", "status": "todo", "suggested_role": "frontend", "dependencies": []},
            {"id": "t2", "title": "BE task", "status": "todo", "suggested_role": "backend", "dependencies": []},
        ])
        result = d.dispatch_one(role="frontend")
        assert result["task_id"] == "t1"
        assert result["assigned_role"] == "frontend"

    def test_dispatch_batch(self):
        d = self._make_dispatcher([
            {"id": "t1", "title": "T1", "status": "todo", "suggested_role": "backend", "dependencies": []},
            {"id": "t2", "title": "T2", "status": "todo", "suggested_role": "frontend", "dependencies": []},
            {"id": "t3", "title": "T3", "status": "todo", "suggested_role": "backend", "dependencies": []},
        ], roles=[
            {"name": "backend", "max_concurrent": 3},
            {"name": "frontend", "max_concurrent": 2},
        ])
        results = d.dispatch_batch()
        assert len(results) == 3

    def test_dispatch_batch_max_count(self):
        d = self._make_dispatcher([
            {"id": "t1", "title": "T1", "status": "todo", "dependencies": []},
            {"id": "t2", "title": "T2", "status": "todo", "dependencies": []},
            {"id": "t3", "title": "T3", "status": "todo", "dependencies": []},
        ])
        results = d.dispatch_batch(max_count=2)
        assert len(results) == 2

    def test_dispatch_by_role(self):
        d = self._make_dispatcher([
            {"id": "t1", "title": "BE1", "status": "todo", "suggested_role": "backend", "dependencies": []},
            {"id": "t2", "title": "FE1", "status": "todo", "suggested_role": "frontend", "dependencies": []},
            {"id": "t3", "title": "BE2", "status": "todo", "suggested_role": "backend", "dependencies": []},
        ], roles=[
            {"name": "backend", "max_concurrent": 3},
            {"name": "frontend", "max_concurrent": 2},
        ])
        results = d.dispatch_by_role("backend")
        assert len(results) == 2
        assert all(r["assigned_role"] == "backend" for r in results)

    def test_mark_done_makes_dependents_ready(self):
        d = self._make_dispatcher([
            {"id": "t1", "title": "T1", "status": "todo", "dependencies": []},
            {"id": "t2", "title": "T2", "status": "todo", "dependencies": ["t1"]},
        ])
        assert len(d.get_ready_tasks()) == 1
        d.mark_done("t1")
        ready = d.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "t2"

    def test_mark_in_progress(self):
        d = self._make_dispatcher([
            {"id": "t1", "title": "T1", "status": "todo", "dependencies": []},
        ])
        d.mark_in_progress("t1")
        assert d.tasks["t1"].status == "in_progress"
        assert len(d.get_ready_tasks()) == 0

    def test_summary(self):
        d = self._make_dispatcher([
            {"id": "t1", "title": "T1", "status": "done", "dependencies": []},
            {"id": "t2", "title": "T2", "status": "todo", "dependencies": []},
            {"id": "t3", "title": "T3", "status": "todo", "dependencies": ["t2"]},
        ], roles=[
            {"name": "backend", "max_concurrent": 3},
        ])
        summary = d.get_task_graph_summary()
        assert summary["total"] == 3
        assert summary["by_status"]["done"] == 1
        assert summary["by_status"]["todo"] == 2
        assert summary["ready"] == 1
        assert summary["blocked"] == 1
        assert "backend" in summary["roles"]


# ─── Integration tests: file I/O ────────────────────────────────────────────


class TestDispatcherFileIO:
    """Tests for loading from JSON files."""

    def test_load_from_files(self, tmp_path: Path):
        graph_file = tmp_path / "task_graph.json"
        roles_file = tmp_path / "roles.json"

        graph_file.write_text(json.dumps({
            "tasks": [
                {"id": "a", "title": "A", "status": "todo", "dependencies": [], "suggested_role": "dev"},
                {"id": "b", "title": "B", "status": "todo", "dependencies": ["a"], "suggested_role": "dev"},
            ]
        }), encoding="utf-8")

        roles_file.write_text(json.dumps({
            "roles": [
                {"name": "dev", "max_concurrent": 2},
            ]
        }), encoding="utf-8")

        d = Dispatcher(task_graph_path=graph_file, roles_path=roles_file).load()
        assert len(d.tasks) == 2
        assert len(d.roles) == 1
        ready = d.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "a"

    def test_load_missing_files(self, tmp_path: Path):
        d = Dispatcher(
            task_graph_path=tmp_path / "nonexistent.json",
            roles_path=tmp_path / "also_missing.json",
        ).load()
        assert len(d.tasks) == 0
        assert len(d.roles) == 0

    def test_load_tasks_as_list(self, tmp_path: Path):
        graph_file = tmp_path / "task_graph.json"
        graph_file.write_text(json.dumps([
            {"id": "x", "title": "X", "status": "todo", "dependencies": []},
        ]), encoding="utf-8")

        d = Dispatcher(task_graph_path=graph_file).load()
        assert len(d.tasks) == 1

    def test_load_roles_as_list(self, tmp_path: Path):
        roles_file = tmp_path / "roles.json"
        roles_file.write_text(json.dumps([
            {"name": "qa", "max_concurrent": 5},
        ]), encoding="utf-8")

        d = Dispatcher(roles_path=roles_file).load()
        assert len(d.roles) == 1
        assert d.roles["qa"].max_concurrent == 5


# ─── API integration test ───────────────────────────────────────────────────


import httpx
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
async def client(tmp_path: Path):
    from fastapi import FastAPI

    # Write sample data to .autoai directory
    autoai_dir = tmp_path / ".autoai"
    autoai_dir.mkdir()
    (autoai_dir / "task_graph.json").write_text(json.dumps({
        "tasks": [
            {"id": "t1", "title": "Task 1", "status": "todo", "suggested_role": "backend", "dependencies": [], "priority": "high"},
            {"id": "t2", "title": "Task 2", "status": "todo", "suggested_role": "frontend", "dependencies": ["t1"], "priority": "medium"},
        ]
    }), encoding="utf-8")
    (autoai_dir / "roles.json").write_text(json.dumps({
        "roles": [
            {"name": "backend", "max_concurrent": 3},
            {"name": "frontend", "max_concurrent": 2},
        ]
    }), encoding="utf-8")

    test_app = FastAPI()

    async def override_get_session():
        async with TestingSession() as session:
            yield session

    test_app.include_router(api_router)
    test_app.dependency_overrides[get_session] = override_get_session

    # Patch the dispatcher path
    import app.api.tasks as tasks_module
    original_dir = tasks_module._DEFAULT_GRAPH_DIR
    tasks_module._DEFAULT_GRAPH_DIR = autoai_dir

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as c:
        yield c

    tasks_module._DEFAULT_GRAPH_DIR = original_dir


@pytest.mark.asyncio
async def test_dispatch_single(client: AsyncClient):
    resp = await client.post("/api/v1/tasks/dispatch", json={"mode": "single"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert len(data["dispatched"]) == 1
    assert data["dispatched"][0]["task_id"] == "t1"  # high priority, no deps
    assert data["summary"]["ready"] == 1


@pytest.mark.asyncio
async def test_dispatch_single_with_role_filter(client: AsyncClient):
    resp = await client.post("/api/v1/tasks/dispatch", json={"mode": "single", "role": "frontend"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0  # t2 is blocked by t1


@pytest.mark.asyncio
async def test_dispatch_batch(client: AsyncClient):
    resp = await client.post("/api/v1/tasks/dispatch", json={"mode": "batch"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1  # only t1 is ready


@pytest.mark.asyncio
async def test_dispatch_invalid_mode(client: AsyncClient):
    resp = await client.post("/api/v1/tasks/dispatch", json={"mode": "invalid"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_dispatch_by_role_missing_role(client: AsyncClient):
    resp = await client.post("/api/v1/tasks/dispatch", json={"mode": "by_role"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_dispatch_default_mode(client: AsyncClient):
    resp = await client.post("/api/v1/tasks/dispatch")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
