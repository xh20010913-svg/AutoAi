import json
import threading
import time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.testclient import TestClient

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


def _make_app():
    from fastapi import FastAPI
    from app.websocket import manager

    manager._connections.clear()

    test_app = FastAPI()

    async def override_get_session():
        async with TestingSession() as session:
            yield session

    test_app.include_router(api_router)
    test_app.dependency_overrides[get_session] = override_get_session
    return test_app


@pytest.fixture
def sync_client():
    app = _make_app()
    with TestClient(app) as client:
        yield client


def _receive_in_thread(ws, timeout=5):
    """Receive a WS message in a background thread with a timeout."""
    result = {}

    def _recv():
        try:
            result["data"] = ws.receive_text()
        except Exception as e:
            result["error"] = str(e)

    t = threading.Thread(target=_recv)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive():
        raise TimeoutError("Timed out waiting for WS message")
    if "error" in result:
        raise RuntimeError(result["error"])
    return result["data"]


def test_ws_connect_and_disconnect(sync_client: TestClient):
    with sync_client.websocket_connect("/api/v1/ws") as ws:
        assert ws is not None


def test_ws_broadcast_on_task_create(sync_client: TestClient):
    with sync_client.websocket_connect("/api/v1/ws") as ws:
        # Start receiving before the HTTP call
        t_recv = threading.Thread(target=lambda: None)

        # Trigger HTTP in a thread, receive in main thread
        results = {}

        def do_create():
            results["resp"] = sync_client.post("/api/v1/tasks", json={"title": "WS Test"})

        t_http = threading.Thread(target=do_create)
        t_http.start()

        raw = _receive_in_thread(ws, timeout=5)
        t_http.join(timeout=5)

        event = json.loads(raw)
        assert event["event"] == "task.created"
        assert event["data"]["title"] == "WS Test"
        assert results["resp"].status_code == 201


def test_ws_broadcast_on_task_update(sync_client: TestClient):
    # Create task first (before WS connects, so no event to drain)
    resp = sync_client.post("/api/v1/tasks", json={"title": "Before"})
    task_id = resp.json()["id"]

    with sync_client.websocket_connect("/api/v1/ws") as ws:
        results = {}

        def do_update():
            results["resp"] = sync_client.put(f"/api/v1/tasks/{task_id}", json={"title": "After"})

        t_http = threading.Thread(target=do_update)
        t_http.start()

        raw = _receive_in_thread(ws, timeout=5)
        t_http.join(timeout=5)

        event = json.loads(raw)
        assert event["event"] == "task.updated"
        assert event["data"]["title"] == "After"


def test_ws_broadcast_on_task_delete(sync_client: TestClient):
    resp = sync_client.post("/api/v1/tasks", json={"title": "Delete Me"})
    task_id = resp.json()["id"]

    with sync_client.websocket_connect("/api/v1/ws") as ws:
        results = {}

        def do_delete():
            results["resp"] = sync_client.delete(f"/api/v1/tasks/{task_id}")

        t_http = threading.Thread(target=do_delete)
        t_http.start()

        raw = _receive_in_thread(ws, timeout=5)
        t_http.join(timeout=5)

        event = json.loads(raw)
        assert event["event"] == "task.deleted"
        assert event["data"]["id"] == task_id


def test_ws_broadcast_on_status_update(sync_client: TestClient):
    resp = sync_client.post("/api/v1/tasks", json={"title": "Status Task"})
    task_id = resp.json()["id"]

    with sync_client.websocket_connect("/api/v1/ws") as ws:
        results = {}

        def do_status():
            results["resp"] = sync_client.patch(f"/api/v1/tasks/{task_id}/status", json={"status": "done"})

        t_http = threading.Thread(target=do_status)
        t_http.start()

        raw = _receive_in_thread(ws, timeout=5)
        t_http.join(timeout=5)

        event = json.loads(raw)
        assert event["event"] == "task.updated"
        assert event["data"]["status"] == "done"


def test_ws_broadcast_on_reorder(sync_client: TestClient):
    r1 = sync_client.post("/api/v1/tasks", json={"title": "A"})
    r2 = sync_client.post("/api/v1/tasks", json={"title": "B"})
    t1_id, t2_id = r1.json()["id"], r2.json()["id"]

    with sync_client.websocket_connect("/api/v1/ws") as ws:
        results = {}

        def do_reorder():
            results["resp"] = sync_client.post("/api/v1/tasks/reorder", json={"task_ids": [t2_id, t1_id]})

        t_http = threading.Thread(target=do_reorder)
        t_http.start()

        raw = _receive_in_thread(ws, timeout=5)
        t_http.join(timeout=5)

        event = json.loads(raw)
        assert event["event"] == "task.reordered"
        assert len(event["data"]["tasks"]) == 2
