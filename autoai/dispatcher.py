from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .db import ensure_db, get_session
from .models import Role, Task
from .roles import load_roles
from .time_utils import utc_now_iso

log = logging.getLogger(__name__)

TASK_GRAPH_PATH = Path(".autoai") / "task_graph.json"

# Priority ordering for scheduling (lower = higher priority)
_PRIORITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


def load_task_graph(project_dir: Path) -> list[dict[str, Any]]:
    """Load task graph from .autoai/task_graph.json."""
    path = project_dir / TASK_GRAPH_PATH
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("tasks", [])


def save_task_graph(project_dir: Path, tasks: list[dict[str, Any]]) -> None:
    """Persist task graph to .autoai/task_graph.json."""
    path = project_dir / TASK_GRAPH_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def _dependencies_satisfied(task: dict[str, Any], all_tasks: list[dict[str, Any]]) -> bool:
    """Return True when every dependency of *task* is done."""
    depends_on = task.get("depends_on", [])
    if not depends_on:
        return True
    lookup = {t["id"]: t for t in all_tasks}
    for dep_id in depends_on:
        dep = lookup.get(dep_id)
        if dep is None or dep.get("status") != "done":
            return False
    return True


def _role_has_budget(role_config: dict[str, Any], budget: dict[str, Any]) -> bool:
    """Return True when the role still has budget remaining."""
    if not budget:
        return True
    token_budget = role_config.get("token_budget", {})
    for key in ("max_prompt_chars", "max_output_chars", "max_files", "timeout_seconds"):
        limit = token_budget.get(key, 0)
        used = budget.get(key, 0)
        if limit and used >= limit:
            return False
    return True


def _score_task(task: dict[str, Any]) -> tuple[int, str]:
    """Return a sort key: (priority_rank, created_at)."""
    priority = task.get("priority", "medium")
    return (_PRIORITY_ORDER.get(priority, 9), task.get("created_at", ""))


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def select_next_task(
    project_dir: Path,
    task_graph: dict[str, Any] | list[dict[str, Any]] | None = None,
    role_budgets: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Pick the best executable task from the task graph.

    Parameters
    ----------
    project_dir:
        Project root (used to load the graph when *task_graph* is ``None``).
    task_graph:
        Either a list of task dicts **or** a dict with a ``"tasks"`` key.
        When ``None`` the graph is loaded from ``.autoai/task_graph.json``.
    role_budgets:
        Optional mapping of ``role_id → {resource: used_so_far}`` used to
        skip roles that have exhausted their budget.
    """
    if task_graph is None:
        tasks = load_task_graph(project_dir)
    elif isinstance(task_graph, dict):
        tasks = task_graph.get("tasks", [])
    else:
        tasks = list(task_graph)

    # Filter to todo tasks whose deps are satisfied
    candidates: list[dict[str, Any]] = []
    for t in tasks:
        if t.get("status") != "todo":
            continue
        if not _dependencies_satisfied(t, tasks):
            continue
        if role_budgets:
            role_id = t.get("suggested_role", "")
            if role_id and role_id in role_budgets:
                # Load role config for budget check
                ensure_db(project_dir)
                with get_session() as session:
                    role_row = session.query(Role).filter(Role.id == role_id).first()
                if role_row:
                    role_cfg = role_row.to_dict()
                    if not _role_has_budget(role_cfg, role_budgets[role_id]):
                        continue
        candidates.append(t)

    if not candidates:
        return None

    candidates.sort(key=_score_task)
    return candidates[0]


def assign_task(
    project_dir: Path,
    task_id: str,
    role: str,
    task_graph: list[dict[str, Any]] | None = None,
) -> bool:
    """Assign *role* to *task_id* in the task graph and DB.

    Returns ``True`` if the task was found and updated.
    """
    if task_graph is None:
        task_graph = load_task_graph(project_dir)

    updated = False
    for t in task_graph:
        if t.get("id") == task_id:
            t["suggested_role"] = role
            t["status"] = "in_progress"
            t["updated_at"] = utc_now_iso()
            updated = True
            break

    if updated:
        save_task_graph(project_dir, task_graph)

    # Also update DB task if it exists
    ensure_db(project_dir)
    with get_session() as session:
        db_task = session.query(Task).filter(Task.id == task_id).first()
        if db_task:
            db_task.assignee = role
            db_task.status = "in_progress"
            db_task.updated_at = utc_now_iso()
            session.commit()
            updated = True

    return updated
