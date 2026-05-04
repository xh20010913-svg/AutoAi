"""Tests for the auto-assign service and API endpoints."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.database import get_session
from app.models.project import Agent, Base, Task
from app.schemas.task import TaskCreate
from app.services.auto_assign import (
    apply_starvation_boost,
    compute_agent_score,
    compute_load_score,
    compute_skill_match,
    get_agent_task_count,
)

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


async def _create_agent(
    session: AsyncSession,
    name: str = "TestAgent",
    role: str = "backend",
    skills: list[str] | None = None,
    status: str = "idle",
    max_concurrent_tasks: int = 3,
    success_rate: float = 1.0,
) -> Agent:
    agent = Agent(
        name=name,
        role=role,
        skills=json.dumps(skills or []),
        status=status,
        max_concurrent_tasks=max_concurrent_tasks,
        success_rate=success_rate,
    )
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return agent


async def _create_task_db(
    session: AsyncSession,
    title: str = "Test Task",
    status: str = "todo",
    priority: str = "medium",
    assignee_id: str | None = None,
    assignee: str = "",
    description: str = "",
) -> Task:
    task = Task(
        title=title,
        description=description,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        assignee=assignee,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


# ─── Unit tests: scoring functions ─────────────────────────────────────────────


class TestSkillMatch:
    def test_role_keyword_in_title(self):
        agent = Agent(name="BE", role="backend", skills="[]")
        task = Task(title="Implement API endpoint", description="")
        score = compute_skill_match(agent, task)
        assert score > 0.3

    def test_role_keyword_in_description(self):
        agent = Agent(name="FE", role="frontend", skills="[]")
        task = Task(title="Fix bug", description="Update React component styling")
        score = compute_skill_match(agent, task)
        assert score > 0.3

    def test_tester_role_match(self):
        agent = Agent(name="QA", role="tester", skills="[]")
        task = Task(title="Write e2e tests", description="")
        score = compute_skill_match(agent, task)
        assert score > 0.3

    def test_no_match_returns_baseline(self):
        agent = Agent(name="PM", role="pm", skills="[]")
        task = Task(title="Unknown topic", description="Nothing relevant")
        score = compute_skill_match(agent, task)
        assert score == 0.3

    def test_skill_tags_match(self):
        agent = Agent(name="BE", role="backend", skills='["python", "api", "database"]')
        task = Task(title="Create python API", description="")
        score = compute_skill_match(agent, task)
        assert score > 0.3

    def test_chinese_keywords(self):
        agent = Agent(name="后端", role="backend", skills="[]")
        task = Task(title="实现后端数据库接口", description="")
        score = compute_skill_match(agent, task)
        assert score > 0.3

    def test_max_score_capped(self):
        agent = Agent(name="BE", role="backend", skills='["api", "database"]')
        task = Task(title="API backend server database endpoint API backend")
        score = compute_skill_match(agent, task)
        assert 0.0 <= score <= 1.0


class TestLoadScore:
    def test_no_load(self):
        agent = Agent(name="A", max_concurrent_tasks=3)
        assert compute_load_score(agent, 0) == 1.0

    def test_half_load(self):
        agent = Agent(name="A", max_concurrent_tasks=4)
        assert compute_load_score(agent, 2) == 0.5

    def test_full_load(self):
        agent = Agent(name="A", max_concurrent_tasks=3)
        assert compute_load_score(agent, 3) == 0.0

    def test_over_capacity(self):
        agent = Agent(name="A", max_concurrent_tasks=3)
        assert compute_load_score(agent, 5) == 0.0

    def test_zero_max_tasks(self):
        agent = Agent(name="A", max_concurrent_tasks=0)
        assert compute_load_score(agent, 0) == 0.0


class TestAgentScore:
    def test_full_score_with_custom_weights(self):
        agent = Agent(name="BE", role="backend", skills="[]", success_rate=0.9, max_concurrent_tasks=10)
        task = Task(title="Implement API endpoint", description="backend server")
        score = compute_agent_score(agent, task, 0, w_skill=0.4, w_load=0.3, w_success=0.3)
        # skill_match > 0, load=1.0, success=0.9
        assert 0.0 < score <= 1.0

    def test_busy_agent_scores_lower(self):
        agent = Agent(name="BE", role="backend", skills="[]", success_rate=1.0, max_concurrent_tasks=3)
        task = Task(title="Test", description="")
        score_idle = compute_agent_score(agent, task, 0)
        score_busy = compute_agent_score(agent, task, 3)
        assert score_idle > score_busy

    def test_low_success_agent_scores_lower(self):
        task = Task(title="Test", description="")
        good = Agent(name="G", role="backend", success_rate=1.0, max_concurrent_tasks=10, skills="[]")
        bad = Agent(name="B", role="backend", success_rate=0.1, max_concurrent_tasks=10, skills="[]")
        assert compute_agent_score(good, task, 0) > compute_agent_score(bad, task, 0)


# ─── Unit tests: starvation boost ─────────────────────────────────────────────


class TestStarvationBoost:
    def test_priority_order_maintained(self):
        now = datetime.utcnow()
        tasks = [
            Task(title="L", priority="low", created_at=now),
            Task(title="H", priority="high", created_at=now),
            Task(title="M", priority="medium", created_at=now),
            Task(title="U", priority="urgent", created_at=now),
        ]
        ordered = apply_starvation_boost(tasks)
        priorities = [t.priority for t in ordered]
        assert priorities == ["urgent", "high", "medium", "low"]

    def test_old_task_gets_boosted(self):
        old_time = datetime.utcnow() - timedelta(minutes=60)
        recent_time = datetime.utcnow()
        tasks = [
            Task(title="Old Medium", priority="medium", created_at=old_time),
            Task(title="New High", priority="high", created_at=recent_time),
        ]
        ordered = apply_starvation_boost(tasks)
        # Old medium task should be boosted and come before new high
        assert ordered[0].title == "Old Medium"

    def test_same_priority_sorted_by_created_at(self):
        t1 = datetime.utcnow() - timedelta(hours=2)
        t2 = datetime.utcnow() - timedelta(hours=1)
        tasks = [
            Task(title="B", priority="medium", created_at=t2),
            Task(title="A", priority="medium", created_at=t1),
        ]
        ordered = apply_starvation_boost(tasks)
        assert ordered[0].title == "A"


# ─── Integration tests: service layer ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_agent_task_count():
    async with TestingSession() as session:
        agent = await _create_agent(session, name="Test BE")
        # No tasks assigned
        count = await get_agent_task_count(session, agent.id)
        assert count == 0

        # Add in-progress task
        task = await _create_task_db(session, assignee_id=agent.id, status="in_progress")
        count = await get_agent_task_count(session, agent.id)
        assert count == 1

        # Add done task (should not count)
        await _create_task_db(session, assignee_id=agent.id, status="done")
        count = await get_agent_task_count(session, agent.id)
        assert count == 1


@pytest.mark.asyncio
async def test_auto_assign_task_via_service():
    async with TestingSession() as session:
        agent = await _create_agent(session, name="BE Agent", role="backend")
        task = await _create_task_db(session, title="Build API", status="todo", description="backend service")

        from app.services.auto_assign import auto_assign_task

        result = await auto_assign_task(session, task.id)
        assert result is not None
        assert result.assignee_id == agent.id
        assert result.assignee == agent.name


@pytest.mark.asyncio
async def test_auto_assign_skips_non_todo():
    async with TestingSession() as session:
        agent = await _create_agent(session, name="Agent")
        task = await _create_task_db(session, title="Done", status="done")

        from app.services.auto_assign import auto_assign_task

        result = await auto_assign_task(session, task.id)
        assert result is None


@pytest.mark.asyncio
async def test_auto_assign_task_not_found():
    async with TestingSession() as session:
        from app.services.auto_assign import auto_assign_task

        result = await auto_assign_task(session, "nonexistent-id")
        assert result is None


@pytest.mark.asyncio
async def test_auto_assign_no_agents():
    async with TestingSession() as session:
        task = await _create_task_db(session, title="Test", status="todo")

        from app.services.auto_assign import auto_assign_task

        result = await auto_assign_task(session, task.id)
        assert result is None


@pytest.mark.asyncio
async def test_auto_assign_all_busy():
    async with TestingSession() as session:
        agent = await _create_agent(session, name="Busy BE", max_concurrent_tasks=1)
        await _create_task_db(session, assignee_id=agent.id, status="in_progress")

        task = await _create_task_db(session, title="New Task", status="todo")

        from app.services.auto_assign import auto_assign_all

        assignments = await auto_assign_all(session)
        assert assignments == []


@pytest.mark.asyncio
async def test_auto_assign_all_respects_priority():
    async with TestingSession() as session:
        agent = await _create_agent(session, name="Agent", max_concurrent_tasks=10)
        await _create_task_db(session, title="Low prio", priority="low", status="todo")
        await _create_task_db(session, title="Urgent!", priority="urgent", status="todo")

        from app.services.auto_assign import auto_assign_all

        assignments = await auto_assign_all(session)
        assert len(assignments) == 2
        # Urgent should be assigned first
        assert assignments[0]["priority"] == "urgent"


@pytest.mark.asyncio
async def test_auto_assign_skips_assigned_tasks():
    async with TestingSession() as session:
        agent = await _create_agent(session, name="Agent")
        # Already assigned todo task
        await _create_task_db(session, title="Already assigned", status="todo", assignee_id=agent.id)
        # Unassigned todo task
        await _create_task_db(session, title="Unassigned", status="todo")

        from app.services.auto_assign import auto_assign_all

        assignments = await auto_assign_all(session)
        assert len(assignments) == 1
        assert assignments[0]["task_title"] == "Unassigned"


@pytest.mark.asyncio
async def test_auto_assign_skips_error_agents():
    async with TestingSession() as session:
        await _create_agent(session, name="Error Agent", status="error")
        task = await _create_task_db(session, title="Task", status="todo")

        from app.services.auto_assign import auto_assign_task

        result = await auto_assign_task(session, task.id)
        assert result is None


@pytest.mark.asyncio
async def test_agent_with_best_score_wins():
    async with TestingSession() as session:
        # Bad agent: low success rate
        await _create_agent(session, name="Bad BE", role="backend", success_rate=0.2, max_concurrent_tasks=10)
        # Good agent: high success rate
        good = await _create_agent(session, name="Good BE", role="backend", success_rate=1.0, max_concurrent_tasks=10)

        task = await _create_task_db(session, title="Build API backend", status="todo")

        from app.services.auto_assign import auto_assign_task

        result = await auto_assign_task(session, task.id)
        assert result is not None
        assert result.assignee_id == good.id


# ─── Integration tests: API endpoints ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_api_auto_assign_single(client: AsyncClient):
    # Create agent via API
    agent_resp = await client.post(
        "/api/v1/agents",
        json={"name": "API Agent", "role": "backend", "skills": ["api"], "max_concurrent_tasks": 5},
    )
    assert agent_resp.status_code == 201
    agent = agent_resp.json()

    # Create task via API
    task_resp = await client.post(
        "/api/v1/tasks",
        json={"title": "Build REST API", "description": "backend work", "priority": "high"},
    )
    assert task_resp.status_code == 201
    task = task_resp.json()

    # Auto-assign
    resp = await client.post(f"/api/v1/tasks/{task['id']}/auto-assign")
    assert resp.status_code == 200
    data = resp.json()
    assert data["assignee_id"] == agent["id"]
    assert data["assignee"] == "API Agent"


@pytest.mark.asyncio
async def test_api_auto_assign_nonexistent_task(client: AsyncClient):
    resp = await client.post("/api/v1/tasks/nonexistent-id/auto-assign")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_api_auto_assign_no_agent(client: AsyncClient):
    task_resp = await client.post("/api/v1/tasks", json={"title": "No agents yet"})
    assert task_resp.status_code == 201
    task = task_resp.json()

    resp = await client.post(f"/api/v1/tasks/{task['id']}/auto-assign")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_api_auto_assign_all(client: AsyncClient):
    # Create agent
    await client.post(
        "/api/v1/agents",
        json={"name": "Batch Agent", "role": "backend", "max_concurrent_tasks": 10},
    )

    # Create tasks
    await client.post("/api/v1/tasks", json={"title": "Task 1", "priority": "high"})
    await client.post("/api/v1/tasks", json={"title": "Task 2", "priority": "low"})

    resp = await client.post("/api/v1/tasks/auto-assign")
    assert resp.status_code == 200
    data = resp.json()
    assert data["assigned"] == 2
    assert len(data["assignments"]) == 2


@pytest.mark.asyncio
async def test_api_auto_assign_all_no_tasks(client: AsyncClient):
    resp = await client.post("/api/v1/tasks/auto-assign")
    assert resp.status_code == 200
    data = resp.json()
    assert data["assigned"] == 0
    assert data["assignments"] == []


@pytest.mark.asyncio
async def test_api_agents_crud(client: AsyncClient):
    # Create
    resp = await client.post(
        "/api/v1/agents",
        json={"name": "CRUD Agent", "role": "tester", "skills": ["e2e", "unit"], "max_concurrent_tasks": 5},
    )
    assert resp.status_code == 201
    agent = resp.json()
    assert agent["name"] == "CRUD Agent"
    assert agent["skills"] == ["e2e", "unit"]
    agent_id = agent["id"]

    # List
    resp = await client.get("/api/v1/agents")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Get
    resp = await client.get(f"/api/v1/agents/{agent_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "CRUD Agent"

    # Update
    resp = await client.put(
        f"/api/v1/agents/{agent_id}",
        json={"name": "Updated Agent", "success_rate": 0.85},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Agent"
    assert resp.json()["success_rate"] == 0.85

    # Delete
    resp = await client.delete(f"/api/v1/agents/{agent_id}")
    assert resp.status_code == 204

    # Verify deleted
    resp = await client.get(f"/api/v1/agents/{agent_id}")
    assert resp.status_code == 404
