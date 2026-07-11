#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Run multiple simulations and export ADR-009 bundles with a batch manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from adsl.export.batch import batch_export_runs  # noqa: E402
from adsl.export.runner import RunSpec  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute multiple ADSL runs and export a batch workshop set."
    )
    parser.add_argument(
        "--specs",
        type=Path,
        required=True,
        help="JSON file listing runs to execute (see data/analyst/example_batch.json).",
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        required=True,
        help="Directory for batch manifest and per-run ADR-009 bundles.",
    )
    parser.add_argument(
        "--quiet-logs",
        action="store_true",
        help="Suppress structlog JSON during simulation.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Parallel worker count for batch runs (default 1 = sequential).",
    )
    parser.add_argument(
        "--scale",
        action="store_true",
        help="Enable scale mode (up to 250 ticks per run).",
    )
    return parser.parse_args()


def _load_specs(path: Path) -> list[RunSpec]:
    data = json.loads(path.read_text(encoding="utf-8"))
    ticks = data.get("ticks", 50)
    specs: list[RunSpec] = []
    for entry in data["runs"]:
        pacing = entry.get("red_pacing") or entry.get("red_pacing_overrides") or {}
        specs.append(
            RunSpec(
                scenario_id=entry["scenario"],
                seed=entry.get("seed", 42),
                ticks=entry.get("ticks", ticks),
                label=entry.get("label"),
                red_pacing_overrides=pacing,
            )
        )
    return specs


def main() -> int:
    args = _parse_args()
    if not args.specs.exists():
        print(f"Specs file not found: {args.specs}", file=sys.stderr)
        return 1

    try:
        specs = _load_specs(args.specs)
        manifest = batch_export_runs(
            specs,
            args.export_dir,
            quiet_logs=args.quiet_logs,
            workers=args.workers,
            scale_mode=args.scale,
        )
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("ADSL Batch Export Complete")
    print(f"Runs exported: {manifest['run_count']}")
    print(f"Batch manifest: {args.export_dir / 'batch_manifest.json'}")
    if (args.export_dir / "comparison_summary.md").exists():
        print(f"Comparison:     {args.export_dir / 'comparison_summary.md'}")
    for run_entry in manifest["runs"]:
        print(f"  - {run_entry.get('label') or run_entry['run_id']}: {run_entry['export_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())