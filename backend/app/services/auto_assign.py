"""
Smart Task Auto-Assignment Service

Scoring model:
  score = skill_match × w_skill + load_score × w_load + success_rate × w_success

Where:
  - skill_match:  0.0-1.0  how well agent skills match the task role/category
  - load_score:   0.0-1.0  1.0 = no load, 0.0 = at max capacity
  - success_rate: 0.0-1.0  agent's historical success rate

Priority queue: urgent > high > medium > low
Starvation prevention: tasks waiting > threshold get priority boost.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.project import Agent, Task

logger = logging.getLogger(__name__)

PRIORITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


def _parse_skills(raw: str) -> list[str]:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []


def compute_skill_match(agent: Agent, task: Task) -> float:
    """Compute how well an agent's skills match a task.

    Uses role match as primary signal, keyword overlap as secondary.
    Returns 0.0-1.0.
    """
    score = 0.0
    task_text = f"{task.title} {task.description}".lower()
    agent_role = agent.role.lower()

    # Primary: role keyword in task title/description
    role_keywords = {
        "backend": ["backend", "api", "server", "数据库", "后端", "database", "endpoint"],
        "frontend": ["frontend", "前端", "ui", "react", "vue", "css", "页面", "component"],
        "tester": ["test", "测试", "qa", "quality", "spec", "e2e"],
        "algorithm": ["算法", "algorithm", "调度", "scheduling", "model"],
        "pm": ["pm", "产品", "product", "需求", "requirement"],
    }

    keywords = role_keywords.get(agent_role, [agent_role])
    matches = sum(1 for kw in keywords if kw in task_text)
    if matches > 0:
        score = min(1.0, matches * 0.3)

    # Secondary: explicit skill overlap
    agent_skills = _parse_skills(agent.skills)
    if agent_skills:
        skill_matches = sum(1 for s in agent_skills if s.lower() in task_text)
        skill_score = min(1.0, skill_matches * 0.25)
        score = max(score, skill_score)

    # Default: if no signals, give a baseline based on role
    if score == 0.0:
        score = 0.3

    return score


def compute_load_score(agent: Agent, current_tasks: int) -> float:
    """Compute load score: 1.0 = no load, 0.0 = at max capacity."""
    if agent.max_concurrent_tasks <= 0:
        return 0.0
    ratio = current_tasks / agent.max_concurrent_tasks
    return max(0.0, 1.0 - ratio)


def compute_agent_score(
    agent: Agent,
    task: Task,
    current_tasks: int,
    w_skill: float | None = None,
    w_load: float | None = None,
    w_success: float | None = None,
) -> float:
    """Compute overall assignment score for an agent on a task."""
    w_skill = w_skill if w_skill is not None else settings.WEIGHT_SKILL_MATCH
    w_load = w_load if w_load is not None else settings.WEIGHT_LOAD
    w_success = w_success if w_success is not None else settings.WEIGHT_SUCCESS_RATE

    skill_match = compute_skill_match(agent, task)
    load_score = compute_load_score(agent, current_tasks)
    success_rate = max(0.0, min(1.0, agent.success_rate))

    return skill_match * w_skill + load_score * w_load + success_rate * w_success


async def get_agent_task_count(session: AsyncSession, agent_id: str) -> int:
    """Count in-progress tasks assigned to an agent."""
    stmt = (
        select(func.count(Task.id))
        .where(Task.assignee_id == agent_id)
        .where(Task.status == "in_progress")
    )
    result = await session.execute(stmt)
    return result.scalar() or 0


def apply_starvation_boost(tasks: list[Task]) -> list[Task]:
    """Boost priority of tasks waiting too long.

    Tasks waiting > STARVATION_THRESHOLD_MINUTES get bumped up in the queue.
    """
    threshold = timedelta(minutes=settings.STARVATION_THRESHOLD_MINUTES)
    now = datetime.utcnow()

    def sort_key(t: Task) -> tuple:
        priority_val = PRIORITY_ORDER.get(t.priority, 2)
        waiting = now - t.created_at
        # Boost: if waiting too long, treat as one priority level higher
        if waiting > threshold:
            priority_val = max(0, priority_val - 1)
        return (priority_val, t.created_at)

    return sorted(tasks, key=sort_key)


async def auto_assign_single(
    session: AsyncSession,
    task: Task,
) -> Agent | None:
    """Find the best agent for a single task.

    Returns the best Agent or None if no suitable agent found.
    """
    # Get all available agents
    result = await session.execute(
        select(Agent).where(Agent.status != "error")
    )
    agents = result.scalars().all()

    if not agents:
        return None

    best_agent: Agent | None = None
    best_score = -1.0

    for agent in agents:
        current_tasks = await get_agent_task_count(session, agent.id)

        # Skip agents at max capacity
        if current_tasks >= agent.max_concurrent_tasks:
            continue

        score = compute_agent_score(agent, task, current_tasks)
        if score > best_score:
            best_score = score
            best_agent = agent

    if best_agent:
        logger.info(
            "Auto-assigned task %s to agent %s (score=%.3f)",
            task.id, best_agent.name, best_score,
        )

    return best_agent


async def auto_assign_task(
    session: AsyncSession,
    task_id: str,
) -> Task | None:
    """Auto-assign a single task by ID.

    Returns the updated Task or None if task/agent not found.
    """
    task = await session.get(Task, task_id)
    if not task:
        return None

    if task.status != "todo":
        return None

    agent = await auto_assign_single(session, task)
    if not agent:
        return None

    task.assignee_id = agent.id
    task.assignee = agent.name
    await session.commit()
    await session.refresh(task)
    return task


async def auto_assign_all(session: AsyncSession) -> list[dict]:
    """Scan all todo tasks and auto-assign them.

    Respects priority queue with starvation prevention.
    Returns list of assignment results.
    """
    # Get all unassigned todo tasks
    result = await session.execute(
        select(Task)
        .where(Task.status == "todo")
        .where(Task.assignee_id.is_(None))
    )
    tasks = list(result.scalars().all())

    if not tasks:
        return []

    # Sort by priority with starvation boost
    ordered = apply_starvation_boost(tasks)

    assignments = []
    for task in ordered:
        agent = await auto_assign_single(session, task)
        if agent:
            task.assignee_id = agent.id
            task.assignee = agent.name
            await session.commit()
            await session.refresh(task)
            assignments.append({
                "task_id": task.id,
                "task_title": task.title,
                "agent_id": agent.id,
                "agent_name": agent.name,
                "priority": task.priority,
            })

    if assignments:
        logger.info("Auto-assigned %d tasks", len(assignments))

    return assignments
