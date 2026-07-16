"""LESO command-line interface."""

from __future__ import annotations

import click

from leso.orchestrator import run_sweep


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
    help="LETF executable name or path.",
)
def run_cmd(config: str, sweep_root: str, device: str, letf_cmd: str) -> None:
    """Run a full sweep from a Sweep YAML."""
    result = run_sweep(
        config,
        sweep_root=sweep_root,
        device=device,
        letf_cmd=letf_cmd,
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


if __name__ == "__main__":
    cli()
