import json
import sys
from pathlib import Path

from click.testing import CliRunner

from leso.cli import _parse_letf_cmd, cli
from leso.config import parse_config
from leso.orchestrator import SweepRunResult, resolve_base_path, run_sweep
from leso.ranker import RankedTrial


def test_parse_letf_cmd_splits_stub_invocation():
    parsed = _parse_letf_cmd("python tests/fixtures/fake_letf.py")
    assert parsed == ["python", "tests/fixtures/fake_letf.py"]


def test_parse_letf_cmd_keeps_simple_name():
    assert _parse_letf_cmd("letf") == "letf"

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FAKE_LETF = FIXTURES / "fake_letf.py"
BASE_YAML = FIXTURES / "base_experiment.yaml"


def _letf_cmd() -> list[str]:
    return [sys.executable, str(FAKE_LETF)]


def test_resolve_base_path_relative(tmp_path):
    base = tmp_path / "base.yaml"
    base.write_text("name: x\ntrain: builtin:mnist\n", encoding="utf-8")
    sweep_yaml = tmp_path / "sweep.yaml"
    sweep_yaml.write_text(
        "name: s\nbase: base.yaml\ngrid:\n  hparams.lr: [0.01]\n",
        encoding="utf-8",
    )
    assert resolve_base_path("base.yaml", sweep_yaml) == base.resolve()


def test_run_sweep_end_to_end(tmp_path):
    sweep_yaml = tmp_path / "sweep.yaml"
    sweep_yaml.write_text(
        f"""name: wired-sweep
base: {BASE_YAML.as_posix()}
grid:
  hparams.lr: [0.01, 0.001]
""",
        encoding="utf-8",
    )

    result = run_sweep(
        sweep_yaml,
        sweep_root=tmp_path / "sweeps",
        letf_cmd=_letf_cmd(),
        sweep_id="test_sweep",
    )

    assert result.sweep_id == "test_sweep"
    assert (result.sweep_dir / "trials" / "trial_000" / "config.yaml").is_file()
    assert (result.sweep_dir / "trials" / "trial_001" / "config.yaml").is_file()
    assert (result.sweep_dir / "sweep_manifest.jsonl").is_file()

    summary_path = result.sweep_dir / "sweep_summary.json"
    assert summary_path.is_file()
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["best_trial_id"] is not None
    assert len(payload["trials"]) == 2
    assert len(result.ranked) == 2


def test_cli_run_invokes_orchestrator(monkeypatch, tmp_path):
    sweep_yaml = tmp_path / "sweep.yaml"
    sweep_yaml.write_text("name: x\nbase: b.yaml\ngrid:\n  hparams.lr: [1]\n", encoding="utf-8")

    called: dict = {}

    def fake_run_sweep(config, **kwargs):
        called["config"] = config
        called["kwargs"] = kwargs
        ranked = [
            RankedTrial(
                rank=1,
                trial_id="trial_000",
                run_id="run_a",
                run_dir=str(tmp_path / "run_a"),
                status="completed",
                score=0.1,
                metric="final_loss",
            )
        ]
        return SweepRunResult(
            sweep_id="cli_sweep",
            sweep_dir=tmp_path / "sweeps" / "cli_sweep",
            config=parse_config(
                {"name": "x", "base": "b.yaml", "grid": {"hparams.lr": [1]}}
            ),
            ranked=ranked,
        )

    monkeypatch.setattr("leso.cli.run_sweep", fake_run_sweep)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            str(sweep_yaml),
            "--sweep-root",
            str(tmp_path / "sweeps"),
            "--letf",
            "my-letf",
        ],
    )
    assert result.exit_code == 0, result.output
    assert called["config"] == str(sweep_yaml)
    assert called["kwargs"]["sweep_root"] == str(tmp_path / "sweeps")
    assert called["kwargs"]["letf_cmd"] == "my-letf"
    assert "Sweep completed: cli_sweep" in result.output
    assert "Best trial: trial_000" in result.output
