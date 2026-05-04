import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.database import get_session
from app.models.project import Agent, Base

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


async def _create_agent(session: AsyncSession, name: str = "Agent-1") -> int:
    agent = Agent(name=name)
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return agent.id


async def _create_task(client: AsyncClient, title: str = "Task", status: str = "todo") -> dict:
    resp = await client.post("/api/v1/tasks", json={"title": title, "status": status})
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Basic task assignment
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_assign_task(client: AsyncClient):
    """Assign a valid task to a valid agent → 201 with correct agent_id and task_id."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    task = await _create_task(client)
    resp = await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task["id"]})
    assert resp.status_code == 201
    data = resp.json()
    assert data["agent_id"] == agent_id
    assert data["task_id"] == task["id"]


@pytest.mark.asyncio
async def test_assign_task_agent_not_found(client: AsyncClient):
    """Assign task to non-existent agent → 404."""
    task = await _create_task(client)
    resp = await client.post("/api/v1/agents/9999/assign", json={"task_id": task["id"]})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_assign_task_task_not_found(client: AsyncClient):
    """Assign non-existent task to agent → 404."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    resp = await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": "nonexistent"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_assignment_allowed(client: AsyncClient):
    """BUG: Assigning the same task to the same agent twice creates duplicate rows.

    The AgentTask model lacks a unique constraint on (agent_id, task_id),
    so duplicate assignments are silently accepted. This inflates active_task_count.
    """
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    task = await _create_task(client)
    resp1 = await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task["id"]})
    assert resp1.status_code == 201
    resp2 = await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task["id"]})
    # Currently succeeds (201) — but ideally should reject with 409 Conflict
    assert resp2.status_code == 201
    # Verify duplicate inflates task count
    status_resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["active_task_count"] == 2  # Bug: should be 1


# ---------------------------------------------------------------------------
# Unassignment
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unassign_task(client: AsyncClient):
    """Assign then unassign → 204."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    task = await _create_task(client)
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task["id"]})
    resp = await client.delete(f"/api/v1/agents/{agent_id}/assign/{task['id']}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_unassign_task_not_found(client: AsyncClient):
    """Unassign non-existent assignment → 404."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    resp = await client.delete(f"/api/v1/agents/{agent_id}/assign/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unassign_returns_agent_to_idle(client: AsyncClient):
    """After unassigning the only task, agent status returns to idle."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    task = await _create_task(client)
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task["id"]})
    # Verify working
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.json()["status"] == "working"
    # Unassign
    await client.delete(f"/api/v1/agents/{agent_id}/assign/{task['id']}")
    # Verify idle
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "idle"
    assert data["active_task_count"] == 0
    assert data["current_task_id"] is None


# ---------------------------------------------------------------------------
# Get agent tasks
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_agent_tasks(client: AsyncClient):
    """List tasks assigned to an agent returns all assignments."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    t1 = await _create_task(client, title="T1")
    t2 = await _create_task(client, title="T2")
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": t1["id"]})
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": t2["id"]})
    resp = await client.get(f"/api/v1/agents/{agent_id}/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_agent_tasks_agent_not_found(client: AsyncClient):
    """List tasks for non-existent agent → 404."""
    resp = await client.get("/api/v1/agents/9999/tasks")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_agent_tasks_empty(client: AsyncClient):
    """Agent with no assignments returns empty list."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    resp = await client.get(f"/api/v1/agents/{agent_id}/tasks")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Agent status queries
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_agent_status_idle(client: AsyncClient):
    """Agent with no tasks returns idle with zero counts."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "idle"
    assert data["active_task_count"] == 0
    assert data["current_task_id"] is None


@pytest.mark.asyncio
async def test_agent_status_working(client: AsyncClient):
    """Agent with assigned task returns working."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    task = await _create_task(client)
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task["id"]})
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "working"
    assert data["active_task_count"] == 1
    assert data["current_task_id"] == task["id"]


@pytest.mark.asyncio
async def test_agent_status_blocked(client: AsyncClient):
    """Agent with blocked task returns blocked status."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    task = await _create_task(client, status="blocked")
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task["id"]})
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "blocked"


@pytest.mark.asyncio
async def test_agent_status_blocked_after_unassign(client: AsyncClient):
    """After unassigning a blocked task, agent returns working if other tasks remain."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    blocked_task = await _create_task(client, status="blocked")
    working_task = await _create_task(client)
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": blocked_task["id"]})
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": working_task["id"]})
    # Unassign the blocked task
    await client.delete(f"/api/v1/agents/{agent_id}/assign/{blocked_task['id']}")
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "working"


@pytest.mark.asyncio
async def test_agent_status_agent_not_found(client: AsyncClient):
    """Status for non-existent agent → 404."""
    resp = await client.get("/api/v1/agents/9999/status")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_agent_status_returns_name(client: AsyncClient):
    """Status response includes agent_name."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session, name="TestAgent")
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.status_code == 200
    assert resp.json()["agent_name"] == "TestAgent"


# ---------------------------------------------------------------------------
# Status/all endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_agent_status_all_empty(client: AsyncClient):
    """status/all with no agents returns empty list."""
    resp = await client.get("/api/v1/agents/status/all")
    assert resp.status_code == 200
    assert resp.json()["agents"] == []


@pytest.mark.asyncio
async def test_agent_status_all(client: AsyncClient):
    """status/all reflects per-agent working/idle correctly."""
    async with TestingSession() as session:
        a1 = await _create_agent(session, "Agent-A")
        a2 = await _create_agent(session, "Agent-B")
    task = await _create_task(client)
    await client.post(f"/api/v1/agents/{a1}/assign", json={"task_id": task["id"]})
    resp = await client.get("/api/v1/agents/status/all")
    assert resp.status_code == 200
    agents = resp.json()["agents"]
    assert len(agents) == 2
    agent_a = next(a for a in agents if a["agent_id"] == a1)
    agent_b = next(a for a in agents if a["agent_id"] == a2)
    assert agent_a["status"] == "working"
    assert agent_b["status"] == "idle"


@pytest.mark.asyncio
async def test_agent_status_all_reflects_unassign(client: AsyncClient):
    """status/all updates after unassigning a task."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    task = await _create_task(client)
    await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task["id"]})
    # Verify working
    resp = await client.get("/api/v1/agents/status/all")
    assert next(a for a in resp.json()["agents"] if a["agent_id"] == agent_id)["status"] == "working"
    # Unassign
    await client.delete(f"/api/v1/agents/{agent_id}/assign/{task['id']}")
    # Verify idle
    resp = await client.get("/api/v1/agents/status/all")
    assert next(a for a in resp.json()["agents"] if a["agent_id"] == agent_id)["status"] == "idle"


# ---------------------------------------------------------------------------
# Bulk assignment — many tasks to one agent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bulk_assignment_single_agent(client: AsyncClient):
    """Assign 50 tasks to one agent — status reports correct count."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    task_ids = []
    for i in range(50):
        t = await _create_task(client, title=f"Bulk-{i}")
        task_ids.append(t["id"])
    # Assign all
    for tid in task_ids:
        resp = await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": tid})
        assert resp.status_code == 201
    # Verify status
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "working"
    assert data["active_task_count"] == 50
    # Verify tasks list
    resp = await client.get(f"/api/v1/agents/{agent_id}/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) == 50


# ---------------------------------------------------------------------------
# Multi-agent scenarios
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_same_task_assigned_to_two_agents(client: AsyncClient):
    """The same task can be assigned to multiple agents."""
    async with TestingSession() as session:
        a1 = await _create_agent(session, "Agent-1")
        a2 = await _create_agent(session, "Agent-2")
    task = await _create_task(client)
    resp1 = await client.post(f"/api/v1/agents/{a1}/assign", json={"task_id": task["id"]})
    resp2 = await client.post(f"/api/v1/agents/{a2}/assign", json={"task_id": task["id"]})
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    # Both should show working
    for aid in [a1, a2]:
        resp = await client.get(f"/api/v1/agents/{aid}/status")
        assert resp.json()["status"] == "working"
        assert resp.json()["active_task_count"] == 1


@pytest.mark.asyncio
async def test_multiple_agents_independent_status(client: AsyncClient):
    """Agents with different task loads report independent statuses."""
    async with TestingSession() as session:
        a1 = await _create_agent(session, "Busy")
        a2 = await _create_agent(session, "Idle")
        a3 = await _create_agent(session, "Blocked")
    t1 = await _create_task(client, title="Work1")
    t2 = await _create_task(client, title="Work2")
    t_blocked = await _create_task(client, title="Blocked", status="blocked")

    await client.post(f"/api/v1/agents/{a1}/assign", json={"task_id": t1["id"]})
    await client.post(f"/api/v1/agents/{a1}/assign", json={"task_id": t2["id"]})
    await client.post(f"/api/v1/agents/{a3}/assign", json={"task_id": t_blocked["id"]})

    resp = await client.get("/api/v1/agents/status/all")
    agents = {a["agent_id"]: a for a in resp.json()["agents"]}

    assert agents[a1]["status"] == "working"
    assert agents[a1]["active_task_count"] == 2
    assert agents[a2]["status"] == "idle"
    assert agents[a2]["active_task_count"] == 0
    assert agents[a3]["status"] == "blocked"
    assert agents[a3]["active_task_count"] == 1


# ---------------------------------------------------------------------------
# Concurrent assignment / unassignment
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_assignments(client: AsyncClient):
    """Concurrently assign multiple tasks to the same agent."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    tasks = [await _create_task(client, title=f"Concurrent-{i}") for i in range(10)]

    async def assign(task_id):
        resp = await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task_id})
        assert resp.status_code == 201

    await asyncio.gather(*(assign(t["id"]) for t in tasks))
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.status_code == 200
    assert resp.json()["active_task_count"] == 10


@pytest.mark.asyncio
async def test_concurrent_assign_unassign(client: AsyncClient):
    """Assign and immediately unassign tasks concurrently."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session)
    tasks = [await _create_task(client, title=f"Race-{i}") for i in range(5)]

    async def assign_then_unassign(task):
        resp = await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task["id"]})
        assert resp.status_code == 201
        resp = await client.delete(f"/api/v1/agents/{agent_id}/assign/{task['id']}")
        assert resp.status_code == 204

    await asyncio.gather(*(assign_then_unassign(t) for t in tasks))
    # After all concurrent assign+unassign, agent should be idle
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.status_code == 200
    assert resp.json()["active_task_count"] == 0
    assert resp.json()["status"] == "idle"


# ---------------------------------------------------------------------------
# Full lifecycle flow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_lifecycle_idle_to_working_to_idle(client: AsyncClient):
    """Full lifecycle: idle → assign → working → unassign → idle."""
    async with TestingSession() as session:
        agent_id = await _create_agent(session, name="Lifecycle-Agent")
    task = await _create_task(client, title="Lifecycle Task")

    # 1. Initial: idle
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    assert resp.json()["status"] == "idle"

    # 2. Assign: working
    resp = await client.post(f"/api/v1/agents/{agent_id}/assign", json={"task_id": task["id"]})
    assert resp.status_code == 201
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    data = resp.json()
    assert data["status"] == "working"
    assert data["current_task_id"] == task["id"]
    assert data["active_task_count"] == 1

    # 3. Verify task appears in tasks list
    resp = await client.get(f"/api/v1/agents/{agent_id}/tasks")
    assert len(resp.json()) == 1
    assert resp.json()[0]["task_id"] == task["id"]

    # 4. Unassign: idle
    resp = await client.delete(f"/api/v1/agents/{agent_id}/assign/{task['id']}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/agents/{agent_id}/status")
    data = resp.json()
    assert data["status"] == "idle"
    assert data["current_task_id"] is None
    assert data["active_task_count"] == 0

    # 5. Verify tasks list is empty
    resp = await client.get(f"/api/v1/agents/{agent_id}/tasks")
    assert resp.json() == []
