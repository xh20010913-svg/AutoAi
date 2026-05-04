"""End-to-end integration tests for Agent management complete workflow.

Tests cover:
1. Agent lifecycle (create → configure → view → update → delete)
2. Task assignment flow (create task → assign → verify status → unassign)
3. Boundary and error cases (non-existent resources, duplicate assignment, concurrent ops)
4. API linkage (Agent config API ↔ Task assignment API)
"""
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


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

async def _create_agent(client: AsyncClient, **overrides):
    payload = {"name": "TestAgent", "role": "coder", "model": "gpt-4", "provider": "openai", **overrides}
    resp = await client.post("/api/v1/agents", json=payload)
    assert resp.status_code == 201
    return resp.json()


async def _create_task(client: AsyncClient, **overrides):
    payload = {"title": "Test Task", **overrides}
    resp = await client.post("/api/v1/tasks", json=payload)
    assert resp.status_code == 201
    return resp.json()


async def _get_agent(client: AsyncClient, agent_id: int):
    resp = await client.get(f"/api/v1/agents/{agent_id}")
    assert resp.status_code == 200
    return resp.json()


async def _get_task(client: AsyncClient, task_id: str):
    resp = await client.get(f"/api/v1/tasks/{task_id}")
    assert resp.status_code == 200
    return resp.json()


# ===========================================================================
# 1. Agent Lifecycle Tests
# ===========================================================================

class TestAgentLifecycle:
    """Test agent creation, configuration, viewing, update, and deletion."""

    @pytest.mark.asyncio
    async def test_create_agent(self, client: AsyncClient):
        """Create an agent and verify defaults."""
        agent = await _create_agent(client)
        assert agent["name"] == "TestAgent"
        assert agent["role"] == "coder"
        assert agent["model"] == "gpt-4"
        assert agent["provider"] == "openai"
        assert agent["status"] == "idle"
        assert agent["active_tasks"] == 0
        assert "id" in agent

    @pytest.mark.asyncio
    async def test_configure_agent(self, client: AsyncClient):
        """Create agent, then update model/provider fields."""
        agent = await _create_agent(client, model="", provider="")
        resp = await client.put(
            f"/api/v1/agents/{agent['id']}",
            json={"model": "claude-3", "provider": "anthropic"},
        )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["model"] == "claude-3"
        assert updated["provider"] == "anthropic"
        assert updated["name"] == agent["name"]  # unchanged

    @pytest.mark.asyncio
    async def test_view_agent_status(self, client: AsyncClient):
        """Verify agent status can be queried after creation."""
        agent = await _create_agent(client, name="Viewer")
        fetched = await _get_agent(client, agent["id"])
        assert fetched["status"] == "idle"
        assert fetched["active_tasks"] == 0

    @pytest.mark.asyncio
    async def test_update_agent_config(self, client: AsyncClient):
        """Modify agent role and verify the update persists."""
        agent = await _create_agent(client, role="reviewer")
        resp = await client.put(
            f"/api/v1/agents/{agent['id']}",
            json={"role": "lead", "name": "UpdatedAgent"},
        )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["role"] == "lead"
        assert updated["name"] == "UpdatedAgent"

    @pytest.mark.asyncio
    async def test_delete_agent(self, client: AsyncClient):
        """Delete agent and verify it's gone."""
        agent = await _create_agent(client)
        resp = await client.delete(f"/api/v1/agents/{agent['id']}")
        assert resp.status_code == 204
        resp = await client.get(f"/api/v1/agents/{agent['id']}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_agent_unassigns_tasks(self, client: AsyncClient):
        """Deleting an agent should unassign all its tasks."""
        agent = await _create_agent(client)
        task = await _create_task(client)
        await client.post("/api/v1/agents/assign", json={"task_id": task["id"], "agent_id": agent["id"]})

        # Delete agent
        resp = await client.delete(f"/api/v1/agents/{agent['id']}")
        assert resp.status_code == 204

        # Task should still exist but be unassigned
        updated_task = await _get_task(client, task["id"])
        assert updated_task["assignee_id"] is None
        assert updated_task["assignee"] == ""

    @pytest.mark.asyncio
    async def test_list_agents(self, client: AsyncClient):
        """List all agents returns the correct count."""
        await _create_agent(client, name="Agent A")
        await _create_agent(client, name="Agent B")
        resp = await client.get("/api/v1/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2


# ===========================================================================
# 2. Task Assignment Flow Tests
# ===========================================================================

class TestTaskAssignmentFlow:
    """Test creating tasks, assigning to agents, verifying status changes."""

    @pytest.mark.asyncio
    async def test_assign_task_to_agent(self, client: AsyncClient):
        """Assign a task to an agent, verify agent becomes working."""
        agent = await _create_agent(client)
        task = await _create_task(client)

        resp = await client.post(
            "/api/v1/agents/assign",
            json={"task_id": task["id"], "agent_id": agent["id"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Task assigned"

        # Verify agent status changed to working
        agent_data = await _get_agent(client, agent["id"])
        assert agent_data["status"] == "working"
        assert agent_data["active_tasks"] == 1

        # Verify task's assignee_id is set
        task_data = await _get_task(client, task["id"])
        assert task_data["assignee_id"] == agent["id"]
        assert task_data["assignee"] == agent["name"]

    @pytest.mark.asyncio
    async def test_unassign_task_from_agent(self, client: AsyncClient):
        """Unassign a task, verify agent goes back to idle."""
        agent = await _create_agent(client)
        task = await _create_task(client)

        await client.post("/api/v1/agents/assign", json={"task_id": task["id"], "agent_id": agent["id"]})

        resp = await client.post("/api/v1/agents/unassign", json={"task_id": task["id"]})
        assert resp.status_code == 200

        # Agent should be idle again
        agent_data = await _get_agent(client, agent["id"])
        assert agent_data["status"] == "idle"
        assert agent_data["active_tasks"] == 0

        # Task should be unassigned
        task_data = await _get_task(client, task["id"])
        assert task_data["assignee_id"] is None
        assert task_data["assignee"] == ""

    @pytest.mark.asyncio
    async def test_multiple_tasks_same_agent(self, client: AsyncClient):
        """Assign multiple tasks to same agent, verify active_tasks count."""
        agent = await _create_agent(client)
        task1 = await _create_task(client, title="Task 1")
        task2 = await _create_task(client, title="Task 2")
        task3 = await _create_task(client, title="Task 3")

        await client.post("/api/v1/agents/assign", json={"task_id": task1["id"], "agent_id": agent["id"]})
        await client.post("/api/v1/agents/assign", json={"task_id": task2["id"], "agent_id": agent["id"]})
        await client.post("/api/v1/agents/assign", json={"task_id": task3["id"], "agent_id": agent["id"]})

        agent_data = await _get_agent(client, agent["id"])
        assert agent_data["active_tasks"] == 3
        assert agent_data["status"] == "working"

    @pytest.mark.asyncio
    async def test_unassign_one_of_multiple_tasks(self, client: AsyncClient):
        """Unassign one task from agent with multiple, agent stays working."""
        agent = await _create_agent(client)
        task1 = await _create_task(client, title="Task 1")
        task2 = await _create_task(client, title="Task 2")

        await client.post("/api/v1/agents/assign", json={"task_id": task1["id"], "agent_id": agent["id"]})
        await client.post("/api/v1/agents/assign", json={"task_id": task2["id"], "agent_id": agent["id"]})

        # Unassign one
        await client.post("/api/v1/agents/unassign", json={"task_id": task1["id"]})

        agent_data = await _get_agent(client, agent["id"])
        assert agent_data["active_tasks"] == 1
        assert agent_data["status"] == "working"  # still has tasks

    @pytest.mark.asyncio
    async def test_reassign_task_to_different_agent(self, client: AsyncClient):
        """Reassigning a task from one agent to another updates both counts."""
        agent_a = await _create_agent(client, name="AgentA")
        agent_b = await _create_agent(client, name="AgentB")
        task = await _create_task(client)

        # Assign to A
        await client.post("/api/v1/agents/assign", json={"task_id": task["id"], "agent_id": agent_a["id"]})

        # Reassign to B
        await client.post("/api/v1/agents/assign", json={"task_id": task["id"], "agent_id": agent_b["id"]})

        a_data = await _get_agent(client, agent_a["id"])
        b_data = await _get_agent(client, agent_b["id"])

        assert a_data["active_tasks"] == 0
        assert a_data["status"] == "idle"
        assert b_data["active_tasks"] == 1
        assert b_data["status"] == "working"

        task_data = await _get_task(client, task["id"])
        assert task_data["assignee_id"] == agent_b["id"]


# ===========================================================================
# 3. Boundary and Error Tests
# ===========================================================================

class TestBoundaryAndErrors:
    """Test error handling for invalid inputs and edge cases."""

    @pytest.mark.asyncio
    async def test_assign_nonexistent_agent(self, client: AsyncClient):
        """Assigning to a non-existent agent returns 404."""
        task = await _create_task(client)
        resp = await client.post(
            "/api/v1/agents/assign",
            json={"task_id": task["id"], "agent_id": 99999},
        )
        assert resp.status_code == 404
        assert "Agent not found" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_assign_nonexistent_task(self, client: AsyncClient):
        """Assigning a non-existent task returns 404."""
        agent = await _create_agent(client)
        resp = await client.post(
            "/api/v1/agents/assign",
            json={"task_id": "nonexistent-id", "agent_id": agent["id"]},
        )
        assert resp.status_code == 404
        assert "Task not found" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_duplicate_assignment(self, client: AsyncClient):
        """Assigning the same task to the same agent twice is idempotent."""
        agent = await _create_agent(client)
        task = await _create_task(client)

        await client.post("/api/v1/agents/assign", json={"task_id": task["id"], "agent_id": agent["id"]})
        resp = await client.post("/api/v1/agents/assign", json={"task_id": task["id"], "agent_id": agent["id"]})
        assert resp.status_code == 200
        assert "already assigned" in resp.json()["message"]

        # Should not double-count
        agent_data = await _get_agent(client, agent["id"])
        assert agent_data["active_tasks"] == 1

    @pytest.mark.asyncio
    async def test_unassign_unassigned_task(self, client: AsyncClient):
        """Unassigning a task that is not assigned succeeds gracefully."""
        task = await _create_task(client)
        resp = await client.post("/api/v1/agents/unassign", json={"task_id": task["id"]})
        assert resp.status_code == 200
        assert "not assigned" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_unassign_nonexistent_task(self, client: AsyncClient):
        """Unassigning a non-existent task returns 404."""
        resp = await client.post("/api/v1/agents/unassign", json={"task_id": "nope"})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, client: AsyncClient):
        """Getting a non-existent agent returns 404."""
        resp = await client.get("/api/v1/agents/99999")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_nonexistent_agent(self, client: AsyncClient):
        """Updating a non-existent agent returns 404."""
        resp = await client.put("/api/v1/agents/99999", json={"name": "ghost"})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_agent(self, client: AsyncClient):
        """Deleting a non-existent agent returns 404."""
        resp = await client.delete("/api/v1/agents/99999")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_rapid_assign_unassign(self, client: AsyncClient):
        """Rapid sequential assign/unassign operations on different tasks."""
        agent = await _create_agent(client)
        tasks = [await _create_task(client, title=f"Task {i}") for i in range(4)]

        # Assign first two
        await client.post("/api/v1/agents/assign", json={"task_id": tasks[0]["id"], "agent_id": agent["id"]})
        await client.post("/api/v1/agents/assign", json={"task_id": tasks[1]["id"], "agent_id": agent["id"]})

        # Rapidly unassign first two and assign next two
        r1 = await client.post("/api/v1/agents/unassign", json={"task_id": tasks[0]["id"]})
        r2 = await client.post("/api/v1/agents/unassign", json={"task_id": tasks[1]["id"]})
        r3 = await client.post("/api/v1/agents/assign", json={"task_id": tasks[2]["id"], "agent_id": agent["id"]})
        r4 = await client.post("/api/v1/agents/assign", json={"task_id": tasks[3]["id"], "agent_id": agent["id"]})

        for r in [r1, r2, r3, r4]:
            assert r.status_code == 200

        agent_data = await _get_agent(client, agent["id"])
        assert agent_data["active_tasks"] == 2
        assert agent_data["status"] == "working"


# ===========================================================================
# 4. API Linkage Tests
# ===========================================================================

class TestAPILinkage:
    """Test that Agent Config API and Task API are properly linked."""

    @pytest.mark.asyncio
    async def test_agent_config_affects_task_assignment(self, client: AsyncClient):
        """Changing agent config doesn't break existing assignments."""
        agent = await _create_agent(client, role="coder")
        task = await _create_task(client)

        await client.post("/api/v1/agents/assign", json={"task_id": task["id"], "agent_id": agent["id"]})

        # Update agent config
        await client.put(
            f"/api/v1/agents/{agent['id']}",
            json={"role": "reviewer", "model": "claude-4"},
        )

        # Assignment should still be intact
        task_data = await _get_task(client, task["id"])
        assert task_data["assignee_id"] == agent["id"]

        agent_data = await _get_agent(client, agent["id"])
        assert agent_data["role"] == "reviewer"
        assert agent_data["model"] == "claude-4"
        assert agent_data["active_tasks"] == 1

    @pytest.mark.asyncio
    async def test_role_change_preserves_assignments(self, client: AsyncClient):
        """Changing agent role doesn't unassign tasks."""
        agent = await _create_agent(client, role="coder")
        task1 = await _create_task(client, title="Bug fix")
        task2 = await _create_task(client, title="Code review")

        await client.post("/api/v1/agents/assign", json={"task_id": task1["id"], "agent_id": agent["id"]})
        await client.post("/api/v1/agents/assign", json={"task_id": task2["id"], "agent_id": agent["id"]})

        # Change role
        await client.put(f"/api/v1/agents/{agent['id']}", json={"role": "lead"})

        # Both tasks still assigned
        agent_data = await _get_agent(client, agent["id"])
        assert agent_data["active_tasks"] == 2
        assert agent_data["role"] == "lead"

        t1 = await _get_task(client, task1["id"])
        t2 = await _get_task(client, task2["id"])
        assert t1["assignee_id"] == agent["id"]
        assert t2["assignee_id"] == agent["id"]

    @pytest.mark.asyncio
    async def test_full_workflow(self, client: AsyncClient):
        """Complete workflow: create agent → create tasks → assign → update agent → unassign."""
        # 1. Create agent
        agent = await _create_agent(client, name="WorkflowAgent", role="coder")
        assert agent["status"] == "idle"

        # 2. Create tasks
        task1 = await _create_task(client, title="Implement feature")
        task2 = await _create_task(client, title="Write tests")

        # 3. Assign tasks
        await client.post("/api/v1/agents/assign", json={"task_id": task1["id"], "agent_id": agent["id"]})
        await client.post("/api/v1/agents/assign", json={"task_id": task2["id"], "agent_id": agent["id"]})

        agent = await _get_agent(client, agent["id"])
        assert agent["status"] == "working"
        assert agent["active_tasks"] == 2

        # 4. Update agent config
        await client.put(
            f"/api/v1/agents/{agent['id']}",
            json={"model": "gpt-4o", "provider": "openai"},
        )

        # 5. Complete first task (unassign)
        await client.post("/api/v1/agents/unassign", json={"task_id": task1["id"]})
        agent = await _get_agent(client, agent["id"])
        assert agent["active_tasks"] == 1
        assert agent["status"] == "working"

        # 6. Complete second task
        await client.post("/api/v1/agents/unassign", json={"task_id": task2["id"]})
        agent = await _get_agent(client, agent["id"])
        assert agent["active_tasks"] == 0
        assert agent["status"] == "idle"

        # 7. Tasks still exist
        t1 = await _get_task(client, task1["id"])
        t2 = await _get_task(client, task2["id"])
        assert t1["assignee_id"] is None
        assert t2["assignee_id"] is None
