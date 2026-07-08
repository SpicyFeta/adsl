"""Tests for Red interdiction agent."""

from pathlib import Path

from adsl.agents.red_interdiction import RedInterdictionAgent, build_red_agent
from adsl.models import (
    ActionType,
    AgentIdentity,
    AgentSide,
    DecisionCategory,
    Observation,
)
from adsl.simulation.engine import SimulationEngine
from adsl.simulation.loader import load_scenario_package

DATASET_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "synthetic" / "logistics_scenario_v1.json"
)


def _strike_agent() -> RedInterdictionAgent:
    package = load_scenario_package(DATASET_PATH)
    element = next(
        item for item in package.red_force_elements if item.role == "STRIKE"
    )
    identity = AgentIdentity(
        agent_id=element.element_id,
        side=AgentSide.RED,
        role=element.role,
    )
    return build_red_agent(identity, force_element=element)


def test_strike_agent_selects_patrol_route_with_audit_trace() -> None:
    agent = _strike_agent()
    package = load_scenario_package(DATASET_PATH)

    observation = Observation(
        run_id="run-test",
        simulation_tick=0,
        agent_id=agent.identity.agent_id,
        agent_side=AgentSide.RED,
        visible_nodes=package.scenario.nodes,
        visible_routes=package.scenario.routes,
        context={
            "patrol_route_ids": ["R-007", "R-009", "R-010"],
            "readiness": 0.87,
            "priority_target": "fob_supply_routes",
            "role": "STRIKE",
        },
    )

    decision = agent.run_turn(observation)
    assert decision.action.action_type == ActionType.ATTACK_ROUTE
    assert decision.action.target_id in {"R-007", "R-009"}
    assert decision.audit_trace.decision_category == DecisionCategory.TARGET_SELECTION
    assert len(decision.audit_trace.reasoning_steps) >= 2
    assert decision.audit_trace.inputs_considered["candidate_count"] > 0


def test_fire_support_agent_selects_hub_node() -> None:
    package = load_scenario_package(DATASET_PATH)
    element = next(
        item for item in package.red_force_elements if item.role == "FIRE_SUPPORT"
    )
    agent = build_red_agent(
        AgentIdentity(
            agent_id=element.element_id,
            side=AgentSide.RED,
            role=element.role,
        ),
        force_element=element,
    )

    observation = Observation(
        run_id="run-test",
        simulation_tick=0,
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

    decision = agent.run_turn(observation)
    assert decision.action.action_type == ActionType.ATTACK_NODE
    assert decision.action.target_id is not None
    assert decision.action.target_id.startswith("N-HUB")


def test_reconnaissance_agent_emits_no_action_trace() -> None:
    package = load_scenario_package(DATASET_PATH)
    element = next(
        item for item in package.red_force_elements if item.role == "RECONNAISSANCE"
    )
    agent = build_red_agent(
        AgentIdentity(
            agent_id=element.element_id,
            side=AgentSide.RED,
            role=element.role,
        ),
        force_element=element,
    )

    observation = Observation(
        run_id="run-test",
        simulation_tick=0,
        agent_id=agent.identity.agent_id,
        agent_side=AgentSide.RED,
        visible_nodes=package.scenario.nodes,
        visible_routes=package.scenario.routes,
        context={
            "patrol_route_ids": element.patrol_route_ids,
            "readiness": element.readiness,
            "capability": element.metadata.get("capability"),
            "role": element.role,
        },
    )

    first = agent.run_turn(observation)
    second = agent.run_turn(observation)
    assert first.action.action_type == ActionType.NO_ACTION
    assert second.action.action_type == ActionType.NO_ACTION
    assert (
        first.audit_trace.action_summary
        == second.audit_trace.action_summary
    )


def test_red_agent_integrates_with_simulation_engine() -> None:
    package = load_scenario_package(DATASET_PATH)
    engine = SimulationEngine(max_ticks=2, seed=7)
    run = engine.run_scenario(package)

    red_traces = [
        trace for trace in engine.audit_traces if trace.agent_side == AgentSide.RED
    ]
    attack_traces = [
        trace
        for trace in red_traces
        if trace.action_type in {ActionType.ATTACK_ROUTE, ActionType.ATTACK_NODE}
    ]

    assert run.status.value == "COMPLETED"
    assert len(red_traces) == 2 * len(package.red_force_elements)
    assert attack_traces
    assert any(
        event.payload.get("applied") is True
        for event in engine.events
        if event.event_type.value == "ACTION_RECORDED"
        and event.agent_id
        and event.agent_id.startswith("RED-")
    )