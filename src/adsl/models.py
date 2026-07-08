"""Canonical Pydantic data models for ADSL Phase 1."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


AUDIT_TRACE_SCHEMA_VERSION = "1.0"


class AgentSide(str, Enum):
    RED = "RED"
    BLUE = "BLUE"


class NodeType(str, Enum):
    DEPOT = "DEPOT"
    HUB = "HUB"
    PORT = "PORT"
    FORWARD_OPERATING_BASE = "FORWARD_OPERATING_BASE"


class NodeStatus(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    DEGRADED = "DEGRADED"
    DESTROYED = "DESTROYED"


class RouteStatus(str, Enum):
    OPEN = "OPEN"
    CONTESTED = "CONTESTED"
    CLOSED = "CLOSED"


class SimulationStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DecisionCategory(str, Enum):
    TARGET_SELECTION = "TARGET_SELECTION"
    ROUTE_ADAPTATION = "ROUTE_ADAPTATION"
    RESOURCE_REALLOCATION = "RESOURCE_REALLOCATION"
    HARDENING = "HARDENING"
    NO_ACTION = "NO_ACTION"


class ActionType(str, Enum):
    ATTACK_NODE = "ATTACK_NODE"
    ATTACK_ROUTE = "ATTACK_ROUTE"
    REROUTE = "REROUTE"
    REALLOCATE = "REALLOCATE"
    HARDEN = "HARDEN"
    NO_ACTION = "NO_ACTION"


class ADSL_LogisticsNode(BaseModel):
    """A node in the contested logistics network."""

    node_id: str
    name: str
    node_type: NodeType
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    capacity: float = Field(ge=0.0, description="Throughput or storage capacity units.")
    current_load: float = Field(default=0.0, ge=0.0)
    status: NodeStatus = NodeStatus.OPERATIONAL
    metadata: dict[str, Any] = Field(default_factory=dict)


class ADSL_LogisticsRoute(BaseModel):
    """A directed route connecting two logistics nodes."""

    route_id: str
    name: str
    source_node_id: str
    target_node_id: str
    capacity: float = Field(ge=0.0)
    transit_time_hours: float = Field(gt=0.0)
    status: RouteStatus = RouteStatus.OPEN
    metadata: dict[str, Any] = Field(default_factory=dict)


class ADSL_Scenario(BaseModel):
    """Scenario definition for a contested logistics stress test."""

    scenario_id: str
    name: str
    description: str
    nodes: list[ADSL_LogisticsNode]
    routes: list[ADSL_LogisticsRoute]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_network_references(self) -> ADSL_Scenario:
        node_ids = {node.node_id for node in self.nodes}
        for route in self.routes:
            if route.source_node_id not in node_ids:
                raise ValueError(
                    f"Route {route.route_id} references unknown source node "
                    f"{route.source_node_id}"
                )
            if route.target_node_id not in node_ids:
                raise ValueError(
                    f"Route {route.route_id} references unknown target node "
                    f"{route.target_node_id}"
                )
        return self


class ADSL_ForceElement(BaseModel):
    """A force element assigned to Red or Blue operations in a scenario."""

    element_id: str
    name: str
    side: AgentSide
    role: str
    home_node_id: str | None = None
    patrol_route_ids: list[str] = Field(default_factory=list)
    readiness: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ADSL_ScenarioPackage(BaseModel):
    """Complete scenario dataset including force elements."""

    scenario: ADSL_Scenario
    blue_force_elements: list[ADSL_ForceElement] = Field(default_factory=list)
    red_force_elements: list[ADSL_ForceElement] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_force_element_sides(self) -> ADSL_ScenarioPackage:
        for element in self.blue_force_elements:
            if element.side != AgentSide.BLUE:
                raise ValueError(
                    f"Blue force element {element.element_id} has side {element.side}"
                )
        for element in self.red_force_elements:
            if element.side != AgentSide.RED:
                raise ValueError(
                    f"Red force element {element.element_id} has side {element.side}"
                )
        return self


class SimulationEventType(str, Enum):
    TICK_START = "TICK_START"
    AGENT_DECISION = "AGENT_DECISION"
    ACTION_RECORDED = "ACTION_RECORDED"
    TICK_END = "TICK_END"
    RUN_STARTED = "RUN_STARTED"
    RUN_COMPLETED = "RUN_COMPLETED"


class SimulationEvent(BaseModel):
    """Recorded simulation event for audit and replay."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    simulation_tick: int = Field(ge=0)
    event_type: SimulationEventType
    agent_id: str | None = None
    agent_side: AgentSide | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ADSL_ReasoningStep(BaseModel):
    """A single step in an agent's reasoning chain."""

    step_index: int = Field(ge=0)
    description: str = Field(min_length=1)
    evidence: dict[str, Any] = Field(default_factory=dict)


class ADSL_AuditTrace(BaseModel):
    """Structured reasoning trace for a single agent decision."""

    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: str = AUDIT_TRACE_SCHEMA_VERSION
    run_id: str
    agent_id: str
    agent_side: AgentSide
    simulation_tick: int = Field(ge=0)
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decision_category: DecisionCategory
    inputs_considered: dict[str, Any] = Field(default_factory=dict)
    reasoning_steps: list[ADSL_ReasoningStep]
    action_type: ActionType
    target_id: str | None = None
    action_summary: str = Field(min_length=1)

    @field_validator("reasoning_steps")
    @classmethod
    def require_reasoning_steps(
        cls, steps: list[ADSL_ReasoningStep]
    ) -> list[ADSL_ReasoningStep]:
        if not steps:
            raise ValueError("AuditTrace must contain at least one reasoning step.")
        return steps


class ADSL_SimulationRun(BaseModel):
    """Metadata for a single simulation execution."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    scenario_id: str
    status: SimulationStatus = SimulationStatus.PENDING
    seed: int = 0
    current_tick: int = Field(default=0, ge=0)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    audit_trace_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentIdentity(BaseModel):
    """Stable identity for a simulation agent."""

    agent_id: str
    side: AgentSide
    role: str


class Observation(BaseModel):
    """Read-only view of simulation state visible to an agent."""

    run_id: str
    simulation_tick: int = Field(ge=0)
    agent_id: str
    agent_side: AgentSide
    visible_nodes: list[ADSL_LogisticsNode] = Field(default_factory=list)
    visible_routes: list[ADSL_LogisticsRoute] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class Action(BaseModel):
    """Validated intent produced by an agent decision."""

    action_type: ActionType
    target_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class DecisionResult(BaseModel):
    """Agent decision output: action plus mandatory audit trace."""

    action: Action
    audit_trace: ADSL_AuditTrace