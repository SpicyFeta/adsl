#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Compare current benchmark results against stored before/after baselines."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BEFORE_AFTER = PROJECT_ROOT / "data" / "performance" / "before_after.json"
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from adsl.export.runner import RunSpec  # noqa: E402
from adsl.performance.benchmark import benchmark_run  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare ADSL benchmark timings against before/after reference data."
    )
    parser.add_argument(
        "--before-after",
        type=Path,
        default=DEFAULT_BEFORE_AFTER,
        help="JSON file with historical comparison rows.",
    )
    parser.add_argument("--scenario", required=True, help="Scenario ID to benchmark.")
    parser.add_argument("--ticks", type=int, default=100, help="Ticks for the run.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--scale",
        action="store_true",
        help="Enable scale mode for extended tick runs.",
    )
    parser.add_argument(
        "--engine-only",
        action="store_true",
        help="Benchmark simulation engine only (exclude export bundle).",
    )
    parser.add_argument("--json", action="store_true", help="Output structured JSON.")
    return parser.parse_args()


def _find_reference(
    data: dict, scenario_id: str, ticks: int, seed: int
) -> dict | None:
    for row in data.get("comparisons", []):
        if (
            row.get("scenario_id") == scenario_id
            and row.get("ticks") == ticks
            and row.get("seed") == seed
        ):
            return row
    return None


def main() -> int:
    args = _parse_args()
    if not args.before_after.exists():
        print(f"Error: {args.before_after} not found", file=sys.stderr)
        return 1

    reference_data = json.loads(args.before_after.read_text(encoding="utf-8"))
    reference = _find_reference(
        reference_data, args.scenario, args.ticks, args.seed
    )

    spec = RunSpec(scenario_id=args.scenario, seed=args.seed, ticks=args.ticks)
    current = benchmark_run(
        spec,
        scale_mode=args.scale,
        engine_only=args.engine_only,
    )

    baseline = None
    if reference is not None:
        baseline = reference.get("after") or reference.get("before")

    improvement_percent = None
    if baseline and baseline.get("elapsed_seconds"):
        before_elapsed = float(baseline["elapsed_seconds"])
        improvement_percent = round(
            (before_elapsed - current.elapsed_seconds) / before_elapsed * 100, 1
        )

    report = {
        "scenario_id": current.scenario_id,
        "ticks": current.ticks,
        "seed": current.seed,
        "engine_only": args.engine_only,
        "current": current.to_dict(),
        "reference": baseline,
        "improvement_percent_vs_reference": improvement_percent,
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print("ADSL Benchmark Comparison")
    print("=" * 60)
    print(f"Scenario: {current.scenario_id}  Ticks: {current.ticks}  Seed: {current.seed}")
    print(f"Mode: {'engine-only' if args.engine_only else 'full run (incl. export)'}")
    print(f"Current:  {current.elapsed_seconds:.3f}s  ({current.ticks_per_second:.1f} ticks/s)")
    if baseline:
        print(
            f"Reference: {baseline.get('elapsed_seconds')}s  "
            f"({baseline.get('ticks_per_second', 'n/a')} ticks/s)"
        )
        if improvement_percent is not None:
            print(f"Improvement vs reference: {improvement_percent}% faster")
    else:
        print("Reference: no matching row in before_after.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())