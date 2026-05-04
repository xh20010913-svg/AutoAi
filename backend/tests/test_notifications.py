import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.database import get_session
from app.models.notification import Notification  # noqa: F401
from app.models.project import Base
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


async def _register_and_login(client: AsyncClient, username: str, email: str) -> str:
    await client.post("/api/v1/auth/register", json={
        "username": username,
        "email": email,
        "password": "pass123",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": username,
        "password": "pass123",
    })
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_list_notifications_empty(client: AsyncClient):
    token = await _register_and_login(client, "listuser", "list@example.com")
    resp = await client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_unread_count_zero(client: AsyncClient):
    token = await _register_and_login(client, "unreaduser", "unread@example.com")
    resp = await client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_task_assign_creates_notification(client: AsyncClient):
    # Register the assignee
    assignee_token = await _register_and_login(client, "assignee1", "assignee1@example.com")

    # Register a second user to create the task
    await _register_and_login(client, "creator1", "creator1@example.com")

    # Create a task assigned to assignee1
    resp = await client.post("/api/v1/tasks", json={
        "title": "Test task",
        "assignee": "assignee1",
    })
    assert resp.status_code == 201

    # Check assignee's notifications
    resp = await client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {assignee_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["type"] == "task_assigned"
    assert "Test task" in data["items"][0]["content"]


@pytest.mark.asyncio
async def test_mark_notification_read(client: AsyncClient):
    token = await _register_and_login(client, "readuser", "read@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a task assigned to self to generate a notification
    await client.post("/api/v1/tasks", json={
        "title": "Self task",
        "assignee": "readuser",
    })

    # Get the notification
    resp = await client.get("/api/v1/notifications", headers=headers)
    notif_id = resp.json()["items"][0]["id"]

    # Mark as read
    resp = await client.put(f"/api/v1/notifications/{notif_id}/read", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True

    # Unread count should be 0
    resp = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert resp.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_mark_all_read(client: AsyncClient):
    token = await _register_and_login(client, "allread", "allread@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create two tasks to generate two notifications
    await client.post("/api/v1/tasks", json={"title": "Task 1", "assignee": "allread"})
    await client.post("/api/v1/tasks", json={"title": "Task 2", "assignee": "allread"})

    # Both should be unread
    resp = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert resp.json()["unread_count"] == 2

    # Mark all as read
    resp = await client.post("/api/v1/notifications/read-all", headers=headers)
    assert resp.status_code == 200

    # Unread count should be 0
    resp = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert resp.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_task_status_done_creates_notification(client: AsyncClient):
    token = await _register_and_login(client, "doneuser", "done@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a task assigned to doneuser
    resp = await client.post("/api/v1/tasks", json={
        "title": "Finish me",
        "assignee": "doneuser",
    })
    task_id = resp.json()["id"]

    # Mark task as done
    await client.patch(f"/api/v1/tasks/{task_id}/status", json={"status": "done"})

    # Check notifications - should have task_assigned + task_completed
    resp = await client.get("/api/v1/notifications", headers=headers)
    data = resp.json()
    assert data["total"] == 2
    types = {n["type"] for n in data["items"]}
    assert "task_assigned" in types
    assert "task_completed" in types


@pytest.mark.asyncio
async def test_pagination(client: AsyncClient):
    token = await _register_and_login(client, "pageuser", "page@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create 3 tasks to get 3 notifications
    for i in range(3):
        await client.post("/api/v1/tasks", json={"title": f"Task {i}", "assignee": "pageuser"})

    # Page 1 with page_size=2
    resp = await client.get("/api/v1/notifications?page=1&page_size=2", headers=headers)
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["page"] == 1

    # Page 2
    resp = await client.get("/api/v1/notifications?page=2&page_size=2", headers=headers)
    data = resp.json()
    assert len(data["items"]) == 1
