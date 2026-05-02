from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from .db import ensure_db, get_session
from .models import ConfigKV
from .time_utils import utc_now_iso

_CONFIG_KEYS = {"goal", "feature_count", "agent_command", "verify_command", "permission_mode", "collaboration_mode", "created_at", "updated_at"}


@dataclass
class AutoAIConfig:
    goal: str
    feature_count: int = 50
    agent_command: str | None = None
    verify_command: str | None = None
    permission_mode: str = "default"
    collaboration_mode: str = "single"
    created_at: str | None = None
    updated_at: str | None = None


def load_config(project_dir: Path) -> AutoAIConfig:
    ensure_db(project_dir)
    with get_session() as session:
        rows = session.query(ConfigKV).all()
        data = {row.key: row.value for row in rows}
    if not data:
        raise FileNotFoundError(
            f"No config found in {project_dir}. Run `python -m autoai init --project-dir {project_dir}` first."
        )
    kwargs: dict[str, Any] = {}
    for f in fields(AutoAIConfig):
        raw = data.get(f.name)
        if raw is None:
            continue
        if f.type == "int":
            kwargs[f.name] = int(raw)
        elif f.type == "str | None":
            kwargs[f.name] = raw if raw else None
        else:
            kwargs[f.name] = raw
    return AutoAIConfig(**kwargs)


def save_config(project_dir: Path, config: AutoAIConfig) -> None:
    ensure_db(project_dir)
    data = _config_to_dict(config)
    with get_session() as session:
        session.query(ConfigKV).delete()
        for key, value in data.items():
            if value is not None:
                session.add(ConfigKV(key=key, value=str(value)))
        session.commit()


def _config_to_dict(config: AutoAIConfig) -> dict[str, Any]:
    result = {}
    for f in fields(AutoAIConfig):
        value = getattr(config, f.name)
        result[f.name] = value
    return result
