#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Run a simulation and export the ADR-009 run bundle."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TICKS = 50
DEFAULT_SEED = 42

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from adsl.export.bundle import build_run_bundle, export_run_bundle  # noqa: E402
from adsl.simulation.engine import SimulationEngine  # noqa: E402
from adsl.simulation.loader import load_scenario_package  # noqa: E402
from adsl.simulation.registry import resolve_scenario_path  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ADSL simulation and export workshop bundle (ADR-009)."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=None,
        help="Path to scenario JSON dataset (overrides --scenario).",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Scenario ID from data/synthetic/scenario_registry.json.",
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=DEFAULT_TICKS,
        help="Number of simulation ticks to execute (max 100).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed recorded on the simulation run.",
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        required=True,
        help="Directory where the run export bundle will be written.",
    )
    parser.add_argument(
        "--quiet-logs",
        action="store_true",
        help="Suppress structlog JSON output during simulation.",
    )
    return parser.parse_args()


def _resolve_dataset(args: argparse.Namespace) -> Path:
    if args.dataset is not None:
        return args.dataset
    if args.scenario is not None:
        return resolve_scenario_path(args.scenario)
    return resolve_scenario_path("kessari-strait-v1")


def main() -> int:
    args = _parse_args()
    dataset_path = _resolve_dataset(args)

    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}", file=sys.stderr)
        return 1

    package = load_scenario_package(dataset_path)
    engine = SimulationEngine(
        max_ticks=args.ticks,
        seed=args.seed,
        quiet_logs=args.quiet_logs,
    )
    run = engine.run_scenario(package)
    if run is None:
        print("Simulation did not produce a run record.", file=sys.stderr)
        return 1

    bundle = build_run_bundle(
        run=run,
        scenario=package.scenario,
        nodes=engine.nodes,
        routes=engine.routes,
        audit_traces=engine.audit_traces,
        events=engine.events,
        scenario_package=package,
        dataset_path=dataset_path,
        ticks_executed=run.current_tick + 1,
    )
    export_path = export_run_bundle(bundle, args.export_dir)

    print("ADSL Run Export Complete (ADR-009)")
    print(f"Scenario:     {package.scenario.scenario_id}")
    print(f"Run ID:       {run.run_id}")
    print(f"Export path:  {export_path}")
    print("Files:")
    for filename in (
        "manifest.json",
        "run_bundle.json",
        "audit_traces.jsonl",
        "simulation_events.jsonl",
        "executive_summary.md",
        "insights.json",
        "insights_report.md",
    ):
        print(f"  - {filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())