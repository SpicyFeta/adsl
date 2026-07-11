#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Benchmark ADSL simulation throughput and check performance baselines."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINES = PROJECT_ROOT / "data" / "performance" / "baselines.json"
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from adsl.export.runner import RunSpec  # noqa: E402
from adsl.performance.benchmark import (  # noqa: E402
    benchmark_run,
    benchmark_suite,
    check_regression,
    load_baselines,
    save_baselines,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark ADSL simulation performance.")
    parser.add_argument("--scenario", default="alpine-valley-v3", help="Scenario ID.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--ticks", type=int, default=100, help="Ticks per run.")
    parser.add_argument(
        "--scale",
        action="store_true",
        help="Enable scale mode (up to 500 ticks; use scale scenario for stress).",
    )
    parser.add_argument(
        "--engine-only",
        action="store_true",
        help="Benchmark simulation engine only (exclude export bundle/analytics).",
    )
    parser.add_argument(
        "--suite",
        type=Path,
        help="JSON file with a list of benchmark runs (overrides --scenario).",
    )
    parser.add_argument(
        "--baselines",
        type=Path,
        default=DEFAULT_BASELINES,
        help="Baseline thresholds JSON for regression checks.",
    )
    parser.add_argument(
        "--update-baselines",
        action="store_true",
        help="Write measured timings back to the baselines file.",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON results.")
    parser.add_argument(
        "--memory",
        action="store_true",
        help="Track peak memory via tracemalloc (adds profiling overhead).",
    )
    return parser.parse_args()


def _load_suite(path: Path, scale_mode: bool) -> list[RunSpec]:
    data = json.loads(path.read_text(encoding="utf-8"))
    specs: list[RunSpec] = []
    for entry in data["runs"]:
        specs.append(
            RunSpec(
                scenario_id=entry["scenario"],
                seed=entry.get("seed", 42),
                ticks=entry.get("ticks", data.get("ticks", 100)),
                label=entry.get("label"),
            )
        )
    return specs


def _format_table(results: list) -> str:
    lines = [
        "ADSL Performance Benchmark",
        "=" * 88,
        f"{'Scenario':<28} {'Ticks':>6} {'Seed':>5} {'Elapsed':>9} {'Ticks/s':>8} "
        f"{'Traces':>7} {'Nodes':>6}",
        "-" * 88,
    ]
    for result in results:
        lines.append(
            f"{result.scenario_id:<28} {result.ticks:>6} {result.seed:>5} "
            f"{result.elapsed_seconds:>8.3f}s {result.ticks_per_second:>8.1f} "
            f"{result.audit_trace_count:>7} {result.node_count:>6}"
        )
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    scale_mode = args.scale

    try:
        if args.suite is not None:
            specs = _load_suite(args.suite, scale_mode)
            results = benchmark_suite(
                specs,
                scale_mode=scale_mode,
                track_memory=args.memory,
                engine_only=args.engine_only,
            )
        else:
            spec = RunSpec(
                scenario_id=args.scenario,
                seed=args.seed,
                ticks=args.ticks,
            )
            results = [
                benchmark_run(
                    spec,
                    scale_mode=scale_mode,
                    track_memory=args.memory,
                    engine_only=args.engine_only,
                )
            ]
    except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps([result.to_dict() for result in results], indent=2))
    else:
        print(_format_table(results))

    violations: list[str] = []
    if args.baselines.exists():
        baselines = load_baselines(args.baselines)
        for result in results:
            violations.extend(check_regression(result, baselines))
        if violations:
            print("\nRegression violations:")
            for item in violations:
                print(f"  • {item}")

    if args.update_baselines:
        baselines_data = (
            load_baselines(args.baselines)
            if args.baselines.exists()
            else {"schema_version": "1.0", "benchmarks": {}}
        )
        for result in results:
            key = f"{result.scenario_id}@{result.ticks}/seed={result.seed}"
            baselines_data["benchmarks"][key] = {
                "max_elapsed_seconds": round(result.elapsed_seconds * 1.5, 4),
                "ticks_per_second": result.ticks_per_second,
                "measured_elapsed_seconds": result.elapsed_seconds,
            }
        save_baselines(args.baselines, baselines_data)
        print(f"\nUpdated baselines: {args.baselines}")

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())