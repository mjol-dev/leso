import json
from pathlib import Path

import pytest

from leso.ranker import (
    extract_metric,
    rank_records,
    rank_sweep,
    read_summary,
)
from leso.tracker import ManifestRecord, write_manifest


def _write_summary(run_dir: Path, final_loss: float, status: str = "completed") -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": status,
        "result": {
            "metrics": {"final_loss": final_loss, "epochs": 1},
            "artifacts": {},
        },
    }
    (run_dir / "summary.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def test_extract_metric_final_loss():
    summary = {
        "result": {"metrics": {"final_loss": 0.42, "epochs": 1}},
    }
    assert extract_metric(summary) == 0.42


def test_rank_records_lower_loss_wins(tmp_path):
    run_a = tmp_path / "experiments" / "run_a"
    run_b = tmp_path / "experiments" / "run_b"
    _write_summary(run_a, 0.5)
    _write_summary(run_b, 0.1)

    records = [
        ManifestRecord(
            trial_id="trial_000",
            run_id="run_a",
            run_dir=str(run_a),
            status="completed",
        ),
        ManifestRecord(
            trial_id="trial_001",
            run_id="run_b",
            run_dir=str(run_b),
            status="completed",
        ),
    ]
    ranked = rank_records(records)
    assert [r.trial_id for r in ranked] == ["trial_001", "trial_000"]
    assert ranked[0].rank == 1
    assert ranked[0].score == 0.1
    assert ranked[1].score == 0.5


def test_failed_trials_sort_last(tmp_path):
    run_ok = tmp_path / "run_ok"
    run_bad = tmp_path / "run_bad"
    _write_summary(run_ok, 0.2)
    run_bad.mkdir(parents=True)

    records = [
        ManifestRecord(
            trial_id="trial_000",
            run_id="run_bad",
            run_dir=str(run_bad),
            status="failed",
        ),
        ManifestRecord(
            trial_id="trial_001",
            run_id="run_ok",
            run_dir=str(run_ok),
            status="completed",
        ),
    ]
    ranked = rank_records(records)
    assert ranked[0].trial_id == "trial_001"
    assert ranked[1].trial_id == "trial_000"
    assert ranked[1].score is None


def test_rank_sweep_writes_summary(tmp_path):
    sweep_dir = tmp_path / "sweeps" / "demo"
    run_a = tmp_path / "experiments" / "run_a"
    run_b = tmp_path / "experiments" / "run_b"
    _write_summary(run_a, 0.9)
    _write_summary(run_b, 0.3)

    write_manifest(
        sweep_dir,
        [
            ManifestRecord(
                trial_id="trial_000",
                run_id="run_a",
                run_dir=str(run_a),
            ),
            ManifestRecord(
                trial_id="trial_001",
                run_id="run_b",
                run_dir=str(run_b),
            ),
        ],
    )

    ranked = rank_sweep(sweep_dir)
    assert ranked[0].trial_id == "trial_001"

    summary_path = sweep_dir / "sweep_summary.json"
    assert summary_path.is_file()
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["metric"] == "final_loss"
    assert payload["lower_is_better"] is True
    assert payload["best_trial_id"] == "trial_001"
    assert payload["best_score"] == 0.3
    assert len(payload["trials"]) == 2


def test_read_summary_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_summary(tmp_path / "nope")
