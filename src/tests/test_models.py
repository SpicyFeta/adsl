"""Tests for canonical ADSL data models."""

import pytest
from pydantic import ValidationError

from adsl.models import (
    ADSL_AuditTrace,
    ADSL_LogisticsNode,
    ADSL_LogisticsRoute,
    ADSL_ReasoningStep,
    ADSL_Scenario,
    ActionType,
    AgentSide,
    DecisionCategory,
    NodeType,
)


def _sample_node(node_id: str = "node-a") -> ADSL_LogisticsNode:
    return ADSL_LogisticsNode(
        node_id=node_id,
        name="Depot Alpha",
        node_type=NodeType.DEPOT,
        latitude=34.0,
        longitude=-118.0,
        capacity=100.0,
    )


def test_scenario_validates_route_node_references() -> None:
    node = _sample_node()
    route = ADSL_LogisticsRoute(
        route_id="route-1",
        name="Alpha to Missing",
        source_node_id=node.node_id,
        target_node_id="missing",
        capacity=50.0,
        transit_time_hours=4.0,
    )
    with pytest.raises(ValidationError):
        ADSL_Scenario(
            scenario_id="scenario-1",
            name="Test",
            description="Test scenario",
            nodes=[node],
            routes=[route],
        )


def test_audit_trace_requires_reasoning_steps() -> None:
    with pytest.raises(ValidationError):
        ADSL_AuditTrace(
            run_id="run-1",
            agent_id="agent-red-1",
            agent_side=AgentSide.RED,
            simulation_tick=1,
            decision_category=DecisionCategory.TARGET_SELECTION,
            inputs_considered={"visible_nodes": 2},
            reasoning_steps=[],
            action_type=ActionType.ATTACK_NODE,
            target_id="node-a",
            action_summary="Attack node-a",
        )


def test_audit_trace_accepts_valid_payload() -> None:
    trace = ADSL_AuditTrace(
        run_id="run-1",
        agent_id="agent-red-1",
        agent_side=AgentSide.RED,
        simulation_tick=1,
        decision_category=DecisionCategory.TARGET_SELECTION,
        inputs_considered={"visible_nodes": 2},
        reasoning_steps=[
            ADSL_ReasoningStep(
                step_index=0,
                description="Selected highest-value depot.",
                evidence={"node_id": "node-a"},
            )
        ],
        action_type=ActionType.ATTACK_NODE,
        target_id="node-a",
        action_summary="Attack node-a",
    )
    assert trace.schema_version == "1.0"
    assert trace.agent_side == AgentSide.RED