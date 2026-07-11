# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for the base Agent class and AuditTrace validation."""

import pytest

from adsl.agents.base import Agent
from adsl.models import (
    Action,
    ADSL_AuditTrace,
    ADSL_ReasoningStep,
    AgentIdentity,
    AgentSide,
    DecisionCategory,
    DecisionResult,
    Observation,
    ActionType,
)


class StubAgent(Agent):
    def perceive(self, observation: Observation) -> None:
        self._observation = observation

    def decide(self, observation: Observation) -> DecisionResult:
        trace = ADSL_AuditTrace(
            run_id=observation.run_id,
            agent_id=self.identity.agent_id,
            agent_side=self.identity.side,
            simulation_tick=observation.simulation_tick,
            decision_category=DecisionCategory.NO_ACTION,
            inputs_considered={"tick": observation.simulation_tick},
            reasoning_steps=[
                ADSL_ReasoningStep(
                    step_index=0,
                    description="No action required.",
                )
            ],
            action_type=ActionType.NO_ACTION,
            action_summary="Hold position",
        )
        return DecisionResult(
            action=Action(action_type=ActionType.NO_ACTION),
            audit_trace=trace,
        )


def test_run_turn_executes_perceive_decide_act() -> None:
    agent = StubAgent(
        AgentIdentity(agent_id="agent-1", side=AgentSide.BLUE, role="logistics")
    )
    observation = Observation(
        run_id="run-1",
        simulation_tick=3,
        agent_id="agent-1",
        agent_side=AgentSide.BLUE,
    )
    decision = agent.run_turn(observation)
    assert decision.audit_trace.action_summary == "Hold position"
    assert agent.last_decision is not None


def test_act_rejects_empty_inputs_considered() -> None:
    agent = StubAgent(
        AgentIdentity(agent_id="agent-1", side=AgentSide.RED, role="strike")
    )
    trace = ADSL_AuditTrace(
        run_id="run-1",
        agent_id="agent-1",
        agent_side=AgentSide.RED,
        simulation_tick=1,
        decision_category=DecisionCategory.TARGET_SELECTION,
        inputs_considered={},
        reasoning_steps=[
            ADSL_ReasoningStep(step_index=0, description="Test step.")
        ],
        action_type=ActionType.NO_ACTION,
        action_summary="No action",
    )
    decision = DecisionResult(
        action=Action(action_type=ActionType.NO_ACTION),
        audit_trace=trace,
    )
    with pytest.raises(ValueError, match="inputs_considered"):
        agent.act(decision)