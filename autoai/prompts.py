from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from .agents import list_agents
from .config import AutoAIConfig
from .constants import FEATURE_FILE, PROGRESS_FILE, SPEC_FILE
from .features import feature_status
from .git_utils import git_log, git_status
from .help_requests import help_context_summary
from .roles import role_context_summary
from .tasks import open_task_summary


def render_prompt(kind: str, project_dir: Path, config: AutoAIConfig) -> str:
    if kind not in {"initializer", "coding"}:
        raise ValueError(f"Unknown prompt kind: {kind}")

    template = _load_template(f"{kind}_prompt.md")
    status = feature_status(project_dir)
    replacements = {
        "PROJECT_DIR": str(project_dir.resolve()),
        "SPEC_FILE": SPEC_FILE,
        "FEATURE_FILE": FEATURE_FILE,
        "PROGRESS_FILE": PROGRESS_FILE,
        "FEATURE_COUNT": str(config.feature_count),
        "GOAL": config.goal,
        "PASSING_COUNT": str(status.passing),
        "TOTAL_COUNT": str(status.total),
        "FAILING_COUNT": str(status.failing),
        "GIT_STATUS": git_status(project_dir) or "(not a git repo or no changes)",
        "GIT_LOG": git_log(project_dir) or "(no git history yet)",
        "VERIFY_COMMAND": config.verify_command or "(none configured)",
        "COLLABORATION_INSTRUCTIONS": collaboration_instructions(project_dir, config),
        "TASK_CONTEXT": open_task_summary(project_dir),
        "HELP_CONTEXT": help_context_summary(project_dir),
        "ROLE_CONTEXT": role_context_summary(project_dir),
    }

    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def _load_template(name: str) -> str:
    return (files("autoai") / "templates" / name).read_text(encoding="utf-8")


def collaboration_instructions(project_dir: Path, config: AutoAIConfig) -> str:
    agents = list_agents(project_dir)
    agent_lines = "\n".join(
        f"- {agent['name']}: {agent.get('description') or 'No description'}"
        for agent in agents
    ) or "- No project subagents are installed yet."

    mode = config.collaboration_mode or "single"
    if mode == "subagents":
        guidance = (
            "Use Claude Code project subagents from `.claude/agents/` when they help. "
            "Start with a short plan, delegate bounded side tasks to the relevant roles, "
            "keep file ownership explicit, then integrate and verify the result."
        )
    elif mode == "agent-team":
        guidance = (
            "Use Claude Code Agent Teams if available. The harness sets "
            "`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` for this mode. Prefer small teams, "
            "plan first, assign disjoint file ownership, monitor progress, and consolidate "
            "the final result. If Agent Teams are unavailable, fall back to project subagents."
        )
    else:
        guidance = (
            "Work as a single autonomous agent. You may still read `.claude/agents/` for role "
            "guidance, but keep the execution simple unless the task clearly benefits from delegation."
        )

    return f"""Mode: `{mode}`

{guidance}

Installed project agents:
{agent_lines}"""
