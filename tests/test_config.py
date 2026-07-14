from pathlib import Path

import pytest

from leso.config import load_config, parse_config


EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "tiny_sweep.yaml"


def test_load_tiny_sweep_example():
    cfg = load_config(EXAMPLES)
    assert cfg.name == "tiny-lr-sweep"
    assert cfg.base == "../letf-monitoring/examples/mnist.yaml"
    assert cfg.grid == {
        "hparams.lr": [0.01, 0.001],
        "hparams.batch_size": [64],
    }


def test_parse_valid_minimal():
    cfg = parse_config(
        {
            "name": "x",
            "base": "base.yaml",
            "grid": {"hparams.lr": [0.01]},
        }
    )
    assert cfg.name == "x"
    assert cfg.base == "base.yaml"
    assert cfg.grid == {"hparams.lr": [0.01]}


def test_missing_required_keys():
    with pytest.raises(ValueError, match="Missing required keys"):
        parse_config({"name": "x", "base": "base.yaml"})


def test_empty_grid_rejected():
    with pytest.raises(ValueError, match="'grid' must be a non-empty mapping"):
        parse_config({"name": "x", "base": "base.yaml", "grid": {}})


def test_empty_grid_list_rejected():
    with pytest.raises(ValueError, match=r"grid\['hparams.lr'\] must be a non-empty list"):
        parse_config(
            {
                "name": "x",
                "base": "base.yaml",
                "grid": {"hparams.lr": []},
            }
        )


def test_config_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("does-not-exist.yaml")
