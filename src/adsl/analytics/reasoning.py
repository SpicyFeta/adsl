# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Explainability helpers — reasoning steps and score breakdowns for insights."""

from __future__ import annotations

from typing import Any


def severity_from_score(score: float) -> str:
    if score >= 70:
        return "critical"
    if score >= 45:
        return "high"
    if score >= 20:
        return "medium"
    return "low"


def contributing_factors_from_route_score(
    *,
    route: dict[str, Any],
    red_attacks: int,
    endpoint_vulnerability: float,
    score: float,
) -> dict[str, float]:
    """Return named score components for route risk (sums to approximate total)."""
    metadata = route.get("metadata") or {}
    factors: dict[str, float] = {}

    status = route.get("status", "OPEN")
    if status == "CLOSED":
        factors["status_closed"] = 40.0
    elif status == "CONTESTED":
        factors["status_contested"] = 25.0

    if metadata.get("chokepoint"):
        factors["chokepoint_metadata"] = 20.0
    risk_level = metadata.get("risk_level", "")
    if risk_level == "critical":
        factors["metadata_risk_critical"] = 15.0
    elif risk_level == "high":
        factors["metadata_risk_high"] = 10.0

    if red_attacks:
        factors["red_attack_pressure"] = min(red_attacks * 6.0, 30.0)
    if endpoint_vulnerability:
        factors["endpoint_vulnerability"] = min(endpoint_vulnerability * 0.15, 15.0)

    factors["total_capped"] = min(score, 100.0)
    return factors


def reasoning_steps_for_route_risk(
    *,
    route: dict[str, Any],
    red_attacks: int,
    endpoint_vulnerability: float,
    factors: dict[str, float],
) -> list[str]:
    steps: list[str] = []
    status = route.get("status", "OPEN")
    metadata = route.get("metadata") or {}

    steps.append(f"Route {route['route_id']} end-state status is {status}.")
    if metadata.get("chokepoint"):
        steps.append("Scenario metadata marks this route as a chokepoint.")
    if metadata.get("corridor"):
        steps.append(f"Route belongs to corridor '{metadata['corridor']}'.")
    if red_attacks:
        steps.append(
            f"Red agents recorded {red_attacks} ATTACK_ROUTE decision(s) targeting this route."
        )
    else:
        steps.append("No direct Red route attacks recorded — score driven by status/metadata.")
    if endpoint_vulnerability >= 20:
        steps.append(
            f"Connected endpoint node vulnerability is elevated ({endpoint_vulnerability:.0f}/100)."
        )

    top_factor = max(
        ((k, v) for k, v in factors.items() if k != "total_capped" and v > 0),
        key=lambda item: item[1],
        default=None,
    )
    if top_factor:
        steps.append(f"Largest contributing factor: {top_factor[0].replace('_', ' ')} (+{top_factor[1]:.0f}).")
    return steps


def reasoning_steps_for_vulnerability(
    *,
    node: dict[str, Any],
    degree: int,
    red_attacks: int,
    route_statuses: dict[str, int],
    score: float,
) -> list[str]:
    metadata = node.get("metadata") or {}
    steps: list[str] = [
        f"Node {node['node_id']} ({node['name']}) status: {node.get('status', 'OPERATIONAL')}.",
        f"Structural connectivity: {degree} incident route(s).",
    ]
    if metadata.get("chokepoint"):
        steps.append("Marked as chokepoint in scenario metadata.")
    if metadata.get("strategic_value") == "critical":
        steps.append("Strategic value classified as critical.")
    if red_attacks:
        steps.append(f"Red executed {red_attacks} ATTACK_NODE action(s) against this node.")
    closed = route_statuses.get("CLOSED", 0)
    contested = route_statuses.get("CONTESTED", 0)
    if closed or contested:
        steps.append(
            f"Adjacent routes at run end: {closed} CLOSED, {contested} CONTESTED."
        )
    steps.append(f"Composite vulnerability score: {score:.0f}/100 (heuristic, not probability).")
    return steps


def reasoning_steps_for_corridor(
    *,
    corridor: str,
    closed: int,
    contested: int,
    total_attacks: int,
    composite: float,
    route_count: int,
) -> list[str]:
    steps = [
        f"Corridor '{corridor}' aggregates {route_count} route(s) via metadata.corridor.",
        f"End-state: {closed} closed, {contested} contested route(s).",
    ]
    if total_attacks:
        steps.append(f"Red recorded {total_attacks} route attacks across this corridor.")
    else:
        steps.append("No corridor-specific Red route attacks — risk from route status aggregation.")
    steps.append(f"Composite corridor risk score: {composite:.0f}/100.")
    return steps