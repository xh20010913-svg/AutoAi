from __future__ import annotations

import contextlib
import io
import threading
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, HTTPException

from ..harness import AutoAIHarness, HarnessOptions
from ..time_utils import utc_now_iso

router = APIRouter(prefix="/api", tags=["run"])


@dataclass
class Job:
    id: str
    project_dir: str
    status: str = "queued"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    returncode: int | None = None
    log: str = ""
    error: str | None = None


class JobStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, Job] = {}

    def add(self, job: Job) -> None:
        with self._lock:
            self._jobs[job.id] = job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            job = self._jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)
            job.updated_at = utc_now_iso()

    def all(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())


job_store = JobStore()

_ws_broadcast: Callable[[dict], None] | None = None


def set_ws_broadcast(fn: Callable[[dict], None]) -> None:
    global _ws_broadcast
    _ws_broadcast = fn


@router.get("/job")
def get_job(id: str = ""):
    job = job_store.get(id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"job": asdict(job)}


@router.post("/run")
def post_run(body: dict[str, Any]):
    pd = Path(body.get("project_dir", "")).expanduser()
    if not body.get("project_dir"):
        raise HTTPException(400, "Missing project_dir")
    max_iterations = _optional_int(body.get("max_iterations"))
    if max_iterations is None and not bool(body.get("continuous", False)):
        max_iterations = 1
    job = _start_run_job(
        project_dir=pd,
        max_iterations=max_iterations,
        sleep_seconds=int(body.get("sleep_seconds", 3)),
        timeout_seconds=_optional_int(body.get("timeout_seconds")),
        stop_on_error=bool(body.get("stop_on_error", True)),
        agent_command=_optional_str(body.get("agent_command")),
        permission_mode=str(body.get("permission_mode", "")) or None,
        collaboration_mode=str(body.get("collaboration_mode", "")) or None,
    )
    return {"job": asdict(job)}


@router.post("/run/stop")
def post_run_stop(body: dict[str, Any]):
    job_id = str(body.get("job_id", ""))
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status == "running":
        job_store.update(job_id, status="stopped")
    return {"job": asdict(job)}


def _start_run_job(
    project_dir: Path,
    max_iterations: int | None,
    sleep_seconds: int,
    timeout_seconds: int | None,
    stop_on_error: bool,
    agent_command: str | None,
    permission_mode: str | None,
    collaboration_mode: str | None,
) -> Job:
    job = Job(id=uuid.uuid4().hex[:12], project_dir=str(project_dir.resolve()))
    job_store.add(job)
    thread = threading.Thread(
        target=_run_job,
        args=(job.id, project_dir, max_iterations, sleep_seconds, timeout_seconds, stop_on_error, agent_command, permission_mode, collaboration_mode),
        daemon=True,
    )
    thread.start()
    return job


def _run_event(job_id: str, event: dict) -> None:
    job_store.update(job_id, status=event.get("type", "running"))
    if _ws_broadcast:
        try:
            _ws_broadcast({"job_id": job_id, **event})
        except Exception:
            pass


def _run_job(
    job_id: str,
    project_dir: Path,
    max_iterations: int | None,
    sleep_seconds: int,
    timeout_seconds: int | None,
    stop_on_error: bool,
    agent_command: str | None,
    permission_mode: str | None,
    collaboration_mode: str | None,
) -> None:
    output = io.StringIO()
    job_store.update(job_id, status="running")
    _run_event(job_id, {"type": "run_started", "project_dir": str(project_dir)})

    def event_callback(event: dict) -> None:
        _run_event(job_id, event)

    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            code = AutoAIHarness(
                project_dir,
                HarnessOptions(
                    max_iterations=max_iterations,
                    sleep_seconds=sleep_seconds,
                    timeout_seconds=timeout_seconds,
                    stop_on_error=stop_on_error,
                    agent_command=agent_command,
                    permission_mode=permission_mode,
                    collaboration_mode=collaboration_mode,
                ),
                event_callback=event_callback,
            ).run()

        if code == 0:
            status = "finished"
        elif code == 2:
            status = "blocked"
        else:
            status = "failed"
        job_store.update(job_id, status=status, returncode=code)
        _run_event(job_id, {"type": "run_finished", "status": status, "returncode": code})
    except Exception as exc:
        job_store.update(job_id, status="failed", returncode=1, error=str(exc))
        _run_event(job_id, {"type": "run_finished", "status": "failed", "error": str(exc)})
    finally:
        job_store.update(job_id, log=output.getvalue())


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)
