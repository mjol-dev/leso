"""Rank sweep trials from LETF summary metrics."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from leso.tracker import ManifestRecord, load_manifest

DEFAULT_SUMMARY_NAME = "sweep_summary.json"
DEFAULT_METRIC_KEY = "final_loss"


@dataclass(frozen=True)
class RankedTrial:
    rank: int
    trial_id: str
    run_id: str
    run_dir: str
    status: str
    score: float | None
    metric: str


def read_summary(run_dir: str | Path) -> dict[str, Any]:
    path = Path(run_dir) / "summary.json"
    if not path.is_file():
        raise FileNotFoundError(f"summary.json not found: {path}")
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"summary.json root must be a mapping: {path}")
    return raw


def extract_metric(summary: dict[str, Any], metric_key: str = DEFAULT_METRIC_KEY) -> float:
    """Read ``result.metrics[<metric_key>]`` from a LETF summary."""
    result = summary.get("result")
    if not isinstance(result, dict):
        raise ValueError("summary missing mapping 'result'")
    metrics = result.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("summary.result missing mapping 'metrics'")
    if metric_key not in metrics:
        raise ValueError(f"summary.result.metrics missing {metric_key!r}")
    value = metrics[metric_key]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"metric {metric_key!r} must be numeric, got {type(value)!r}")
    return float(value)


def score_record(
    record: ManifestRecord,
    *,
    metric_key: str = DEFAULT_METRIC_KEY,
) -> float | None:
    """Return metric score for a completed trial, or None if unscored."""
    if record.status != "completed":
        return None
    summary = read_summary(record.run_dir)
    return extract_metric(summary, metric_key=metric_key)


def rank_records(
    records: list[ManifestRecord],
    *,
    metric_key: str = DEFAULT_METRIC_KEY,
    lower_is_better: bool = True,
) -> list[RankedTrial]:
    """Order trials by metric; unscored/failed trials sort last."""
    scored: list[tuple[ManifestRecord, float | None]] = []
    for record in records:
        try:
            score = score_record(record, metric_key=metric_key)
        except (FileNotFoundError, ValueError):
            score = None
        scored.append((record, score))

    def sort_key(item: tuple[ManifestRecord, float | None]) -> tuple[int, float, str]:
        _record, score = item
        if score is None:
            return (1, 0.0, _record.trial_id)
        # lower_is_better: ascending; else negate for descending
        ordered = score if lower_is_better else -score
        return (0, ordered, _record.trial_id)

    scored.sort(key=sort_key)

    ranked: list[RankedTrial] = []
    for index, (record, score) in enumerate(scored, start=1):
        ranked.append(
            RankedTrial(
                rank=index,
                trial_id=record.trial_id,
                run_id=record.run_id,
                run_dir=record.run_dir,
                status=record.status,
                score=score,
                metric=metric_key,
            )
        )
    return ranked


def write_sweep_summary(
    sweep_dir: str | Path,
    ranked: list[RankedTrial],
    *,
    metric_key: str = DEFAULT_METRIC_KEY,
    lower_is_better: bool = True,
    name: str = DEFAULT_SUMMARY_NAME,
) -> Path:
    """Write ranked sweep summary JSON under ``sweep_dir``."""
    path = Path(sweep_dir) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    best = next((row for row in ranked if row.score is not None), None)
    payload = {
        "metric": metric_key,
        "lower_is_better": lower_is_better,
        "best_trial_id": None if best is None else best.trial_id,
        "best_run_id": None if best is None else best.run_id,
        "best_score": None if best is None else best.score,
        "trials": [asdict(row) for row in ranked],
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    return path


def rank_sweep(
    sweep_dir: str | Path,
    *,
    metric_key: str = DEFAULT_METRIC_KEY,
    lower_is_better: bool = True,
) -> list[RankedTrial]:
    """Load manifest, rank trials, write ``sweep_summary.json``."""
    records = load_manifest(sweep_dir)
    ranked = rank_records(
        records,
        metric_key=metric_key,
        lower_is_better=lower_is_better,
    )
    write_sweep_summary(
        sweep_dir,
        ranked,
        metric_key=metric_key,
        lower_is_better=lower_is_better,
    )
    return ranked
