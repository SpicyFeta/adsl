# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for alpine valley scenario v3 (Phase 3 Increment 2)."""

from pathlib import Path

from adsl.export.bundle import EXPORT_SCHEMA_VERSION, build_run_bundle
from adsl.models import NodeStatus, RouteStatus, SimulationStatus
from adsl.simulation.engine import SimulationEngine
from adsl.simulation.loader import load_scenario_package
from adsl.simulation.registry import resolve_scenario_path

SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"
V3_TICKS = 100
V3_SEED = 42


def test_alpine_valley_v3_loads() -> None:
    path = resolve_scenario_path("alpine-valley-v3", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    assert package.scenario.scenario_id == "alpine-valley-v3"
    assert package.scenario.metadata["topology"] == "alpine_dual_corridor"
    assert len(package.scenario.nodes) == 11
    assert len(package.scenario.routes) == 16
    assert len(package.blue_force_elements) == 7
    assert len(package.red_force_elements) == 4


def test_alpine_valley_v3_100_tick_workshop_profile() -> None:
    """Dual-corridor scenario sustains workshops with limited node loss and route pressure."""
    path = resolve_scenario_path("alpine-valley-v3", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    agent_count = len(package.red_force_elements) + len(package.blue_force_elements)

    engine = SimulationEngine(max_ticks=V3_TICKS, seed=V3_SEED, quiet_logs=True)
    run = engine.run_scenario(package)

    assert run is not None
    assert run.status == SimulationStatus.COMPLETED
    assert run.current_tick == V3_TICKS - 1
    assert len(engine.audit_traces) == V3_TICKS * agent_count

    destroyed = sum(1 for node in engine.nodes if node.status == NodeStatus.DESTROYED)
    destruction_fraction = destroyed / len(engine.nodes)
    assert destruction_fraction < 0.4, (
        f"Expected <40% node destruction; got {destroyed}/{len(engine.nodes)} "
        f"({destruction_fraction:.1%})"
    )

    route_statuses = {route.status for route in engine.routes}
    assert RouteStatus.OPEN in route_statuses
    assert RouteStatus.CLOSED in route_statuses or RouteStatus.CONTESTED in route_statuses
    assert len(route_statuses) >= 2


def test_alpine_valley_v3_export_bundle() -> None:
    path = resolve_scenario_path("alpine-valley-v3", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    engine = SimulationEngine(max_ticks=50, seed=V3_SEED, quiet_logs=True)
    run = engine.run_scenario(package)

    bundle = build_run_bundle(
        run=run,
        scenario=package.scenario,
        nodes=engine.nodes,
        routes=engine.routes,
        audit_traces=engine.audit_traces,
        events=engine.events,
        scenario_package=package,
        dataset_path=path,
        ticks_executed=run.current_tick + 1,
    )

    assert bundle["scenario"]["scenario_id"] == "alpine-valley-v3"
    assert bundle["export_schema_version"] == EXPORT_SCHEMA_VERSION