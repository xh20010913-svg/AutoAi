from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

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
