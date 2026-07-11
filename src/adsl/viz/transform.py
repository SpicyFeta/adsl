# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Transform ADR-009 run bundles into compact visualization payloads."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from adsl.analytics.report import generate_insights_report

VIZ_SCHEMA_VERSION = "1.1"


NODE_STATUS_COLORS = {
    "OPERATIONAL": "#22c55e",
    "DEGRADED": "#eab308",
    "DESTROYED": "#ef4444",
}

ROUTE_STATUS_COLORS = {
    "OPEN": "#22c55e",
    "CONTESTED": "#f97316",
    "CLOSED": "#ef4444",
}


def _count_red_activity(audit_traces: list[dict[str, Any]]) -> dict[str, Any]:
    route_attacks: Counter[str] = Counter()
    node_attacks: Counter[str] = Counter()
    red_actions: Counter[str] = Counter()

    for trace in audit_traces:
        if trace.get("agent_side") != "RED":
            continue
        action = trace.get("action_type", "")
        red_actions[action] += 1
        if action == "ATTACK_ROUTE":
            target = trace.get("target_id")
            if target:
                route_attacks[target] += 1
        elif action == "ATTACK_NODE":
            target = trace.get("target_id")
            if target:
                node_attacks[target] += 1

    return {
        "by_action": dict(red_actions),
        "route_attacks": dict(route_attacks),
        "node_attacks": dict(node_attacks),
        "total_attacks": red_actions.get("ATTACK_ROUTE", 0) + red_actions.get("ATTACK_NODE", 0),
    }


def _compute_node_degrees(routes: list[dict[str, Any]]) -> dict[str, int]:
    degree: dict[str, int] = defaultdict(int)
    for route in routes:
        degree[route["source_node_id"]] += 1
        degree[route["target_node_id"]] += 1
    return dict(degree)


def _risk_severity(score: float) -> str:
    if score >= 70:
        return "critical"
    if score >= 45:
        return "high"
    if score >= 20:
        return "medium"
    return "low"


def _build_analytics_lookup(
    insights: dict[str, Any],
) -> tuple[dict[str, float], dict[str, float], set[str], dict[str, str]]:
    """Index node/route risk scores, focus area IDs, and corridor names."""
    node_risks: dict[str, float] = {}
    route_risks: dict[str, float] = {}
    focus_ids: set[str] = set()
    corridor_names: dict[str, str] = {}

    for item in insights.get("findings", {}).get("node_risks", []):
        node_risks[item["entity_id"]] = item["metrics"].get("risk_score", 0)

    for item in insights.get("findings", {}).get("vulnerabilities", []):
        node_risks.setdefault(
            item["entity_id"],
            item["metrics"].get("vulnerability_score", 0),
        )

    for item in insights.get("findings", {}).get("route_risks", []):
        route_risks[item["entity_id"]] = item["metrics"].get("risk_score", 0)

    for area in insights.get("recommended_focus_areas", []):
        focus_ids.add(area["entity_id"])

    for item in insights.get("findings", {}).get("corridor_risks", []):
        corridor_names[item["entity_id"]] = item.get("entity_name", item["entity_id"])

    return node_risks, route_risks, focus_ids, corridor_names


def _is_bottleneck(node: dict[str, Any], degree: int) -> bool:
    metadata = node.get("metadata") or {}
    if metadata.get("chokepoint"):
        return True
    if metadata.get("strategic_value") == "critical" and degree >= 3:
        return True
    return degree >= 5


def build_viz_payload(
    bundle: dict[str, Any],
    *,
    insights: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a compact, visualization-ready payload from an ADR-009 run bundle.

    Source data is read-only; audit traces are aggregated, not modified.
    Analytics risk scores and focus areas are merged when ``insights`` is provided
    or generated from the bundle.
    """
    run = bundle["run"]
    scenario = bundle["scenario"]
    execution = bundle["execution"]
    stats = bundle["summary_statistics"]
    nodes_raw = bundle["network_state"]["nodes"]
    routes_raw = bundle["network_state"]["routes"]
    degrees = _compute_node_degrees(routes_raw)
    red_activity = _count_red_activity(bundle["audit_traces"])

    insights_report = insights or generate_insights_report(bundle)
    node_risk_lookup, route_risk_lookup, focus_ids, corridor_names = _build_analytics_lookup(
        insights_report
    )

    nodes: list[dict[str, Any]] = []
    latitudes: list[float] = []
    longitudes: list[float] = []

    for node in nodes_raw:
        lat = float(node["latitude"])
        lng = float(node["longitude"])
        latitudes.append(lat)
        longitudes.append(lng)
        degree = degrees.get(node["node_id"], 0)
        metadata = node.get("metadata") or {}
        risk_score = node_risk_lookup.get(node["node_id"], 0.0)
        nodes.append(
            {
                "id": node["node_id"],
                "name": node["name"],
                "node_type": node["node_type"],
                "status": node["status"],
                "latitude": lat,
                "longitude": lng,
                "degree": degree,
                "is_chokepoint": bool(metadata.get("chokepoint")),
                "is_bottleneck": _is_bottleneck(node, degree),
                "red_attacks": red_activity["node_attacks"].get(node["node_id"], 0),
                "risk_score": round(risk_score, 1),
                "risk_severity": _risk_severity(risk_score),
                "is_focus_area": node["node_id"] in focus_ids,
                "corridor": metadata.get("corridor"),
                "color": NODE_STATUS_COLORS.get(node["status"], "#94a3b8"),
            }
        )

    node_positions = {node["node_id"]: (node["latitude"], node["longitude"]) for node in nodes_raw}

    routes: list[dict[str, Any]] = []
    for route in routes_raw:
        metadata = route.get("metadata") or {}
        corridor = metadata.get("corridor")
        risk_score = route_risk_lookup.get(route["route_id"], 0.0)
        routes.append(
            {
                "id": route["route_id"],
                "name": route["name"],
                "source_id": route["source_node_id"],
                "target_id": route["target_node_id"],
                "status": route["status"],
                "is_chokepoint": bool(metadata.get("chokepoint")),
                "is_contested": route["status"] == "CONTESTED",
                "red_attacks": red_activity["route_attacks"].get(route["route_id"], 0),
                "risk_score": round(risk_score, 1),
                "risk_severity": _risk_severity(risk_score),
                "is_focus_area": route["route_id"] in focus_ids or (
                    corridor is not None and corridor in focus_ids
                ),
                "corridor": corridor,
                "color": ROUTE_STATUS_COLORS.get(route["status"], "#94a3b8"),
            }
        )

    bounds = {
        "min_lat": min(latitudes) if latitudes else 0.0,
        "max_lat": max(latitudes) if latitudes else 0.0,
        "min_lng": min(longitudes) if longitudes else 0.0,
        "max_lng": max(longitudes) if longitudes else 0.0,
    }

    by_action = stats.get("audit_traces_by_action", {})

    top_route_risks = sorted(routes, key=lambda r: r["risk_score"], reverse=True)[:5]
    top_node_risks = sorted(nodes, key=lambda n: n["risk_score"], reverse=True)[:5]

    return {
        "schema_version": VIZ_SCHEMA_VERSION,
        "run_id": run["run_id"],
        "label": execution.get("label"),
        "scenario_id": run["scenario_id"],
        "scenario_name": scenario.get("name", run["scenario_id"]),
        "seed": execution["seed"],
        "ticks_executed": execution["ticks_executed"],
        "status": run["status"],
        "metrics": {
            "destroyed_node_count": stats["destroyed_node_count"],
            "destroyed_node_fraction": stats["destroyed_node_fraction"],
            "node_status_counts": stats["node_status_counts"],
            "route_status_counts": stats["route_status_counts"],
            "attack_route_count": by_action.get("ATTACK_ROUTE", 0),
            "attack_node_count": by_action.get("ATTACK_NODE", 0),
            "no_action_count": by_action.get("NO_ACTION", 0),
            "harden_count": by_action.get("HARDEN", 0),
            "reroute_count": by_action.get("REROUTE", 0),
            "audit_trace_count": len(bundle["audit_traces"]),
        },
        "red_activity": red_activity,
        "bounds": bounds,
        "nodes": nodes,
        "routes": routes,
        "node_positions": {
            node_id: {"lat": pos[0], "lng": pos[1]}
            for node_id, pos in node_positions.items()
        },
        "analytics_overlay": {
            "schema_version": insights_report.get("schema_version", "1.0"),
            "key_insights": insights_report.get("key_insights", [])[:5],
            "structured_insights": insights_report.get("structured_insights", [])[:6],
            "actionable_recommendations": insights_report.get(
                "actionable_recommendations", []
            )[:6],
            "recommended_focus_areas": insights_report.get("recommended_focus_areas", [])[:6],
            "corridor_risks": insights_report.get("findings", {}).get("corridor_risks", [])[:5],
            "top_node_risks": [
                {"id": n["id"], "name": n["name"], "risk_score": n["risk_score"]}
                for n in top_node_risks
                if n["risk_score"] >= 20
            ],
            "top_route_risks": [
                {"id": r["id"], "name": r["name"], "risk_score": r["risk_score"]}
                for r in top_route_risks
                if r["risk_score"] >= 20
            ],
            "corridor_names": corridor_names,
        },
    }