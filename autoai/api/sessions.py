from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..constants import session_dir

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("")
def get_sessions(project_dir: str):
    pd = Path(project_dir).expanduser()
    return {"sessions": _session_history(pd)}


@router.get("/{session_id}")
def get_session_detail(session_id: str, project_dir: str):
    pd = Path(project_dir).expanduser()
    if not session_id:
        raise HTTPException(400, "Missing session id")
    return {"session": _session_detail(pd, session_id)}


def _session_history(project_dir: Path) -> list[dict]:
    root = session_dir(project_dir)
    if not root.exists():
        return []
    grouped: dict[str, dict] = {}
    for file in root.iterdir():
        if not file.is_file():
            continue
        session_id, file_kind = _split_session_filename(file.name)
        item = grouped.setdefault(
            session_id,
            {"id": session_id, "files": [], "updated_at": file.stat().st_mtime, "kind": _session_kind_from_id(session_id)},
        )
        item["files"].append({"name": file.name, "kind": file_kind, "size": file.stat().st_size})
        item["updated_at"] = max(item["updated_at"], file.stat().st_mtime)
    return sorted(grouped.values(), key=lambda item: item["id"], reverse=True)


def _session_detail(project_dir: Path, session_id: str) -> dict:
    root = session_dir(project_dir)
    if not root.exists():
        raise HTTPException(404, "No sessions directory")
    detail = {"id": session_id, "kind": _session_kind_from_id(session_id), "files": {}}
    for file in root.iterdir():
        if file.is_file() and file.name.startswith(session_id + "."):
            _, file_kind = _split_session_filename(file.name)
            detail["files"][file_kind] = file.read_text(encoding="utf-8", errors="replace")
    return detail


def _split_session_filename(filename: str) -> tuple[str, str]:
    suffixes = {
        ".prompt.md": "prompt",
        ".agent.stdout.log": "agent_stdout",
        ".agent.stderr.log": "agent_stderr",
        ".verify.stdout.log": "verify_stdout",
        ".verify.stderr.log": "verify_stderr",
    }
    for suffix, kind in suffixes.items():
        if filename.endswith(suffix):
            return filename[: -len(suffix)], kind
    return filename.split(".", 1)[0], "other"


def _session_kind_from_id(session_id: str) -> str:
    if "-initializer-" in session_id:
        return "initializer"
    if "-coding-" in session_id:
        return "coding"
    return "unknown"
