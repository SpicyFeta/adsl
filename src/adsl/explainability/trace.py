# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""AuditTrace generation helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from adsl.models import (
    ADSL_AuditTrace,
    ADSL_ReasoningStep,
    ActionType,
    AgentSide,
    DecisionCategory,
)


class AuditTraceBuilder:
    """Fluent builder for constructing validated ADSL_AuditTrace instances."""

    def __init__(
        self,
        *,
        run_id: str,
        agent_id: str,
        agent_side: AgentSide,
        simulation_tick: int,
        decision_category: DecisionCategory,
    ) -> None:
        self._run_id = run_id
        self._agent_id = agent_id
        self._agent_side = agent_side
        self._simulation_tick = simulation_tick
        self._decision_category = decision_category
        self._inputs_considered: dict = {}
        self._reasoning_steps: list[ADSL_ReasoningStep] = []
        self._action_type: ActionType | None = None
        self._target_id: str | None = None
        self._action_summary: str | None = None
        self._recorded_at: datetime | None = None

    def with_inputs(self, inputs: dict) -> AuditTraceBuilder:
        self._inputs_considered = inputs
        return self

    def add_reasoning_step(
        self, description: str, *, evidence: dict | None = None
    ) -> AuditTraceBuilder:
        step = ADSL_ReasoningStep(
            step_index=len(self._reasoning_steps),
            description=description,
            evidence=evidence or {},
        )
        self._reasoning_steps.append(step)
        return self

    def with_action(
        self,
        action_type: ActionType,
        *,
        target_id: str | None = None,
        action_summary: str,
    ) -> AuditTraceBuilder:
        self._action_type = action_type
        self._target_id = target_id
        self._action_summary = action_summary
        return self

    def recorded_at(self, timestamp: datetime) -> AuditTraceBuilder:
        self._recorded_at = timestamp
        return self

    def build(self) -> ADSL_AuditTrace:
        if self._action_type is None or self._action_summary is None:
            raise ValueError("AuditTraceBuilder requires action_type and action_summary.")

        return ADSL_AuditTrace(
            run_id=self._run_id,
            agent_id=self._agent_id,
            agent_side=self._agent_side,
            simulation_tick=self._simulation_tick,
            recorded_at=self._recorded_at or datetime.now(timezone.utc),
            decision_category=self._decision_category,
            inputs_considered=self._inputs_considered,
            reasoning_steps=self._reasoning_steps,
            action_type=self._action_type,
            target_id=self._target_id,
            action_summary=self._action_summary,
        )