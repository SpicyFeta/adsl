#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Generate the continental-mega-scale-v5 large-network stress scenario."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_ROOT / "data" / "synthetic" / "logistics_scenario_mega.json"

CORRIDORS = ("alpha", "bravo", "charlie", "delta", "echo", "foxtrot")
ROWS = len(CORRIDORS)
COLS = 6


def _node_id(row: int, col: int) -> str:
    return f"N-{CORRIDORS[row].upper()}-{col + 1}"


def _route_id(source: str, target: str) -> str:
    return f"R-{_short(source)}-{_short(target)}"


def _short(node_id: str) -> str:
    return node_id.removeprefix("N-")


def build_scenario() -> dict:
    nodes: list[dict] = []
    routes: list[dict] = []

    nodes.append(
        {
            "node_id": "N-MAIN-PORT",
            "name": "Continental Mega Port",
            "node_type": "PORT",
            "latitude": 38.0,
            "longitude": -78.0,
            "capacity": 1200.0,
            "current_load": 900.0,
            "status": "OPERATIONAL",
            "metadata": {
                "strategic_value": "critical",
                "topology": "mega_grid",
            },
        }
    )

    for row in range(ROWS):
        corridor = CORRIDORS[row]
        for col in range(COLS):
            if col in (0, 2, 4):
                node_type = "DEPOT"
            elif col in (1, 3):
                node_type = "HUB"
            else:
                node_type = "FORWARD_OPERATING_BASE"
            nodes.append(
                {
                    "node_id": _node_id(row, col),
                    "name": f"{corridor.title()} Node {col + 1}",
                    "node_type": node_type,
                    "latitude": 38.2 + row * 0.25,
                    "longitude": -77.5 + col * 0.2,
                    "capacity": 280.0 - col * 15,
                    "current_load": 200.0 - col * 12,
                    "status": "OPERATIONAL",
                    "metadata": {
                        "strategic_value": "high" if col < 4 else "medium",
                        "corridor": corridor,
                        "chokepoint": col in (1, 3),
                        "topology": "mega_grid",
                    },
                }
            )

    for row in range(ROWS):
        corridor = CORRIDORS[row]
        row_nodes = [_node_id(row, col) for col in range(COLS)]
        routes.append(
            {
                "route_id": f"R-PORT-{_short(row_nodes[0])}",
                "name": f"Port to {corridor.title()}",
                "source_node_id": "N-MAIN-PORT",
                "target_node_id": row_nodes[0],
                "capacity": 100.0,
                "transit_time_hours": 5.0 + row * 0.5,
                "status": "OPEN",
                "metadata": {"corridor": corridor, "topology": "mega_grid"},
            }
        )
        for col in range(COLS - 1):
            source, target = row_nodes[col], row_nodes[col + 1]
            routes.append(
                {
                    "route_id": _route_id(source, target),
                    "name": f"{corridor.title()} segment {col + 1}",
                    "source_node_id": source,
                    "target_node_id": target,
                    "capacity": 75.0,
                    "transit_time_hours": 3.0 + col * 0.4,
                    "status": "OPEN",
                    "metadata": {
                        "corridor": corridor,
                        "chokepoint": col in (0, 2),
                        "topology": "mega_grid",
                    },
                }
            )

    red_elements = []
    blue_elements = []
    for row, corridor in enumerate(CORRIDORS):
        corridor_routes = [r["route_id"] for r in routes if r["metadata"]["corridor"] == corridor]
        red_elements.extend(
            [
                {
                    "element_id": f"RED-{corridor.upper()}-STRIKE",
                    "name": f"{corridor.title()} Strike",
                    "side": "RED",
                    "role": "STRIKE",
                    "home_node_id": _node_id(row, 0),
                    "patrol_route_ids": corridor_routes[:5],
                    "readiness": 0.9,
                    "metadata": {
                        "strike_cooldown_ticks": 2,
                        "strike_budget": 40,
                    },
                },
                {
                    "element_id": f"RED-{corridor.upper()}-FIRE",
                    "name": f"{corridor.title()} Fire Support",
                    "side": "RED",
                    "role": "FIRE_SUPPORT",
                    "home_node_id": _node_id(row, 2),
                    "patrol_route_ids": corridor_routes[2:6],
                    "readiness": 0.85,
                    "metadata": {"capability": "indirect_fire"},
                },
            ]
        )
        blue_elements.extend(
            [
                {
                    "element_id": f"BLUE-{corridor.upper()}-LOG",
                    "name": f"{corridor.title()} Logistics",
                    "side": "BLUE",
                    "role": "LOGISTICS_MANAGER",
                    "home_node_id": _node_id(row, 0),
                    "patrol_route_ids": corridor_routes,
                    "readiness": 0.95,
                    "metadata": {"priority_mission": "corridor_sustainment"},
                },
                {
                    "element_id": f"BLUE-{corridor.upper()}-COORD",
                    "name": f"{corridor.title()} Coordinator",
                    "side": "BLUE",
                    "role": "ROUTE_COORDINATOR",
                    "home_node_id": _node_id(row, 1),
                    "patrol_route_ids": corridor_routes[:4],
                    "readiness": 0.92,
                    "metadata": {},
                },
                {
                    "element_id": f"BLUE-{corridor.upper()}-SEC",
                    "name": f"{corridor.title()} Security",
                    "side": "BLUE",
                    "role": "ROUTE_SECURITY",
                    "home_node_id": _node_id(row, 3),
                    "patrol_route_ids": corridor_routes[2:5],
                    "readiness": 0.9,
                    "metadata": {"priority_mission": "chokepoint_hardening"},
                },
                {
                    "element_id": f"BLUE-{corridor.upper()}-DEPOT",
                    "name": f"{corridor.title()} Depot Ops",
                    "side": "BLUE",
                    "role": "DEPOT_OPERATOR",
                    "home_node_id": _node_id(row, 0),
                    "patrol_route_ids": [corridor_routes[0]],
                    "readiness": 0.88,
                    "metadata": {},
                },
            ]
        )

    return {
        "scenario": {
            "scenario_id": "continental-mega-scale-v5",
            "name": "Continental Mega-Scale Grid",
            "description": (
                "A 37-node, six-corridor mega grid for large-network performance validation. "
                "24 Red and 24 Blue agents exercise observation, decision, and export paths "
                "at scale without opening theater-scale modeling scope."
            ),
            "metadata": {
                "topology": "continental_mega_grid",
                "scale_test": True,
                "node_count": len(nodes),
                "agent_count": len(red_elements) + len(blue_elements),
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
        f"Agents: {len(payload['red_force_elements']) + len(payload['blue_force_elements'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())