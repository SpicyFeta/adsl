# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Core simulation engine for ADSL Phase 1."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from adsl.agents.base import Agent
from adsl.agents.blue_logistics import build_blue_agent
from adsl.agents.red_interdiction import build_red_agent
from adsl.models import (
    Action,
    ActionType,
    ADSL_AuditTrace,
    ADSL_ForceElement,
    ADSL_LogisticsNode,
    ADSL_LogisticsRoute,
    ADSL_Scenario,
    ADSL_ScenarioPackage,
    ADSL_SimulationRun,
    AgentIdentity,
    AgentSide,
    NodeStatus,
    Observation,
    RouteStatus,
    SimulationEvent,
    SimulationEventType,
    SimulationStatus,
)
from adsl.simulation.deconfliction import (
    SUPPRESSION_REASON,
    TickTargetRegistry,
)
from adsl.simulation.hardening import apply_attack_route, apply_harden
from adsl.performance.config import DEFAULT_MAX_TICKS, SCALE_MAX_TICKS
from adsl.performance.network_index import NetworkIndex  # noqa: F401 — re-export path
from adsl.simulation.observation_cache import SideObservationCache, build_side_observation_cache
from adsl.simulation.orchestration import (
    build_force_element_context,
    snapshot_nodes,
    snapshot_routes,
    sort_force_elements,
)
from adsl.utils.logging import configure_logging, get_logger


class SimulationEngine:
    """
    Tick-based simulation engine (ADR-004).

    Orchestrates Red-then-Blue agent turns per tick, builds observations,
    records events and audit traces, and emits structured logs.
    """

    def __init__(
        self,
        *,
        max_ticks: int = DEFAULT_MAX_TICKS,
        seed: int = 0,
        quiet_logs: bool = False,
        scale_mode: bool = False,
    ) -> None:
        if max_ticks < 1:
            raise ValueError("max_ticks must be at least 1.")
        tick_cap = SCALE_MAX_TICKS if scale_mode else DEFAULT_MAX_TICKS
        if max_ticks > tick_cap:
            raise ValueError(
                f"ADSL supports at most {tick_cap} ticks"
                f"{' in scale mode' if scale_mode else ''}; got {max_ticks}."
            )

        configure_logging(quiet=quiet_logs)
        self._log = get_logger("adsl.simulation.engine")
        self._emit_logs = not quiet_logs
        self._max_ticks = max_ticks
        self._seed = seed
        self._scale_mode = scale_mode

        self._nodes: list[ADSL_LogisticsNode] = []
        self._routes: list[ADSL_LogisticsRoute] = []
        self._network_index = NetworkIndex([], [])
        self._red_agents: list[tuple[Agent, ADSL_ForceElement]] = []
        self._blue_agents: list[tuple[Agent, ADSL_ForceElement]] = []
        self._run: ADSL_SimulationRun | None = None
        self._events: list[SimulationEvent] = []
        self._audit_traces: list[ADSL_AuditTrace] = []
        self._tick_targets = TickTargetRegistry()

    @property
    def run(self) -> ADSL_SimulationRun | None:
        return self._run

    @property
    def events(self) -> list[SimulationEvent]:
        return list(self._events)

    @property
    def audit_traces(self) -> list[ADSL_AuditTrace]:
        return list(self._audit_traces)

    @property
    def nodes(self) -> list[ADSL_LogisticsNode]:
        return snapshot_nodes(self._nodes)

    @property
    def routes(self) -> list[ADSL_LogisticsRoute]:
        return snapshot_routes(self._routes)

    def run_scenario(self, scenario: ADSL_ScenarioPackage | ADSL_Scenario) -> ADSL_SimulationRun:
        """Execute a scenario package (or bare scenario with no force elements)."""
        package = self._coerce_scenario_package(scenario)
        self._initialize_run(package.scenario)
        self._initialize_state(package)
        self._initialize_agents(package)

        assert self._run is not None
        if self._emit_logs:
            self._log.info(
                "simulation_run_started",
                run_id=self._run.run_id,
                scenario_id=package.scenario.scenario_id,
                max_ticks=self._max_ticks,
                red_agents=len(self._red_agents),
                blue_agents=len(self._blue_agents),
            )
        self._record_event(
            SimulationEventType.RUN_STARTED,
            tick=0,
            payload={
                "scenario_id": package.scenario.scenario_id,
                "max_ticks": self._max_ticks,
                "seed": self._seed,
            },
        )

        for tick in range(self._max_ticks):
            self._run.current_tick = tick
            self._execute_tick(tick)

        self._complete_run()
        return self._run

    def _coerce_scenario_package(
        self, scenario: ADSL_ScenarioPackage | ADSL_Scenario
    ) -> ADSL_ScenarioPackage:
        if isinstance(scenario, ADSL_ScenarioPackage):
            return scenario
        return ADSL_ScenarioPackage(scenario=scenario)

    def _initialize_run(self, scenario: ADSL_Scenario) -> None:
        self._run = ADSL_SimulationRun(
            scenario_id=scenario.scenario_id,
            seed=self._seed,
            status=SimulationStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            metadata={"scenario_name": scenario.name},
        )
        self._events = []
        self._audit_traces = []

    def _initialize_state(self, package: ADSL_ScenarioPackage) -> None:
        self._nodes = deepcopy(package.scenario.nodes)
        self._routes = deepcopy(package.scenario.routes)
        self._network_index = NetworkIndex(self._nodes, self._routes)

    def _initialize_agents(self, package: ADSL_ScenarioPackage) -> None:
        self._red_agents = [
            (self._agent_from_force_element(element), element)
            for element in sort_force_elements(package.red_force_elements)
        ]
        self._blue_agents = [
            (self._agent_from_force_element(element), element)
            for element in sort_force_elements(package.blue_force_elements)
        ]

    def _agent_from_force_element(self, element: ADSL_ForceElement) -> Agent:
        identity = AgentIdentity(
            agent_id=element.element_id,
            side=element.side,
            role=element.role,
        )
        if element.side == AgentSide.RED:
            return build_red_agent(identity, force_element=element)
        return build_blue_agent(identity, force_element=element)

    def _execute_tick(self, tick: int) -> None:
        assert self._run is not None

        self._tick_targets.clear()
        if self._emit_logs:
            self._log.info("tick_started", run_id=self._run.run_id, tick=tick)
        self._record_event(SimulationEventType.TICK_START, tick=tick)

        red_cache: SideObservationCache | None = None
        red_cache_dirty = True
        for agent, element in self._red_agents:
            if red_cache_dirty or red_cache is None:
                red_cache = build_side_observation_cache(
                    AgentSide.RED, self._nodes, self._routes
                )
                red_cache_dirty = False
            state_changed = self._execute_agent_turn(
                agent, element, tick, observation_cache=red_cache
            )
            if state_changed:
                red_cache_dirty = True

        blue_cache: SideObservationCache | None = None
        blue_cache_dirty = True
        for agent, element in self._blue_agents:
            if blue_cache_dirty or blue_cache is None:
                blue_cache = build_side_observation_cache(
                    AgentSide.BLUE, self._nodes, self._routes
                )
                blue_cache_dirty = False
            state_changed = self._execute_agent_turn(
                agent, element, tick, observation_cache=blue_cache
            )
            if state_changed:
                blue_cache_dirty = True

        if self._emit_logs:
            self._log.info("tick_completed", run_id=self._run.run_id, tick=tick)
        self._record_event(SimulationEventType.TICK_END, tick=tick)

    def _execute_agent_turn(
        self,
        agent: Agent,
        element: ADSL_ForceElement,
        tick: int,
        *,
        observation_cache: SideObservationCache,
    ) -> bool:
        """Execute one agent turn. Returns True when network state may have changed."""
        assert self._run is not None

        observation = self._build_observation(
            agent, element, tick, observation_cache=observation_cache
        )
        decision = agent.run_turn(observation)
        action = decision.action

        self._record_audit_trace(decision.audit_trace)
        self._record_event(
            SimulationEventType.AGENT_DECISION,
            tick=tick,
            agent_id=agent.identity.agent_id,
            agent_side=agent.identity.side,
            payload={
                "trace_id": decision.audit_trace.trace_id,
                "decision_category": decision.audit_trace.decision_category.value,
                "action_type": action.action_type.value,
                "action_summary": decision.audit_trace.action_summary,
            },
        )

        state_changed = self._apply_action(
            action, tick, agent.identity.agent_id, agent_side=agent.identity.side
        )
        if self._emit_logs:
            self._log.info(
                "agent_decision_recorded",
                run_id=self._run.run_id,
                tick=tick,
                agent_id=agent.identity.agent_id,
                agent_side=agent.identity.side.value,
                trace_id=decision.audit_trace.trace_id,
                action_type=action.action_type.value,
            )
        return state_changed

    def _build_observation(
        self,
        agent: Agent,
        element: ADSL_ForceElement,
        tick: int,
        *,
        observation_cache: SideObservationCache,
    ) -> Observation:
        assert self._run is not None

        side = agent.identity.side
        context = {
            "seed": self._seed,
            "scenario_id": self._run.scenario_id,
            **build_force_element_context(element),
            "nodes_by_id": observation_cache.nodes_by_id,
            "routes_by_id": observation_cache.routes_by_id,
            "routes_by_source": observation_cache.routes_by_source,
            "routes_by_target": observation_cache.routes_by_target,
        }

        return Observation(
            run_id=self._run.run_id,
            simulation_tick=tick,
            agent_id=agent.identity.agent_id,
            agent_side=side,
            visible_nodes=observation_cache.visible_nodes,
            visible_routes=observation_cache.visible_routes,
            context=context,
        )

    def _apply_action(
        self,
        action: Action,
        tick: int,
        agent_id: str,
        *,
        agent_side: AgentSide | None = None,
    ) -> bool:
        """Apply action to simulation state per ADR-004/ADR-008 semantics.

        Returns True when live node/route state may have changed (invalidates
        per-tick observation caches for subsequent agents on the same side).
        """
        assert self._run is not None

        suppressed, target_key, claimed_by = self._tick_targets.should_suppress(
            action, agent_id
        )
        if suppressed:
            self._record_event(
                SimulationEventType.ACTION_SUPPRESSED,
                tick=tick,
                agent_id=agent_id,
                agent_side=agent_side,
                payload={
                    "suppressed_agent_id": agent_id,
                    "action_type": action.action_type.value,
                    "target_id": action.target_id,
                    "target_key": target_key,
                    "claimed_by_agent_id": claimed_by,
                    "reason": SUPPRESSION_REASON,
                },
            )
            self._record_event(
                SimulationEventType.ACTION_RECORDED,
                tick=tick,
                agent_id=agent_id,
                agent_side=agent_side,
                payload={
                    "action_type": action.action_type.value,
                    "target_id": action.target_id,
                    "parameters": action.parameters,
                    "applied": False,
                    "suppressed": True,
                    "target_key": target_key,
                    "claimed_by_agent_id": claimed_by,
                },
            )
            if self._emit_logs:
                self._log.info(
                    "action_suppressed",
                    run_id=self._run.run_id,
                    tick=tick,
                    agent_id=agent_id,
                    action_type=action.action_type.value,
                    target_id=action.target_id,
                    claimed_by_agent_id=claimed_by,
                )
            return False

        applied = False
        absorbed = False
        if action.action_type == ActionType.ATTACK_ROUTE and action.target_id:
            applied, absorbed = self._apply_attack_route(action.target_id)
        elif action.action_type == ActionType.ATTACK_NODE and action.target_id:
            applied = self._apply_attack_node(action.target_id)
        elif action.action_type == ActionType.HARDEN and action.target_id:
            applied = self._apply_harden(action.target_id)
        elif action.action_type == ActionType.REROUTE and action.target_id:
            applied = self._apply_reroute(action)
        elif action.action_type == ActionType.REALLOCATE and action.target_id:
            applied = self._apply_reallocate(action)

        self._record_event(
            SimulationEventType.ACTION_RECORDED,
            tick=tick,
            agent_id=agent_id,
            agent_side=agent_side,
            payload={
                "action_type": action.action_type.value,
                "target_id": action.target_id,
                "parameters": action.parameters,
                "applied": applied,
                "suppressed": False,
                "absorbed": absorbed,
            },
        )
        if self._emit_logs:
            self._log.info(
                "action_recorded",
                run_id=self._run.run_id,
                tick=tick,
                agent_id=agent_id,
                action_type=action.action_type.value,
                target_id=action.target_id,
                applied=applied,
                absorbed=absorbed,
            )
        return applied

    def _apply_attack_route(self, route_id: str) -> tuple[bool, bool]:
        route = self._network_index.get_route(route_id)
        if route is None:
            return False, False
        return apply_attack_route(route)

    def _apply_attack_node(self, node_id: str) -> bool:
        node = self._network_index.get_node(node_id)
        if node is None:
            return False
        if node.status == NodeStatus.OPERATIONAL:
            node.status = NodeStatus.DEGRADED
            return True
        if node.status == NodeStatus.DEGRADED:
            node.status = NodeStatus.DESTROYED
            return True
        return False

    def _apply_harden(self, route_id: str) -> bool:
        route = self._network_index.get_route(route_id)
        if route is None:
            return False
        return apply_harden(route)

    def _apply_reroute(self, action: Action) -> bool:
        from_route_id = action.parameters.get("from_route_id")
        to_route_id = action.target_id
        if not from_route_id or not to_route_id:
            return False

        from_route = self._network_index.get_route(from_route_id)
        to_route = self._network_index.get_route(to_route_id)
        if from_route is None or to_route is None:
            return False
        if to_route.status != RouteStatus.OPEN:
            return False

        from_route.metadata["bypassed"] = True
        to_route.metadata["reroute_from"] = from_route_id
        to_route.metadata["active_reroute"] = True
        return True

    def _apply_reallocate(self, action: Action) -> bool:
        from_node_id = action.parameters.get("from_node_id")
        to_node_id = action.target_id
        transfer = action.parameters.get("transfer_amount", 0.0)
        if not from_node_id or not to_node_id or transfer <= 0:
            return False

        from_node = self._network_index.get_node(from_node_id)
        to_node = self._network_index.get_node(to_node_id)
        if from_node is None or to_node is None:
            return False

        amount = min(
            float(transfer),
            from_node.current_load,
            to_node.capacity - to_node.current_load,
        )
        if amount <= 0:
            return False

        from_node.current_load -= amount
        to_node.current_load += amount
        from_node.metadata["reallocated_out"] = (
            from_node.metadata.get("reallocated_out", 0.0) + amount
        )
        to_node.metadata["reallocated_in"] = (
            to_node.metadata.get("reallocated_in", 0.0) + amount
        )
        return True

    def _record_audit_trace(self, trace: ADSL_AuditTrace) -> None:
        assert self._run is not None

        self._audit_traces.append(trace)
        self._run.audit_trace_ids.append(trace.trace_id)
        if self._emit_logs:
            self._log.info(
                "audit_trace_recorded",
                run_id=self._run.run_id,
                trace_id=trace.trace_id,
                agent_id=trace.agent_id,
                agent_side=trace.agent_side.value,
                simulation_tick=trace.simulation_tick,
                decision_category=trace.decision_category.value,
            )

    def _record_event(
        self,
        event_type: SimulationEventType,
        *,
        tick: int,
        agent_id: str | None = None,
        agent_side: AgentSide | None = None,
        payload: dict | None = None,
    ) -> None:
        assert self._run is not None

        event = SimulationEvent(
            run_id=self._run.run_id,
            simulation_tick=tick,
            event_type=event_type,
            agent_id=agent_id,
            agent_side=agent_side,
            payload=payload or {},
        )
        self._events.append(event)

    def _complete_run(self) -> None:
        assert self._run is not None

        self._run.status = SimulationStatus.COMPLETED
        self._run.completed_at = datetime.now(timezone.utc)
        self._record_event(
            SimulationEventType.RUN_COMPLETED,
            tick=self._run.current_tick,
            payload={
                "total_events": len(self._events),
                "total_audit_traces": len(self._audit_traces),
            },
        )
        if self._emit_logs:
            self._log.info(
                "simulation_run_completed",
                run_id=self._run.run_id,
                ticks_executed=self._max_ticks,
                audit_traces=len(self._audit_traces),
                events=len(self._events),
            )