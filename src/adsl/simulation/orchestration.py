"""Simulation orchestration policy helpers (ADR-004)."""

from __future__ import annotations

from copy import deepcopy

from adsl.models import (
    ADSL_ForceElement,
    ADSL_LogisticsNode,
    ADSL_LogisticsRoute,
    AgentSide,
    NodeStatus,
)


def sort_force_elements(elements: list[ADSL_ForceElement]) -> list[ADSL_ForceElement]:
    """Return force elements in deterministic ascending element_id order."""
    return sorted(elements, key=lambda element: element.element_id)


def build_force_element_context(element: ADSL_ForceElement) -> dict:
    """Build observation context payload for a force element."""
    return {
        "force_element_id": element.element_id,
        "force_element_name": element.name,
        "role": element.role,
        "home_node_id": element.home_node_id,
        "patrol_route_ids": list(element.patrol_route_ids),
        "readiness": element.readiness,
        "unit_type": element.metadata.get("unit_type"),
        "capability": element.metadata.get("capability"),
        "priority_target": element.metadata.get("priority_target"),
    }


def visible_nodes_for_side(
    side: AgentSide, nodes: list[ADSL_LogisticsNode]
) -> list[ADSL_LogisticsNode]:
    """Apply Phase 1 fog-of-war rules for node visibility."""
    if side == AgentSide.RED:
        return deepcopy(nodes)
    return deepcopy([node for node in nodes if node.status != NodeStatus.DESTROYED])


def visible_routes_for_side(
    side: AgentSide, routes: list[ADSL_LogisticsRoute]
) -> list[ADSL_LogisticsRoute]:
    """Apply Phase 1 fog-of-war rules for route visibility."""
    # Phase 1: both sides see the full route network state.
    del side  # Reserved for future asymmetric route visibility.
    return deepcopy(routes)