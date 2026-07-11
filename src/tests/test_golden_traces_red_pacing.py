# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Golden trace tests for Red agent pacing (ADR-010)."""

from __future__ import annotations

import json
from pathlib import Path

from adsl.agents.red_interdiction import build_red_agent
from adsl.models import (
    ADSL_ForceElement,
    ADSL_LogisticsNode,
    ADSL_LogisticsRoute,
    ADSL_Scenario,
    ActionType,
    AgentIdentity,
    AgentSide,
    NodeType,
    Observation,
    RouteStatus,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "golden_traces"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def test_golden_cooldown_hold_after_route_attack() -> None:
    expected = _load_fixture("red_pacing_cooldown_hold.json")

    striker = ADSL_ForceElement(
        element_id="RED-STRIKE-GOLDEN",
        name="Golden Striker",
        side=AgentSide.RED,
        role="STRIKE",
        patrol_route_ids=["R-OPEN"],
        readiness=0.9,
        metadata={"strike_cooldown_ticks": 3},
    )
    scenario = ADSL_Scenario(
        scenario_id="golden-cooldown",
        name="Golden Cooldown",
        description="",
        nodes=[
            ADSL_LogisticsNode(
                node_id="N-A",
                name="A",
                node_type=NodeType.PORT,
                latitude=1.0,
                longitude=2.0,
                capacity=100.0,
            ),
            ADSL_LogisticsNode(
                node_id="N-B",
                name="B",
                node_type=NodeType.FORWARD_OPERATING_BASE,
                latitude=1.1,
                longitude=2.1,
                capacity=100.0,
            ),
        ],
        routes=[
            ADSL_LogisticsRoute(
                route_id="R-OPEN",
                name="Corridor",
                source_node_id="N-A",
                target_node_id="N-B",
                capacity=40.0,
                transit_time_hours=2.0,
                status=RouteStatus.OPEN,
                metadata={"risk_level": "high"},
            )
        ],
    )
    agent = build_red_agent(
        AgentIdentity(
            agent_id=striker.element_id,
            side=AgentSide.RED,
            role=striker.role,
        ),
        force_element=striker,
    )

    attack = agent.run_turn(
        Observation(
            run_id="golden-cooldown",
            simulation_tick=0,
            agent_id=striker.element_id,
            agent_side=AgentSide.RED,
            visible_nodes=scenario.nodes,
            visible_routes=scenario.routes,
            context={"patrol_route_ids": ["R-OPEN"], "readiness": 0.9},
        )
    )
    hold = agent.run_turn(
        Observation(
            run_id="golden-cooldown",
            simulation_tick=1,
            agent_id=striker.element_id,
            agent_side=AgentSide.RED,
            visible_nodes=scenario.nodes,
            visible_routes=scenario.routes,
            context={"patrol_route_ids": ["R-OPEN"], "readiness": 0.9},
        )
    )

    assert attack.action.action_type == ActionType.ATTACK_ROUTE
    assert attack.action.target_id == expected["attack"]["target_id"]

    assert hold.action.action_type == ActionType.NO_ACTION
    assert hold.audit_trace.action_summary == expected["hold"]["action_summary"]
    assert (
        hold.audit_trace.inputs_considered["cooldown_remaining"]
        == expected["hold"]["cooldown_remaining"]
    )
    assert any(
        "ADR-010" in step.description for step in hold.audit_trace.reasoning_steps
    )


def test_golden_budget_exhaustion_hold() -> None:
    expected = _load_fixture("red_pacing_budget_exhausted.json")

    striker = ADSL_ForceElement(
        element_id="RED-STRIKE-BUDGET-GOLDEN",
        name="Budget Golden",
        side=AgentSide.RED,
        role="STRIKE",
        patrol_route_ids=["R-OPEN"],
        readiness=0.9,
        metadata={"strike_budget": 1, "strike_cooldown_ticks": 1},
    )
    scenario = ADSL_Scenario(
        scenario_id="golden-budget",
        name="Golden Budget",
        description="",
        nodes=[
            ADSL_LogisticsNode(
                node_id="N-A",
                name="A",
                node_type=NodeType.PORT,
                latitude=1.0,
                longitude=2.0,
                capacity=100.0,
            ),
            ADSL_LogisticsNode(
                node_id="N-B",
                name="B",
                node_type=NodeType.FORWARD_OPERATING_BASE,
                latitude=1.1,
                longitude=2.1,
                capacity=100.0,
            ),
        ],
        routes=[
            ADSL_LogisticsRoute(
                route_id="R-OPEN",
                name="Corridor",
                source_node_id="N-A",
                target_node_id="N-B",
                capacity=40.0,
                transit_time_hours=2.0,
                status=RouteStatus.OPEN,
                metadata={"risk_level": "high"},
            )
        ],
    )
    agent = build_red_agent(
        AgentIdentity(
            agent_id=striker.element_id,
            side=AgentSide.RED,
            role=striker.role,
        ),
        force_element=striker,
    )

    agent.run_turn(
        Observation(
            run_id="golden-budget",
            simulation_tick=0,
            agent_id=striker.element_id,
            agent_side=AgentSide.RED,
            visible_nodes=scenario.nodes,
            visible_routes=scenario.routes,
            context={"patrol_route_ids": ["R-OPEN"], "readiness": 0.9},
        )
    )
    hold = agent.run_turn(
        Observation(
            run_id="golden-budget",
            simulation_tick=2,
            agent_id=striker.element_id,
            agent_side=AgentSide.RED,
            visible_nodes=scenario.nodes,
            visible_routes=scenario.routes,
            context={"patrol_route_ids": ["R-OPEN"], "readiness": 0.9},
        )
    )

    assert hold.action.action_type == ActionType.NO_ACTION
    assert hold.audit_trace.action_summary == expected["hold"]["action_summary"]
    assert (
        hold.audit_trace.inputs_considered["strike_budget_remaining"]
        == expected["hold"]["strike_budget_remaining"]
    )
    assert (
        hold.audit_trace.inputs_considered["pacing_hold_reason"]
        == expected["hold"]["pacing_hold_reason"]
    )