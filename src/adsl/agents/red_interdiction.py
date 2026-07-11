# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Red interdiction agent — rule-based target selection with ADR-010 pacing."""

from __future__ import annotations

from adsl.agents.base import Agent
from adsl.agents.red_pacing import RedPacingState
from adsl.explainability.trace import AuditTraceBuilder
from adsl.models import (
    Action,
    ActionType,
    ADSL_ForceElement,
    ADSL_LogisticsNode,
    ADSL_LogisticsRoute,
    AgentIdentity,
    AgentSide,
    DecisionCategory,
    DecisionResult,
    NodeStatus,
    NodeType,
    Observation,
    RouteStatus,
)

RISK_WEIGHTS: dict[str, float] = {
    "critical": 4.0,
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}

STRATEGIC_VALUE_WEIGHTS: dict[str, float] = {
    "critical": 4.0,
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}

NODE_TYPE_WEIGHTS: dict[NodeType, float] = {
    NodeType.FORWARD_OPERATING_BASE: 3.0,
    NodeType.PORT: 2.5,
    NodeType.DEPOT: 2.0,
    NodeType.HUB: 1.5,
}

ROLE_STRIKE = "STRIKE"
ROLE_FIRE_SUPPORT = "FIRE_SUPPORT"
ROLE_RECONNAISSANCE = "RECONNAISSANCE"


class RedInterdictionAgent(Agent):
    """
    Red agent using deterministic utility scoring with ADR-010 strike pacing.

    - STRIKE: attack highest-value route on patrol list
    - FIRE_SUPPORT: attack highest-value node (hubs/depots/ports)
    - RECONNAISSANCE: NO_ACTION with surveillance reasoning trace
    """

    def __init__(
        self,
        identity: AgentIdentity,
        *,
        force_element: ADSL_ForceElement | None = None,
    ) -> None:
        super().__init__(identity)
        self._force_element = force_element
        self._patrol_route_ids: set[str] = set()
        self._readiness: float = 1.0
        self._priority_target: str | None = None
        self._capability: str | None = None
        self._engaged_targets: set[str] = set()
        self._pacing = RedPacingState()

        if force_element is not None:
            self._patrol_route_ids = set(force_element.patrol_route_ids)
            self._readiness = force_element.readiness
            self._priority_target = force_element.metadata.get("priority_target")
            self._capability = force_element.metadata.get("capability")
            self._pacing = RedPacingState.from_metadata(force_element.metadata)

    def perceive(self, observation: Observation) -> None:
        context = observation.context
        patrol_ids = context.get("patrol_route_ids")
        if patrol_ids is not None:
            self._patrol_route_ids = set(patrol_ids)
        readiness = context.get("readiness")
        if readiness is not None:
            self._readiness = float(readiness)
        self._priority_target = context.get("priority_target", self._priority_target)
        self._capability = context.get("capability", self._capability)
        cooldown = context.get("strike_cooldown_ticks")
        if cooldown is not None:
            self._pacing.strike_cooldown_ticks = int(cooldown)

    def decide(self, observation: Observation) -> DecisionResult:
        role = self.identity.role
        node_index = observation.context.get("nodes_by_id") or {
            node.node_id: node for node in observation.visible_nodes
        }

        if role == ROLE_RECONNAISSANCE:
            return self._decide_reconnaissance(observation)

        if role == ROLE_FIRE_SUPPORT:
            return self._decide_node_attack(observation, node_index)

        return self._decide_route_attack(observation, node_index)

    def reset(self) -> None:
        super().reset()
        self._engaged_targets.clear()
        self._pacing.reset()

    def _decide_reconnaissance(self, observation: Observation) -> DecisionResult:
        monitored = self._top_routes_for_surveillance(observation.visible_routes, limit=3)
        route_ids = [entry["route_id"] for entry in monitored]

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
                    "role": self.identity.role,
                    "capability": self._capability,
                    "patrol_route_ids": sorted(self._patrol_route_ids),
                    "monitored_routes": route_ids,
                    "visible_route_count": len(observation.visible_routes),
                }
            )
            .add_reasoning_step(
                "Reconnaissance posture: monitor high-throughput routes for convoy timing.",
                evidence={"monitored_routes": monitored},
            )
            .add_reasoning_step(
                "No strike authorized — intelligence collection only in Phase 1 recon mode.",
            )
            .with_action(
                ActionType.NO_ACTION,
                action_summary="Continue surveillance — no strike",
            )
            .build()
        )
        return DecisionResult(
            action=Action(action_type=ActionType.NO_ACTION),
            audit_trace=trace,
        )

    def _decide_route_attack(
        self,
        observation: Observation,
        node_index: dict[str, ADSL_LogisticsNode],
    ) -> DecisionResult:
        tick = observation.simulation_tick

        if not self._pacing.has_strike_budget():
            return self._pacing_hold_result(
                observation,
                pacing_hold_reason="strike_budget_exhausted",
                strike_budget_remaining=0,
                summary="Hold — strike budget exhausted",
            )

        if self._pacing.is_route_cooldown_active(tick):
            return self._pacing_hold_result(
                observation,
                pacing_hold_reason="route_cooldown_active",
                cooldown_remaining=self._pacing.route_cooldown_remaining(tick),
                summary="Hold — strike cooldown active",
            )

        candidates = self._score_routes(
            observation.visible_routes, node_index, tick=tick
        )
        selected = self._select_best(candidates)

        if selected is None:
            return self._no_action_result(
                observation,
                decision_category=DecisionCategory.NO_ACTION,
                summary="Hold — no attackable routes on patrol",
                inputs={
                    "role": self.identity.role,
                    "patrol_route_ids": sorted(self._patrol_route_ids),
                    "candidate_count": 0,
                },
                reasoning=[
                    "Evaluated patrol routes for interdiction suitability.",
                    "No attackable routes remain on patrol; holding fire.",
                ],
            )

        route = selected["route"]
        utility = selected["utility"]
        self._engaged_targets.add(route.route_id)
        self._pacing.record_route_attack(tick, route.route_id)

        budget_remaining = self._pacing.strike_budget_remaining
        trace = (
            AuditTraceBuilder(
                run_id=observation.run_id,
                agent_id=self.identity.agent_id,
                agent_side=AgentSide.RED,
                simulation_tick=observation.simulation_tick,
                decision_category=DecisionCategory.TARGET_SELECTION,
            )
            .with_inputs(
                {
                    "role": self.identity.role,
                    "patrol_route_ids": sorted(self._patrol_route_ids),
                    "priority_target": self._priority_target,
                    "readiness": self._readiness,
                    "candidate_count": len(candidates),
                    "strike_budget_remaining": budget_remaining,
                    "top_candidates": [
                        {
                            "route_id": entry["route"].route_id,
                            "utility": round(entry["utility"], 3),
                        }
                        for entry in candidates[:3]
                    ],
                }
            )
            .add_reasoning_step(
                "ADR-010: route strike pacing clear; cooldown and budget gates passed.",
                evidence={
                    "cooldown_remaining": 0,
                    "strike_budget_remaining": budget_remaining,
                },
            )
            .add_reasoning_step(
                "Screened patrol routes for interdiction value using risk, status, and FOB connectivity.",
                evidence={"evaluated_routes": len(candidates)},
            )
            .add_reasoning_step(
                f"Selected route {route.route_id} ({route.name}) with utility {utility:.2f}.",
                evidence={
                    "route_id": route.route_id,
                    "utility": utility,
                    "risk_level": route.metadata.get("risk_level"),
                    "status": route.status.value,
                    "harden_level": route.metadata.get("harden_level", 0),
                },
            )
            .add_reasoning_step(
                (
                    "ADR-008: target route has active hardening; attack may be absorbed."
                    if int(route.metadata.get("harden_level", 0)) > 0
                    else "ADR-008: no active hardening on target route."
                ),
                evidence={"harden_level": route.metadata.get("harden_level", 0)},
            )
            .with_action(
                ActionType.ATTACK_ROUTE,
                target_id=route.route_id,
                action_summary=f"Attack route {route.route_id} ({route.name})",
            )
            .build()
        )
        return DecisionResult(
            action=Action(
                action_type=ActionType.ATTACK_ROUTE,
                target_id=route.route_id,
                parameters={
                    "utility_score": utility,
                    "modality": self._capability or "interdiction",
                },
            ),
            audit_trace=trace,
        )

    def _decide_node_attack(
        self,
        observation: Observation,
        node_index: dict[str, ADSL_LogisticsNode],
    ) -> DecisionResult:
        tick = observation.simulation_tick

        if not self._pacing.has_strike_budget():
            return self._pacing_hold_result(
                observation,
                pacing_hold_reason="strike_budget_exhausted",
                strike_budget_remaining=0,
                summary="Hold — strike budget exhausted",
            )

        if self._pacing.is_node_cooldown_active(tick):
            return self._pacing_hold_result(
                observation,
                pacing_hold_reason="node_cooldown_active",
                cooldown_remaining=self._pacing.node_cooldown_remaining(tick),
                summary="Hold — strike cooldown active",
            )

        patrol_node_ids = self._patrol_endpoint_nodes(observation.visible_routes)
        candidates = self._score_nodes(
            observation.visible_nodes,
            patrol_node_ids=patrol_node_ids,
            tick=tick,
        )
        selected = self._select_best(candidates)

        if selected is None:
            return self._no_action_result(
                observation,
                decision_category=DecisionCategory.NO_ACTION,
                summary="Hold — no attackable nodes in battlespace",
                inputs={
                    "role": self.identity.role,
                    "patrol_route_ids": sorted(self._patrol_route_ids),
                    "candidate_count": 0,
                },
                reasoning=[
                    "Evaluated logistics nodes for fire support targeting.",
                    "No attackable nodes remain; holding fire.",
                ],
            )

        node = selected["node"]
        utility = selected["utility"]
        self._engaged_targets.add(node.node_id)
        self._pacing.record_node_attack(tick, node.node_id)

        budget_remaining = self._pacing.strike_budget_remaining
        trace = (
            AuditTraceBuilder(
                run_id=observation.run_id,
                agent_id=self.identity.agent_id,
                agent_side=AgentSide.RED,
                simulation_tick=observation.simulation_tick,
                decision_category=DecisionCategory.TARGET_SELECTION,
            )
            .with_inputs(
                {
                    "role": self.identity.role,
                    "priority_target": self._priority_target,
                    "readiness": self._readiness,
                    "patrol_route_ids": sorted(self._patrol_route_ids),
                    "candidate_count": len(candidates),
                    "strike_budget_remaining": budget_remaining,
                    "top_candidates": [
                        {
                            "node_id": entry["node"].node_id,
                            "utility": round(entry["utility"], 3),
                        }
                        for entry in candidates[:3]
                    ],
                }
            )
            .add_reasoning_step(
                "ADR-010: node strike pacing clear; cooldown and budget gates passed.",
                evidence={
                    "cooldown_remaining": 0,
                    "strike_budget_remaining": budget_remaining,
                },
            )
            .add_reasoning_step(
                "Screened nodes by strategic value, type, load, and patrol route affiliation.",
                evidence={"evaluated_nodes": len(candidates)},
            )
            .add_reasoning_step(
                f"Selected node {node.node_id} ({node.name}) with utility {utility:.2f}.",
                evidence={
                    "node_id": node.node_id,
                    "utility": utility,
                    "strategic_value": node.metadata.get("strategic_value"),
                    "status": node.status.value,
                },
            )
            .with_action(
                ActionType.ATTACK_NODE,
                target_id=node.node_id,
                action_summary=f"Attack node {node.node_id} ({node.name})",
            )
            .build()
        )
        return DecisionResult(
            action=Action(
                action_type=ActionType.ATTACK_NODE,
                target_id=node.node_id,
                parameters={
                    "utility_score": utility,
                    "modality": self._capability or "area_denial",
                },
            ),
            audit_trace=trace,
        )

    def _score_routes(
        self,
        routes: list[ADSL_LogisticsRoute],
        node_index: dict[str, ADSL_LogisticsNode],
        *,
        tick: int,
    ) -> list[dict]:
        scored: list[dict] = []
        for route in routes:
            if route.status == RouteStatus.CLOSED:
                continue
            if self._patrol_route_ids and route.route_id not in self._patrol_route_ids:
                continue
            if self._pacing.is_target_in_rotation_window(route.route_id, tick):
                continue

            risk = route.metadata.get("risk_level", "medium")
            utility = RISK_WEIGHTS.get(str(risk), 2.0)

            if route.status == RouteStatus.OPEN:
                utility += 1.0

            target_node = node_index.get(route.target_node_id)
            if target_node and target_node.node_type == NodeType.FORWARD_OPERATING_BASE:
                utility += 2.0

            if self._priority_target == "fob_supply_routes" and target_node:
                if target_node.node_type == NodeType.FORWARD_OPERATING_BASE:
                    utility += 1.5

            if route.route_id in self._engaged_targets:
                utility -= 0.5

            utility *= self._readiness
            scored.append({"route": route, "utility": utility})

        scored.sort(key=lambda entry: (-entry["utility"], entry["route"].route_id))
        return scored

    def _score_nodes(
        self,
        nodes: list[ADSL_LogisticsNode],
        *,
        patrol_node_ids: set[str],
        tick: int,
    ) -> list[dict]:
        scored: list[dict] = []

        for node in nodes:
            if node.status == NodeStatus.DESTROYED:
                continue
            if node.node_type not in {
                NodeType.HUB,
                NodeType.DEPOT,
                NodeType.PORT,
            }:
                continue
            if self._pacing.is_target_in_rotation_window(node.node_id, tick):
                continue

            strategic = node.metadata.get("strategic_value", "medium")
            utility = STRATEGIC_VALUE_WEIGHTS.get(str(strategic), 2.0)
            utility += NODE_TYPE_WEIGHTS.get(node.node_type, 1.0)

            if node.capacity > 0:
                load_ratio = node.current_load / node.capacity
                utility += min(load_ratio, 1.0)

            if node.node_id in patrol_node_ids:
                utility += 1.5

            if self._priority_target == "hub_nodes" and node.node_type == NodeType.HUB:
                utility += 2.0

            if node.node_id in self._engaged_targets:
                utility -= 0.5

            utility *= self._readiness
            scored.append({"node": node, "utility": utility})

        scored.sort(key=lambda entry: (-entry["utility"], entry["node"].node_id))
        return scored

    def _patrol_endpoint_nodes(self, routes: list[ADSL_LogisticsRoute]) -> set[str]:
        endpoints: set[str] = set()
        for route in routes:
            if route.route_id in self._patrol_route_ids:
                endpoints.add(route.source_node_id)
                endpoints.add(route.target_node_id)
        return endpoints

    def _top_routes_for_surveillance(
        self, routes: list[ADSL_LogisticsRoute], *, limit: int
    ) -> list[dict]:
        patrol_routes = [
            route for route in routes if route.route_id in self._patrol_route_ids
        ]
        ranked = sorted(
            patrol_routes,
            key=lambda route: (-route.capacity, route.route_id),
        )
        return [
            {
                "route_id": route.route_id,
                "capacity": route.capacity,
                "status": route.status.value,
            }
            for route in ranked[:limit]
        ]

    def _select_best(self, candidates: list[dict]) -> dict | None:
        if not candidates:
            return None
        best_utility = candidates[0]["utility"]
        if best_utility <= 0:
            return None
        return candidates[0]

    def _pacing_hold_result(
        self,
        observation: Observation,
        *,
        pacing_hold_reason: str,
        summary: str,
        cooldown_remaining: int | None = None,
        strike_budget_remaining: int | None = None,
    ) -> DecisionResult:
        evidence: dict = {"pacing_hold_reason": pacing_hold_reason}
        if cooldown_remaining is not None:
            evidence["cooldown_remaining"] = cooldown_remaining
        if strike_budget_remaining is not None:
            evidence["strike_budget_remaining"] = strike_budget_remaining

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
                    "role": self.identity.role,
                    "patrol_route_ids": sorted(self._patrol_route_ids),
                    "strike_cooldown_ticks": self._pacing.strike_cooldown_ticks,
                    **evidence,
                }
            )
            .add_reasoning_step(
                "ADR-010: strike pacing gate active; holding fire per Red variety policy.",
                evidence=evidence,
            )
            .with_action(ActionType.NO_ACTION, action_summary=summary)
            .build()
        )
        return DecisionResult(
            action=Action(action_type=ActionType.NO_ACTION),
            audit_trace=trace,
        )

    def _no_action_result(
        self,
        observation: Observation,
        *,
        decision_category: DecisionCategory,
        summary: str,
        inputs: dict,
        reasoning: list[str],
    ) -> DecisionResult:
        builder = AuditTraceBuilder(
            run_id=observation.run_id,
            agent_id=self.identity.agent_id,
            agent_side=AgentSide.RED,
            simulation_tick=observation.simulation_tick,
            decision_category=decision_category,
        ).with_inputs(inputs)
        for line in reasoning:
            builder.add_reasoning_step(line)
        trace = builder.with_action(ActionType.NO_ACTION, action_summary=summary).build()
        return DecisionResult(
            action=Action(action_type=ActionType.NO_ACTION),
            audit_trace=trace,
        )


def build_red_agent(
    identity: AgentIdentity, *, force_element: ADSL_ForceElement | None = None
) -> RedInterdictionAgent:
    """Factory for Red interdiction agents."""
    return RedInterdictionAgent(identity, force_element=force_element)