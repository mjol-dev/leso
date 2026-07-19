"""Inspect a finished sweep directory (manifest + summary)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from leso.ranker import DEFAULT_SUMMARY_NAME
from leso.tracker import ManifestRecord, load_manifest


def read_sweep_summary(
    sweep_dir: str | Path,
    *,
    name: str = DEFAULT_SUMMARY_NAME,
) -> dict[str, Any]:
    path = Path(sweep_dir) / name
    if not path.is_file():
        raise FileNotFoundError(f"Sweep summary not found: {path}")
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"Sweep summary root must be a mapping: {path}")
    return raw


def _score_by_trial(summary: dict[str, Any]) -> dict[str, float | None]:
    scores: dict[str, float | None] = {}
    trials = summary.get("trials")
    if not isinstance(trials, list):
        return scores
    for row in trials:
        if not isinstance(row, dict):
            continue
        trial_id = row.get("trial_id")
        if not isinstance(trial_id, str):
            continue
        score = row.get("score")
        if score is None:
            scores[trial_id] = None
        elif isinstance(score, (int, float)) and not isinstance(score, bool):
            scores[trial_id] = float(score)
    return scores


def format_status_report(sweep_dir: str | Path) -> str:
    """Build a human-readable status report for ``sweep_dir``."""
    root = Path(sweep_dir).resolve()
    records = load_manifest(root)
    summary = read_sweep_summary(root)
    scores = _score_by_trial(summary)
    metric = summary.get("metric", "final_loss")

    lines = [f"Sweep: {root}"]
    best_id = summary.get("best_trial_id")
    best_score = summary.get("best_score")
    best_run = summary.get("best_run_id")
    if best_id is not None:
        lines.append(
            f"Best: {best_id} {metric}={best_score} run_id={best_run}"
        )
    else:
        lines.append("Best: (none)")

    lines.append("")
    lines.append("Trials:")
    if not records:
        lines.append("  (none)")
    else:
        for record in records:
            lines.append(_format_trial_line(record, scores.get(record.trial_id), metric))
    return "\n".join(lines) + "\n"


def _format_trial_line(
    record: ManifestRecord,
    score: float | None,
    metric: str,
) -> str:
    score_part = f"{metric}={score}" if score is not None else f"{metric}=-"
    run_part = record.run_id or "-"
    return f"  {record.trial_id}  {record.status}  {score_part}  run_id={run_part}"
