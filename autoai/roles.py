from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .db import ensure_db, get_session
from .models import Role, RoleSecret


DEFAULT_BUDGETS = {
    "high": {"max_prompt_chars": 60000, "max_output_chars": 12000, "max_files": 30, "timeout_seconds": 7200},
    "medium": {"max_prompt_chars": 32000, "max_output_chars": 8000, "max_files": 14, "timeout_seconds": 3600},
    "low": {"max_prompt_chars": 14000, "max_output_chars": 4000, "max_files": 6, "timeout_seconds": 1800},
}

_ALWAYS_ROLES = {"project-manager", "implementer", "tester", "reviewer"}

ROLE_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "id": "project-manager",
        "display_name": "Project Manager",
        "description": "Owns project decomposition, priorities, role assignment, and final coordination.",
        "cost_tier": "high",
        "model_tier": "high",
        "task_types": ["planning", "architecture", "coordination", "final-review"],
        "tools": ["Read", "Grep", "Glob", "Bash"],
        "authority": {"can_decompose_tasks": True, "can_assign_tasks": True, "can_change_architecture": True, "can_mark_done": False},
        "scope": {"write_paths": [".autoai/tasks.json", ".autoai/roles.json", ".autoai/messages.jsonl", "autoai-progress.md"], "read_paths": ["**/*"]},
        "always": True,
    },
    {
        "id": "agent-orchestrator",
        "display_name": "Agent Orchestrator",
        "description": "Designs and maintains multi-agent workflow, dispatch, communication, and boundary rules.",
        "cost_tier": "high",
        "model_tier": "high",
        "task_types": ["agent-orchestration", "dispatcher", "workflow"],
        "tools": ["Read", "Grep", "Glob", "Bash", "Edit", "Write"],
        "keywords": ["agent", "multi-agent", "subagent", "协同", "多agent", "角色", "调度", "orchestration", "automation"],
    },
    {
        "id": "frontend-developer",
        "display_name": "Frontend Developer",
        "description": "Builds the browser UI, interaction states, responsive layout, and user-facing workflows.",
        "cost_tier": "medium",
        "model_tier": "medium",
        "task_types": ["frontend", "ui", "ux", "dashboard"],
        "tools": ["Read", "Grep", "Glob", "Bash", "Edit", "Write"],
        "keywords": ["ui", "web", "frontend", "dashboard", "界面", "前端", "看板", "页面", "app"],
    },
    {
        "id": "backend-developer",
        "display_name": "Backend Developer",
        "description": "Builds APIs, project state, persistence, daemon/runtime behavior, and server-side flows.",
        "cost_tier": "medium",
        "model_tier": "medium",
        "task_types": ["backend", "api", "persistence", "daemon"],
        "tools": ["Read", "Grep", "Glob", "Bash", "Edit", "Write"],
        "keywords": ["api", "server", "backend", "daemon", "runtime", "数据库", "后端", "接口", "服务"],
    },
    {
        "id": "implementer",
        "display_name": "Implementer",
        "description": "Implements one assigned feature or bugfix inside explicit file ownership boundaries.",
        "cost_tier": "medium",
        "model_tier": "medium",
        "task_types": ["implementation", "bugfix"],
        "tools": ["Read", "Grep", "Glob", "Bash", "Edit", "Write"],
        "authority": {"can_decompose_tasks": False, "can_assign_tasks": False, "can_change_architecture": False, "can_mark_done": False},
        "always": True,
    },
    {
        "id": "tester",
        "display_name": "Tester",
        "description": "Verifies user flows, tests, regressions, and evidence before a task is considered complete.",
        "cost_tier": "medium",
        "model_tier": "medium",
        "task_types": ["testing", "verification", "qa"],
        "tools": ["Read", "Grep", "Glob", "Bash", "Edit", "Write"],
        "always": True,
    },
    {
        "id": "security-reviewer",
        "display_name": "Security Reviewer",
        "description": "Reviews permissions, API keys, external actions, secrets, and risky automation behavior.",
        "cost_tier": "medium",
        "model_tier": "medium",
        "task_types": ["security", "permissions", "secrets", "policy-review"],
        "tools": ["Read", "Grep", "Glob", "Bash"],
        "keywords": ["permission", "api key", "secret", "auth", "权限", "密钥", "安全"],
    },
    {
        "id": "reviewer",
        "display_name": "Reviewer",
        "description": "Reviews completed work for correctness, regressions, missing tests, and boundary violations.",
        "cost_tier": "high",
        "model_tier": "high",
        "task_types": ["review", "quality", "risk"],
        "tools": ["Read", "Grep", "Glob", "Bash"],
        "always": True,
    },
)


def generate_roles(goal: str, spec_text: str | None = None, max_roles: int = 8) -> list[dict[str, Any]]:
    text = f"{goal}\n{spec_text or ''}".lower()
    selected: list[dict[str, Any]] = []
    for role in ROLE_CATALOG:
        if role.get("always") or any(keyword.lower() in text for keyword in role.get("keywords", [])):
            selected.append(_role_from_catalog(role))

    if len(selected) > max_roles:
        always = [role for role in selected if role["id"] in _ALWAYS_ROLES]
        optional = [role for role in selected if role["id"] not in {item["id"] for item in always}]
        selected = always + optional[: max(0, max_roles - len(always))]

    return selected


def load_roles(project_dir: Path) -> list[dict[str, Any]]:
    ensure_db(project_dir)
    with get_session() as session:
        roles = session.query(Role).all()
        return [_normalize_role(r.to_dict()) for r in roles]


def save_roles(project_dir: Path, roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ensure_db(project_dir)
    normalized = [_normalize_role(item) for item in roles]
    with get_session() as session:
        session.query(Role).delete()
        for data in normalized:
            session.add(Role.from_dict(data))
        session.commit()
    return normalized


def roles_for_api(project_dir: Path) -> list[dict[str, Any]]:
    ensure_db(project_dir)
    with get_session() as session:
        secrets = {s.role_id: s.api_key for s in session.query(RoleSecret).all()}
    payload = []
    for role in load_roles(project_dir):
        role = dict(role)
        role["has_api_key"] = bool(secrets.get(role["id"]))
        role["api_key"] = ""
        payload.append(role)
    return payload


def save_roles_from_api(project_dir: Path, roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ensure_db(project_dir)
    clean_roles = []
    with get_session() as session:
        for item in roles:
            role = dict(item)
            role_id = str(role.get("id") or "").strip()
            api_key = str(role.pop("api_key", "") or "").strip()
            if api_key:
                existing = session.query(RoleSecret).filter(RoleSecret.role_id == role_id).first()
                if existing:
                    existing.api_key = api_key
                else:
                    session.add(RoleSecret(role_id=role_id, api_key=api_key))
            if role.get("clear_api_key"):
                session.query(RoleSecret).filter(RoleSecret.role_id == role_id).delete()
            role.pop("clear_api_key", None)
            role.pop("has_api_key", None)
            clean_roles.append(role)
        session.commit()
    saved = save_roles(project_dir, clean_roles)
    return roles_for_api(project_dir) if saved else []


def role_context_summary(project_dir: Path) -> str:
    roles = load_roles(project_dir)
    if not roles:
        return "No role policy is configured yet."
    lines = [
        "Role policy:",
        "- If a role has no custom model or API key, use the default agent command/model/key.",
        "- Roles must stay inside their authority and scope; if blocked or out of scope, create a Help request.",
        "",
    ]
    for role in roles:
        model = role.get("model") or "default"
        provider = role.get("provider") or "default"
        budget = role["token_budget"]
        lines.append(
            f"- {role['id']} ({role['cost_tier']} cost, {role['model_tier']} model): {role['description']}"
        )
        lines.append(
            f"  model={model}, provider={provider}, "
            f"budget={budget['max_prompt_chars']} prompt chars/{budget['max_output_chars']} output chars/{budget['max_files']} files"
        )
        lines.append(f"  task types: {', '.join(role['task_types'])}")
        lines.append(f"  write scope: {', '.join(role['scope']['write_paths'])}")
    return "\n".join(lines)


def _role_from_catalog(source: dict[str, Any]) -> dict[str, Any]:
    cost_tier = source.get("cost_tier", "medium")
    return {
        "id": source["id"],
        "display_name": source["display_name"],
        "description": source["description"],
        "provider": "default",
        "model": "",
        "model_tier": source.get("model_tier", cost_tier),
        "cost_tier": cost_tier,
        "api_key_env": "",
        "token_budget": deepcopy(DEFAULT_BUDGETS[cost_tier]),
        "task_types": list(source.get("task_types", [])),
        "tools": list(source.get("tools", [])),
        "authority": deepcopy(source.get("authority", {"can_decompose_tasks": False, "can_assign_tasks": False, "can_change_architecture": False, "can_mark_done": False})),
        "scope": deepcopy(source.get("scope", {"write_paths": ["assigned_only"], "read_paths": ["assigned_area", "task_spec.md", "autoai-progress.md"]})),
    }


def _normalize_role(item: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError("Each role must be an object.")
    role_id = str(item.get("id") or "").strip()
    if not role_id:
        raise ValueError("Role id is required.")
    cost_tier = str(item.get("cost_tier") or "medium")
    if cost_tier not in DEFAULT_BUDGETS:
        raise ValueError(f"Invalid role cost tier: {cost_tier}")
    budget = dict(DEFAULT_BUDGETS[cost_tier])
    budget.update(item.get("token_budget") or {})
    scope = item.get("scope") or {}
    authority = item.get("authority") or {}
    return {
        "id": role_id,
        "display_name": str(item.get("display_name") or role_id).strip(),
        "description": str(item.get("description") or "").strip(),
        "provider": str(item.get("provider") or "default").strip(),
        "model": str(item.get("model") or "").strip(),
        "model_tier": str(item.get("model_tier") or cost_tier).strip(),
        "cost_tier": cost_tier,
        "api_key_env": str(item.get("api_key_env") or "").strip(),
        "token_budget": {
            "max_prompt_chars": int(budget.get("max_prompt_chars") or DEFAULT_BUDGETS[cost_tier]["max_prompt_chars"]),
            "max_output_chars": int(budget.get("max_output_chars") or DEFAULT_BUDGETS[cost_tier]["max_output_chars"]),
            "max_files": int(budget.get("max_files") or DEFAULT_BUDGETS[cost_tier]["max_files"]),
            "timeout_seconds": int(budget.get("timeout_seconds") or DEFAULT_BUDGETS[cost_tier]["timeout_seconds"]),
        },
        "task_types": _string_list(item.get("task_types")),
        "tools": _string_list(item.get("tools")),
        "authority": {
            "can_decompose_tasks": bool(authority.get("can_decompose_tasks", False)),
            "can_assign_tasks": bool(authority.get("can_assign_tasks", False)),
            "can_change_architecture": bool(authority.get("can_change_architecture", False)),
            "can_mark_done": bool(authority.get("can_mark_done", False)),
        },
        "scope": {
            "write_paths": _string_list(scope.get("write_paths")) or ["assigned_only"],
            "read_paths": _string_list(scope.get("read_paths")) or ["assigned_area", "task_spec.md", "autoai-progress.md"],
        },
    }


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = value.replace("\n", ",").split(",")
    elif isinstance(value, list):
        raw_items = value
    else:
        raw_items = [value]
    return [str(item).strip() for item in raw_items if str(item).strip()]
