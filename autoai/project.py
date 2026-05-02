from __future__ import annotations

from pathlib import Path

from .config import AutoAIConfig, save_config
from .constants import (
    PROGRESS_FILE,
    SPEC_FILE,
    VERIFICATION_DIR,
    control_dir,
    session_dir,
)
from .db import init_db
from .git_utils import commit_all, ensure_git_repo
from .roles import generate_roles, save_roles
from .state import RunState, save_state
from .time_utils import utc_now_iso


def init_project(
    project_dir: Path,
    goal: str,
    feature_count: int,
    agent_command: str | None,
    verify_command: str | None,
    permission_mode: str,
    init_git: bool,
    collaboration_mode: str = "single",
    spec_text: str | None = None,
    spec_filename: str | None = None,
) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    control_dir(project_dir).mkdir(parents=True, exist_ok=True)
    session_dir(project_dir).mkdir(parents=True, exist_ok=True)
    (project_dir / VERIFICATION_DIR).mkdir(parents=True, exist_ok=True)

    init_db(project_dir)

    now = utc_now_iso()
    save_config(
        project_dir,
        AutoAIConfig(
            goal=goal,
            feature_count=feature_count,
            agent_command=agent_command,
            verify_command=verify_command,
            permission_mode=permission_mode,
            collaboration_mode=collaboration_mode,
            created_at=now,
            updated_at=now,
        ),
    )
    save_state(project_dir, RunState(created_at=now, updated_at=now))

    _write_if_missing(project_dir / SPEC_FILE, _spec_text(goal, spec_text, spec_filename))
    _write_if_missing(project_dir / PROGRESS_FILE, _progress_text(goal, now))
    _write_if_missing(project_dir / ".gitignore", _gitignore_text())
    _write_if_missing(project_dir / "init.sh", _init_sh_text())
    _write_if_missing(project_dir / "init.ps1", _init_ps1_text())

    if not project_dir.joinpath(control_dir(project_dir), "roles_initialized").exists():
        save_roles(project_dir, generate_roles(goal, spec_text))
        project_dir.joinpath(control_dir(project_dir), "roles_initialized").write_text("1")

    if init_git and ensure_git_repo(project_dir):
        commit_all(project_dir, "Initialize AutoAI long-running project")


def _write_if_missing(path: Path, text: str) -> None:
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _spec_text(goal: str, spec_text: str | None, spec_filename: str | None) -> str:
    if spec_text and spec_text.strip():
        source = f"\nSource document: `{spec_filename}`\n" if spec_filename else ""
        return f"""# Task Specification
{source}
## Goal

{goal or "See the uploaded requirements below."}

## Uploaded Requirements

{spec_text.strip()}
"""

    return f"""# Task Specification

## Goal

{goal}

## Notes For Agents

- Expand this spec into a durable `feature_list.json` during the initializer session.
- Prefer small, verifiable slices of work.
- Keep the project runnable after every session.
"""


def _progress_text(goal: str, created_at: str) -> str:
    return f"""# AutoAI Progress

Created: {created_at}

Goal:
{goal}

## Session Log

- {created_at}: Project initialized. Waiting for initializer agent.
"""


def _gitignore_text() -> str:
    return """.autoai/sessions/*.stdout.log
.autoai/sessions/*.stderr.log
.autoai/sessions/*.prompt.md
.autoai/tmp/
.autoai/role_secrets.json
.autoai/autoai.db
node_modules/
.venv/
__pycache__/
*.pyc
"""


def _init_sh_text() -> str:
    return """#!/usr/bin/env sh
set -eu

echo "No project-specific startup command has been configured yet."
echo "The initializer or a later coding session should update init.sh once the stack is chosen."
"""


def _init_ps1_text() -> str:
    return """Write-Host "No project-specific startup command has been configured yet."
Write-Host "The initializer or a later coding session should update init.ps1 once the stack is chosen."
"""
