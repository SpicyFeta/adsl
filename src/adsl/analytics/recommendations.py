# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Actionable analyst recommendations derived from insight reports."""

from __future__ import annotations

from typing import Any

from adsl.analytics.evidence import make_evidence


def _append_unique(
    recommendations: list[dict[str, Any]],
    seen: set[str],
    item: dict[str, Any],
) -> None:
    key = item.get("recommendation_id", "")
    if key in seen:
        return
    seen.add(key)
    recommendations.append(item)


def build_actionable_recommendations(report: dict[str, Any], *, limit: int = 10) -> list[dict[str, Any]]:
    """
    Derive prioritized, specific recommendations from a v1.1 insights report.

    Each recommendation links to evidence and target entities for traceability.
    """
    findings = report.get("findings", {})
    stats = report.get("summary_statistics", {})
    recommendations: list[dict[str, Any]] = []
    seen: set[str] = set()

    destroyed = stats.get("destroyed_node_count", 0)
    if destroyed:
        fraction = stats.get("destroyed_node_fraction", 0.0)
        _append_unique(
            recommendations,
            seen,
            {
                "priority": 1,
                "recommendation_id": "recover-destroyed-nodes",
                "action": (
                    f"Assess recovery options for {destroyed} destroyed node(s) "
                    f"({fraction:.0%} of network) — reroute and reallocate before next stress cycle."
                ),
                "rationale": "End-state network has non-operational nodes limiting throughput.",
                "target_entity_kind": "network",
                "target_entity_id": report.get("scenario_id", "network"),
                "evidence": make_evidence(
                    source="summary_statistics",
                    counts={
                        "destroyed_node_count": destroyed,
                        "destroyed_node_fraction": fraction,
                    },
                ),
            },
        )

    for corridor in findings.get("corridor_risks", [])[:3]:
        metrics = corridor.get("metrics", {})
        composite = metrics.get("composite_risk_score", 0)
        if composite < 40:
            continue
        closed = metrics.get("closed_routes", 0)
        corridor_id = corridor["entity_id"]
        _append_unique(
            recommendations,
            seen,
            {
                "priority": 2 if composite >= 65 else 3,
                "recommendation_id": f"corridor-alternate-{corridor_id}",
                "action": (
                    f"Open a workshop review of alternate paths around corridor '{corridor_id}' "
                    f"— {closed} route(s) closed, composite risk {composite:.0f}/100."
                ),
                "rationale": corridor["summary"],
                "target_entity_kind": "corridor",
                "target_entity_id": corridor_id,
                "evidence": corridor.get("evidence", {}),
                "reasoning_steps": corridor.get("reasoning_steps", []),
            },
        )

    for node in findings.get("node_risks", [])[:2]:
        score = node.get("metrics", {}).get("risk_score", 0)
        if score < 45:
            continue
        node_id = node["entity_id"]
        _append_unique(
            recommendations,
            seen,
            {
                "priority": 3,
                "recommendation_id": f"node-harden-{node_id}",
                "action": (
                    f"Prioritize Blue hardening or reallocation at {node.get('entity_name', node_id)} "
                    f"(risk {score:.0f}/100) — verify adjacent route status before next run."
                ),
                "rationale": node["summary"],
                "target_entity_kind": "node",
                "target_entity_id": node_id,
                "evidence": node.get("evidence", {}),
                "reasoning_steps": node.get("reasoning_steps", []),
            },
        )

    for route in findings.get("route_risks", [])[:2]:
        score = route.get("metrics", {}).get("risk_score", 0)
        attacks = route.get("metrics", {}).get("red_attacks", 0)
        if score < 50 or attacks < 3:
            continue
        route_id = route["entity_id"]
        _append_unique(
            recommendations,
            seen,
            {
                "priority": 3,
                "recommendation_id": f"route-contest-{route_id}",
                "action": (
                    f"Task route security element to harden {route.get('entity_name', route_id)} "
                    f"— {attacks} Red attacks, risk {score:.0f}/100."
                ),
                "rationale": route["summary"],
                "target_entity_kind": "route",
                "target_entity_id": route_id,
                "evidence": route.get("evidence", {}),
                "reasoning_steps": route.get("reasoning_steps", []),
            },
        )

    for pattern in findings.get("red_patterns", []):
        pattern_id = pattern.get("pattern_id")
        if pattern_id == "route_focus":
            target = pattern.get("metrics", {}).get("target_id", "unknown")
            _append_unique(
                recommendations,
                seen,
                {
                    "priority": 2,
                    "recommendation_id": f"red-focus-counter-{target}",
                    "action": (
                        f"Run a what-if with adjusted Red pacing on {target} — "
                        f"Red concentrated {pattern['metrics'].get('share_of_route_attacks', 0):.0%} "
                        "of route attacks here."
                    ),
                    "rationale": pattern["summary"],
                    "target_entity_kind": "route",
                    "target_entity_id": target,
                    "evidence": pattern.get("evidence", {}),
                    "reasoning_steps": pattern.get("reasoning_steps", []),
                },
            )
        elif pattern_id == "sustained_pressure":
            _append_unique(
                recommendations,
                seen,
                {
                    "priority": 2,
                    "recommendation_id": "red-sustained-pressure",
                    "action": (
                        "Compare against a slower Red pacing spec — sustained attack tick rate "
                        "may exhaust Blue adaptation budget within current tick window."
                    ),
                    "rationale": pattern["summary"],
                    "target_entity_kind": "red_pattern",
                    "target_entity_id": pattern_id,
                    "evidence": pattern.get("evidence", {}),
                    "reasoning_steps": pattern.get("reasoning_steps", []),
                },
            )

    for area in report.get("recommended_focus_areas", [])[:2]:
        _append_unique(
            recommendations,
            seen,
            {
                "priority": area.get("priority", 4),
                "recommendation_id": f"focus-{area['entity_kind']}-{area['entity_id']}",
                "action": f"Workshop focus: {area['area']} — {area['rationale']}",
                "rationale": "Derived from ranked focus area analysis.",
                "target_entity_kind": area.get("entity_kind", "unknown"),
                "target_entity_id": area["entity_id"],
                "evidence": area.get("evidence", {}),
            },
        )

    recommendations.sort(key=lambda item: item["priority"])
    return recommendations[:limit]