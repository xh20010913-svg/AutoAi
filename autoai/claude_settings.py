from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def claude_settings_path(home: Path | None = None) -> Path:
    root = home if home is not None else Path.home()
    return root / ".claude" / "settings.json"


def read_claude_settings(home: Path | None = None) -> dict[str, Any]:
    path = claude_settings_path(home)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def claude_settings_status(home: Path | None = None) -> dict[str, Any]:
    path = claude_settings_path(home)
    data = read_claude_settings(home)
    permissions = data.get("permissions", {})
    return {
        "path": str(path),
        "exists": path.exists(),
        "skipDangerousModePermissionPrompt": bool(
            permissions.get("skipDangerousModePermissionPrompt", False)
        ),
    }


def set_skip_dangerous_mode_prompt(enabled: bool, home: Path | None = None) -> dict[str, Any]:
    path = claude_settings_path(home)
    data = read_claude_settings(home)
    permissions = data.get("permissions", {})
    if not isinstance(permissions, dict):
        permissions = {}
    permissions["skipDangerousModePermissionPrompt"] = bool(enabled)
    data["permissions"] = permissions

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return claude_settings_status(home)
