import pytest

from leso.expand import expand_grid


def test_expand_2x2_product():
    overlays = expand_grid(
        {
            "hparams.lr": [0.01, 0.001],
            "hparams.batch_size": [32, 64],
        }
    )
    assert len(overlays) == 4
    assert overlays == [
        {"hparams.lr": 0.01, "hparams.batch_size": 32},
        {"hparams.lr": 0.01, "hparams.batch_size": 64},
        {"hparams.lr": 0.001, "hparams.batch_size": 32},
        {"hparams.lr": 0.001, "hparams.batch_size": 64},
    ]


def test_expand_single_axis():
    overlays = expand_grid({"hparams.lr": [0.01, 0.001]})
    assert overlays == [
        {"hparams.lr": 0.01},
        {"hparams.lr": 0.001},
    ]


def test_expand_empty_grid_rejected():
    with pytest.raises(ValueError, match="'grid' must be a non-empty mapping"):
        expand_grid({})
