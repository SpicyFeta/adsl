# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Golden trace tests for hardening v2 and deconfliction (ADR-008)."""

from __future__ import annotations

import json
from pathlib import Path

from adsl.models import (
    ADSL_ForceElement,
    ADSL_LogisticsNode,
    ADSL_LogisticsRoute,
    ADSL_Scenario,
    ADSL_ScenarioPackage,
    ActionType,
    AgentSide,
    NodeType,
    RouteStatus,
    SimulationEventType,
)
from adsl.simulation.engine import SimulationEngine
from adsl.simulation.loader import load_scenario_package
from adsl.simulation.registry import resolve_scenario_path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "golden_traces"
SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def test_golden_deconfliction_trace_seed1() -> None:
    """Reproducible same-tick suppression golden trace (seed=1, tick=1)."""
    expected = _load_fixture("deconfliction_tick1.json")

    scenario = ADSL_Scenario(
        scenario_id="golden-deconflict",
        name="Golden Deconflict",
        description="Deterministic deconfliction fixture.",
        nodes=[
            ADSL_LogisticsNode(
                node_id="N-A",
                name="Port A",
                node_type=NodeType.PORT,
                latitude=1.0,
                longitude=2.0,
                capacity=100.0,
            ),
            ADSL_LogisticsNode(
                node_id="N-B",
                name="Hub B",
                node_type=NodeType.HUB,
                latitude=1.1,
                longitude=2.1,
                capacity=100.0,
            ),
        ],
        routes=[
            ADSL_LogisticsRoute(
                route_id="R-CONTEST",
                name="Contested Link",
                source_node_id="N-A",
                target_node_id="N-B",
                capacity=30.0,
                transit_time_hours=2.0,
                status=RouteStatus.OPEN,
                metadata={"risk_level": "high"},
            )
        ],
    )
    red_a = ADSL_ForceElement(
        element_id="RED-STRIKE-01",
        name="Red A",
        side=AgentSide.RED,
        role="STRIKE",
        patrol_route_ids=["R-CONTEST"],
        readiness=0.9,
    )
    red_b = ADSL_ForceElement(
        element_id="RED-STRIKE-02",
        name="Red B",
        side=AgentSide.RED,
        role="STRIKE",
        patrol_route_ids=["R-CONTEST"],
        readiness=0.9,
    )
    package = ADSL_ScenarioPackage(
        scenario=scenario,
        red_force_elements=[red_a, red_b],
        blue_force_elements=[],
    )

    engine = SimulationEngine(max_ticks=1, seed=1, quiet_logs=True)
    engine.run_scenario(package)

    suppressed = [
        event.payload
        for event in engine.events
        if event.event_type == SimulationEventType.ACTION_SUPPRESSED
    ]
    recorded = [
        event.payload
        for event in engine.events
        if event.event_type == SimulationEventType.ACTION_RECORDED
    ]

    assert suppressed == expected["action_suppressed"]
    assert recorded == expected["action_recorded"]


def test_golden_hardening_absorption_kessari_seed42() -> None:
    """Golden trace: first attack on hardened route is absorbed (kessari-v1, seed=42)."""
    expected = _load_fixture("hardening_kessari_seed42.json")

    path = resolve_scenario_path("kessari-strait-v1", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    engine = SimulationEngine(max_ticks=30, seed=42, quiet_logs=True)
    engine.run_scenario(package)

    harden_traces = [
        trace for trace in engine.audit_traces if trace.action_type == ActionType.HARDEN
    ]
    assert harden_traces
    first_harden = harden_traces[0]
    assert first_harden.target_id == expected["first_harden"]["target_id"]
    assert first_harden.simulation_tick == expected["first_harden"]["tick"]
    assert any(
        "ADR-008" in step.description for step in first_harden.reasoning_steps
    )

    absorbed = [
        event.payload
        for event in engine.events
        if event.event_type == SimulationEventType.ACTION_RECORDED
        and event.payload.get("absorbed") is True
    ]
    assert absorbed
    assert absorbed[0] == expected["first_absorbed_attack"]

    route = next(
        route for route in engine.routes if route.route_id == expected["route_snapshot"]["route_id"]
    )
    assert route.status.value == expected["route_snapshot"]["status"]
    assert route.metadata.get("harden_absorbed", 0) >= expected["route_snapshot"][
        "harden_absorbed_min"
    ]