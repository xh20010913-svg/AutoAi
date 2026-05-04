"""
End-to-end integration tests for AutoAi kanban board flows.

Tests cover the complete task lifecycle: create → status transitions → edit → delete,
board state management across columns, position ordering, and edge cases.

Note: Auth and WebSocket features are not yet implemented in the backend,
so those flows (401 on unauthenticated access, real-time push notifications)
are skipped with clear markers.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.database import get_session
from app.models.project import Base

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_task(client: AsyncClient, **overrides):
    """Create a task and return the JSON response."""
    payload = {"title": "Test Task", **overrides}
    resp = await client.post("/api/v1/tasks", json=payload)
    assert resp.status_code == 201, f"Create failed: {resp.text}"
    return resp.json()


async def _get_board(client: AsyncClient):
    """Fetch all tasks and group by status → simulates kanban columns."""
    resp = await client.get("/api/v1/tasks")
    assert resp.status_code == 200
    tasks = resp.json()
    board = {}
    for t in tasks:
        board.setdefault(t["status"], []).append(t)
    return board


# ===================================================================
# 1. Kanban Board — Full Task Lifecycle
# ===================================================================


class TestKanbanLifecycle:
    """Simulate a user interacting with the kanban board from creation to deletion."""

    async def test_create_task_appears_in_todo_column(self, client: AsyncClient):
        """A newly created task should appear in the 'todo' column by default."""
        task = await _create_task(client, title="Write docs")
        assert task["status"] == "todo"

        board = await _get_board(client)
        assert len(board.get("todo", [])) == 1
        assert board["todo"][0]["title"] == "Write docs"

    async def test_drag_todo_to_in_progress(self, client: AsyncClient):
        """Dragging a task from Todo to In Progress updates its status."""
        task = await _create_task(client, title="Implement feature")
        resp = await client.patch(
            f"/api/v1/tasks/{task['id']}/status",
            json={"status": "in_progress", "position": 0},
        )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["status"] == "in_progress"
        assert updated["position"] == 0

        board = await _get_board(client)
        assert "todo" not in board or len(board["todo"]) == 0
        assert len(board["in_progress"]) == 1

    async def test_drag_in_progress_to_done(self, client: AsyncClient):
        """Moving a task through the full pipeline: todo → in_progress → done."""
        task = await _create_task(client, title="Ship it")

        # todo → in_progress
        await client.patch(
            f"/api/v1/tasks/{task['id']}/status",
            json={"status": "in_progress"},
        )
        # in_progress → done
        resp = await client.patch(
            f"/api/v1/tasks/{task['id']}/status",
            json={"status": "done"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"

        board = await _get_board(client)
        assert len(board.get("done", [])) == 1

    async def test_edit_task_title_and_priority(self, client: AsyncClient):
        """User can edit a task's title and priority from the detail panel."""
        task = await _create_task(client, title="Original", priority="low")
        resp = await client.put(
            f"/api/v1/tasks/{task['id']}",
            json={"title": "Updated Title", "priority": "high"},
        )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["title"] == "Updated Title"
        assert updated["priority"] == "high"
        # Other fields should be unchanged
        assert updated["status"] == "todo"

    async def test_delete_task_removes_from_board(self, client: AsyncClient):
        """Deleting a task removes it from the kanban board entirely."""
        task = await _create_task(client, title="Will be deleted")
        resp = await client.delete(f"/api/v1/tasks/{task['id']}")
        assert resp.status_code == 204

        # Verify gone
        resp = await client.get(f"/api/v1/tasks/{task['id']}")
        assert resp.status_code == 404

        board = await _get_board(client)
        assert all(
            task["id"] != t["id"]
            for column in board.values()
            for t in column
        )

    async def test_full_lifecycle_in_order(self, client: AsyncClient):
        """Complete flow: create → move to in_progress → edit → move to done → delete."""
        # 1. Create
        task = await _create_task(client, title="Lifecycle task", priority="medium")
        task_id = task["id"]

        # 2. Move to in_progress
        resp = await client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "in_progress", "position": 0},
        )
        assert resp.json()["status"] == "in_progress"

        # 3. Edit title and priority
        resp = await client.put(
            f"/api/v1/tasks/{task_id}",
            json={"title": "Lifecycle task (reviewed)", "priority": "high"},
        )
        assert resp.json()["title"] == "Lifecycle task (reviewed)"
        assert resp.json()["priority"] == "high"
        assert resp.json()["status"] == "in_progress"  # unchanged

        # 4. Move to done
        resp = await client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "done"},
        )
        assert resp.json()["status"] == "done"

        # 5. Verify final state
        resp = await client.get(f"/api/v1/tasks/{task_id}")
        data = resp.json()
        assert data["title"] == "Lifecycle task (reviewed)"
        assert data["priority"] == "high"
        assert data["status"] == "done"

        # 6. Delete
        resp = await client.delete(f"/api/v1/tasks/{task_id}")
        assert resp.status_code == 204


# ===================================================================
# 2. Board Column State — Multiple Tasks Per Column
# ===================================================================


class TestBoardColumns:
    """Test kanban board with multiple tasks distributed across columns."""

    async def test_multiple_tasks_in_same_column(self, client: AsyncClient):
        """Multiple tasks can exist in the same status column."""
        await _create_task(client, title="Todo 1", status="todo")
        await _create_task(client, title="Todo 2", status="todo")
        await _create_task(client, title="In Progress 1", status="in_progress")

        board = await _get_board(client)
        assert len(board["todo"]) == 2
        assert len(board["in_progress"]) == 1

    async def test_filter_by_status_returns_correct_column(self, client: AsyncClient):
        """Filtering by status returns only tasks in that column."""
        await _create_task(client, title="T1", status="todo")
        await _create_task(client, title="T2", status="in_progress")
        await _create_task(client, title="T3", status="done")

        for status in ("todo", "in_progress", "done"):
            resp = await client.get("/api/v1/tasks", params={"status": status})
            assert resp.status_code == 200
            tasks = resp.json()
            assert len(tasks) == 1
            assert tasks[0]["status"] == status

    async def test_tasks_ordered_by_position_within_column(self, client: AsyncClient):
        """Tasks within a column are ordered by their position field."""
        await _create_task(client, title="Third", status="todo", position=2)
        await _create_task(client, title="First", status="todo", position=0)
        await _create_task(client, title="Second", status="todo", position=1)

        resp = await client.get("/api/v1/tasks", params={"status": "todo"})
        tasks = resp.json()
        assert [t["title"] for t in tasks] == ["First", "Second", "Third"]

    async def test_reorder_within_column(self, client: AsyncClient):
        """Reordering tasks changes their position within a column."""
        t1 = await _create_task(client, title="A", status="todo")
        t2 = await _create_task(client, title="B", status="todo")
        t3 = await _create_task(client, title="C", status="todo")

        # Reverse order
        resp = await client.post(
            "/api/v1/tasks/reorder",
            json={"task_ids": [t3["id"], t2["id"], t1["id"]]},
        )
        assert resp.status_code == 200
        reordered = resp.json()
        assert [t["id"] for t in reordered] == [t3["id"], t2["id"], t1["id"]]
        assert [t["position"] for t in reordered] == [0, 1, 2]


# ===================================================================
# 3. Multi-Task Scenarios — Independent Data
# ===================================================================


class TestMultiTaskScenarios:
    """Verify that tasks are independent and data isolation works correctly."""

    async def test_editing_one_task_does_not_affect_others(self, client: AsyncClient):
        """Updating one task should leave other tasks unchanged."""
        t1 = await _create_task(client, title="Task 1", priority="low")
        t2 = await _create_task(client, title="Task 2", priority="low")

        await client.put(f"/api/v1/tasks/{t1['id']}", json={"title": "Modified"})

        resp = await client.get(f"/api/v1/tasks/{t2['id']}")
        assert resp.json()["title"] == "Task 2"
        assert resp.json()["priority"] == "low"

    async def test_deleting_one_task_leaves_others(self, client: AsyncClient):
        """Deleting one task should not affect other tasks."""
        t1 = await _create_task(client, title="Delete me")
        t2 = await _create_task(client, title="Keep me")

        await client.delete(f"/api/v1/tasks/{t1['id']}")

        resp = await client.get(f"/api/v1/tasks/{t2['id']}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Keep me"

    async def test_status_change_does_not_affect_other_tasks(self, client: AsyncClient):
        """Moving one task to a new column doesn't change other tasks' status."""
        t1 = await _create_task(client, title="Moving", status="todo")
        t2 = await _create_task(client, title="Staying", status="todo")

        await client.patch(f"/api/v1/tasks/{t1['id']}/status", json={"status": "done"})

        resp = await client.get(f"/api/v1/tasks/{t2['id']}")
        assert resp.json()["status"] == "todo"

    async def test_parallel_lifecycle_multiple_tasks(self, client: AsyncClient):
        """Multiple tasks can independently move through the pipeline."""
        tasks = []
        for i in range(4):
            t = await _create_task(client, title=f"Task {i}", status="todo")
            tasks.append(t)

        # Move tasks 0,1 to in_progress
        for t in tasks[:2]:
            await client.patch(f"/api/v1/tasks/{t['id']}/status", json={"status": "in_progress"})

        # Move task 0 to done
        await client.patch(f"/api/v1/tasks/{tasks[0]['id']}/status", json={"status": "done"})

        board = await _get_board(client)
        assert len(board.get("todo", [])) == 2
        assert len(board.get("in_progress", [])) == 1
        assert len(board.get("done", [])) == 1


# ===================================================================
# 4. Edge Cases & Error Handling
# ===================================================================


class TestEdgeCases:
    """Validate API behavior on invalid inputs and boundary conditions."""

    async def test_get_nonexistent_task_returns_404(self, client: AsyncClient):
        resp = await client.get("/api/v1/tasks/nonexistent-id")
        assert resp.status_code == 404

    async def test_update_nonexistent_task_returns_404(self, client: AsyncClient):
        resp = await client.put("/api/v1/tasks/nonexistent-id", json={"title": "x"})
        assert resp.status_code == 404

    async def test_delete_nonexistent_task_returns_404(self, client: AsyncClient):
        resp = await client.delete("/api/v1/tasks/nonexistent-id")
        assert resp.status_code == 404

    async def test_update_status_nonexistent_task_returns_404(self, client: AsyncClient):
        resp = await client.patch(
            "/api/v1/tasks/nonexistent-id/status", json={"status": "done"}
        )
        assert resp.status_code == 404

    async def test_reorder_with_nonexistent_id_returns_404(self, client: AsyncClient):
        t1 = await _create_task(client, title="Exists")
        resp = await client.post(
            "/api/v1/tasks/reorder",
            json={"task_ids": [t1["id"], "fake-id"]},
        )
        assert resp.status_code == 404

    async def test_create_task_missing_title_returns_422(self, client: AsyncClient):
        """Title is required — missing title should return validation error."""
        resp = await client.post("/api/v1/tasks", json={})
        assert resp.status_code == 422

    async def test_list_empty_board(self, client: AsyncClient):
        """Listing tasks on an empty board returns an empty list."""
        resp = await client.get("/api/v1/tasks")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_filter_status_with_no_matches(self, client: AsyncClient):
        """Filtering by a status that has no tasks returns an empty list."""
        await _create_task(client, title="Only todo", status="todo")
        resp = await client.get("/api/v1/tasks", params={"status": "done"})
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_task_with_all_fields(self, client: AsyncClient):
        """Creating a task with all fields set."""
        resp = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Full task",
                "description": "A detailed description",
                "status": "in_progress",
                "priority": "high",
                "assignee": "alice",
                "position": 5,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Full task"
        assert data["description"] == "A detailed description"
        assert data["status"] == "in_progress"
        assert data["priority"] == "high"
        assert data["assignee"] == "alice"
        assert data["position"] == 5

    async def test_update_only_one_field(self, client: AsyncClient):
        """PUT with partial update should only change specified fields."""
        task = await _create_task(
            client, title="Original", description="Desc", priority="low"
        )
        resp = await client.put(
            f"/api/v1/tasks/{task['id']}", json={"priority": "high"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Original"
        assert data["description"] == "Desc"
        assert data["priority"] == "high"

    async def test_double_delete_returns_404(self, client: AsyncClient):
        """Deleting a task twice — first succeeds, second returns 404."""
        task = await _create_task(client, title="Delete me twice")
        resp = await client.delete(f"/api/v1/tasks/{task['id']}")
        assert resp.status_code == 204

        resp = await client.delete(f"/api/v1/tasks/{task['id']}")
        assert resp.status_code == 404


# ===================================================================
# 5. Auth Flow Tests (Skipped — Not Yet Implemented)
# ===================================================================


@pytest.mark.skip(reason="Auth system not yet implemented in the backend")
class TestAuthFlow:
    """
    Placeholder for authentication integration tests.

    When auth is implemented, these tests should cover:
    - User registration → auto-login → token issued
    - Token expiry → re-login flow
    - Accessing protected endpoints without token → 401
    - Accessing protected endpoints with invalid token → 401
    """

    async def test_register_login_get_token(self, client: AsyncClient):
        ...

    async def test_token_expiry_relogin(self, client: AsyncClient):
        ...

    async def test_no_token_returns_401(self, client: AsyncClient):
        ...


# ===================================================================
# 6. WebSocket Tests (Skipped — Not Yet Implemented)
# ===================================================================


@pytest.mark.skip(reason="WebSocket not yet implemented in the backend")
class TestWebSocketNotifications:
    """
    Placeholder for WebSocket integration tests.

    When WebSocket is implemented, these tests should cover:
    - Task update pushes notification to connected clients
    - Multiple users receive the same event
    """

    async def test_task_update_pushes_notification(self, client: AsyncClient):
        ...

    async def test_multiple_users_receive_event(self, client: AsyncClient):
        ...
