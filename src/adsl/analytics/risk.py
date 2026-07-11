# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Route and corridor risk scoring from run bundles."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from adsl.analytics.evidence import make_evidence
from adsl.analytics.reasoning import (
    contributing_factors_from_route_score,
    reasoning_steps_for_corridor,
    reasoning_steps_for_route_risk,
)


def _red_route_attacks(audit_traces: list[dict[str, Any]]) -> tuple[Counter[str], dict[str, list[str]]]:
    attacks: Counter[str] = Counter()
    trace_ids_by_route: dict[str, list[str]] = defaultdict(list)

    for trace in audit_traces:
        if trace.get("agent_side") != "RED":
            continue
        if trace.get("action_type") != "ATTACK_ROUTE":
            continue
        target = trace.get("target_id")
        if not target:
            continue
        attacks[target] += 1
        trace_ids_by_route[target].append(trace["trace_id"])

    return attacks, dict(trace_ids_by_route)


def _node_vulnerability_lookup(bundle: dict[str, Any]) -> dict[str, float]:
    from adsl.analytics.bottlenecks import detect_vulnerabilities

    lookup: dict[str, float] = {}
    for finding in detect_vulnerabilities(bundle, top_n=50):
        lookup[finding["entity_id"]] = finding["metrics"]["vulnerability_score"]
    return lookup


def _route_risk_score(
    *,
    route: dict[str, Any],
    red_attacks: int,
    endpoint_vulnerability: float,
) -> float:
    metadata = route.get("metadata") or {}
    score = 0.0

    status = route.get("status", "OPEN")
    if status == "CLOSED":
        score += 40.0
    elif status == "CONTESTED":
        score += 25.0

    if metadata.get("chokepoint"):
        score += 20.0
    risk_level = metadata.get("risk_level", "")
    if risk_level == "critical":
        score += 15.0
    elif risk_level == "high":
        score += 10.0

    score += min(red_attacks * 6.0, 30.0)
    score += min(endpoint_vulnerability * 0.15, 15.0)

    return min(score, 100.0)


def score_node_risks(bundle: dict[str, Any], *, top_n: int = 8) -> list[dict[str, Any]]:
    """
    Score key nodes by criticality and Red interdiction exposure.

    Uses the same heuristic model as vulnerability detection but exposes
    ``risk_score`` for consistency with route/corridor scoring.
    """
    from adsl.analytics.bottlenecks import detect_vulnerabilities

    node_risks: list[dict[str, Any]] = []
    for finding in detect_vulnerabilities(bundle, top_n=top_n):
        score = finding["metrics"]["vulnerability_score"]
        node_risks.append(
            {
                **finding,
                "insight_type": "node_risk",
                "metrics": {
                    **finding["metrics"],
                    "risk_score": score,
                },
                "summary": (
                    f"{finding['entity_name']} risk {score:.0f}/100 "
                    f"({finding['metrics']['status']}, "
                    f"{finding['metrics']['red_node_attacks']} Red node attacks)."
                ),
            }
        )
    return node_risks


def score_route_risks(bundle: dict[str, Any], *, top_n: int = 10) -> list[dict[str, Any]]:
    """Score individual routes by status, metadata, Red pressure, and endpoint vulnerability."""
    routes = bundle["network_state"]["routes"]
    route_attacks, trace_ids_by_route = _red_route_attacks(bundle["audit_traces"])
    node_vuln = _node_vulnerability_lookup(bundle)

    scored: list[dict[str, Any]] = []
    for route in routes:
        route_id = route["route_id"]
        attacks = route_attacks.get(route_id, 0)
        endpoint_vuln = max(
            node_vuln.get(route["source_node_id"], 0.0),
            node_vuln.get(route["target_node_id"], 0.0),
        )
        score = _route_risk_score(
            route=route,
            red_attacks=attacks,
            endpoint_vulnerability=endpoint_vuln,
        )

        metadata = route.get("metadata") or {}
        factors = contributing_factors_from_route_score(
            route=route,
            red_attacks=attacks,
            endpoint_vulnerability=endpoint_vuln,
            score=score,
        )
        reasoning = reasoning_steps_for_route_risk(
            route=route,
            red_attacks=attacks,
            endpoint_vulnerability=endpoint_vuln,
            factors=factors,
        )
        recommendation = None
        if route["status"] == "CLOSED":
            recommendation = (
                f"Activate Blue reroute policy for closed route {route['name']} — "
                "verify open alternate shares source or target node."
            )
        elif attacks >= 5:
            recommendation = (
                f"Assign route security to harden {route['name']} — sustained Red pressure "
                f"({attacks} attacks)."
            )

        scored.append(
            {
                "insight_type": "route_risk",
                "severity": "critical" if score >= 70 else "high" if score >= 45 else "medium",
                "entity_kind": "route",
                "entity_id": route_id,
                "entity_name": route["name"],
                "summary": (
                    f"{route['name']} risk {score:.0f}/100 — {route['status']}, "
                    f"{attacks} Red attacks."
                ),
                "recommendation": recommendation,
                "metrics": {
                    "risk_score": round(score, 1),
                    "status": route["status"],
                    "red_attacks": attacks,
                    "corridor": metadata.get("corridor"),
                    "chokepoint": bool(metadata.get("chokepoint")),
                    "contributing_factors": factors,
                },
                "reasoning_steps": reasoning,
                "evidence": make_evidence(
                    source="audit_traces+network_state.routes",
                    entity_ids=[route_id],
                    trace_ids=trace_ids_by_route.get(route_id, [])[:10] or None,
                    counts={"risk_score": round(score, 1), "red_attacks": attacks},
                    reasoning_steps=reasoning,
                ),
            }
        )

    scored.sort(key=lambda item: item["metrics"]["risk_score"], reverse=True)
    return scored[:top_n]


def score_corridor_risks(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Aggregate route risk scores by corridor metadata (or 'unassigned')."""
    routes = bundle["network_state"]["routes"]
    route_attacks, trace_ids_by_route = _red_route_attacks(bundle["audit_traces"])
    node_vuln = _node_vulnerability_lookup(bundle)

    by_corridor: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for route in routes:
        metadata = route.get("metadata") or {}
        corridor = metadata.get("corridor") or "unassigned"
        by_corridor[corridor].append(route)

    findings: list[dict[str, Any]] = []
    for corridor, corridor_routes in sorted(by_corridor.items()):
        route_scores: list[float] = []
        closed = contested = open_count = 0
        total_attacks = 0
        trace_ids: list[str] = []
        route_ids: list[str] = []

        for route in corridor_routes:
            route_id = route["route_id"]
            attacks = route_attacks.get(route_id, 0)
            endpoint_vuln = max(
                node_vuln.get(route["source_node_id"], 0.0),
                node_vuln.get(route["target_node_id"], 0.0),
            )
            route_scores.append(
                _route_risk_score(
                    route=route,
                    red_attacks=attacks,
                    endpoint_vulnerability=endpoint_vuln,
                )
            )
            total_attacks += attacks
            route_ids.append(route_id)
            trace_ids.extend(trace_ids_by_route.get(route_id, [])[:3])

            status = route["status"]
            if status == "CLOSED":
                closed += 1
            elif status == "CONTESTED":
                contested += 1
            else:
                open_count += 1

        avg_score = sum(route_scores) / len(route_scores) if route_scores else 0.0
        max_score = max(route_scores) if route_scores else 0.0
        closure_fraction = closed / len(corridor_routes) if corridor_routes else 0.0

        composite = min(avg_score * 0.6 + max_score * 0.25 + closure_fraction * 40.0, 100.0)
        reasoning = reasoning_steps_for_corridor(
            corridor=corridor,
            closed=closed,
            contested=contested,
            total_attacks=total_attacks,
            composite=composite,
            route_count=len(corridor_routes),
        )
        recommendation = None
        if closed >= 1 and composite >= 40:
            recommendation = (
                f"Workshop compare corridor '{corridor}' against alternate ridge/corridor — "
                f"{closed}/{len(corridor_routes)} routes closed at run end."
            )
        elif total_attacks >= 10:
            recommendation = (
                f"Run what-if with slower Red pacing on '{corridor}' — "
                f"{total_attacks} route attacks concentrated in this corridor."
            )

        findings.append(
            {
                "insight_type": "corridor_risk",
                "severity": (
                    "critical" if composite >= 65 else "high" if composite >= 40 else "medium"
                ),
                "entity_kind": "corridor",
                "entity_id": corridor,
                "entity_name": corridor.replace("_", " ").title(),
                "summary": (
                    f"Corridor '{corridor}' composite risk {composite:.0f}/100 — "
                    f"{closed} closed, {contested} contested, {total_attacks} Red attacks."
                ),
                "recommendation": recommendation,
                "metrics": {
                    "composite_risk_score": round(composite, 1),
                    "average_route_risk": round(avg_score, 1),
                    "max_route_risk": round(max_score, 1),
                    "route_count": len(corridor_routes),
                    "closed_routes": closed,
                    "contested_routes": contested,
                    "open_routes": open_count,
                    "total_red_attacks": total_attacks,
                    "closure_fraction": round(closure_fraction, 3),
                },
                "reasoning_steps": reasoning,
                "evidence": make_evidence(
                    source="network_state.routes.metadata.corridor",
                    entity_ids=route_ids,
                    trace_ids=trace_ids[:15] or None,
                    counts={
                        "composite_risk_score": round(composite, 1),
                        "closed_routes": closed,
                        "total_red_attacks": total_attacks,
                    },
                    reasoning_steps=reasoning,
                ),
            }
        )

    findings.sort(key=lambda item: item["metrics"]["composite_risk_score"], reverse=True)
    return findings