from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .constants import claude_agents_dir
from .roles import load_roles


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    description: str
    model: str
    tools: str
    body: str


DEFAULT_AGENTS: tuple[AgentDefinition, ...] = (
    AgentDefinition(
        name="team-lead",
        description="Use for decomposing a task, assigning ownership, coordinating teammates, and synthesizing results.",
        model="inherit",
        tools="Read, Grep, Glob, Bash, Edit, Write",
        body="""# Team Lead

You coordinate multi-agent work for this project.

Responsibilities:
- Read `task_spec.md`, `autoai-progress.md`, and feature/task data before planning.
- Split work into small streams with explicit file ownership.
- Keep teams small, usually two to four contributors.
- Ask implementers to report changed files, verification performed, blockers, and residual risk.
- Integrate results into one coherent final state and update project progress files.
""",
    ),
    AgentDefinition(
        name="architect",
        description="Use for system design, boundaries, data flow, and implementation plans before code changes.",
        model="inherit",
        tools="Read, Grep, Glob, Bash",
        body="""# Architect

You design the technical approach before implementation.

Responsibilities:
- Inspect the existing codebase before proposing changes.
- Prefer the local stack and conventions over new dependencies.
- Identify ownership boundaries, interfaces, risks, and verification strategy.
- Produce a concise plan that implementers can execute independently.
""",
    ),
    AgentDefinition(
        name="implementer",
        description="Use for building an assigned implementation slice within clear file ownership boundaries.",
        model="inherit",
        tools="Read, Grep, Glob, Bash, Edit, Write",
        body="""# Implementer

You build one assigned slice of work.

Responsibilities:
- Stay inside the file/module ownership assigned by the lead.
- Do not revert edits made by others.
- Keep changes small, runnable, and consistent with existing patterns.
- Report changed files, verification, and any blocker before handing back.
""",
    ),
    AgentDefinition(
        name="tester",
        description="Use for verification planning, test implementation, regression checks, and evidence capture.",
        model="inherit",
        tools="Read, Grep, Glob, Bash, Edit, Write",
        body="""# Tester

You verify behavior from the user's perspective.

Responsibilities:
- Choose the strongest available verification path for the task.
- Add or adjust focused tests when the risk justifies it.
- Capture useful evidence in `verification/` when logs, screenshots, or transcripts help future sessions.
- Report exact commands, outcomes, and remaining gaps.
""",
    ),
    AgentDefinition(
        name="reviewer",
        description="Use for code review, reliability review, security review, and missing-test checks.",
        model="inherit",
        tools="Read, Grep, Glob, Bash",
        body="""# Reviewer

You review completed work before it is considered done.

Responsibilities:
- Prioritize bugs, regressions, security issues, and missing verification.
- Reference files and lines where possible.
- Deduplicate findings and rank by severity.
- Confirm when no blocking issues are found and name residual risk.
""",
    ),
)


def install_default_agents(project_dir: Path, overwrite: bool = False) -> list[dict[str, str]]:
    root = claude_agents_dir(project_dir)
    root.mkdir(parents=True, exist_ok=True)
    installed: list[dict[str, str]] = []
    for agent in DEFAULT_AGENTS:
        path = root / f"{agent.name}.md"
        if overwrite or not path.exists():
            path.write_text(render_agent(agent), encoding="utf-8")
        installed.append(_agent_payload(path, agent))
    return installed


def sync_agents_from_roles(project_dir: Path, overwrite: bool = True) -> list[dict[str, str]]:
    root = claude_agents_dir(project_dir)
    root.mkdir(parents=True, exist_ok=True)
    synced: list[dict[str, str]] = []
    for role in load_roles(project_dir):
        path = root / f"{role['id']}.md"
        if overwrite or not path.exists():
            path.write_text(_render_role_agent(role), encoding="utf-8")
        synced.append({
            "name": role["id"],
            "description": role["description"],
            "model": role["model"] or "inherit",
            "tools": ", ".join(role["tools"]),
            "path": str(path.resolve()),
        })
    return synced


def list_agents(project_dir: Path) -> list[dict[str, str]]:
    root = claude_agents_dir(project_dir)
    if not root.exists():
        return []
    agents = []
    for path in sorted(root.glob("*.md")):
        agents.append(_parse_agent_file(path))
    return agents


def render_agent(agent: AgentDefinition) -> str:
    return f"""---
name: {agent.name}
description: {agent.description}
tools: {agent.tools}
model: {agent.model}
---

{agent.body.strip()}
"""


def _agent_payload(path: Path, agent: AgentDefinition) -> dict[str, str]:
    payload = asdict(agent)
    payload["path"] = str(path.resolve())
    return payload


def _parse_agent_file(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    data = {
        "name": path.stem,
        "description": "",
        "tools": "",
        "model": "",
        "path": str(path.resolve()),
    }
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for raw_line in parts[1].splitlines():
                if ":" not in raw_line:
                    continue
                key, value = raw_line.split(":", 1)
                key = key.strip()
                if key in data:
                    data[key] = value.strip()
    return data


def _render_role_agent(role: dict) -> str:
    model = role.get("model") or "inherit"
    tools = ", ".join(role.get("tools") or ["Read", "Grep", "Glob"])
    budget = role.get("token_budget") or {}
    task_types = ", ".join(role.get("task_types") or [])
    write_paths = ", ".join((role.get("scope") or {}).get("write_paths") or [])
    read_paths = ", ".join((role.get("scope") or {}).get("read_paths") or [])
    authority = role.get("authority") or {}
    return f"""---
name: {role['id']}
description: {role.get('description') or role.get('display_name') or role['id']}
tools: {tools}
model: {model}
---

# {role.get('display_name') or role['id']}

{role.get('description') or ''}

## Budget And Cost

- Cost tier: {role.get('cost_tier', 'medium')}
- Model tier: {role.get('model_tier', 'medium')}
- Max prompt chars: {budget.get('max_prompt_chars', '')}
- Max output chars: {budget.get('max_output_chars', '')}
- Max files: {budget.get('max_files', '')}
- Timeout seconds: {budget.get('timeout_seconds', '')}

## Task Boundary

- Allowed task types: {task_types}
- Write paths: {write_paths}
- Read paths: {read_paths}

## Authority

- Can decompose tasks: {authority.get('can_decompose_tasks', False)}
- Can assign tasks: {authority.get('can_assign_tasks', False)}
- Can change architecture: {authority.get('can_change_architecture', False)}
- Can mark done: {authority.get('can_mark_done', False)}

If a task is outside this boundary, create a Help request instead of expanding scope.
Do not reveal or print API keys. If no role-specific model or API key is configured, use the default session settings.
"""
