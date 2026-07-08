"""Placeholder Red and Blue agents for simulation engine development."""

from __future__ import annotations

from adsl.agents.base import Agent
from adsl.explainability.trace import AuditTraceBuilder
from adsl.models import (
    Action,
    ActionType,
    AgentIdentity,
    AgentSide,
    DecisionCategory,
    DecisionResult,
    Observation,
)


class PlaceholderRedAgent(Agent):
    """Placeholder Red agent — emits NO_ACTION with a valid audit trace."""

    def perceive(self, observation: Observation) -> None:
        self._last_observation = observation

    def decide(self, observation: Observation) -> DecisionResult:
        contested_routes = [
            route.route_id
            for route in observation.visible_routes
            if route.status.value == "CONTESTED"
        ]
        trace = (
            AuditTraceBuilder(
                run_id=observation.run_id,
                agent_id=self.identity.agent_id,
                agent_side=AgentSide.RED,
                simulation_tick=observation.simulation_tick,
                decision_category=DecisionCategory.NO_ACTION,
            )
            .with_inputs(
                {
                    "visible_nodes": len(observation.visible_nodes),
                    "visible_routes": len(observation.visible_routes),
                    "contested_routes": contested_routes,
                    "role": self.identity.role,
                }
            )
            .add_reasoning_step(
                "Placeholder Red agent: surveying contested routes for future targeting.",
                evidence={"contested_route_count": len(contested_routes)},
            )
            .add_reasoning_step(
                "No strike authorized in placeholder mode; holding for simulation skeleton.",
            )
            .with_action(
                ActionType.NO_ACTION,
                action_summary="Hold — placeholder Red agent (no strike)",
            )
            .build()
        )
        return DecisionResult(
            action=Action(action_type=ActionType.NO_ACTION),
            audit_trace=trace,
        )


class PlaceholderBlueAgent(Agent):
    """Placeholder Blue agent — emits NO_ACTION with a valid audit trace."""

    def perceive(self, observation: Observation) -> None:
        self._last_observation = observation

    def decide(self, observation: Observation) -> DecisionResult:
        closed_routes = [
            route.route_id
            for route in observation.visible_routes
            if route.status.value == "CLOSED"
        ]
        trace = (
            AuditTraceBuilder(
                run_id=observation.run_id,
                agent_id=self.identity.agent_id,
                agent_side=AgentSide.BLUE,
                simulation_tick=observation.simulation_tick,
                decision_category=DecisionCategory.NO_ACTION,
            )
            .with_inputs(
                {
                    "visible_nodes": len(observation.visible_nodes),
                    "visible_routes": len(observation.visible_routes),
                    "closed_routes": closed_routes,
                    "role": self.identity.role,
                }
            )
            .add_reasoning_step(
                "Placeholder Blue agent: assessing route closures and depot loads.",
                evidence={"closed_route_count": len(closed_routes)},
            )
            .add_reasoning_step(
                "No adaptation executed in placeholder mode; awaiting full agent logic.",
            )
            .with_action(
                ActionType.NO_ACTION,
                action_summary="Hold — placeholder Blue agent (no adaptation)",
            )
            .build()
        )
        return DecisionResult(
            action=Action(action_type=ActionType.NO_ACTION),
            audit_trace=trace,
        )


def build_placeholder_agent(identity: AgentIdentity) -> Agent:
    """Factory for placeholder agents based on force element side."""
    if identity.side == AgentSide.RED:
        return PlaceholderRedAgent(identity)
    return PlaceholderBlueAgent(identity)