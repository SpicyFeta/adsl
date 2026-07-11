# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for hardening v2 mechanics (ADR-008)."""

from adsl.models import ADSL_LogisticsRoute, RouteStatus
from adsl.simulation.hardening import HARDEN_LEVEL_INITIAL, apply_attack_route, apply_harden
from adsl.simulation.engine import SimulationEngine
from adsl.simulation.loader import load_scenario_package
from adsl.simulation.registry import resolve_scenario_path
from adsl.models import ActionType

SYNTHETIC_DIR = __import__("pathlib").Path(__file__).resolve().parents[2] / "data" / "synthetic"


def _contested_route() -> ADSL_LogisticsRoute:
    return ADSL_LogisticsRoute(
        route_id="R-TEST",
        name="Test Corridor",
        source_node_id="N-A",
        target_node_id="N-B",
        capacity=40.0,
        transit_time_hours=2.0,
        status=RouteStatus.CONTESTED,
    )


def test_harden_sets_harden_level_and_restores_open() -> None:
    route = _contested_route()
    assert apply_harden(route) is True
    assert route.status == RouteStatus.OPEN
    assert route.metadata["harden_level"] == HARDEN_LEVEL_INITIAL
    assert route.metadata["hardened"] is True


def test_first_attack_absorbed_second_degrades() -> None:
    route = _contested_route()
    apply_harden(route)

    applied, absorbed = apply_attack_route(route)
    assert applied is True
    assert absorbed is True
    assert route.status == RouteStatus.OPEN
    assert route.metadata["harden_level"] == 0
    assert route.metadata["harden_absorbed"] == 1

    applied, absorbed = apply_attack_route(route)
    assert applied is True
    assert absorbed is False
    assert route.status == RouteStatus.CONTESTED


def test_blue_harden_traces_cite_adr008() -> None:
    dataset = resolve_scenario_path("kessari-strait-v1", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(dataset)
    engine = SimulationEngine(max_ticks=20, seed=42, quiet_logs=True)
    engine.run_scenario(package)

    harden_traces = [
        trace for trace in engine.audit_traces if trace.action_type == ActionType.HARDEN
    ]
    assert harden_traces
    assert any(
        "ADR-008" in step.description
        for trace in harden_traces
        for step in trace.reasoning_steps
    )