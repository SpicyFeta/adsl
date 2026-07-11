#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Profile an ADSL simulation run and print hotspot summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from adsl.export.runner import RunSpec  # noqa: E402
from adsl.performance.profiler import profile_run  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile ADSL simulation CPU and memory.")
    parser.add_argument("--scenario", default="continental-mega-scale-v5")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ticks", type=int, default=100)
    parser.add_argument("--scale", action="store_true", help="Enable scale mode.")
    parser.add_argument("--json", action="store_true", help="Output JSON report.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    spec = RunSpec(scenario_id=args.scenario, seed=args.seed, ticks=args.ticks)
    try:
        report = profile_run(spec, scale_mode=args.scale)
    except (ValueError, KeyError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"Profile: {report.scenario_id} | {report.ticks} ticks | {report.elapsed_seconds}s")
        print(f"Peak memory: {report.peak_memory_mb} MB")
        print(report.hotspot_summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())