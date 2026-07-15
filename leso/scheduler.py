"""Run materialized trial configs via the LETF CLI."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


_RUN_ID_RE = re.compile(r"^Run completed:\s*(.+)\s*$", re.MULTILINE)
_RUN_DIR_RE = re.compile(r"^Directory:\s*(.+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class LetfRunResult:
    run_id: str
    run_dir: Path
    config: Path


def parse_letf_run_output(stdout: str) -> tuple[str, Path]:
    """Extract run_id and run_dir from ``letf run`` stdout."""
    id_match = _RUN_ID_RE.search(stdout)
    dir_match = _RUN_DIR_RE.search(stdout)
    if id_match is None or dir_match is None:
        raise ValueError(
            "Could not parse letf run output; expected "
            "'Run completed: <run_id>' and 'Directory: <run_dir>'"
        )
    return id_match.group(1).strip(), Path(dir_match.group(1).strip())


def _letf_argv(letf_cmd: str | Sequence[str]) -> list[str]:
    if isinstance(letf_cmd, str):
        return [letf_cmd]
    return list(letf_cmd)


def run_letf_trial(
    config: str | Path,
    *,
    root: str | Path = "experiments",
    device: str = "cpu",
    letf_cmd: str | Sequence[str] = "letf",
) -> LetfRunResult:
    """Invoke ``letf run`` once for a trial YAML. Returns run_id and run_dir."""
    config_path = Path(config)
    if not config_path.is_file():
        raise FileNotFoundError(f"Trial config not found: {config_path}")

    cmd = [
        *_letf_argv(letf_cmd),
        "run",
        str(config_path),
        "--root",
        str(root),
        "--device",
        device,
    ]
    completed = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"letf run failed (exit {completed.returncode}) for {config_path}:\n"
            f"{completed.stderr or completed.stdout}"
        )

    run_id, run_dir = parse_letf_run_output(completed.stdout)
    return LetfRunResult(run_id=run_id, run_dir=run_dir, config=config_path)


def run_letf_trials(
    configs: Sequence[str | Path],
    *,
    root: str | Path = "experiments",
    device: str = "cpu",
    letf_cmd: str | Sequence[str] = "letf",
) -> list[LetfRunResult]:
    """Sequentially run ``letf run`` for each trial config."""
    results: list[LetfRunResult] = []
    for config in configs:
        results.append(
            run_letf_trial(
                config,
                root=root,
                device=device,
                letf_cmd=letf_cmd,
            )
        )
    return results
