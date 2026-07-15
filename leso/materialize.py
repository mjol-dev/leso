"""Materialize trial LETF YAMLs from base + overlays."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


def set_nested_path(data: dict[str, Any], path: str, value: Any) -> None:
    """Set a dotted path on a nested dict (mutates ``data``)."""
    parts = path.split(".")
    if not parts or any(not p for p in parts):
        raise ValueError(f"Invalid path: {path!r}")

    cursor: dict[str, Any] = data
    for key in parts[:-1]:
        nested = cursor.get(key)
        if nested is None:
            nested = {}
            cursor[key] = nested
        if not isinstance(nested, dict):
            raise ValueError(f"Cannot descend into non-mapping at {key!r} in {path!r}")
        cursor = nested
    cursor[parts[-1]] = value


def load_base_config(base_path: str | Path) -> dict[str, Any]:
    path = Path(base_path)
    if not path.is_file():
        raise FileNotFoundError(f"Base config not found: {path}")
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"Base config root must be a mapping: {path}")
    return raw


def apply_overlay(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of ``base`` with overlay paths applied."""
    result = copy.deepcopy(base)
    for path, value in overlay.items():
        set_nested_path(result, path, value)
    return result


def materialize_trial(
    base_path: str | Path,
    overlay: dict[str, Any],
    output_path: str | Path,
) -> Path:
    """Load base, apply one overlay, write trial YAML. Returns output path."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    merged = apply_overlay(load_base_config(base_path), overlay)
    with out.open("w", encoding="utf-8") as f:
        yaml.safe_dump(merged, f, sort_keys=False)
    return out


def materialize_trials(
    base_path: str | Path,
    overlays: list[dict[str, Any]],
    trials_dir: str | Path,
) -> list[Path]:
    """Write one trial YAML per overlay under ``trials_dir``."""
    root = Path(trials_dir)
    paths: list[Path] = []
    for i, overlay in enumerate(overlays):
        trial_id = f"trial_{i:03d}"
        out = root / trial_id / "config.yaml"
        paths.append(materialize_trial(base_path, overlay, out))
    return paths