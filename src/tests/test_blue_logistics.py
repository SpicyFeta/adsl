# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for Blue logistics adaptation agent."""

from copy import deepcopy
from pathlib import Path

from adsl.agents.blue_logistics import BlueLogisticsAgent, build_blue_agent
from adsl.models import (
    ActionType,
    AgentIdentity,
    AgentSide,
    DecisionCategory,
    Observation,
    RouteStatus,
)
from adsl.simulation.engine import SimulationEngine
from adsl.simulation.loader import load_scenario_package

DATASET_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "synthetic" / "logistics_scenario_v1.json"
)


def _blue_element(role: str):
    package = load_scenario_package(DATASET_PATH)
    return next(item for item in package.blue_force_elements if item.role == role)


def test_route_security_hardens_contested_patrol_route() -> None:
    element = _blue_element("ROUTE_SECURITY")
    agent = build_blue_agent(
        AgentIdentity(
            agent_id=element.element_id,
            side=AgentSide.BLUE,
            role=element.role,
        ),
        force_element=element,
    )
    package = load_scenario_package(DATASET_PATH)
    routes = deepcopy(package.scenario.routes)
    for route in routes:
        if route.route_id == "R-006":
            route.status = RouteStatus.OPEN
        if route.route_id == "R-007":
            route.status = RouteStatus.CONTESTED

    observation = Observation(
        run_id="run-test",
        simulation_tick=1,
        agent_id=element.element_id,
        agent_side=AgentSide.BLUE,
        visible_nodes=package.scenario.nodes,
        visible_routes=routes,
        context={
            "patrol_route_ids": element.patrol_route_ids,
            "home_node_id": element.home_node_id,
            "readiness": element.readiness,
            "role": element.role,
        },
    )

    decision = agent.run_turn(observation)
    assert decision.action.action_type == ActionType.HARDEN
    assert decision.action.target_id == "R-007"
    assert decision.audit_trace.decision_category == DecisionCategory.HARDENING
    assert decision.audit_trace.inputs_considered["policy_rule"] == "P2"


def test_depot_operator_reroutes_closed_patrol_route() -> None:
    element = _blue_element("DEPOT_OPERATOR")
    agent = build_blue_agent(
        AgentIdentity(
            agent_id=element.element_id,
            side=AgentSide.BLUE,
            role=element.role,
        ),
        force_element=element,
    )
    package = load_scenario_package(DATASET_PATH)
    routes = deepcopy(package.scenario.routes)
    for route in routes:
        if route.route_id == "R-009":
            route.status = RouteStatus.OPEN

    observation = Observation(
        run_id="run-test",
        simulation_tick=1,
        agent_id=element.element_id,
        agent_side=AgentSide.BLUE,
        visible_nodes=package.scenario.nodes,
        visible_routes=routes,
        context={
            "patrol_route_ids": element.patrol_route_ids,
            "home_node_id": element.home_node_id,
            "readiness": element.readiness,
            "role": element.role,
            "priority_mission": element.metadata.get("priority_mission"),
        },
    )

    decision = agent.run_turn(observation)
    assert decision.action.action_type == ActionType.REROUTE
    assert decision.action.parameters["from_route_id"] == "R-010"
    assert decision.action.target_id == "R-009"
    assert decision.audit_trace.inputs_considered["policy_rule"] == "P1"


def test_stable_network_produces_no_action_with_trace() -> None:
    element = _blue_element("MEDICAL_LOGISTICS")
    agent = build_blue_agent(
        AgentIdentity(
            agent_id=element.element_id,
            side=AgentSide.BLUE,
            role=element.role,
        ),
        force_element=element,
    )
    package = load_scenario_package(DATASET_PATH)

    observation = Observation(
        run_id="run-test",
        simulation_tick=0,
        agent_id=element.element_id,
        agent_side=AgentSide.BLUE,
        visible_nodes=package.scenario.nodes,
        visible_routes=package.scenario.routes,
        context={
            "patrol_route_ids": element.patrol_route_ids,
            "home_node_id": element.home_node_id,
            "readiness": element.readiness,
            "role": element.role,
        },
    )

    decision = agent.run_turn(observation)
    assert decision.action.action_type == ActionType.NO_ACTION
    assert decision.audit_trace.inputs_considered["policy_rule"] == "P6"


def test_blue_agent_integrates_with_engine_after_red_attacks() -> None:
    package = load_scenario_package(DATASET_PATH)
    engine = SimulationEngine(max_ticks=2, seed=11)
    run = engine.run_scenario(package)

    blue_traces = [
        trace for trace in engine.audit_traces if trace.agent_side == AgentSide.BLUE
    ]
    adaptation_actions = {
        ActionType.REROUTE,
        ActionType.REALLOCATE,
        ActionType.HARDEN,
    }
    blue_adaptations = [trace for trace in blue_traces if trace.action_type in adaptation_actions]

    assert run.status.value == "COMPLETED"
    assert len(blue_traces) == 2 * len(package.blue_force_elements)
    assert blue_adaptations
    assert any(
        event.payload.get("applied") is True
        for event in engine.events
        if event.agent_side == AgentSide.BLUE
        and event.event_type.value == "ACTION_RECORDED"
    )