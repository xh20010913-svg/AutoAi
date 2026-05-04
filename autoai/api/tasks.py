from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from ..dispatcher import assign_task, load_task_graph, select_next_task
from ..tasks import create_task, list_tasks, update_task, update_task_status

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _get_project_dir(body: dict[str, Any]) -> Path:
    raw = body.get("project_dir", "")
    if not raw:
        raise HTTPException(400, "Missing project_dir")
    return Path(raw).expanduser()


@router.get("")
def get_tasks(project_dir: str):
    pd = Path(project_dir).expanduser()
    return {"tasks": list_tasks(pd)}


@router.post("")
def post_task(body: dict[str, Any]):
    pd = _get_project_dir(body)
    task = create_task(
        project_dir=pd,
        title=str(body.get("title", "")),
        description=str(body.get("description", "")),
        priority=str(body.get("priority", "medium")),
        assignee=str(body.get("assignee", "")),
        status=str(body.get("status", "todo")),
    )
    return {"task": task}


@router.patch("/{task_id}")
def patch_task(task_id: str, body: dict[str, Any]):
    pd = _get_project_dir(body)
    fields = {}
    for key in ("title", "description", "status", "priority", "assignee"):
        if key in body:
            fields[key] = body[key]
    try:
        task = update_task(pd, task_id, **fields)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"task": task}


@router.post("/assign")
def post_assign(body: dict[str, Any]):
    """Manually assign a task to a role."""
    pd = _get_project_dir(body)
    task_id = str(body.get("task_id", ""))
    role = str(body.get("role", ""))
    if not task_id:
        raise HTTPException(400, "Missing task_id")
    if not role:
        raise HTTPException(400, "Missing role")
    task_graph = body.get("task_graph")
    if task_graph is not None and not isinstance(task_graph, list):
        task_graph = None
    ok = assign_task(pd, task_id, role, task_graph=task_graph)
    if not ok:
        raise HTTPException(404, f"Task not found: {task_id}")
    return {"status": "assigned", "task_id": task_id, "role": role}


@router.get("/next")
def get_next_task(project_dir: str, role_budgets: str | None = None):
    """Return the next executable task from the task graph."""
    pd = Path(project_dir).expanduser()
    budgets = None
    if role_budgets:
        try:
            budgets = json.loads(role_budgets)
        except json.JSONDecodeError:
            raise HTTPException(400, "role_budgets must be valid JSON")
    task = select_next_task(pd, role_budgets=budgets)
    if task is None:
        return {"task": None}
    return {"task": task}
