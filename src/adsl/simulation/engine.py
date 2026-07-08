"""Core simulation engine for ADSL Phase 1."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from adsl.agents.base import Agent
from adsl.agents.placeholders import build_placeholder_agent
from adsl.models import (
    Action,
    ADSL_AuditTrace,
    ADSL_ForceElement,
    ADSL_LogisticsNode,
    ADSL_LogisticsRoute,
    ADSL_Scenario,
    ADSL_ScenarioPackage,
    ADSL_SimulationRun,
    AgentIdentity,
    AgentSide,
    Observation,
    SimulationEvent,
    SimulationEventType,
    SimulationStatus,
)
from adsl.utils.logging import configure_logging, get_logger

DEFAULT_MAX_TICKS = 100


class SimulationEngine:
    """
    Tick-based simulation engine.

    Orchestrates Red-then-Blue agent turns per tick, builds observations,
    records events and audit traces, and emits structured logs.
    """

    def __init__(self, *, max_ticks: int = DEFAULT_MAX_TICKS, seed: int = 0) -> None:
        if max_ticks < 1:
            raise ValueError("max_ticks must be at least 1.")
        if max_ticks > DEFAULT_MAX_TICKS:
            raise ValueError(
                f"Phase 1 supports at most {DEFAULT_MAX_TICKS} ticks; got {max_ticks}."
            )

        configure_logging()
        self._log = get_logger("adsl.simulation.engine")
        self._max_ticks = max_ticks
        self._seed = seed

        self._nodes: list[ADSL_LogisticsNode] = []
        self._routes: list[ADSL_LogisticsRoute] = []
        self._red_agents: list[Agent] = []
        self._blue_agents: list[Agent] = []
        self._run: ADSL_SimulationRun | None = None
        self._events: list[SimulationEvent] = []
        self._audit_traces: list[ADSL_AuditTrace] = []

    @property
    def run(self) -> ADSL_SimulationRun | None:
        return self._run

    @property
    def events(self) -> list[SimulationEvent]:
        return list(self._events)

    @property
    def audit_traces(self) -> list[ADSL_AuditTrace]:
        return list(self._audit_traces)

    def run_scenario(self, scenario: ADSL_ScenarioPackage | ADSL_Scenario) -> ADSL_SimulationRun:
        """Execute a scenario package (or bare scenario with no force elements)."""
        package = self._coerce_scenario_package(scenario)
        self._initialize_run(package.scenario)
        self._initialize_state(package)
        self._initialize_agents(package)

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

    def _initialize_agents(self, package: ADSL_ScenarioPackage) -> None:
        self._red_agents = [
            self._agent_from_force_element(element)
            for element in package.red_force_elements
        ]
        self._blue_agents = [
            self._agent_from_force_element(element)
            for element in package.blue_force_elements
        ]

    def _agent_from_force_element(self, element: ADSL_ForceElement) -> Agent:
        identity = AgentIdentity(
            agent_id=element.element_id,
            side=element.side,
            role=element.role,
        )
        return build_placeholder_agent(identity)

    def _execute_tick(self, tick: int) -> None:
        assert self._run is not None

        self._log.info("tick_started", run_id=self._run.run_id, tick=tick)
        self._record_event(SimulationEventType.TICK_START, tick=tick)

        for agent in self._red_agents:
            self._execute_agent_turn(agent, tick)

        for agent in self._blue_agents:
            self._execute_agent_turn(agent, tick)

        self._log.info("tick_completed", run_id=self._run.run_id, tick=tick)
        self._record_event(SimulationEventType.TICK_END, tick=tick)

    def _execute_agent_turn(self, agent: Agent, tick: int) -> None:
        assert self._run is not None

        observation = self._build_observation(agent, tick)
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

        self._apply_action(action, tick, agent.identity.agent_id)
        self._log.info(
            "agent_decision_recorded",
            run_id=self._run.run_id,
            tick=tick,
            agent_id=agent.identity.agent_id,
            agent_side=agent.identity.side.value,
            trace_id=decision.audit_trace.trace_id,
            action_type=action.action_type.value,
        )

    def _build_observation(self, agent: Agent, tick: int) -> Observation:
        assert self._run is not None

        visible_nodes = self._visible_nodes_for(agent.identity.side)
        visible_routes = self._visible_routes_for(agent.identity.side)

        return Observation(
            run_id=self._run.run_id,
            simulation_tick=tick,
            agent_id=agent.identity.agent_id,
            agent_side=agent.identity.side,
            visible_nodes=visible_nodes,
            visible_routes=visible_routes,
            context={
                "seed": self._seed,
                "scenario_id": self._run.scenario_id,
                "role": agent.identity.role,
            },
        )

    def _visible_nodes_for(self, side: AgentSide) -> list[ADSL_LogisticsNode]:
        if side == AgentSide.RED:
            return deepcopy(self._nodes)
        return deepcopy(
            [node for node in self._nodes if node.status.value != "DESTROYED"]
        )

    def _visible_routes_for(self, side: AgentSide) -> list[ADSL_LogisticsRoute]:
        if side == AgentSide.RED:
            return deepcopy(self._routes)
        return deepcopy(self._routes)

    def _apply_action(self, action: Action, tick: int, agent_id: str) -> None:
        """Record action application. Full state mutation deferred to later phases."""
        assert self._run is not None

        self._record_event(
            SimulationEventType.ACTION_RECORDED,
            tick=tick,
            agent_id=agent_id,
            payload={
                "action_type": action.action_type.value,
                "target_id": action.target_id,
                "parameters": action.parameters,
            },
        )
        self._log.info(
            "action_recorded",
            run_id=self._run.run_id,
            tick=tick,
            agent_id=agent_id,
            action_type=action.action_type.value,
            target_id=action.target_id,
        )

    def _record_audit_trace(self, trace: ADSL_AuditTrace) -> None:
        assert self._run is not None

        self._audit_traces.append(trace)
        self._run.audit_trace_ids.append(trace.trace_id)
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
        self._log.info(
            "simulation_run_completed",
            run_id=self._run.run_id,
            ticks_executed=self._max_ticks,
            audit_traces=len(self._audit_traces),
            events=len(self._events),
        )