from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config
from .constants import FEATURE_FILE
from .features import feature_status, validate_feature_invariants
from .harness import AutoAIHarness, HarnessOptions
from .project import init_project
from .prompts import render_prompt
from .state import load_state


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            goal = _read_goal(args)
            init_project(
                project_dir=args.project_dir,
                goal=goal,
                feature_count=args.feature_count,
                agent_command=args.agent_command,
                verify_command=args.verify_command,
                permission_mode=args.permission_mode,
                init_git=not args.no_git,
                collaboration_mode=args.collaboration_mode,
            )
            print(f"Initialized AutoAI project at {args.project_dir.resolve()}")
            return 0

        if args.command == "run":
            options = HarnessOptions(
                max_iterations=args.max_iterations,
                sleep_seconds=args.sleep_seconds,
                timeout_seconds=args.timeout_seconds,
                stop_on_error=args.stop_on_error,
                dry_run=args.dry_run,
                agent_command=args.agent_command,
                permission_mode=args.permission_mode,
                collaboration_mode=args.collaboration_mode,
            )
            return AutoAIHarness(args.project_dir, options).run()

        if args.command == "serve":
            from .server import serve
            serve(host=args.host, port=args.port)
            return 0

        if args.command == "status":
            return _status(args.project_dir)

        if args.command == "validate":
            result = validate_feature_invariants(args.project_dir)
            for message in result.messages:
                print(message)
            return 0 if result.ok else 1

        if args.command == "prompt":
            config = load_config(args.project_dir)
            print(render_prompt(args.kind, args.project_dir, config))
            return 0

        parser.print_help()
        return 2
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autoai",
        description="Long-running autonomous agent harness.",
    )
    sub = parser.add_subparsers(dest="command")

    init = sub.add_parser("init", help="Create a resumable long-running project.")
    init.add_argument("--project-dir", type=Path, required=True)
    init.add_argument("--goal", type=str)
    init.add_argument("--goal-file", type=Path)
    init.add_argument("--feature-count", type=int, default=50)
    init.add_argument("--agent-command", type=str)
    init.add_argument("--verify-command", type=str)
    init.add_argument(
        "--permission-mode",
        choices=["default", "acceptEdits", "auto", "bypassPermissions"],
        default="default",
    )
    init.add_argument(
        "--collaboration-mode",
        choices=["single", "subagents", "agent-team"],
        default="single",
    )
    init.add_argument("--no-git", action="store_true")

    run = sub.add_parser("run", help="Run autonomous sessions until stopped or complete.")
    run.add_argument("--project-dir", type=Path, required=True)
    run.add_argument("--agent-command", type=str)
    run.add_argument("--max-iterations", type=int)
    run.add_argument("--sleep-seconds", type=int, default=3)
    run.add_argument("--timeout-seconds", type=int)
    run.add_argument("--stop-on-error", action="store_true")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument(
        "--permission-mode",
        choices=["default", "acceptEdits", "auto", "bypassPermissions"],
    )
    run.add_argument(
        "--collaboration-mode",
        choices=["single", "subagents", "agent-team"],
    )

    serve = sub.add_parser("serve", help="Start the FastAPI backend server.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=18765)

    status = sub.add_parser("status", help="Show current progress.")
    status.add_argument("--project-dir", type=Path, required=True)

    validate = sub.add_parser("validate", help="Validate feature_list.json invariants.")
    validate.add_argument("--project-dir", type=Path, required=True)

    prompt = sub.add_parser("prompt", help="Render the prompt for a session.")
    prompt.add_argument("--project-dir", type=Path, required=True)
    prompt.add_argument("--kind", choices=["initializer", "coding"], required=True)

    return parser


def _read_goal(args: argparse.Namespace) -> str:
    if args.goal and args.goal_file:
        raise ValueError("Use either --goal or --goal-file, not both.")
    if args.goal_file:
        return args.goal_file.read_text(encoding="utf-8").strip()
    if args.goal:
        return args.goal.strip()
    return "Describe the long-running objective in task_spec.md before starting the harness."


def _status(project_dir: Path) -> int:
    state = load_state(project_dir)
    config = load_config(project_dir)
    features = feature_status(project_dir)
    first_run_pending = not (project_dir / FEATURE_FILE).exists()

    print(f"Project: {project_dir.resolve()}")
    print(f"Goal: {config.goal}")
    print(f"Next session: {state.next_session}")
    print(f"Last status: {state.last_status}")
    print(f"Features: {features.passing}/{features.total} passing")
    print(f"Permission mode: {config.permission_mode}")
    print(f"Collaboration mode: {config.collaboration_mode}")
    if first_run_pending:
        print("First run pending: initializer session will create feature_list.json")

    validation = validate_feature_invariants(project_dir)
    print("Validation: " + ("ok" if validation.ok else "failed"))
    for message in validation.messages:
        print(f"- {message}")
    return 0 if validation.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
