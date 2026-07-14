"""SweepConfig loading and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SweepConfig:
    name: str
    base: str
    grid: dict[str, list[Any]] = field(default_factory=dict)


def load_config(path: str | Path) -> SweepConfig:
    """Load and validate a sweep YAML file."""
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with config_path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"Config root must be a mapping: {config_path}")

    return parse_config(raw)


def parse_config(raw: dict[str, Any]) -> SweepConfig:
    """Validate a raw dict and return SweepConfig."""
    missing = [key for key in ("name", "base", "grid") if key not in raw]
    if missing:
        raise ValueError(f"Missing required keys: {', '.join(missing)}")

    name = raw["name"]
    base = raw["base"]
    grid = raw["grid"]

    if not isinstance(name, str) or not name.strip():
        raise ValueError("'name' must be a non-empty string")
    if not isinstance(base, str) or not base.strip():
        raise ValueError("'base' must be a non-empty string")
    if not isinstance(grid, dict):
        raise ValueError("'grid' must be a mapping")
    if not grid:
        raise ValueError("'grid' must be a non-empty mapping")

    parsed_grid: dict[str, list[Any]] = {}
    for key, values in grid.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("grid keys must be non-empty strings")
        if not isinstance(values, list):
            raise ValueError(f"grid[{key!r}] must be a list")
        if not values:
            raise ValueError(f"grid[{key!r}] must be a non-empty list")
        parsed_grid[key.strip()] = list(values)

    return SweepConfig(
        name=name.strip(),
        base=base.strip(),
        grid=parsed_grid,
    )
