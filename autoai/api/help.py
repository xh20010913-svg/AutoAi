from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from ..help_requests import answer_help_request, close_help_request, create_help_request, list_help_requests

router = APIRouter(prefix="/api/help", tags=["help"])


def _get_project_dir(body: dict[str, Any]) -> Path:
    raw = body.get("project_dir", "")
    if not raw:
        raise HTTPException(400, "Missing project_dir")
    return Path(raw).expanduser()


@router.get("")
def get_help(project_dir: str):
    pd = Path(project_dir).expanduser()
    return {"help_requests": list_help_requests(pd)}


@router.post("")
def post_help(body: dict[str, Any]):
    pd = _get_project_dir(body)
    try:
        req = create_help_request(
            project_dir=pd,
            title=str(body.get("title", "")),
            detail=str(body.get("detail", "")),
            severity=str(body.get("severity", "blocking")),
            task_id=str(body.get("task_id", "")),
            role_id=str(body.get("role_id", "")),
            session_id=str(body.get("session_id", "")),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"help_request": req}


@router.post("/{request_id}/answer")
def post_answer(request_id: str, body: dict[str, Any]):
    pd = _get_project_dir(body)
    try:
        req = answer_help_request(pd, request_id, str(body.get("answer", "")))
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"help_request": req}


@router.post("/{request_id}/close")
def post_close(request_id: str, body: dict[str, Any]):
    pd = _get_project_dir(body)
    try:
        req = close_help_request(pd, request_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"help_request": req}
