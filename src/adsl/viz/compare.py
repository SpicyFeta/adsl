# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Build visualization comparison payloads between two runs."""

from __future__ import annotations

from typing import Any

from adsl.viz.transform import VIZ_SCHEMA_VERSION, build_viz_payload


def _index_by_id(items: list[dict[str, Any]], key: str = "id") -> dict[str, dict[str, Any]]:
    return {item[key]: item for item in items}


def build_viz_comparison(
    baseline_bundle: dict[str, Any],
    compare_bundle: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a side-by-side comparison payload for dashboard diff highlighting.

    Compares network status and analytics risk scores between two ADR-009 bundles.
    """
    baseline = build_viz_payload(baseline_bundle)
    compare = build_viz_payload(compare_bundle)

    node_diffs: list[dict[str, Any]] = []
    baseline_nodes = _index_by_id(baseline["nodes"])
    compare_nodes = _index_by_id(compare["nodes"])

    for node_id, compare_node in compare_nodes.items():
        base_node = baseline_nodes.get(node_id)
        if base_node is None:
            continue
        status_changed = base_node["status"] != compare_node["status"]
        risk_delta = compare_node.get("risk_score", 0) - base_node.get("risk_score", 0)
        if status_changed or abs(risk_delta) >= 10:
            node_diffs.append(
                {
                    "id": node_id,
                    "name": compare_node["name"],
                    "baseline_status": base_node["status"],
                    "compare_status": compare_node["status"],
                    "status_changed": status_changed,
                    "baseline_risk": base_node.get("risk_score", 0),
                    "compare_risk": compare_node.get("risk_score", 0),
                    "risk_delta": round(risk_delta, 1),
                    "direction": "worsened" if risk_delta > 0 or _status_worsened(
                        base_node["status"], compare_node["status"]
                    ) else "improved",
                }
            )

    route_diffs: list[dict[str, Any]] = []
    baseline_routes = _index_by_id(baseline["routes"])
    compare_routes = _index_by_id(compare["routes"])

    for route_id, compare_route in compare_routes.items():
        base_route = baseline_routes.get(route_id)
        if base_route is None:
            continue
        status_changed = base_route["status"] != compare_route["status"]
        risk_delta = compare_route.get("risk_score", 0) - base_route.get("risk_score", 0)
        if status_changed or abs(risk_delta) >= 10:
            route_diffs.append(
                {
                    "id": route_id,
                    "name": compare_route["name"],
                    "baseline_status": base_route["status"],
                    "compare_status": compare_route["status"],
                    "status_changed": status_changed,
                    "baseline_risk": base_route.get("risk_score", 0),
                    "compare_risk": compare_route.get("risk_score", 0),
                    "risk_delta": round(risk_delta, 1),
                    "direction": "worsened" if risk_delta > 0 or _status_worsened(
                        base_route["status"], compare_route["status"]
                    ) else "improved",
                }
            )

    node_diffs.sort(key=lambda item: abs(item["risk_delta"]), reverse=True)
    route_diffs.sort(key=lambda item: abs(item["risk_delta"]), reverse=True)

    metric_deltas = {
        "destroyed_nodes": (
            compare["metrics"]["destroyed_node_count"]
            - baseline["metrics"]["destroyed_node_count"]
        ),
        "closed_routes": (
            (compare["metrics"]["route_status_counts"].get("CLOSED", 0))
            - (baseline["metrics"]["route_status_counts"].get("CLOSED", 0))
        ),
        "attack_route": (
            compare["metrics"]["attack_route_count"] - baseline["metrics"]["attack_route_count"]
        ),
    }

    return {
        "schema_version": VIZ_SCHEMA_VERSION,
        "baseline": {
            "run_id": baseline["run_id"],
            "label": baseline.get("label"),
            "scenario_id": baseline["scenario_id"],
        },
        "compare": {
            "run_id": compare["run_id"],
            "label": compare.get("label"),
            "scenario_id": compare["scenario_id"],
        },
        "metric_deltas": metric_deltas,
        "node_diffs": node_diffs[:12],
        "route_diffs": route_diffs[:12],
        "worsened_node_ids": [
            item["id"] for item in node_diffs if item["direction"] == "worsened"
        ],
        "worsened_route_ids": [
            item["id"] for item in route_diffs if item["direction"] == "worsened"
        ],
    }


def _status_worsened(baseline_status: str, compare_status: str) -> bool:
    severity = {
        "OPERATIONAL": 0,
        "OPEN": 0,
        "DEGRADED": 1,
        "CONTESTED": 2,
        "CLOSED": 3,
        "DESTROYED": 4,
    }
    return severity.get(compare_status, 0) > severity.get(baseline_status, 0)