from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

_engine = None
_session_factory: sessionmaker[Session] | None = None


class Base(DeclarativeBase):
    pass


def init_db(project_dir: Path) -> None:
    global _engine, _session_factory
    close_db()
    db_path = project_dir / ".autoai" / "autoai.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    _session_factory = sessionmaker(bind=_engine)
    from . import models  # noqa: F401 — ensure models are registered
    Base.metadata.create_all(_engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    session = _session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ensure_db(project_dir: Path) -> None:
    if _engine is None:
        init_db(project_dir)


def close_db() -> None:
    global _engine, _session_factory
    if _engine is not None:
        # Close all connections in the pool
        _engine.dispose()
        _engine = None
        _session_factory = None
