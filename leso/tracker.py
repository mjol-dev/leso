"""Sweep-level trial inventory (manifest)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from leso.scheduler import LetfRunResult

DEFAULT_MANIFEST_NAME = "sweep_manifest.jsonl"


@dataclass(frozen=True)
class ManifestRecord:
    trial_id: str
    run_id: str
    run_dir: str
    status: str = "completed"
    config: str | None = None


def trial_id_from_config_path(config: str | Path) -> str:
    """Derive trial id from ``.../<trial_id>/config.yaml`` layout."""
    path = Path(config)
    if path.name != "config.yaml":
        raise ValueError(
            f"Expected config.yaml path to derive trial id, got: {path}"
        )
    trial_id = path.parent.name
    if not trial_id:
        raise ValueError(f"Could not derive trial id from: {path}")
    return trial_id


def manifest_path(sweep_dir: str | Path, name: str = DEFAULT_MANIFEST_NAME) -> Path:
    return Path(sweep_dir) / name


def append_record(sweep_dir: str | Path, record: ManifestRecord) -> Path:
    """Append one inventory row to the sweep manifest (JSONL)."""
    path = manifest_path(sweep_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(record), sort_keys=True) + "\n")
    return path


def write_manifest(
    sweep_dir: str | Path,
    records: Sequence[ManifestRecord],
    *,
    name: str = DEFAULT_MANIFEST_NAME,
) -> Path:
    """Overwrite the sweep manifest with the given records."""
    path = manifest_path(sweep_dir, name=name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(asdict(record), sort_keys=True) + "\n")
    return path


def load_manifest(
    sweep_dir: str | Path,
    *,
    name: str = DEFAULT_MANIFEST_NAME,
) -> list[ManifestRecord]:
    """Load inventory rows from the sweep manifest."""
    path = manifest_path(sweep_dir, name=name)
    if not path.is_file():
        raise FileNotFoundError(f"Manifest not found: {path}")

    records: list[ManifestRecord] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            raw: dict[str, Any] = json.loads(text)
            try:
                records.append(
                    ManifestRecord(
                        trial_id=str(raw["trial_id"]),
                        run_id=str(raw["run_id"]),
                        run_dir=str(raw["run_dir"]),
                        status=str(raw.get("status", "completed")),
                        config=None if raw.get("config") is None else str(raw["config"]),
                    )
                )
            except KeyError as exc:
                raise ValueError(
                    f"Invalid manifest row at {path}:{line_no}: missing {exc}"
                ) from exc
    return records


def record_from_letf_result(
    result: LetfRunResult,
    *,
    trial_id: str | None = None,
    status: str = "completed",
) -> ManifestRecord:
    """Build a manifest row from a scheduler result."""
    tid = trial_id if trial_id is not None else trial_id_from_config_path(result.config)
    return ManifestRecord(
        trial_id=tid,
        run_id=result.run_id,
        run_dir=str(result.run_dir),
        status=status,
        config=str(result.config),
    )


def track_results(
    sweep_dir: str | Path,
    results: Iterable[LetfRunResult],
    *,
    status: str = "completed",
) -> Path:
    """Write a full manifest for a sequence of LETF run results."""
    records = [
        record_from_letf_result(result, status=status) for result in results
    ]
    return write_manifest(sweep_dir, records)
