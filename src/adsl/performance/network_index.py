# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""O(1) network lookups for simulation hot paths."""

from __future__ import annotations

from adsl.models import ADSL_LogisticsNode, ADSL_LogisticsRoute, RouteStatus


class NetworkIndex:
    """Index nodes and routes by ID and endpoint for constant-time engine lookups."""

    def __init__(
        self,
        nodes: list[ADSL_LogisticsNode],
        routes: list[ADSL_LogisticsRoute],
    ) -> None:
        self._nodes_by_id = {node.node_id: node for node in nodes}
        self._routes_by_id = {route.route_id: route for route in routes}
        self._routes_by_source: dict[str, list[ADSL_LogisticsRoute]] = {}
        self._routes_by_target: dict[str, list[ADSL_LogisticsRoute]] = {}
        for route in routes:
            self._routes_by_source.setdefault(route.source_node_id, []).append(route)
            self._routes_by_target.setdefault(route.target_node_id, []).append(route)

    def get_node(self, node_id: str) -> ADSL_LogisticsNode | None:
        return self._nodes_by_id.get(node_id)

    def get_route(self, route_id: str) -> ADSL_LogisticsRoute | None:
        return self._routes_by_id.get(route_id)

    def routes_from_source(self, node_id: str) -> list[ADSL_LogisticsRoute]:
        return self._routes_by_source.get(node_id, [])

    def routes_to_target(self, node_id: str) -> list[ADSL_LogisticsRoute]:
        return self._routes_by_target.get(node_id, [])

    def open_alternates_for_route(
        self, route: ADSL_LogisticsRoute
    ) -> list[ADSL_LogisticsRoute]:
        """Return open routes sharing source or target with *route*, excluding itself."""
        seen: set[str] = set()
        alternates: list[ADSL_LogisticsRoute] = []
        for candidate in (
            self._routes_by_source.get(route.source_node_id, [])
            + self._routes_by_target.get(route.target_node_id, [])
        ):
            if candidate.route_id == route.route_id or candidate.route_id in seen:
                continue
            if candidate.status != RouteStatus.OPEN:
                continue
            seen.add(candidate.route_id)
            alternates.append(candidate)
        alternates.sort(key=lambda item: item.route_id)
        return alternates