# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Per-tick observation caches to avoid redundant snapshot work."""

from __future__ import annotations

from dataclasses import dataclass

from adsl.models import ADSL_LogisticsNode, ADSL_LogisticsRoute, AgentSide
from adsl.simulation.orchestration import visible_nodes_for_side, visible_routes_for_side


@dataclass(frozen=True)
class SideObservationCache:
    """Reusable observation payloads for all agents on one side within a tick."""

    visible_nodes: list[ADSL_LogisticsNode]
    visible_routes: list[ADSL_LogisticsRoute]
    nodes_by_id: dict[str, ADSL_LogisticsNode]
    routes_by_id: dict[str, ADSL_LogisticsRoute]
    routes_by_source: dict[str, list[ADSL_LogisticsRoute]]
    routes_by_target: dict[str, list[ADSL_LogisticsRoute]]


def _index_routes_by_endpoint(
    routes: list[ADSL_LogisticsRoute],
) -> tuple[dict[str, list[ADSL_LogisticsRoute]], dict[str, list[ADSL_LogisticsRoute]]]:
    by_source: dict[str, list[ADSL_LogisticsRoute]] = {}
    by_target: dict[str, list[ADSL_LogisticsRoute]] = {}
    for route in routes:
        by_source.setdefault(route.source_node_id, []).append(route)
        by_target.setdefault(route.target_node_id, []).append(route)
    return by_source, by_target


def build_side_observation_cache(
    side: AgentSide,
    nodes: list[ADSL_LogisticsNode],
    routes: list[ADSL_LogisticsRoute],
) -> SideObservationCache:
    """
    Build one observation snapshot set per side per tick.

    All agents on the same side within a tick share these read-only snapshots
    (ADR-002: agents do not mutate observation state).
    """
    visible_nodes = visible_nodes_for_side(side, nodes)
    visible_routes = visible_routes_for_side(side, routes)
    nodes_by_id = {node.node_id: node for node in visible_nodes}
    routes_by_id = {route.route_id: route for route in visible_routes}
    routes_by_source, routes_by_target = _index_routes_by_endpoint(visible_routes)
    return SideObservationCache(
        visible_nodes=visible_nodes,
        visible_routes=visible_routes,
        nodes_by_id=nodes_by_id,
        routes_by_id=routes_by_id,
        routes_by_source=routes_by_source,
        routes_by_target=routes_by_target,
    )