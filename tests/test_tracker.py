from pathlib import Path

import pytest

from leso.scheduler import LetfRunResult
from leso.tracker import (
    ManifestRecord,
    append_record,
    load_manifest,
    record_from_letf_result,
    track_results,
    trial_id_from_config_path,
    write_manifest,
)


def test_trial_id_from_config_path(tmp_path):
    config = tmp_path / "trials" / "trial_000" / "config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("name: x\n", encoding="utf-8")
    assert trial_id_from_config_path(config) == "trial_000"


def test_trial_id_from_config_path_rejects_bad_name(tmp_path):
    config = tmp_path / "trial_000" / "other.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("name: x\n", encoding="utf-8")
    with pytest.raises(ValueError, match="config.yaml"):
        trial_id_from_config_path(config)


def test_write_and_load_manifest(tmp_path):
    sweep_dir = tmp_path / "sweeps" / "demo"
    records = [
        ManifestRecord(
            trial_id="trial_000",
            run_id="run_a",
            run_dir=str(tmp_path / "experiments" / "run_a"),
            status="completed",
            config=str(tmp_path / "trials" / "trial_000" / "config.yaml"),
        ),
        ManifestRecord(
            trial_id="trial_001",
            run_id="run_b",
            run_dir=str(tmp_path / "experiments" / "run_b"),
            status="failed",
        ),
    ]
    path = write_manifest(sweep_dir, records)
    assert path == sweep_dir / "sweep_manifest.jsonl"

    loaded = load_manifest(sweep_dir)
    assert loaded == records


def test_append_record(tmp_path):
    sweep_dir = tmp_path / "sweep"
    first = ManifestRecord(
        trial_id="trial_000",
        run_id="run_a",
        run_dir="/tmp/run_a",
    )
    second = ManifestRecord(
        trial_id="trial_001",
        run_id="run_b",
        run_dir="/tmp/run_b",
    )
    append_record(sweep_dir, first)
    append_record(sweep_dir, second)
    assert load_manifest(sweep_dir) == [first, second]


def test_track_results_from_letf(tmp_path):
    config0 = tmp_path / "trials" / "trial_000" / "config.yaml"
    config1 = tmp_path / "trials" / "trial_001" / "config.yaml"
    for config in (config0, config1):
        config.parent.mkdir(parents=True)
        config.write_text("name: x\n", encoding="utf-8")

    results = [
        LetfRunResult(
            run_id="run_a",
            run_dir=tmp_path / "experiments" / "run_a",
            config=config0,
        ),
        LetfRunResult(
            run_id="run_b",
            run_dir=tmp_path / "experiments" / "run_b",
            config=config1,
        ),
    ]
    sweep_dir = tmp_path / "sweeps" / "s1"
    track_results(sweep_dir, results)
    loaded = load_manifest(sweep_dir)
    assert [r.trial_id for r in loaded] == ["trial_000", "trial_001"]
    assert [r.run_id for r in loaded] == ["run_a", "run_b"]


def test_record_from_letf_result_explicit_trial_id(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("name: x\n", encoding="utf-8")
    result = LetfRunResult(
        run_id="run_a",
        run_dir=tmp_path / "run_a",
        config=config,
    )
    record = record_from_letf_result(result, trial_id="trial_009", status="failed")
    assert record.trial_id == "trial_009"
    assert record.status == "failed"


def test_load_manifest_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_manifest(tmp_path / "missing_sweep")
