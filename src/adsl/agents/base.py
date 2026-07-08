"""Base agent class and AuditTrace integration for ADSL Phase 1."""

from __future__ import annotations

from abc import ABC, abstractmethod

from adsl.models import (
    Action,
    ADSL_AuditTrace,
    AgentIdentity,
    DecisionResult,
    Observation,
)


class Agent(ABC):
    """
    Base class for all Phase 1 agents.

    Lifecycle: perceive → decide → act

    - perceive: ingest observation and update internal state (no simulation mutation)
    - decide: produce Action and mandatory ADSL_AuditTrace
    - act: validate trace and expose action to the simulation engine
    """

    def __init__(self, identity: AgentIdentity) -> None:
        self._identity = identity
        self._last_decision: DecisionResult | None = None

    @property
    def identity(self) -> AgentIdentity:
        return self._identity

    @abstractmethod
    def perceive(self, observation: Observation) -> None:
        """Ingest observation; update internal state if needed."""

    @abstractmethod
    def decide(self, observation: Observation) -> DecisionResult:
        """Produce a decision and mandatory audit trace."""

    def act(self, decision: DecisionResult) -> Action:
        """
        AuditTrace integration point.

        Validates the trace, stores the decision, and returns the action
        for the simulation engine to validate and apply.
        """
        self._validate_audit_trace(decision.audit_trace)
        self._last_decision = decision
        return decision.action

    def run_turn(self, observation: Observation) -> DecisionResult:
        """Execute the full perceive → decide → act lifecycle for one turn."""
        self.perceive(observation)
        decision = self.decide(observation)
        self.act(decision)
        return decision

    def reset(self) -> None:
        """Return agent to initial state for a new simulation run."""
        self._last_decision = None

    @property
    def last_decision(self) -> DecisionResult | None:
        return self._last_decision

    @staticmethod
    def _validate_audit_trace(trace: ADSL_AuditTrace) -> None:
        if not trace.reasoning_steps:
            raise ValueError(
                f"Agent decision trace {trace.trace_id} is missing reasoning steps."
            )
        if not trace.action_summary.strip():
            raise ValueError(
                f"Agent decision trace {trace.trace_id} is missing action_summary."
            )
        if not trace.inputs_considered:
            raise ValueError(
                f"Agent decision trace {trace.trace_id} is missing inputs_considered."
            )