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

## Status

SweepConfig, grid expansion, and materialize (base + overlay → trial YAML) are implemented with unit tests. N× letf run next.