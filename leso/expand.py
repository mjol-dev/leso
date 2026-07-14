"""Expand a SweepConfig grid into trial overlays."""

from __future__ import annotations

import itertools
from typing import Any


def expand_grid(grid: dict[str, list[Any]]) -> list[dict[str, Any]]:
    """Cartesian product of grid path -> value lists into trial overlays.

    Stable key order follows insertion order of ``grid``.
    """
    if not grid:
        raise ValueError("'grid' must be a non-empty mapping")

    keys = list(grid.keys())
    value_lists: list[list[Any]] = []
    for key in keys:
        values = grid[key]
        if not isinstance(values, list) or not values:
            raise ValueError(f"grid[{key!r}] must be a non-empty list")
        value_lists.append(values)

    overlays: list[dict[str, Any]] = []
    for combo in itertools.product(*value_lists):
        overlays.append(dict(zip(keys, combo, strict=True)))
    return overlays
