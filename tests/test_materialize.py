from pathlib import Path

import yaml

from leso.expand import expand_grid
from leso.materialize import (
    apply_overlay,
    materialize_trial,
    materialize_trials,
    set_nested_path,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "base_experiment.yaml"


def test_set_nested_path():
    data = {"hparams": {"lr": 0.01, "batch_size": 64}}
    set_nested_path(data, "hparams.batch_size", 32)
    assert data["hparams"]["batch_size"] == 32
    assert data["hparams"]["lr"] == 0.01


def test_apply_overlay_does_not_mutate_base():
    base = {"hparams": {"lr": 0.01}}
    overlay = {"hparams.lr": 0.001}
    merged = apply_overlay(base, overlay)
    assert merged["hparams"]["lr"] == 0.001
    assert base["hparams"]["lr"] == 0.01


def test_materialize_trial(tmp_path):
    out = tmp_path / "trial_000" / "config.yaml"
    path = materialize_trial(FIXTURE, {"hparams.lr": 0.001}, out)
    assert path == out
    with out.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data["hparams"]["lr"] == 0.001
    assert data["hparams"]["batch_size"] == 64
    assert data["name"] == "fixture-base"


def test_materialize_trials_from_expand(tmp_path):
    overlays = expand_grid({"hparams.lr": [0.01, 0.001]})
    paths = materialize_trials(FIXTURE, overlays, tmp_path / "trials")
    assert len(paths) == 2
    assert paths[0].name == "config.yaml"
    assert (tmp_path / "trials" / "trial_000" / "config.yaml").is_file()
    assert (tmp_path / "trials" / "trial_001" / "config.yaml").is_file()