from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .config import load_config, save_config
from .constants import FEATURE_FILE, PROGRESS_FILE, session_dir
from .features import feature_status, validate_feature_invariants
from .git_utils import git_status
from .help_requests import open_help_requests
from .prompts import render_prompt
from .runner import run_agent_command, run_verify_command
from .state import load_state, save_state
from .time_utils import utc_now_iso


@dataclass
class HarnessOptions:
    max_iterations: int | None = None
    sleep_seconds: int = 3
    timeout_seconds: int | None = None
    stop_on_error: bool = False
    dry_run: bool = False
    agent_command: str | None = None
    permission_mode: str | None = None
    collaboration_mode: str | None = None


class AutoAIHarness:
    def __init__(
        self,
        project_dir: Path,
        options: HarnessOptions,
        event_callback: Callable[[dict[str, Any]], None] | None = None,
    ):
        self.project_dir = project_dir
        self.options = options
        self.event_callback = event_callback
        self.config = load_config(project_dir)
        self._apply_options()

    def _apply_options(self) -> None:
        updated = False
        if self.options.agent_command:
            self.config.agent_command = self.options.agent_command
            updated = True
        if self.options.permission_mode:
            self.config.permission_mode = self.options.permission_mode
            updated = True
        if self.options.collaboration_mode:
            self.config.collaboration_mode = self.options.collaboration_mode
            updated = True
        if updated:
            self.config.updated_at = utc_now_iso()
            save_config(self.project_dir, self.config)

    def _emit(self, event: dict[str, Any]) -> None:
        if self.event_callback:
            try:
                self.event_callback(event)
            except Exception:
                pass

    def run(self) -> int:
        command = self.config.agent_command
        if not command and not self.options.dry_run:
            raise ValueError(
                "No agent command configured. Pass --agent-command or set it during init. "
                "The command must read the prompt from stdin or use {prompt_file}."
            )

        state = load_state(self.project_dir)
        iterations = 0

        while True:
            if self.options.max_iterations is not None and iterations >= self.options.max_iterations:
                return 0

            pending_help = open_help_requests(self.project_dir)
            if pending_help:
                print("Open human help request(s) are waiting. Stopping until the user answers:")
                for request in pending_help:
                    print(f"- {request['id']}: {request['title']}")
                self._emit({"type": "run_blocked", "help_requests": len(pending_help)})
                return 2

            kind = self._session_kind()
            session_id = f"{state.next_session:04d}-{kind}-{utc_now_iso().replace(':', '')}"
            prompt = render_prompt(kind, self.project_dir, self.config)
            prompt_file = session_dir(self.project_dir) / f"{session_id}.prompt.md"
            prompt_file.parent.mkdir(parents=True, exist_ok=True)
            prompt_file.write_text(prompt, encoding="utf-8")

            print(f"\n=== AutoAI session {state.next_session}: {kind} ===")
            print(f"Prompt: {prompt_file}")

            self._emit({"type": "session_started", "session_id": session_id, "kind": kind, "session_num": state.next_session})

            if self.options.dry_run:
                print(prompt)
                return 0

            verify = run_verify_command(
                self.config.verify_command,
                self.project_dir,
                self.options.timeout_seconds,
            )
            if verify is not None:
                self._write_command_logs(session_id, "verify", verify.stdout, verify.stderr)
                print(f"Verify command exit code: {verify.returncode}")
                if not verify.ok and self.options.stop_on_error:
                    self._record_session(state, session_id, "verify-failed")
                    return verify.returncode

            env_extra = {
                "AUTOAI_PROJECT_DIR": str(self.project_dir.resolve()),
                "AUTOAI_SESSION_ID": session_id,
                "AUTOAI_SESSION_KIND": kind,
                "AUTOAI_PERMISSION_MODE": self.config.permission_mode,
                "AUTOAI_COLLABORATION_MODE": self.config.collaboration_mode,
            }
            if self.config.collaboration_mode == "agent-team":
                env_extra["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"

            result = run_agent_command(
                command=command,
                prompt=prompt,
                prompt_file=prompt_file,
                cwd=self.project_dir,
                timeout_seconds=self.options.timeout_seconds,
                env_extra=env_extra,
                permission_mode=self.config.permission_mode,
            )
            self._write_command_logs(session_id, "agent", result.stdout, result.stderr)

            validation = validate_feature_invariants(self.project_dir)
            validation_ok = validation.ok
            validation_messages = list(validation.messages)
            if kind == "initializer" and not (self.project_dir / FEATURE_FILE).exists():
                validation_ok = False
                validation_messages.append("Initializer session ended without creating feature_list.json.")

            if not validation_ok:
                for message in validation_messages:
                    print(f"Feature validation: {message}")

            pending_help = open_help_requests(self.project_dir)
            if pending_help:
                validation_messages.append(
                    f"{len(pending_help)} open human help request(s) are waiting."
                )

            status = "ok" if result.ok and validation_ok else "failed"
            if pending_help:
                status = "blocked"

            self._append_progress(session_id, kind, status, result.returncode, validation_messages)
            self._record_session(state, session_id, status)
            state.next_session += 1
            save_state(self.project_dir, state)

            summary = feature_status(self.project_dir)
            print(
                f"Session finished with status={status}; "
                f"features {summary.passing}/{summary.total} passing."
            )

            self._emit({
                "type": "session_finished",
                "session_id": session_id,
                "status": status,
                "features": {"total": summary.total, "passing": summary.passing, "failing": summary.failing},
            })

            if summary.complete:
                print("All features are passing. Stopping.")
                return 0

            if status == "blocked":
                print("Human help is required. Answer it in the UI Help tab, then run again.")
                return 2

            if status != "ok" and self.options.stop_on_error:
                return result.returncode or 1

            iterations += 1
            if self.options.max_iterations is not None and iterations >= self.options.max_iterations:
                return 0

            time.sleep(self.options.sleep_seconds)

    def _session_kind(self) -> str:
        return "initializer" if not (self.project_dir / FEATURE_FILE).exists() else "coding"

    def _write_command_logs(self, session_id: str, label: str, stdout: str, stderr: str) -> None:
        root = session_dir(self.project_dir)
        root.mkdir(parents=True, exist_ok=True)
        (root / f"{session_id}.{label}.stdout.log").write_text(stdout, encoding="utf-8")
        (root / f"{session_id}.{label}.stderr.log").write_text(stderr, encoding="utf-8")

    def _append_progress(
        self,
        session_id: str,
        kind: str,
        status: str,
        returncode: int,
        validation_messages: list[str],
    ) -> None:
        summary = feature_status(self.project_dir)
        dirty = git_status(self.project_dir) or "(clean or not a git repo)"
        lines = [
            "",
            f"### {utc_now_iso()} - {session_id}",
            "",
            f"- Kind: {kind}",
            f"- Status: {status}",
            f"- Agent return code: {returncode}",
            f"- Feature progress: {summary.passing}/{summary.total} passing",
            f"- Git status: {dirty}",
        ]
        if validation_messages:
            lines.append("- Validation:")
            lines.extend(f"  - {message}" for message in validation_messages)
        lines.append("")
        progress = self.project_dir / PROGRESS_FILE
        existing = progress.read_text(encoding="utf-8") if progress.exists() else ""
        progress.write_text(existing + "\n".join(lines) + "\n", encoding="utf-8")

    def _record_session(self, state: Any, session_id: str, status: str) -> None:
        state.last_status = status
        state.last_session_id = session_id
        if status == "ok":
            state.consecutive_failures = 0
        else:
            state.consecutive_failures += 1
