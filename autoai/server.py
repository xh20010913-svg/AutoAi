from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import agents, help, run, sessions, tasks
from .claude_settings import claude_settings_status, set_skip_dangerous_mode_prompt
from .config import AutoAIConfig, load_config
from .constants import FEATURE_FILE, PROGRESS_FILE, session_dir
from .features import feature_status, validate_feature_invariants
from .help_requests import open_help_requests
from .project import init_project
from .prompts import render_prompt
from .roles import roles_for_api
from .state import load_state

app = FastAPI(title="AutoAI", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(help.router)
app.include_router(agents.router)
app.include_router(sessions.router)
app.include_router(run.router)

# --- WebSocket ---
_ws_clients: set[WebSocket] = set()


async def _ws_handler(ws: WebSocket):
    await ws.accept()
    _ws_clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        _ws_clients.discard(ws)
    except Exception:
        _ws_clients.discard(ws)


def _broadcast(event: dict) -> None:
    if not _ws_clients:
        return
    msg = json.dumps(event, ensure_ascii=False)
    loop = None
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        pass
    if loop and loop.is_running():
        for ws in list(_ws_clients):
            try:
                asyncio.create_task(ws.send_text(msg))
            except Exception:
                _ws_clients.discard(ws)


run.set_ws_broadcast(_broadcast)

app.add_websocket_route("/ws", _ws_handler)


# --- REST endpoints ---
@app.get("/api/status")
def api_status(project_dir: str = ""):
    if not project_dir:
        return JSONResponse({"error": "Missing project_dir"}, 400)
    pd = Path(project_dir).expanduser()
    config = _safe_config(pd)
    state = load_state(pd)
    status = feature_status(pd)
    validation = validate_feature_invariants(pd)
    help_open = open_help_requests(pd) if pd.exists() else []
    roles = roles_for_api(pd) if config else []
    return {
        "project_dir": str(pd.resolve()),
        "exists": pd.exists(),
        "configured": config is not None,
        "goal": config.goal if config else "",
        "feature_count": config.feature_count if config else 50,
        "agent_command": config.agent_command if config else "",
        "verify_command": config.verify_command if config else "",
        "permission_mode": config.permission_mode if config else "default",
        "collaboration_mode": config.collaboration_mode if config else "single",
        "next_session": state.next_session,
        "last_status": state.last_status,
        "last_session_id": state.last_session_id,
        "consecutive_failures": state.consecutive_failures,
        "features": {
            "total": status.total,
            "passing": status.passing,
            "failing": status.failing,
            "complete": status.complete,
        },
        "first_run_pending": not (pd / FEATURE_FILE).exists(),
        "validation": {"ok": validation.ok, "messages": validation.messages},
        "help": {"open": len(help_open)},
        "roles": {
            "total": len(roles),
            "custom_models": sum(1 for r in roles if r.get("model")),
            "custom_keys": sum(1 for r in roles if r.get("has_api_key") or r.get("api_key_env")),
        },
        "sessions_dir": str(session_dir(pd).resolve()),
    }


@app.post("/api/init")
def api_init(body: dict[str, Any]):
    pd = Path(body.get("project_dir", "")).expanduser()
    if not body.get("project_dir"):
        return JSONResponse({"error": "Missing project_dir"}, 400)
    init_project(
        project_dir=pd,
        goal=str(body.get("goal", "")).strip(),
        feature_count=int(body.get("feature_count", 50)),
        agent_command=_optional_str(body.get("agent_command")),
        verify_command=_optional_str(body.get("verify_command")),
        permission_mode=str(body.get("permission_mode", "default")),
        init_git=bool(body.get("init_git", True)),
        collaboration_mode=str(body.get("collaboration_mode", "single")),
        spec_text=_optional_str(body.get("spec_text")),
        spec_filename=_optional_str(body.get("spec_filename")),
    )
    from .agents import sync_agents_from_roles
    if bool(body.get("install_agents", True)):
        sync_agents_from_roles(pd)
    return api_status(str(pd.resolve()))


@app.get("/api/spec")
def api_spec(project_dir: str = ""):
    pd = Path(project_dir).expanduser()
    spec = pd / "task_spec.md"
    return {"spec": spec.read_text(encoding="utf-8") if spec.exists() else ""}


@app.get("/api/progress")
def api_progress(project_dir: str = ""):
    pd = Path(project_dir).expanduser()
    progress = pd / PROGRESS_FILE
    return {"progress": progress.read_text(encoding="utf-8") if progress.exists() else ""}


@app.get("/api/prompts/{kind}")
def api_prompt(kind: str, project_dir: str = ""):
    pd = Path(project_dir).expanduser()
    config = load_config(pd)
    return {"prompt": render_prompt(kind, pd, config)}


@app.get("/api/validate")
def api_validate(project_dir: str = ""):
    pd = Path(project_dir).expanduser()
    result = validate_feature_invariants(pd)
    return {"ok": result.ok, "messages": result.messages}


@app.get("/api/claude-settings")
def api_claude_settings():
    return {"settings": claude_settings_status()}


@app.post("/api/claude-settings/skip-bypass")
def api_claude_skip_bypass(body: dict[str, Any]):
    settings = set_skip_dangerous_mode_prompt(bool(body.get("enabled", True)))
    return {"settings": settings}


# --- Static files (Electron frontend) ---
_STATIC_DIR = Path(__file__).parent / "ui_static"


@app.get("/")
def index():
    index_file = _STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "AutoAI backend is running. Open the Electron app to use the UI."}


def _safe_config(project_dir: Path) -> AutoAIConfig | None:
    try:
        return load_config(project_dir)
    except FileNotFoundError:
        return None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def status_payload(project_dir: Path) -> dict[str, Any]:
    """Build status payload for a project dir (used by tests and API)."""
    config = _safe_config(project_dir)
    state = load_state(project_dir)
    status = feature_status(project_dir)
    validation = validate_feature_invariants(project_dir)
    help_open = open_help_requests(project_dir) if project_dir.exists() else []
    roles = roles_for_api(project_dir) if config else []
    return {
        "project_dir": str(project_dir.resolve()),
        "exists": project_dir.exists(),
        "configured": config is not None,
        "goal": config.goal if config else "",
        "feature_count": config.feature_count if config else 50,
        "agent_command": config.agent_command if config else "",
        "verify_command": config.verify_command if config else "",
        "permission_mode": config.permission_mode if config else "default",
        "collaboration_mode": config.collaboration_mode if config else "single",
        "next_session": state.next_session,
        "last_status": state.last_status,
        "last_session_id": state.last_session_id,
        "consecutive_failures": state.consecutive_failures,
        "features": {
            "total": status.total,
            "passing": status.passing,
            "failing": status.failing,
            "complete": status.complete,
        },
        "first_run_pending": not (project_dir / FEATURE_FILE).exists(),
        "validation": {"ok": validation.ok, "messages": validation.messages},
        "help": {"open": len(help_open)},
        "roles": {
            "total": len(roles),
            "custom_models": sum(1 for r in roles if r.get("model")),
            "custom_keys": sum(1 for r in roles if r.get("has_api_key") or r.get("api_key_env")),
        },
        "sessions_dir": str(session_dir(project_dir).resolve()),
    }


def prompt_text(project_dir: Path, kind: str) -> str:
    config = load_config(project_dir)
    return render_prompt(kind, project_dir, config)


def serve(host: str = "127.0.0.1", port: int = 18765) -> None:
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")
