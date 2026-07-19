"""LESO command-line interface."""

from __future__ import annotations

import os
import shlex

import click

from leso.orchestrator import run_sweep
from leso.status import format_status_report


def _parse_letf_cmd(letf_cmd: str) -> str | list[str]:
    """Allow ``--letf "python path/to/fake_letf.py"`` for stub dry-runs."""
    parts = shlex.split(letf_cmd, posix=(os.name != "nt"))
    return parts if len(parts) > 1 else letf_cmd


@click.group()
def cli() -> None:
    """Lightweight Experiment Sweep / Orchestrator."""


@cli.command("run")
@click.argument("config", type=click.Path(exists=True, dir_okay=False, path_type=str))
@click.option(
    "--sweep-root",
    default="sweeps",
    show_default=True,
    help="Directory under which the sweep folder is created.",
)
@click.option("--device", default="cpu", show_default=True)
@click.option(
    "--letf",
    "letf_cmd",
    default="letf",
    show_default=True,
    help='LETF executable, or a quoted command e.g. "python tests/fixtures/fake_letf.py".',
)
def run_cmd(config: str, sweep_root: str, device: str, letf_cmd: str) -> None:
    """Run a full sweep from a Sweep YAML."""
    result = run_sweep(
        config,
        sweep_root=sweep_root,
        device=device,
        letf_cmd=_parse_letf_cmd(letf_cmd),
    )
    click.echo(f"Sweep completed: {result.sweep_id}")
    click.echo(f"Directory: {result.sweep_dir}")
    if result.ranked:
        best = next((row for row in result.ranked if row.score is not None), None)
        if best is not None:
            click.echo(
                f"Best trial: {best.trial_id} "
                f"({best.metric}={best.score}) run_id={best.run_id}"
            )
        click.echo(f"Summary: {result.sweep_dir / 'sweep_summary.json'}")


@cli.command("status")
@click.argument(
    "sweep_dir",
    type=click.Path(exists=True, file_okay=False, path_type=str),
)
def status_cmd(sweep_dir: str) -> None:
    """Print trial inventory and ranking for a finished sweep directory."""
    click.echo(format_status_report(sweep_dir), nl=False)


if __name__ == "__main__":
    cli()
