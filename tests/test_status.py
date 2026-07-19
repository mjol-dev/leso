import json
from pathlib import Path

from click.testing import CliRunner

from leso.cli import cli
from leso.status import format_status_report, read_sweep_summary
from leso.tracker import ManifestRecord, write_manifest


def _write_finished_sweep(sweep_dir: Path) -> None:
    write_manifest(
        sweep_dir,
        [
            ManifestRecord(
                trial_id="trial_000",
                run_id="run-a",
                run_dir=str(sweep_dir / "experiments" / "run-a"),
                status="completed",
            ),
            ManifestRecord(
                trial_id="trial_001",
                run_id="run-b",
                run_dir=str(sweep_dir / "experiments" / "run-b"),
                status="completed",
            ),
        ],
    )
    summary = {
        "metric": "final_loss",
        "lower_is_better": True,
        "best_trial_id": "trial_000",
        "best_run_id": "run-a",
        "best_score": 0.25,
        "trials": [
            {
                "rank": 1,
                "trial_id": "trial_000",
                "run_id": "run-a",
                "run_dir": str(sweep_dir / "experiments" / "run-a"),
                "status": "completed",
                "score": 0.25,
                "metric": "final_loss",
            },
            {
                "rank": 2,
                "trial_id": "trial_001",
                "run_id": "run-b",
                "run_dir": str(sweep_dir / "experiments" / "run-b"),
                "status": "completed",
                "score": 0.9,
                "metric": "final_loss",
            },
        ],
    }
    (sweep_dir / "sweep_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )


def test_read_sweep_summary(tmp_path):
    _write_finished_sweep(tmp_path)
    payload = read_sweep_summary(tmp_path)
    assert payload["best_trial_id"] == "trial_000"
    assert payload["best_score"] == 0.25


def test_format_status_report(tmp_path):
    _write_finished_sweep(tmp_path)
    report = format_status_report(tmp_path)
    assert f"Sweep: {tmp_path.resolve()}" in report
    assert "Best: trial_000 final_loss=0.25 run_id=run-a" in report
    assert "trial_000  completed  final_loss=0.25  run_id=run-a" in report
    assert "trial_001  completed  final_loss=0.9  run_id=run-b" in report


def test_cli_status(tmp_path):
    _write_finished_sweep(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["status", str(tmp_path)])
    assert result.exit_code == 0
    assert "Best: trial_000" in result.output
    assert "trial_001" in result.output
