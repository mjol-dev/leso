"""End-to-end sweep orchestration (runner sequence wiring)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from leso.config import SweepConfig, load_config
from leso.expand import expand_grid
from leso.materialize import materialize_trials
from leso.ranker import RankedTrial, rank_sweep
from leso.scheduler import run_letf_trial
from leso.tracker import ManifestRecord, record_from_letf_result, trial_id_from_config_path, write_manifest


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "sweep"


def make_sweep_id(name: str, when: datetime | None = None) -> str:
    ts = (when or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}_{_slugify(name)}"


def resolve_base_path(base: str, sweep_config_path: Path) -> Path:
    """Resolve SweepConfig.base relative to the sweep YAML location."""
    base_path = Path(base)
    if not base_path.is_absolute():
        base_path = (sweep_config_path.parent / base_path).resolve()
    else:
        base_path = base_path.resolve()
    if not base_path.is_file():
        raise FileNotFoundError(f"Base experiment config not found: {base_path}")
    return base_path


@dataclass(frozen=True)
class SweepRunResult:
    sweep_id: str
    sweep_dir: Path
    config: SweepConfig
    ranked: list[RankedTrial]


def run_sweep(
    config_path: str | Path,
    *,
    sweep_root: str | Path = "sweeps",
    device: str = "cpu",
    letf_cmd: str | Sequence[str] = "letf",
    sweep_id: str | None = None,
) -> SweepRunResult:
    """Wire expand → materialize → N× letf run → track → rank for one Sweep YAML."""
    config_file = Path(config_path).resolve()
    cfg = load_config(config_file)
    base_path = resolve_base_path(cfg.base, config_file)

    sid = sweep_id or make_sweep_id(cfg.name)
    sweep_dir = Path(sweep_root) / sid
    if sweep_dir.exists():
        raise FileExistsError(f"Sweep directory already exists: {sweep_dir}")

    trials_dir = sweep_dir / "trials"
    experiments_root = sweep_dir / "experiments"

    overlays = expand_grid(cfg.grid)
    trial_configs = materialize_trials(base_path, overlays, trials_dir)

    records: list[ManifestRecord] = []
    for trial_config in trial_configs:
        trial_id = trial_id_from_config_path(trial_config)
        try:
            result = run_letf_trial(
                trial_config,
                root=experiments_root,
                device=device,
                letf_cmd=letf_cmd,
            )
            records.append(
                record_from_letf_result(result, trial_id=trial_id, status="completed")
            )
        except (RuntimeError, FileNotFoundError, ValueError):
            records.append(
                ManifestRecord(
                    trial_id=trial_id,
                    run_id="",
                    run_dir="",
                    status="failed",
                    config=str(trial_config),
                )
            )

    write_manifest(sweep_dir, records)
    ranked = rank_sweep(sweep_dir)
    return SweepRunResult(
        sweep_id=sid,
        sweep_dir=sweep_dir,
        config=cfg,
        ranked=ranked,
    )
