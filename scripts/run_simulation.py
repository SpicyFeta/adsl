#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Run ADSL contested logistics simulation and print an audit trace summary."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TICKS = 50
DEFAULT_SEED = 42

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from adsl.export.bundle import build_run_bundle, export_run_bundle  # noqa: E402
from adsl.models import SimulationEventType  # noqa: E402
from adsl.ontology.integration import (  # noqa: E402
    build_run_sync_payload,
    is_ontology_sync_enabled,
    sync_run_to_ontology,
)
from adsl.simulation.engine import SimulationEngine  # noqa: E402
from adsl.simulation.loader import load_scenario_package  # noqa: E402
from adsl.simulation.registry import list_scenario_ids, resolve_scenario_path  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ADSL contested logistics simulation."
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
        default="kessari-strait-v1",
        help=(
            "Scenario ID from data/synthetic/scenario_registry.json "
            f"(known: {', '.join(list_scenario_ids())})."
        ),
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
        "--sync-ontology",
        action="store_true",
        help="Enable Palantir Ontology placeholder sync (or set ADSL_ONTOLOGY_SYNC_ENABLED=true).",
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=None,
        help="Write ADR-009 run export bundle to this directory after simulation.",
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
    return resolve_scenario_path(args.scenario)


def _print_header(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def _print_run_summary(engine: SimulationEngine) -> None:
    run = engine.run
    if run is None:
        print("No simulation run recorded.")
        return

    _print_header("Simulation Run")
    print(f"Run ID:       {run.run_id}")
    print(f"Scenario:     {run.scenario_id}")
    print(f"Status:       {run.status.value}")
    print(f"Ticks:        {run.current_tick + 1}")
    print(f"Seed:         {run.seed}")
    print(f"Traces:       {len(engine.audit_traces)}")
    print(f"Events:       {len(engine.events)}")


def _print_network_summary(engine: SimulationEngine) -> None:
    _print_header("Network State (End of Run)")
    node_statuses = Counter(node.status.value for node in engine.nodes)
    route_statuses = Counter(route.status.value for route in engine.routes)
    print(f"Nodes:  {dict(node_statuses)}")
    print(f"Routes: {dict(route_statuses)}")


def _print_key_events(engine: SimulationEngine, *, limit: int = 12) -> None:
    _print_header(f"Key Events (last {limit} action/decision events)")
    actionable = [
        event
        for event in engine.events
        if event.event_type
        in {SimulationEventType.AGENT_DECISION, SimulationEventType.ACTION_RECORDED}
    ]
    for event in actionable[-limit:]:
        side = event.agent_side.value if event.agent_side else "-"
        agent = event.agent_id or "-"
        detail = ""
        if event.event_type == SimulationEventType.AGENT_DECISION:
            detail = (
                f"{event.payload.get('action_type')} — "
                f"{event.payload.get('action_summary', '')}"
            )
        elif event.event_type == SimulationEventType.ACTION_RECORDED:
            applied = event.payload.get("applied", False)
            detail = (
                f"{event.payload.get('action_type')} "
                f"target={event.payload.get('target_id')} applied={applied}"
            )
        print(
            f"  tick {event.simulation_tick:>3} | {side:>4} | {agent:<14} | "
            f"{event.event_type.value:<16} | {detail}"
        )


def _print_audit_trace_summary(engine: SimulationEngine, *, limit: int = 8) -> None:
    _print_header("Audit Trace Summary")
    by_side = Counter(trace.agent_side.value for trace in engine.audit_traces)
    by_action = Counter(trace.action_type.value for trace in engine.audit_traces)
    by_category = Counter(trace.decision_category.value for trace in engine.audit_traces)
    print(f"By side:      {dict(by_side)}")
    print(f"By action:    {dict(by_action)}")
    print(f"By category:  {dict(by_category)}")

    _print_header(f"Sample Audit Traces (last {limit})")
    for trace in engine.audit_traces[-limit:]:
        first_step = trace.reasoning_steps[0].description if trace.reasoning_steps else ""
        print(
            f"  tick {trace.simulation_tick:>3} | {trace.agent_side.value:>4} | "
            f"{trace.agent_id:<14} | {trace.action_type.value:<12} | "
            f"{trace.action_summary}"
        )
        print(f"           rule/category: {trace.decision_category.value} | {first_step[:70]}")


def _print_ontology_summary(
    engine: SimulationEngine, package, *, sync_enabled: bool
) -> None:
    run = engine.run
    if run is None:
        return

    payload = build_run_sync_payload(
        run=run,
        nodes=engine.nodes,
        routes=engine.routes,
        audit_traces=engine.audit_traces,
        events=engine.events,
        scenario_package=package,
    )
    _print_header("Palantir Ontology Payload (ADR-006)")
    for key, items in payload.items():
        print(f"  {key:<18} {len(items):>5} objects")

    if sync_enabled:
        sync_result = sync_run_to_ontology(
            run=run,
            nodes=engine.nodes,
            routes=engine.routes,
            audit_traces=engine.audit_traces,
            events=engine.events,
            scenario_package=package,
        )
        print(f"  Sync enabled:     {sync_result['sync_enabled']}")
        print(f"  Placeholder RIDs: {len(sync_result['written_rids'])}")
    else:
        print("  Sync enabled:     false (offline mode)")


def main() -> int:
    args = _parse_args()
    sync_enabled = args.sync_ontology or is_ontology_sync_enabled()
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

    print("ADSL — Contested Logistics Simulation")
    print(f"Dataset: {dataset_path.name}")
    print(f"Scenario: {package.scenario.scenario_id}")
    print(f"Nodes: {len(package.scenario.nodes)} | Routes: {len(package.scenario.routes)}")
    print(
        f"Force elements: {len(package.red_force_elements)} Red, "
        f"{len(package.blue_force_elements)} Blue"
    )

    _print_run_summary(engine)
    _print_network_summary(engine)
    _print_key_events(engine)
    _print_audit_trace_summary(engine)
    _print_ontology_summary(engine, package, sync_enabled=sync_enabled)

    if args.export_dir is not None:
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
        _print_header("Run Export (ADR-009)")
        print(f"Export path: {export_path}")

    print()
    print("Simulation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())