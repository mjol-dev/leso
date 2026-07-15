import sys
from pathlib import Path

import pytest

from leso.scheduler import (
    parse_letf_run_output,
    run_letf_trial,
    run_letf_trials,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FAKE_LETF = FIXTURES / "fake_letf.py"
BASE_YAML = FIXTURES / "base_experiment.yaml"


def _letf_cmd() -> list[str]:
    return [sys.executable, str(FAKE_LETF)]


def test_parse_letf_run_output():
    run_id, run_dir = parse_letf_run_output(
        "Run completed: abc123\nDirectory: C:/tmp/experiments/abc123\n"
    )
    assert run_id == "abc123"
    assert run_dir == Path("C:/tmp/experiments/abc123")


def test_parse_letf_run_output_missing_lines():
    with pytest.raises(ValueError, match="Could not parse"):
        parse_letf_run_output("nope\n")


def test_run_letf_trial(tmp_path):
    result = run_letf_trial(
        BASE_YAML,
        root=tmp_path / "experiments",
        letf_cmd=_letf_cmd(),
    )
    assert result.config == BASE_YAML
    assert result.run_id.startswith("stub_")
    assert result.run_dir.is_dir()
    assert (result.run_dir / "summary.json").is_file()


def test_run_letf_trials_sequential(tmp_path):
    configs = [BASE_YAML, BASE_YAML]
    results = run_letf_trials(
        configs,
        root=tmp_path / "experiments",
        letf_cmd=_letf_cmd(),
    )
    assert len(results) == 2
    assert results[0].run_id == results[1].run_id
    assert all(r.run_dir.is_dir() for r in results)


def test_run_letf_trial_missing_config(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_letf_trial(
            tmp_path / "missing.yaml",
            root=tmp_path / "experiments",
            letf_cmd=_letf_cmd(),
        )
