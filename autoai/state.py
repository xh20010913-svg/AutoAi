from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .db import ensure_db, get_session
from .models import RunStateRow
from .time_utils import utc_now_iso


@dataclass
class RunState:
    next_session: int = 1
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    last_status: str = "never-run"
    last_session_id: str | None = None
    consecutive_failures: int = 0


def load_state(project_dir: Path) -> RunState:
    ensure_db(project_dir)
    with get_session() as session:
        row = session.query(RunStateRow).filter(RunStateRow.id == 1).first()
        if not row:
            return RunState()
        return RunState(
            next_session=row.next_session,
            created_at=row.created_at,
            updated_at=row.updated_at,
            last_status=row.last_status,
            last_session_id=row.last_session_id or None,
            consecutive_failures=row.consecutive_failures,
        )


def save_state(project_dir: Path, state: RunState) -> None:
    state.updated_at = utc_now_iso()
    ensure_db(project_dir)
    with get_session() as session:
        row = session.query(RunStateRow).filter(RunStateRow.id == 1).first()
        if row:
            row.next_session = state.next_session
            row.created_at = state.created_at
            row.updated_at = state.updated_at
            row.last_status = state.last_status
            row.last_session_id = state.last_session_id or ""
            row.consecutive_failures = state.consecutive_failures
        else:
            session.add(RunStateRow(
                id=1,
                next_session=state.next_session,
                created_at=state.created_at,
                updated_at=state.updated_at,
                last_status=state.last_status,
                last_session_id=state.last_session_id or "",
                consecutive_failures=state.consecutive_failures,
            ))
        session.commit()
