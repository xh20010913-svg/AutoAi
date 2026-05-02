from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from ..agents import install_default_agents, list_agents, sync_agents_from_roles
from ..config import load_config
from ..roles import generate_roles, roles_for_api, save_roles, save_roles_from_api

router = APIRouter(prefix="/api", tags=["agents"])


@router.get("/roles")
def get_roles(project_dir: str):
    pd = Path(project_dir).expanduser()
    return {"roles": roles_for_api(pd)}


@router.post("/roles/generate")
def post_roles_generate(body: dict[str, Any]):
    pd = Path(body.get("project_dir", "")).expanduser()
    if not body.get("project_dir"):
        raise HTTPException(400, "Missing project_dir")
    config = load_config(pd)
    spec_path = pd / "task_spec.md"
    spec_text = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
    roles = save_roles(pd, generate_roles(config.goal, spec_text))
    sync_agents_from_roles(pd)
    return {"roles": roles_for_api(pd), "generated": len(roles)}


@router.put("/roles")
def put_roles(body: dict[str, Any]):
    pd = Path(body.get("project_dir", "")).expanduser()
    if not body.get("project_dir"):
        raise HTTPException(400, "Missing project_dir")
    roles = save_roles_from_api(pd, body.get("roles") or [])
    sync_agents_from_roles(pd)
    return {"roles": roles}


@router.get("/agents")
def get_agents(project_dir: str):
    pd = Path(project_dir).expanduser()
    return {"agents": list_agents(pd)}


@router.post("/agents/install-defaults")
def post_install_agents(body: dict[str, Any]):
    pd = Path(body.get("project_dir", "")).expanduser()
    if not body.get("project_dir"):
        raise HTTPException(400, "Missing project_dir")
    overwrite = bool(body.get("overwrite", True))
    agents = sync_agents_from_roles(pd, overwrite=overwrite)
    if not agents:
        agents = install_default_agents(pd, overwrite=bool(body.get("overwrite", False)))
    return {"agents": agents}
