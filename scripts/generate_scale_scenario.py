#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Generate the continental-grid-scale-v4 stress scenario dataset."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_ROOT / "data" / "synthetic" / "logistics_scenario_scale.json"

CORRIDORS = ("alpha", "bravo", "charlie", "delta")
ROWS = 4
COLS = 4


def _node_id(row: int, col: int) -> str:
    return f"N-{CORRIDORS[row].upper()}-{col + 1}"


def _route_id(source: str, target: str) -> str:
    return f"R-{source}-{_short(target)}"


def _short(node_id: str) -> str:
    return node_id.removeprefix("N-")


def build_scenario() -> dict:
    nodes: list[dict] = []
    routes: list[dict] = []

    nodes.append(
        {
            "node_id": "N-MAIN-PORT",
            "name": "Continental Main Port",
            "node_type": "PORT",
            "latitude": 40.0,
            "longitude": -75.0,
            "capacity": 800.0,
            "current_load": 620.0,
            "status": "OPERATIONAL",
            "metadata": {
                "strategic_value": "critical",
                "hardening_level": "high",
                "topology": "scale_grid",
            },
        }
    )

    for row in range(ROWS):
        corridor = CORRIDORS[row]
        for col in range(COLS):
            node_id = _node_id(row, col)
            node_type = "HUB" if col == 1 else "DEPOT" if col == 0 else "FORWARD_OPERATING_BASE"
            nodes.append(
                {
                    "node_id": node_id,
                    "name": f"{corridor.title()} Sector Node {col + 1}",
                    "node_type": node_type,
                    "latitude": 40.5 + row * 0.35,
                    "longitude": -74.5 + col * 0.35,
                    "capacity": 300.0 - col * 40,
                    "current_load": 220.0 - col * 30,
                    "status": "OPERATIONAL",
                    "metadata": {
                        "strategic_value": "high" if col < 2 else "medium",
                        "corridor": corridor,
                        "chokepoint": col == 1,
                        "topology": "scale_grid",
                    },
                }
            )

    for row in range(ROWS):
        corridor = CORRIDORS[row]
        row_nodes = [_node_id(row, col) for col in range(COLS)]
        routes.append(
            {
                "route_id": f"R-PORT-{_short(row_nodes[0])}",
                "name": f"Port to {corridor.title()} Entry",
                "source_node_id": "N-MAIN-PORT",
                "target_node_id": row_nodes[0],
                "capacity": 90.0,
                "transit_time_hours": 6.0 + row,
                "status": "OPEN",
                "metadata": {
                    "corridor": corridor,
                    "risk_level": "medium",
                    "topology": "scale_grid",
                },
            }
        )
        for col in range(COLS - 1):
            source = row_nodes[col]
            target = row_nodes[col + 1]
            routes.append(
                {
                    "route_id": _route_id(source, target),
                    "name": f"{corridor.title()} leg {col + 1}->{col + 2}",
                    "source_node_id": source,
                    "target_node_id": target,
                    "capacity": 70.0 - col * 5,
                    "transit_time_hours": 4.0 + col,
                    "status": "OPEN",
                    "metadata": {
                        "corridor": corridor,
                        "chokepoint": col == 0,
                        "risk_level": "high" if col == 0 else "medium",
                        "topology": "scale_grid",
                    },
                }
            )

    red_elements = []
    blue_elements = []
    for row, corridor in enumerate(CORRIDORS):
        corridor_routes = [route["route_id"] for route in routes if route["metadata"]["corridor"] == corridor]
        red_elements.append(
            {
                "element_id": f"RED-{corridor.upper()}-STRIKE",
                "name": f"{corridor.title()} Strike Cell",
                "side": "RED",
                "role": "STRIKE",
                "home_node_id": _node_id(row, 0),
                "patrol_route_ids": corridor_routes[:4],
                "readiness": 0.9,
                "metadata": {
                    "unit_type": "interdiction_cell",
                    "strike_cooldown_ticks": 2,
                    "strike_budget": 30,
                    "priority_target": f"{corridor}_corridors",
                },
            }
        )
        red_elements.append(
            {
                "element_id": f"RED-{corridor.upper()}-RECON",
                "name": f"{corridor.title()} Recon Element",
                "side": "RED",
                "role": "RECONNAISSANCE",
                "home_node_id": _node_id(row, 1),
                "patrol_route_ids": corridor_routes[:3],
                "readiness": 0.85,
                "metadata": {"unit_type": "surveillance_team"},
            }
        )
        blue_elements.extend(
            [
                {
                    "element_id": f"BLUE-{corridor.upper()}-LOG",
                    "name": f"{corridor.title()} Logistics Manager",
                    "side": "BLUE",
                    "role": "LOGISTICS_MANAGER",
                    "home_node_id": _node_id(row, 0),
                    "patrol_route_ids": corridor_routes,
                    "readiness": 0.95,
                    "metadata": {
                        "unit_type": "logistics_convoy",
                        "priority_mission": "corridor_sustainment",
                    },
                },
                {
                    "element_id": f"BLUE-{corridor.upper()}-SEC",
                    "name": f"{corridor.title()} Route Security",
                    "side": "BLUE",
                    "role": "ROUTE_SECURITY",
                    "home_node_id": _node_id(row, 1),
                    "patrol_route_ids": corridor_routes[:3],
                    "readiness": 0.9,
                    "metadata": {
                        "unit_type": "security_element",
                        "priority_mission": "chokepoint_hardening",
                    },
                },
                {
                    "element_id": f"BLUE-{corridor.upper()}-DEPOT",
                    "name": f"{corridor.title()} Depot Operator",
                    "side": "BLUE",
                    "role": "DEPOT_OPERATOR",
                    "home_node_id": _node_id(row, 0),
                    "patrol_route_ids": [corridor_routes[0]] if corridor_routes else [],
                    "readiness": 0.88,
                    "metadata": {"unit_type": "depot_team"},
                },
            ]
        )

    return {
        "scenario": {
            "scenario_id": "continental-grid-scale-v4",
            "name": "Continental Grid Scale Stress Network",
            "description": (
                "An 18-node, quad-corridor grid designed for performance and scale testing. "
                "Four parallel supply corridors with chokepoint hubs stress multi-agent "
                "orchestration and batch analyst workflows at higher tick counts."
            ),
            "metadata": {
                "theater": "Continental Scale Exercise Zone",
                "duration_days": 30,
                "contestation_level": "moderate",
                "primary_objective": "Sustain tri-corridor grid resupply under parallel interdiction",
                "topology": "continental_grid_scale",
                "scale_test": True,
            },
            "nodes": nodes,
            "routes": routes,
        },
        "red_force_elements": red_elements,
        "blue_force_elements": blue_elements,
    }


def main() -> int:
    payload = build_scenario()
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    print(
        f"Nodes: {len(payload['scenario']['nodes'])}, "
        f"Routes: {len(payload['scenario']['routes'])}, "
        f"Red: {len(payload['red_force_elements'])}, "
        f"Blue: {len(payload['blue_force_elements'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())