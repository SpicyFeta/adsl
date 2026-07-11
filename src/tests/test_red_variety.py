# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for Red agent variety mechanics (ADR-010)."""

from __future__ import annotations

from pathlib import Path

from adsl.agents.red_interdiction import RedInterdictionAgent, build_red_agent
from adsl.models import (
    ADSL_ForceElement,
    ADSL_LogisticsNode,
    ADSL_LogisticsRoute,
    ADSL_Scenario,
    ADSL_ScenarioPackage,
    ActionType,
    AgentIdentity,
    AgentSide,
    DecisionCategory,
    NodeType,
    Observation,
    RouteStatus,
)
from adsl.simulation.engine import SimulationEngine
from adsl.simulation.loader import load_scenario_package
from adsl.simulation.registry import resolve_scenario_path

SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"
PHASE2_BASELINE_ATTACK_ROUTE = 7
PHASE2_BASELINE_DISTINCT_ROUTE_TARGETS = 5


def _strike_observation(
    agent: RedInterdictionAgent,
    package: ADSL_ScenarioPackage,
    *,
    tick: int,
) -> Observation:
    element = next(
        item for item in package.red_force_elements if item.role == "STRIKE"
    )
    return Observation(
        run_id="run-pacing-test",
        simulation_tick=tick,
        agent_id=agent.identity.agent_id,
        agent_side=AgentSide.RED,
        visible_nodes=package.scenario.nodes,
        visible_routes=package.scenario.routes,
        context={
            "patrol_route_ids": element.patrol_route_ids,
            "readiness": element.readiness,
            "priority_target": element.metadata.get("priority_target"),
            "role": element.role,
        },
    )


def test_strike_agent_holds_during_route_cooldown() -> None:
    path = SYNTHETIC_DIR / "logistics_scenario_v1.json"
    package = load_scenario_package(path)
    agent = _strike_agent_from_package(package)

    attack = agent.run_turn(_strike_observation(agent, package, tick=0))
    assert attack.action.action_type == ActionType.ATTACK_ROUTE

    hold = agent.run_turn(_strike_observation(agent, package, tick=1))
    assert hold.action.action_type == ActionType.NO_ACTION
    assert "cooldown" in hold.audit_trace.action_summary.lower()
    assert any(
        "ADR-010" in step.description for step in hold.audit_trace.reasoning_steps
    )
    assert hold.audit_trace.inputs_considered.get("cooldown_remaining", 0) > 0


def test_strike_budget_limits_attacks() -> None:
    scenario = ADSL_Scenario(
        scenario_id="budget-test",
        name="Budget Test",
        description="Minimal scenario for strike budget.",
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
                name="FOB B",
                node_type=NodeType.FORWARD_OPERATING_BASE,
                latitude=1.1,
                longitude=2.1,
                capacity=100.0,
            ),
        ],
        routes=[
            ADSL_LogisticsRoute(
                route_id="R-OPEN",
                name="Open Corridor",
                source_node_id="N-A",
                target_node_id="N-B",
                capacity=50.0,
                transit_time_hours=2.0,
                status=RouteStatus.OPEN,
                metadata={"risk_level": "high"},
            )
        ],
    )
    striker = ADSL_ForceElement(
        element_id="RED-STRIKE-BUDGET",
        name="Budget Striker",
        side=AgentSide.RED,
        role="STRIKE",
        patrol_route_ids=["R-OPEN"],
        readiness=0.9,
        metadata={"strike_budget": 2, "strike_cooldown_ticks": 1},
    )
    agent = build_red_agent(
        AgentIdentity(
            agent_id=striker.element_id,
            side=AgentSide.RED,
            role=striker.role,
        ),
        force_element=striker,
    )

    obs = Observation(
        run_id="budget-run",
        simulation_tick=0,
        agent_id=agent.identity.agent_id,
        agent_side=AgentSide.RED,
        visible_nodes=scenario.nodes,
        visible_routes=scenario.routes,
        context={"patrol_route_ids": striker.patrol_route_ids, "readiness": 0.9},
    )

    first = agent.run_turn(obs)
    assert first.action.action_type == ActionType.ATTACK_ROUTE

    second = agent.run_turn(
        Observation(
            run_id="budget-run",
            simulation_tick=2,
            agent_id=agent.identity.agent_id,
            agent_side=AgentSide.RED,
            visible_nodes=scenario.nodes,
            visible_routes=scenario.routes,
            context={"patrol_route_ids": striker.patrol_route_ids, "readiness": 0.9},
        )
    )
    assert second.action.action_type == ActionType.ATTACK_ROUTE

    third = agent.run_turn(
        Observation(
            run_id="budget-run",
            simulation_tick=4,
            agent_id=agent.identity.agent_id,
            agent_side=AgentSide.RED,
            visible_nodes=scenario.nodes,
            visible_routes=scenario.routes,
            context={"patrol_route_ids": striker.patrol_route_ids, "readiness": 0.9},
        )
    )
    assert third.action.action_type == ActionType.NO_ACTION
    assert third.audit_trace.inputs_considered.get("strike_budget_remaining") == 0
    assert any(
        "ADR-010" in step.description for step in third.audit_trace.reasoning_steps
    )


def test_kessari_v1_pacing_improves_attack_route_metric() -> None:
    path = resolve_scenario_path("kessari-strait-v1", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    engine = SimulationEngine(max_ticks=100, seed=42, quiet_logs=True)
    engine.run_scenario(package)

    attack_route_traces = [
        trace
        for trace in engine.audit_traces
        if trace.action_type == ActionType.ATTACK_ROUTE
    ]
    distinct_targets = {trace.target_id for trace in attack_route_traces}

    attack_count_improved = len(attack_route_traces) <= PHASE2_BASELINE_ATTACK_ROUTE
    distinct_improved = len(distinct_targets) >= PHASE2_BASELINE_DISTINCT_ROUTE_TARGETS
    assert attack_count_improved or distinct_improved


def test_pacing_regression_v1_v2_and_v3_scenarios() -> None:
    for scenario_id in ("kessari-strait-v1", "island-chokepoint-v2", "alpine-valley-v3"):
        path = resolve_scenario_path(scenario_id, synthetic_dir=SYNTHETIC_DIR)
        package = load_scenario_package(path)
        engine = SimulationEngine(max_ticks=100, seed=42, quiet_logs=True)
        run = engine.run_scenario(package)
        assert run.status.value == "COMPLETED"


def _strike_agent_from_package(package: ADSL_ScenarioPackage) -> RedInterdictionAgent:
    element = next(
        item for item in package.red_force_elements if item.role == "STRIKE"
    )
    return build_red_agent(
        AgentIdentity(
            agent_id=element.element_id,
            side=AgentSide.RED,
            role=element.role,
        ),
        force_element=element,
    )