# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Bottleneck and vulnerability detection from run bundles."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from adsl.analytics.evidence import make_evidence
from adsl.analytics.reasoning import reasoning_steps_for_vulnerability


def _compute_node_degrees(routes: list[dict[str, Any]]) -> dict[str, int]:
    degree: dict[str, int] = defaultdict(int)
    for route in routes:
        degree[route["source_node_id"]] += 1
        degree[route["target_node_id"]] += 1
    return dict(degree)


def _red_attacks_by_target(audit_traces: list[dict[str, Any]]) -> tuple[Counter[str], Counter[str], list[str]]:
    route_attacks: Counter[str] = Counter()
    node_attacks: Counter[str] = Counter()
    trace_ids: list[str] = []

    for trace in audit_traces:
        if trace.get("agent_side") != "RED":
            continue
        action = trace.get("action_type", "")
        target = trace.get("target_id")
        if not target:
            continue
        if action == "ATTACK_ROUTE":
            route_attacks[target] += 1
            trace_ids.append(trace["trace_id"])
        elif action == "ATTACK_NODE":
            node_attacks[target] += 1
            trace_ids.append(trace["trace_id"])

    return route_attacks, node_attacks, trace_ids


def _route_status_by_node(routes: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    by_node: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for route in routes:
        status = route["status"]
        by_node[route["source_node_id"]][status] += 1
        by_node[route["target_node_id"]][status] += 1
    return {node_id: dict(counts) for node_id, counts in by_node.items()}


def _is_structural_bottleneck(node: dict[str, Any], degree: int) -> bool:
    metadata = node.get("metadata") or {}
    if metadata.get("chokepoint"):
        return True
    if metadata.get("strategic_value") == "critical" and degree >= 3:
        return True
    return degree >= 5


def _vulnerability_score(
    *,
    node: dict[str, Any],
    degree: int,
    red_attacks: int,
    route_statuses: dict[str, int],
) -> float:
    metadata = node.get("metadata") or {}
    score = 0.0

    if metadata.get("chokepoint"):
        score += 25.0
    if metadata.get("strategic_value") == "critical":
        score += 20.0
    score += min(degree * 4.0, 20.0)
    score += min(red_attacks * 5.0, 25.0)

    status = node.get("status", "OPERATIONAL")
    if status == "DESTROYED":
        score += 30.0
    elif status == "DEGRADED":
        score += 15.0

    closed = route_statuses.get("CLOSED", 0)
    contested = route_statuses.get("CONTESTED", 0)
    score += min(closed * 8.0, 24.0)
    score += min(contested * 4.0, 12.0)

    return min(score, 100.0)


def detect_bottlenecks(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify structural bottlenecks in the network."""
    nodes = bundle["network_state"]["nodes"]
    routes = bundle["network_state"]["routes"]
    degrees = _compute_node_degrees(routes)
    route_attacks, node_attacks, _ = _red_attacks_by_target(bundle["audit_traces"])

    findings: list[dict[str, Any]] = []
    for node in nodes:
        node_id = node["node_id"]
        degree = degrees.get(node_id, 0)
        if not _is_structural_bottleneck(node, degree):
            continue

        metadata = node.get("metadata") or {}
        route_statuses = _route_status_by_node(routes).get(node_id, {})
        connected_attacks = sum(
            route_attacks.get(route["route_id"], 0)
            for route in routes
            if route["source_node_id"] == node_id or route["target_node_id"] == node_id
        )
        reasoning = [
            f"Node degree {degree} meets structural bottleneck threshold.",
        ]
        if metadata.get("chokepoint"):
            reasoning.append("Scenario metadata flags this node as a chokepoint.")
        if metadata.get("strategic_value") == "critical" and degree >= 3:
            reasoning.append("Critical strategic value with high connectivity.")
        if connected_attacks:
            reasoning.append(f"{connected_attacks} Red attacks on routes incident to this node.")

        recommendation = (
            f"Map Blue reroute contingencies that bypass {node['name']} "
            f"before corridor saturation (degree {degree})."
        )
        findings.append(
            {
                "insight_type": "bottleneck",
                "severity": "high" if metadata.get("chokepoint") else "medium",
                "entity_kind": "node",
                "entity_id": node_id,
                "entity_name": node["name"],
                "summary": (
                    f"{node['name']} is a structural bottleneck "
                    f"(degree {degree}"
                    f"{', chokepoint' if metadata.get('chokepoint') else ''})."
                ),
                "recommendation": recommendation,
                "metrics": {
                    "degree": degree,
                    "status": node["status"],
                    "red_node_attacks": node_attacks.get(node_id, 0),
                    "connected_route_attacks": connected_attacks,
                },
                "reasoning_steps": reasoning,
                "evidence": make_evidence(
                    source="network_state.nodes",
                    entity_ids=[node_id],
                    counts={"degree": degree, "connected_route_attacks": connected_attacks},
                    details={"metadata": metadata, "adjacent_route_statuses": route_statuses},
                    reasoning_steps=reasoning,
                ),
            }
        )

    findings.sort(key=lambda item: item["metrics"]["degree"], reverse=True)
    return findings


def detect_vulnerabilities(bundle: dict[str, Any], *, top_n: int = 8) -> list[dict[str, Any]]:
    """Rank nodes by operational vulnerability using structure, status, and Red pressure."""
    nodes = bundle["network_state"]["nodes"]
    routes = bundle["network_state"]["routes"]
    degrees = _compute_node_degrees(routes)
    _, node_attacks, attack_trace_ids = _red_attacks_by_target(bundle["audit_traces"])
    route_status_by_node = _route_status_by_node(routes)

    scored: list[dict[str, Any]] = []
    for node in nodes:
        node_id = node["node_id"]
        red_attacks = node_attacks.get(node_id, 0)
        route_statuses = route_status_by_node.get(node_id, {})
        score = _vulnerability_score(
            node=node,
            degree=degrees.get(node_id, 0),
            red_attacks=red_attacks,
            route_statuses=route_statuses,
        )
        if score < 20.0:
            continue

        reasoning = reasoning_steps_for_vulnerability(
            node=node,
            degree=degrees.get(node_id, 0),
            red_attacks=red_attacks,
            route_statuses=route_statuses,
            score=score,
        )
        recommendation = None
        if node["status"] in {"DEGRADED", "DESTROYED"}:
            recommendation = (
                f"Task logistics manager to reallocate load away from {node['name']} "
                f"and validate downstream corridor capacity."
            )
        elif red_attacks >= 2:
            recommendation = (
                f"Review Red targeting of {node['name']} — {red_attacks} node attacks recorded; "
                "consider hardening adjacent routes."
            )

        scored.append(
            {
                "insight_type": "vulnerability",
                "severity": "critical" if score >= 70 else "high" if score >= 45 else "medium",
                "entity_kind": "node",
                "entity_id": node_id,
                "entity_name": node["name"],
                "summary": (
                    f"{node['name']} vulnerability score {score:.0f}/100 "
                    f"({node['status']}, {red_attacks} Red node attacks)."
                ),
                "recommendation": recommendation,
                "metrics": {
                    "vulnerability_score": round(score, 1),
                    "degree": degrees.get(node_id, 0),
                    "status": node["status"],
                    "red_node_attacks": red_attacks,
                    "adjacent_route_statuses": route_statuses,
                },
                "reasoning_steps": reasoning,
                "evidence": make_evidence(
                    source="audit_traces+network_state",
                    entity_ids=[node_id],
                    trace_ids=attack_trace_ids[:5] if red_attacks else None,
                    counts={
                        "vulnerability_score": round(score, 1),
                        "red_node_attacks": red_attacks,
                    },
                    reasoning_steps=reasoning,
                ),
            }
        )

    scored.sort(key=lambda item: item["metrics"]["vulnerability_score"], reverse=True)
    return scored[:top_n]