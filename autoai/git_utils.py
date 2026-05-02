from __future__ import annotations

import subprocess
from pathlib import Path


def git_available() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def is_git_repo(project_dir: Path) -> bool:
    result = _git(project_dir, ["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def ensure_git_repo(project_dir: Path) -> bool:
    if not git_available():
        return False
    if is_git_repo(project_dir):
        return True
    return _git(project_dir, ["init"]).returncode == 0


def git_log(project_dir: Path, limit: int = 8) -> str:
    if not is_git_repo(project_dir):
        return ""
    result = _git(project_dir, ["log", f"--max-count={limit}", "--oneline"])
    return result.stdout.strip()


def git_status(project_dir: Path) -> str:
    if not is_git_repo(project_dir):
        return ""
    result = _git(project_dir, ["status", "--short"])
    return result.stdout.strip()


def commit_all(project_dir: Path, message: str) -> tuple[bool, str]:
    if not ensure_git_repo(project_dir):
        return False, "git is not available"

    _git(project_dir, ["add", "."])
    status = git_status(project_dir)
    if not status:
        return True, "nothing to commit"

    result = _git(project_dir, ["commit", "-m", message])
    if result.returncode == 0:
        return True, result.stdout.strip()
    return False, (result.stderr or result.stdout).strip()


def _git(project_dir: Path, args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
