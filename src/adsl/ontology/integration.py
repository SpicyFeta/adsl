# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Palantir Ontology integration layer for ADSL Phase 1 (ADR-006)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from adsl.ontology.sdk_client import get_sdk_client
from adsl.models import (
    ADSL_AuditTrace,
    ADSL_ForceElement,
    ADSL_LogisticsNode,
    ADSL_LogisticsRoute,
    ADSL_ScenarioPackage,
    ADSL_SimulationRun,
    AUDIT_TRACE_SCHEMA_VERSION,
    SimulationEvent,
)

SOURCE_SYSTEM = "ADSL_PHASE1"

ONTOLOGY_OBJECT_TYPES = {
    "logistics_node": "ADSL_LogisticsNode",
    "logistics_route": "ADSL_LogisticsRoute",
    "audit_trace": "ADSL_AuditTrace",
    "simulation_run": "ADSL_SimulationRun",
    "force_element": "ADSL_ForceElement",
    "simulation_event": "ADSL_SimulationEvent",
}


def _mapping_metadata() -> dict[str, str]:
    return {
        "source_system": SOURCE_SYSTEM,
        "mapped_at": datetime.now(timezone.utc).isoformat(),
    }


def map_logistics_node_to_ontology(node: ADSL_LogisticsNode) -> dict[str, Any]:
    """Map ADSL_LogisticsNode to an Ontology object payload."""
    return {
        "object_type": ONTOLOGY_OBJECT_TYPES["logistics_node"],
        "primary_key": node.node_id,
        "properties": {
            **_mapping_metadata(),
            "node_id": node.node_id,
            "name": node.name,
            "node_type": node.node_type.value,
            "latitude": node.latitude,
            "longitude": node.longitude,
            "capacity": node.capacity,
            "current_load": node.current_load,
            "status": node.status.value,
            "metadata": node.metadata,
        },
    }


def map_logistics_route_to_ontology(route: ADSL_LogisticsRoute) -> dict[str, Any]:
    """Map ADSL_LogisticsRoute to an Ontology object payload."""
    return {
        "object_type": ONTOLOGY_OBJECT_TYPES["logistics_route"],
        "primary_key": route.route_id,
        "properties": {
            **_mapping_metadata(),
            "route_id": route.route_id,
            "name": route.name,
            "source_node_id": route.source_node_id,
            "target_node_id": route.target_node_id,
            "capacity": route.capacity,
            "transit_time_hours": route.transit_time_hours,
            "status": route.status.value,
            "metadata": route.metadata,
        },
    }


def map_audit_trace_to_ontology(trace: ADSL_AuditTrace) -> dict[str, Any]:
    """Map ADSL_AuditTrace to an Ontology object payload."""
    return {
        "object_type": ONTOLOGY_OBJECT_TYPES["audit_trace"],
        "primary_key": trace.trace_id,
        "properties": {
            **_mapping_metadata(),
            "adsl_schema_version": trace.schema_version,
            "trace_id": trace.trace_id,
            "run_id": trace.run_id,
            "agent_id": trace.agent_id,
            "agent_side": trace.agent_side.value,
            "simulation_tick": trace.simulation_tick,
            "recorded_at": trace.recorded_at.isoformat(),
            "decision_category": trace.decision_category.value,
            "inputs_considered": trace.inputs_considered,
            "reasoning_steps": [
                {
                    "step_index": step.step_index,
                    "description": step.description,
                    "evidence": step.evidence,
                }
                for step in trace.reasoning_steps
            ],
            "action_type": trace.action_type.value,
            "target_id": trace.target_id,
            "action_summary": trace.action_summary,
        },
    }


def map_simulation_run_to_ontology(run: ADSL_SimulationRun) -> dict[str, Any]:
    """Map ADSL_SimulationRun to an Ontology object payload."""
    return {
        "object_type": ONTOLOGY_OBJECT_TYPES["simulation_run"],
        "primary_key": run.run_id,
        "properties": {
            **_mapping_metadata(),
            "run_id": run.run_id,
            "scenario_id": run.scenario_id,
            "status": run.status.value,
            "seed": run.seed,
            "current_tick": run.current_tick,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "audit_trace_count": len(run.audit_trace_ids),
            "audit_trace_ids": list(run.audit_trace_ids),
            "metadata": run.metadata,
        },
    }


def map_force_element_to_ontology(element: ADSL_ForceElement) -> dict[str, Any]:
    """Map ADSL_ForceElement to an Ontology object payload."""
    return {
        "object_type": ONTOLOGY_OBJECT_TYPES["force_element"],
        "primary_key": element.element_id,
        "properties": {
            **_mapping_metadata(),
            "element_id": element.element_id,
            "name": element.name,
            "side": element.side.value,
            "role": element.role,
            "home_node_id": element.home_node_id,
            "patrol_route_ids": list(element.patrol_route_ids),
            "readiness": element.readiness,
            "metadata": element.metadata,
        },
    }


def map_simulation_event_to_ontology(event: SimulationEvent) -> dict[str, Any]:
    """Map SimulationEvent to an Ontology object payload."""
    return {
        "object_type": ONTOLOGY_OBJECT_TYPES["simulation_event"],
        "primary_key": event.event_id,
        "properties": {
            **_mapping_metadata(),
            "event_id": event.event_id,
            "run_id": event.run_id,
            "simulation_tick": event.simulation_tick,
            "event_type": event.event_type.value,
            "agent_id": event.agent_id,
            "agent_side": event.agent_side.value if event.agent_side else None,
            "recorded_at": event.recorded_at.isoformat(),
            "payload": event.payload,
        },
    }


def build_scenario_bootstrap_payload(
    package: ADSL_ScenarioPackage,
) -> list[dict[str, Any]]:
    """Build Ontology upsert payloads for scenario network and force elements."""
    payloads: list[dict[str, Any]] = []
    for node in package.scenario.nodes:
        payloads.append(map_logistics_node_to_ontology(node))
    for route in package.scenario.routes:
        payloads.append(map_logistics_route_to_ontology(route))
    for element in package.blue_force_elements + package.red_force_elements:
        payloads.append(map_force_element_to_ontology(element))
    return payloads


def build_run_sync_payload(
    *,
    run: ADSL_SimulationRun,
    nodes: list[ADSL_LogisticsNode],
    routes: list[ADSL_LogisticsRoute],
    audit_traces: list[ADSL_AuditTrace],
    events: list[SimulationEvent],
    scenario_package: ADSL_ScenarioPackage | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    Build a complete Ontology sync payload for a finished simulation run.

    Returns categorized payload lists per ADR-006 sync policy.
    """
    bootstrap = (
        build_scenario_bootstrap_payload(scenario_package)
        if scenario_package is not None
        else []
    )

    return {
        "bootstrap": bootstrap,
        "simulation_run": [map_simulation_run_to_ontology(run)],
        "logistics_nodes": [map_logistics_node_to_ontology(node) for node in nodes],
        "logistics_routes": [map_logistics_route_to_ontology(route) for route in routes],
        "audit_traces": [map_audit_trace_to_ontology(trace) for trace in audit_traces],
        "simulation_events": [map_simulation_event_to_ontology(event) for event in events],
    }


def is_ontology_sync_enabled() -> bool:
    """Return True when live Ontology sync is enabled via environment."""
    return os.getenv("ADSL_ONTOLOGY_SYNC_ENABLED", "false").lower() in {
        "1",
        "true",
        "yes",
    }


def read_ontology_object(object_type: str, primary_key: str) -> dict[str, Any] | None:
    """
    Read an object from the Palantir Ontology via SDK client (ADR-007).

    Offline / preparation phase: returns None when sync is disabled.
    """
    if not is_ontology_sync_enabled():
        return None
    return get_sdk_client().read_object(object_type, primary_key)


def write_ontology_object(payload: dict[str, Any]) -> str:
    """
    Write a single object to the Palantir Ontology via SDK client (ADR-007).

    Preparation phase: delegates to sdk_client placeholder (synthetic RID).
    Live SDK wiring replaces client internals at Increment 2 activation.
    """
    return get_sdk_client().write_object(payload)


def write_ontology_objects(payloads: list[dict[str, Any]]) -> list[str]:
    """Batch write via SDK client adapter."""
    return get_sdk_client().write_objects_batch(payloads)


def sync_run_to_ontology(
    *,
    run: ADSL_SimulationRun,
    nodes: list[ADSL_LogisticsNode],
    routes: list[ADSL_LogisticsRoute],
    audit_traces: list[ADSL_AuditTrace],
    events: list[SimulationEvent],
    scenario_package: ADSL_ScenarioPackage | None = None,
) -> dict[str, Any]:
    """
    Sync a completed simulation run to the Palantir Ontology.

    Phase 1: builds payloads and performs placeholder writes when enabled.
    """
    payload = build_run_sync_payload(
        run=run,
        nodes=nodes,
        routes=routes,
        audit_traces=audit_traces,
        events=events,
        scenario_package=scenario_package,
    )

    result: dict[str, Any] = {
        "sync_enabled": is_ontology_sync_enabled(),
        "payload_counts": {key: len(value) for key, value in payload.items()},
        "written_rids": [],
    }

    if not is_ontology_sync_enabled():
        return result

    all_payloads: list[dict[str, Any]] = []
    for key in ("bootstrap", "simulation_run", "logistics_nodes", "logistics_routes"):
        all_payloads.extend(payload[key])
    all_payloads.extend(payload["audit_traces"])
    all_payloads.extend(payload["simulation_events"])

    result["written_rids"] = write_ontology_objects(all_payloads)
    return result