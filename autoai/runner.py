from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


def run_agent_command(
    command: str,
    prompt: str,
    prompt_file: Path,
    cwd: Path,
    timeout_seconds: int | None,
    env_extra: dict[str, str] | None = None,
    permission_mode: str = "default",
) -> CommandResult:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    expanded = apply_permission_mode(
        command.replace("{prompt_file}", str(prompt_file))
        .replace("{project_dir}", str(cwd.resolve()))
        .replace("{cwd}", str(cwd.resolve())),
        permission_mode,
    )

    try:
        completed = subprocess.run(
            expanded,
            cwd=cwd,
            input=prompt,
            capture_output=True,
            text=True,
            shell=True,
            timeout=timeout_seconds,
            env=env,
            check=False,
        )
        return CommandResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            returncode=124,
            stdout=exc.stdout or "",
            stderr=(exc.stderr or "") + "\nCommand timed out.",
            timed_out=True,
        )


def run_verify_command(
    command: str | None,
    cwd: Path,
    timeout_seconds: int | None,
) -> CommandResult | None:
    if not command:
        return None
    return run_agent_command(
        command=command,
        prompt="",
        prompt_file=cwd / ".autoai" / "verify.prompt.txt",
        cwd=cwd,
        timeout_seconds=timeout_seconds,
    )


def apply_permission_mode(command: str, permission_mode: str | None) -> str:
    mode = (permission_mode or "default").strip()
    if mode in {"", "default"}:
        return command
    if "--permission-mode" in command or "--dangerously-skip-permissions" in command:
        return command

    flag = _permission_flag(mode)
    if not flag:
        return command

    stripped = command.lstrip()
    leading = command[: len(command) - len(stripped)]
    lowered = stripped.lower()
    if lowered == "claude":
        return f"{leading}claude {flag}"
    if lowered.startswith("claude "):
        return f"{leading}claude {flag} {stripped[len('claude '):]}"
    return f"{command} {flag}"


def _permission_flag(mode: str) -> str | None:
    if mode == "acceptEdits":
        return "--permission-mode acceptEdits"
    if mode == "auto":
        return "--permission-mode auto"
    if mode in {"bypassPermissions", "dangerously-skip"}:
        return "--dangerously-skip-permissions"
    return None
