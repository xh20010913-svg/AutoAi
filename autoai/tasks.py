from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from .db import ensure_db, get_session
from .models import Task
from .time_utils import utc_now_iso


VALID_STATUSES = {"backlog", "todo", "in_progress", "in_review", "done", "blocked", "cancelled"}
VALID_PRIORITIES = {"low", "medium", "high", "urgent"}


def list_tasks(project_dir: Path) -> list[dict[str, Any]]:
    ensure_db(project_dir)
    with get_session() as session:
        tasks = session.query(Task).order_by(Task.created_at).all()
        return [t.to_dict() for t in tasks]


def create_task(
    project_dir: Path,
    title: str,
    description: str = "",
    priority: str = "medium",
    assignee: str = "",
    status: str = "todo",
) -> dict[str, Any]:
    title = title.strip()
    if not title:
        raise ValueError("Task title is required.")
    _validate_status(status)
    _validate_priority(priority)
    ensure_db(project_dir)
    now = utc_now_iso()
    task = Task(
        id="T-" + uuid.uuid4().hex[:8],
        title=title,
        description=description.strip(),
        status=status,
        priority=priority,
        assignee=assignee.strip(),
        created_at=now,
        updated_at=now,
    )
    with get_session() as session:
        session.add(task)
        session.commit()
        return task.to_dict()


def update_task_status(project_dir: Path, task_id: str, status: str) -> dict[str, Any]:
    _validate_status(status)
    ensure_db(project_dir)
    with get_session() as session:
        task = session.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        task.status = status
        task.updated_at = utc_now_iso()
        session.commit()
        return task.to_dict()


def update_task(project_dir: Path, task_id: str, **fields: Any) -> dict[str, Any]:
    ensure_db(project_dir)
    with get_session() as session:
        task = session.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        for key, value in fields.items():
            if key == "status" and value is not None:
                _validate_status(value)
                task.status = value
            elif key == "priority" and value is not None:
                _validate_priority(value)
                task.priority = value
            elif key in ("title", "description", "assignee") and value is not None:
                setattr(task, key, value)
        task.updated_at = utc_now_iso()
        session.commit()
        return task.to_dict()


def open_task_summary(project_dir: Path, limit: int = 12) -> str:
    tasks = [
        item
        for item in list_tasks(project_dir)
        if item["status"] not in {"done", "cancelled"}
    ]
    if not tasks:
        return "No open tasks are recorded."
    order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    tasks.sort(key=lambda item: (order.get(item["priority"], 9), item["created_at"]))
    lines = ["Open task queue:"]
    for task in tasks[:limit]:
        assignee = f", assignee={task['assignee']}" if task["assignee"] else ""
        lines.append(
            f"- {task['id']} [{task['priority']}/{task['status']}{assignee}] {task['title']}"
        )
        if task["description"]:
            lines.append(f"  {task['description']}")
    if len(tasks) > limit:
        lines.append(f"- ... {len(tasks) - limit} more open tasks omitted from this prompt.")
    return "\n".join(lines)


def _validate_status(status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid task status: {status}")


def _validate_priority(priority: str) -> None:
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"Invalid task priority: {priority}")
