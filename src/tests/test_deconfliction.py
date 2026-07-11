# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for same-tick action deconfliction (ADR-008)."""

from pathlib import Path

from adsl.models import (
    ADSL_ForceElement,
    ADSL_LogisticsNode,
    ADSL_LogisticsRoute,
    ADSL_Scenario,
    ADSL_ScenarioPackage,
    Action,
    ActionType,
    AgentSide,
    NodeType,
    RouteStatus,
    SimulationEventType,
)
from adsl.simulation.deconfliction import TickTargetRegistry, action_target_key
from adsl.simulation.engine import SimulationEngine

SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"


def test_action_target_key_for_route_actions() -> None:
    action = Action(action_type=ActionType.ATTACK_ROUTE, target_id="R-001")
    assert action_target_key(action) == "route:R-001"


def test_tick_registry_suppresses_duplicate_claims() -> None:
    registry = TickTargetRegistry()
    first = Action(action_type=ActionType.ATTACK_ROUTE, target_id="R-001")
    second = Action(action_type=ActionType.HARDEN, target_id="R-001")

    suppress, _, _ = registry.should_suppress(first, "RED-STRIKE-01")
    assert suppress is False

    suppress, target_key, claimed_by = registry.should_suppress(second, "RED-STRIKE-02")
    assert suppress is True
    assert target_key == "route:R-001"
    assert claimed_by == "RED-STRIKE-01"


def test_engine_emits_action_suppressed_on_same_tick_conflict() -> None:
    scenario = ADSL_Scenario(
        scenario_id="deconflict-test-v1",
        name="Deconflict Test",
        description="Minimal scenario for same-tick suppression.",
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

    suppressed_events = [
        event
        for event in engine.events
        if event.event_type == SimulationEventType.ACTION_SUPPRESSED
    ]
    assert len(suppressed_events) == 1
    payload = suppressed_events[0].payload
    assert payload["reason"] == "same_tick_target_conflict"
    assert payload["claimed_by_agent_id"] == "RED-STRIKE-01"
    assert payload["suppressed_agent_id"] == "RED-STRIKE-02"