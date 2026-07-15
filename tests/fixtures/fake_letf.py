"""Minimal LETF CLI stub for scheduler tests.

Usage: python fake_letf.py run <config.yaml> --root <dir> [--device cpu]
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="letf")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("config")
    run.add_argument("--root", default="experiments")
    run.add_argument("--device", default="cpu")
    args = parser.parse_args(argv)

    if args.command != "run":
        return 2

    config = Path(args.config)
    if not config.is_file():
        print(f"Config not found: {config}", flush=True)
        return 1

    digest = hashlib.sha1(str(config.resolve()).encode()).hexdigest()[:8]
    run_id = f"stub_{digest}"
    run_dir = Path(args.root) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "summary.json").write_text(
        '{"status": "completed"}\n',
        encoding="utf-8",
    )

    print(f"Run completed: {run_id}")
    print(f"Directory: {run_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
