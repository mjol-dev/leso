# LESO — Lightweight Experiment Sweep / Orchestrator

Multi-run hyperparameter sweeps that drive [LETF](https://github.com/mjol-dev/letf-monitoring) per trial and rank results (including AWO metrics when present in run dirs).

Portfolio stack: **LESO** (many + select) → **LETF** (one experiment) → optional **AWO** (inside each LETF run).

## Place / purpose / I/O

| | |
|---|---|
| **Place** | Above LETF; consumes LETF `run_dir`s (AWO only via those). |
| **Purpose** | Orchestrate multi-run hparam sweeps over LETF and rank trials. |
| **I/O** | Sweep YAML in → N× `letf run` → sweep summary / ranking out. |

## Runner sequence

`expand grid` → `materialize trial config` → `N× letf run` → `track` → `rank`

## Setup

Python 3.10+. LETF must be installed and on `PATH` for real sweeps (tests use a stub).

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Quickstart

```bash
# Full sweep with real LETF on PATH (needs sibling letf-monitoring / installed letf)
leso run examples/tiny_sweep.yaml
```

### Stub dry-run (no real LETF)

Uses the in-repo fixture base config and `tests/fixtures/fake_letf.py`:

```bash
# From the LESO repo root, after pip install -e ".[dev]"
leso run examples/tiny_sweep_local.yaml --letf "python tests/fixtures/fake_letf.py"
```

This still creates `sweeps/<sweep_id>/` with trials, experiments, manifest, and summary.

Sweep layout:

```text
sweeps/<sweep_id>/
  trials/trial_XXX/config.yaml
  experiments/<run_id>/
  sweep_manifest.jsonl
  sweep_summary.json
```

## Status

MVP runner sequence wired end-to-end: `leso run <sweep.yaml>` → expand → materialize → N× `letf run` → track → rank (`final_loss`).