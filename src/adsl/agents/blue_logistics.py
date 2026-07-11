# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Blue logistics adaptation agent — policy-driven response to Red damage."""

from __future__ import annotations

from adsl.agents.base import Agent
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

ROLE_ROUTE_SECURITY = "ROUTE_SECURITY"
ROLE_LOGISTICS_MANAGER = "LOGISTICS_MANAGER"
ROLE_ROUTE_COORDINATOR = "ROUTE_COORDINATOR"
ROLE_DEPOT_OPERATOR = "DEPOT_OPERATOR"
ROLE_DISTRIBUTION_CONTROLLER = "DISTRIBUTION_CONTROLLER"
ROLE_MEDICAL_LOGISTICS = "MEDICAL_LOGISTICS"

REROUTE_ROLES = {
    ROLE_LOGISTICS_MANAGER,
    ROLE_ROUTE_COORDINATOR,
    ROLE_MEDICAL_LOGISTICS,
}

REALLOCATE_ROLES = {
    ROLE_DEPOT_OPERATOR,
    ROLE_DISTRIBUTION_CONTROLLER,
}

LOAD_STRESS_THRESHOLD = 0.85
FOB_STRESS_THRESHOLD = 0.80
REALLOCATE_TRANSFER_RATIO = 0.15
MIN_SPARE_CAPACITY_RATIO = 0.15


class BlueLogisticsAgent(Agent):
    """
    Phase 1 Blue agent implementing ADR-005 adaptation policy (P1–P6).

    Actions: REROUTE, REALLOCATE, HARDEN, NO_ACTION.
    """

    def __init__(
        self,
        identity: AgentIdentity,
        *,
        force_element: ADSL_ForceElement | None = None,
    ) -> None:
        super().__init__(identity)
        self._patrol_route_ids: set[str] = set()
        self._home_node_id: str | None = None
        self._readiness: float = 1.0
        self._priority_mission: str | None = None

        if force_element is not None:
            self._patrol_route_ids = set(force_element.patrol_route_ids)
            self._home_node_id = force_element.home_node_id
            self._readiness = force_element.readiness
            self._priority_mission = force_element.metadata.get("priority_mission")

    def perceive(self, observation: Observation) -> None:
        context = observation.context
        patrol_ids = context.get("patrol_route_ids")
        if patrol_ids is not None:
            self._patrol_route_ids = set(patrol_ids)
        home_node_id = context.get("home_node_id")
        if home_node_id is not None:
            self._home_node_id = home_node_id
        readiness = context.get("readiness")
        if readiness is not None:
            self._readiness = float(readiness)
        self._priority_mission = context.get("priority_mission", self._priority_mission)

    def decide(self, observation: Observation) -> DecisionResult:
        routes_by_id = observation.context.get("routes_by_id") or {
            route.route_id: route for route in observation.visible_routes
        }
        nodes_by_id = observation.context.get("nodes_by_id") or {
            node.node_id: node for node in observation.visible_nodes
        }
        patrol_routes = [
            routes_by_id[route_id]
            for route_id in sorted(self._patrol_route_ids)
            if route_id in routes_by_id
        ]
        patrol_statuses = {route.route_id: route.status.value for route in patrol_routes}

        inputs_base = {
            "role": self.identity.role,
            "readiness": self._readiness,
            "priority_mission": self._priority_mission,
            "patrol_route_ids": sorted(self._patrol_route_ids),
            "patrol_route_statuses": patrol_statuses,
            "home_node_id": self._home_node_id,
            "home_node_status": (
                nodes_by_id[self._home_node_id].status.value
                if self._home_node_id and self._home_node_id in nodes_by_id
                else None
            ),
        }

        route_indexes = (
            observation.context.get("routes_by_source"),
            observation.context.get("routes_by_target"),
        )

        p1 = self._evaluate_p1_reroute_closed(
            patrol_routes, observation.visible_routes, route_indexes=route_indexes
        )
        if p1 is not None:
            return self._build_reroute_result(observation, inputs_base, p1, policy_rule="P1")

        p2 = self._evaluate_p2_harden(patrol_routes)
        if p2 is not None:
            return self._build_harden_result(observation, inputs_base, p2, policy_rule="P2")

        p3 = self._evaluate_p3_reroute_contested(
            patrol_routes, observation.visible_routes, route_indexes=route_indexes
        )
        if p3 is not None:
            return self._build_reroute_result(observation, inputs_base, p3, policy_rule="P3")

        p4 = self._evaluate_p4_reallocate_home(nodes_by_id)
        if p4 is not None:
            return self._build_reallocate_result(observation, inputs_base, p4, policy_rule="P4")

        p5 = self._evaluate_p5_reallocate_fob(
            patrol_routes, nodes_by_id, observation.visible_routes
        )
        if p5 is not None:
            return self._build_reallocate_result(observation, inputs_base, p5, policy_rule="P5")

        return self._build_no_action_result(
            observation,
            inputs_base,
            policy_rule="P6",
            reasoning=[
                "Assessed patrol routes and home node against ADR-005 priorities P1–P5.",
                "No qualifying threat on patrol scope; accepting current operational risk.",
            ],
        )

    def _evaluate_p1_reroute_closed(
        self,
        patrol_routes: list[ADSL_LogisticsRoute],
        all_routes: list[ADSL_LogisticsRoute],
        *,
        route_indexes: tuple[
            dict[str, list[ADSL_LogisticsRoute]] | None,
            dict[str, list[ADSL_LogisticsRoute]] | None,
        ] = (None, None),
    ) -> dict | None:
        routes_by_source, routes_by_target = route_indexes
        for route in patrol_routes:
            if route.status != RouteStatus.CLOSED:
                continue
            alternate = self._find_alternate_route(
                route,
                all_routes,
                routes_by_source=routes_by_source,
                routes_by_target=routes_by_target,
            )
            if alternate is not None:
                return {"from_route": route, "to_route": alternate}
        return None

    def _evaluate_p2_harden(
        self, patrol_routes: list[ADSL_LogisticsRoute]
    ) -> dict | None:
        if self.identity.role != ROLE_ROUTE_SECURITY:
            return None
        for route in patrol_routes:
            if route.status == RouteStatus.CONTESTED:
                return {"route": route}
        return None

    def _evaluate_p3_reroute_contested(
        self,
        patrol_routes: list[ADSL_LogisticsRoute],
        all_routes: list[ADSL_LogisticsRoute],
        *,
        route_indexes: tuple[
            dict[str, list[ADSL_LogisticsRoute]] | None,
            dict[str, list[ADSL_LogisticsRoute]] | None,
        ] = (None, None),
    ) -> dict | None:
        if self.identity.role not in REROUTE_ROLES:
            return None
        routes_by_source, routes_by_target = route_indexes
        for route in patrol_routes:
            if route.status != RouteStatus.CONTESTED:
                continue
            alternate = self._find_alternate_route(
                route,
                all_routes,
                routes_by_source=routes_by_source,
                routes_by_target=routes_by_target,
            )
            if alternate is not None:
                return {"from_route": route, "to_route": alternate}
        return None

    def _evaluate_p4_reallocate_home(
        self, nodes_by_id: dict[str, ADSL_LogisticsNode]
    ) -> dict | None:
        if not self._home_node_id or self._home_node_id not in nodes_by_id:
            return None

        source = nodes_by_id[self._home_node_id]
        if not self._node_needs_reallocation(source):
            return None

        target = self._find_reallocation_target(nodes_by_id, exclude_id=source.node_id)
        if target is None:
            return None

        return {"from_node": source, "to_node": target}

    def _evaluate_p5_reallocate_fob(
        self,
        patrol_routes: list[ADSL_LogisticsRoute],
        nodes_by_id: dict[str, ADSL_LogisticsNode],
        all_routes: list[ADSL_LogisticsRoute],
    ) -> dict | None:
        if self.identity.role not in REALLOCATE_ROLES:
            return None

        fob_nodes = self._patrol_fob_endpoints(patrol_routes, nodes_by_id, all_routes)
        if not any(
            self._node_fob_stressed(nodes_by_id[node_id])
            for node_id in sorted(fob_nodes)
            if node_id in nodes_by_id
        ):
            return None

        source = self._find_stressed_supply_node(nodes_by_id, patrol_routes, all_routes)
        if source is None:
            return None

        target = self._find_reallocation_target(nodes_by_id, exclude_id=source.node_id)
        if target is None:
            return None

        return {"from_node": source, "to_node": target}

    def _find_alternate_route(
        self,
        disrupted: ADSL_LogisticsRoute,
        all_routes: list[ADSL_LogisticsRoute],
        *,
        routes_by_source: dict[str, list[ADSL_LogisticsRoute]] | None = None,
        routes_by_target: dict[str, list[ADSL_LogisticsRoute]] | None = None,
    ) -> ADSL_LogisticsRoute | None:
        if routes_by_source is not None and routes_by_target is not None:
            seen: set[str] = set()
            alternates: list[ADSL_LogisticsRoute] = []
            for candidate in (
                routes_by_source.get(disrupted.source_node_id, [])
                + routes_by_target.get(disrupted.target_node_id, [])
            ):
                if candidate.route_id == disrupted.route_id or candidate.route_id in seen:
                    continue
                if candidate.status != RouteStatus.OPEN:
                    continue
                seen.add(candidate.route_id)
                alternates.append(candidate)
            alternates.sort(key=lambda route: route.route_id)
            return alternates[0] if alternates else None

        alternates = [
            route
            for route in all_routes
            if route.route_id != disrupted.route_id
            and route.status == RouteStatus.OPEN
            and (
                route.source_node_id == disrupted.source_node_id
                or route.target_node_id == disrupted.target_node_id
            )
        ]
        alternates.sort(key=lambda route: route.route_id)
        return alternates[0] if alternates else None

    def _find_reallocation_target(
        self,
        nodes_by_id: dict[str, ADSL_LogisticsNode],
        *,
        exclude_id: str,
    ) -> ADSL_LogisticsNode | None:
        candidates = []
        for node in nodes_by_id.values():
            if node.node_id == exclude_id:
                continue
            if node.status == NodeStatus.DESTROYED:
                continue
            if node.capacity <= 0:
                continue
            spare_ratio = (node.capacity - node.current_load) / node.capacity
            if spare_ratio >= MIN_SPARE_CAPACITY_RATIO:
                candidates.append((node, spare_ratio))

        candidates.sort(key=lambda item: (-item[1], item[0].node_id))
        return candidates[0][0] if candidates else None

    def _find_stressed_supply_node(
        self,
        nodes_by_id: dict[str, ADSL_LogisticsNode],
        patrol_routes: list[ADSL_LogisticsRoute],
        all_routes: list[ADSL_LogisticsRoute],
    ) -> ADSL_LogisticsNode | None:
        if self._home_node_id and self._home_node_id in nodes_by_id:
            home = nodes_by_id[self._home_node_id]
            if self._node_needs_reallocation(home):
                return home

        endpoint_ids = self._patrol_endpoint_ids(patrol_routes, all_routes)
        for node_id in sorted(endpoint_ids):
            node = nodes_by_id.get(node_id)
            if node and node.node_type in {NodeType.DEPOT, NodeType.HUB}:
                if self._node_needs_reallocation(node):
                    return node
        return None

    def _patrol_endpoint_ids(
        self,
        patrol_routes: list[ADSL_LogisticsRoute],
        all_routes: list[ADSL_LogisticsRoute],
    ) -> set[str]:
        routes_by_id = {route.route_id: route for route in all_routes}
        endpoints: set[str] = set()
        for route in patrol_routes:
            ref = routes_by_id.get(route.route_id, route)
            endpoints.add(ref.source_node_id)
            endpoints.add(ref.target_node_id)
        return endpoints

    def _patrol_fob_endpoints(
        self,
        patrol_routes: list[ADSL_LogisticsRoute],
        nodes_by_id: dict[str, ADSL_LogisticsNode],
        all_routes: list[ADSL_LogisticsRoute],
    ) -> set[str]:
        fob_ids: set[str] = set()
        for node_id in self._patrol_endpoint_ids(patrol_routes, all_routes):
            node = nodes_by_id.get(node_id)
            if node and node.node_type == NodeType.FORWARD_OPERATING_BASE:
                fob_ids.add(node_id)
        return fob_ids

    @staticmethod
    def _node_needs_reallocation(node: ADSL_LogisticsNode) -> bool:
        if node.status == NodeStatus.DEGRADED:
            return True
        if node.capacity <= 0:
            return False
        return (node.current_load / node.capacity) >= LOAD_STRESS_THRESHOLD

    @staticmethod
    def _node_fob_stressed(node: ADSL_LogisticsNode) -> bool:
        if node.capacity <= 0:
            return False
        return (node.current_load / node.capacity) >= FOB_STRESS_THRESHOLD

    def _build_reroute_result(
        self,
        observation: Observation,
        inputs_base: dict,
        selection: dict,
        *,
        policy_rule: str,
    ) -> DecisionResult:
        from_route: ADSL_LogisticsRoute = selection["from_route"]
        to_route: ADSL_LogisticsRoute = selection["to_route"]
        inputs = {
            **inputs_base,
            "policy_rule": policy_rule,
            "from_route_id": from_route.route_id,
            "to_route_id": to_route.route_id,
        }
        trace = (
            AuditTraceBuilder(
                run_id=observation.run_id,
                agent_id=self.identity.agent_id,
                agent_side=AgentSide.BLUE,
                simulation_tick=observation.simulation_tick,
                decision_category=DecisionCategory.ROUTE_ADAPTATION,
            )
            .with_inputs(inputs)
            .add_reasoning_step(
                f"{policy_rule}: patrol route {from_route.route_id} is {from_route.status.value}; "
                "seeking alternate open path per ADR-005.",
            )
            .add_reasoning_step(
                f"Rerouting flow from {from_route.route_id} to alternate {to_route.route_id}.",
                evidence={
                    "from_status": from_route.status.value,
                    "to_status": to_route.status.value,
                },
            )
            .with_action(
                ActionType.REROUTE,
                target_id=to_route.route_id,
                action_summary=(
                    f"Reroute from {from_route.route_id} to {to_route.route_id}"
                ),
            )
            .build()
        )
        return DecisionResult(
            action=Action(
                action_type=ActionType.REROUTE,
                target_id=to_route.route_id,
                parameters={
                    "from_route_id": from_route.route_id,
                    "to_route_id": to_route.route_id,
                    "policy_rule": policy_rule,
                },
            ),
            audit_trace=trace,
        )

    def _build_harden_result(
        self,
        observation: Observation,
        inputs_base: dict,
        selection: dict,
        *,
        policy_rule: str,
    ) -> DecisionResult:
        route: ADSL_LogisticsRoute = selection["route"]
        inputs = {
            **inputs_base,
            "policy_rule": policy_rule,
            "target_route_id": route.route_id,
        }
        trace = (
            AuditTraceBuilder(
                run_id=observation.run_id,
                agent_id=self.identity.agent_id,
                agent_side=AgentSide.BLUE,
                simulation_tick=observation.simulation_tick,
                decision_category=DecisionCategory.HARDENING,
            )
            .with_inputs(inputs)
            .add_reasoning_step(
                f"{policy_rule}: security element hardening contested patrol route {route.route_id}.",
            )
            .add_reasoning_step(
                "ADR-008: applying harden_level=1; first subsequent route attack will be absorbed.",
                evidence={"route_status": route.status.value, "policy": "ADR-008"},
            )
            .with_action(
                ActionType.HARDEN,
                target_id=route.route_id,
                action_summary=f"Harden contested route {route.route_id}",
            )
            .build()
        )
        return DecisionResult(
            action=Action(
                action_type=ActionType.HARDEN,
                target_id=route.route_id,
                parameters={"policy_rule": policy_rule},
            ),
            audit_trace=trace,
        )

    def _build_reallocate_result(
        self,
        observation: Observation,
        inputs_base: dict,
        selection: dict,
        *,
        policy_rule: str,
    ) -> DecisionResult:
        from_node: ADSL_LogisticsNode = selection["from_node"]
        to_node: ADSL_LogisticsNode = selection["to_node"]
        transfer = min(
            from_node.current_load,
            from_node.capacity * REALLOCATE_TRANSFER_RATIO,
            to_node.capacity - to_node.current_load,
        )
        inputs = {
            **inputs_base,
            "policy_rule": policy_rule,
            "from_node_id": from_node.node_id,
            "to_node_id": to_node.node_id,
            "transfer_amount": round(transfer, 2),
        }
        trace = (
            AuditTraceBuilder(
                run_id=observation.run_id,
                agent_id=self.identity.agent_id,
                agent_side=AgentSide.BLUE,
                simulation_tick=observation.simulation_tick,
                decision_category=DecisionCategory.RESOURCE_REALLOCATION,
            )
            .with_inputs(inputs)
            .add_reasoning_step(
                f"{policy_rule}: supply node {from_node.node_id} stressed "
                f"(status={from_node.status.value}, load={from_node.current_load:.1f}).",
            )
            .add_reasoning_step(
                f"Reallocating {transfer:.1f} units to {to_node.node_id} "
                f"(spare capacity available).",
                evidence={
                    "from_load_ratio": round(from_node.current_load / from_node.capacity, 3)
                    if from_node.capacity
                    else 0,
                    "to_load_ratio": round(to_node.current_load / to_node.capacity, 3)
                    if to_node.capacity
                    else 0,
                },
            )
            .with_action(
                ActionType.REALLOCATE,
                target_id=to_node.node_id,
                action_summary=(
                    f"Reallocate {transfer:.1f} units from {from_node.node_id} "
                    f"to {to_node.node_id}"
                ),
            )
            .build()
        )
        return DecisionResult(
            action=Action(
                action_type=ActionType.REALLOCATE,
                target_id=to_node.node_id,
                parameters={
                    "from_node_id": from_node.node_id,
                    "to_node_id": to_node.node_id,
                    "transfer_amount": transfer,
                    "policy_rule": policy_rule,
                },
            ),
            audit_trace=trace,
        )

    def _build_no_action_result(
        self,
        observation: Observation,
        inputs_base: dict,
        *,
        policy_rule: str,
        reasoning: list[str],
    ) -> DecisionResult:
        inputs = {**inputs_base, "policy_rule": policy_rule}
        builder = AuditTraceBuilder(
            run_id=observation.run_id,
            agent_id=self.identity.agent_id,
            agent_side=AgentSide.BLUE,
            simulation_tick=observation.simulation_tick,
            decision_category=DecisionCategory.NO_ACTION,
        ).with_inputs(inputs)
        for line in reasoning:
            builder.add_reasoning_step(line)
        trace = builder.with_action(
            ActionType.NO_ACTION,
            action_summary="Accept risk — network stable on patrol scope",
        ).build()
        return DecisionResult(
            action=Action(action_type=ActionType.NO_ACTION),
            audit_trace=trace,
        )


def build_blue_agent(
    identity: AgentIdentity, *, force_element: ADSL_ForceElement | None = None
) -> BlueLogisticsAgent:
    """Factory for Blue logistics adaptation agents."""
    return BlueLogisticsAgent(identity, force_element=force_element)