from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .constants import FEATURE_FILE, feature_baseline_file


@dataclass
class FeatureStatus:
    total: int = 0
    passing: int = 0
    failing: int = 0

    @property
    def complete(self) -> bool:
        return self.total > 0 and self.passing == self.total


@dataclass
class ValidationResult:
    ok: bool
    messages: list[str] = field(default_factory=list)
    baseline_created: bool = False


def feature_path(project_dir: Path) -> Path:
    return project_dir / FEATURE_FILE


def load_features(project_dir: Path) -> list[dict[str, Any]]:
    path = feature_path(project_dir)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list.")
    return data


def feature_status(project_dir: Path) -> FeatureStatus:
    features = load_features(project_dir)
    passing = sum(1 for item in features if bool(item.get("passes", False)))
    total = len(features)
    return FeatureStatus(total=total, passing=passing, failing=total - passing)


def lock_feature_baseline(project_dir: Path, force: bool = False) -> bool:
    features = load_features(project_dir)
    if not features:
        return False

    path = feature_baseline_file(project_dir)
    if path.exists() and not force:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_strip_passes(features), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return True


def validate_feature_invariants(project_dir: Path) -> ValidationResult:
    features = load_features(project_dir)
    if not features:
        return ValidationResult(ok=True, messages=["feature_list.json does not exist yet."])

    shape_errors = _validate_shape(features)
    if shape_errors:
        return ValidationResult(ok=False, messages=shape_errors)

    baseline_path = feature_baseline_file(project_dir)
    if not baseline_path.exists():
        created = lock_feature_baseline(project_dir)
        return ValidationResult(
            ok=True,
            baseline_created=created,
            messages=["Created feature baseline; future sessions may only change passes."],
        )

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    current = _strip_passes(features)
    if baseline != current:
        return ValidationResult(
            ok=False,
            messages=[
                "feature_list.json changed outside the passes field.",
                "Restore removed/edited feature definitions or intentionally refresh the baseline.",
            ],
        )

    return ValidationResult(ok=True, messages=["Feature invariants OK."])


def _validate_shape(features: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(features, start=1):
        if not isinstance(item, dict):
            errors.append(f"Feature #{index} must be an object.")
            continue

        feature_id = item.get("id")
        if not isinstance(feature_id, str) or not feature_id:
            errors.append(f"Feature #{index} is missing a non-empty string id.")
        elif feature_id in seen_ids:
            errors.append(f"Duplicate feature id: {feature_id}")
        else:
            seen_ids.add(feature_id)

        if not isinstance(item.get("category"), str) or not item.get("category"):
            errors.append(f"Feature #{index} is missing category.")
        if not isinstance(item.get("description"), str) or not item.get("description"):
            errors.append(f"Feature #{index} is missing description.")
        if not isinstance(item.get("steps"), list) or not item.get("steps"):
            errors.append(f"Feature #{index} must have non-empty steps.")
        if "passes" not in item or not isinstance(item.get("passes"), bool):
            errors.append(f"Feature #{index} must include boolean passes.")
    return errors


def _strip_passes(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stripped: list[dict[str, Any]] = []
    for item in features:
        copy = dict(item)
        copy.pop("passes", None)
        stripped.append(copy)
    return stripped
