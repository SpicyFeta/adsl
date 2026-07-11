# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Automated insight report generation from ADR-009 run bundles."""

from __future__ import annotations

from typing import Any

from adsl.analytics.bottlenecks import detect_bottlenecks, detect_vulnerabilities
from adsl.analytics.recommendations import build_actionable_recommendations
from adsl.analytics.red_patterns import analyze_red_patterns
from adsl.analytics.risk import score_corridor_risks, score_node_risks, score_route_risks

INSIGHTS_SCHEMA_VERSION = "1.1"


def _build_critical_highlights(
    *,
    bottlenecks: list[dict[str, Any]],
    vulnerabilities: list[dict[str, Any]],
    route_risks: list[dict[str, Any]],
    corridor_risks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    candidates.extend(bottlenecks)
    candidates.extend(vulnerabilities)
    candidates.extend(route_risks)
    candidates.extend(corridor_risks)

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    candidates.sort(
        key=lambda item: (
            severity_rank.get(item.get("severity", "low"), 9),
            -(
                item.get("metrics", {}).get("vulnerability_score")
                or item.get("metrics", {}).get("risk_score")
                or item.get("metrics", {}).get("composite_risk_score")
                or 0
            ),
        )
    )

    seen: set[str] = set()
    highlights: list[dict[str, Any]] = []
    for item in candidates:
        key = f"{item.get('entity_kind')}:{item.get('entity_id')}"
        if key in seen:
            continue
        seen.add(key)
        if item.get("severity") in {"critical", "high"}:
            highlights.append(item)
        if len(highlights) >= 6:
            break
    return highlights


def _build_structured_insights(
    *,
    stats: dict[str, Any],
    critical_highlights: list[dict[str, Any]],
    corridor_risks: list[dict[str, Any]],
    red_analysis: dict[str, Any],
    scenario_id: str,
) -> list[dict[str, Any]]:
    """Rich insight objects with reasoning, evidence, and recommended actions."""
    structured: list[dict[str, Any]] = []

    destroyed = stats.get("destroyed_node_count", 0)
    if destroyed:
        fraction = stats.get("destroyed_node_fraction", 0.0)
        structured.append(
            {
                "insight_id": "network-destruction",
                "category": "network_state",
                "severity": "critical" if fraction >= 0.3 else "high",
                "headline": f"{destroyed} nodes destroyed ({fraction:.0%} of network)",
                "detail": "End-state network has non-operational nodes limiting throughput.",
                "action": "Prioritize recovery corridors and reallocation before extending tick count.",
                "reasoning_steps": [
                    f"summary_statistics.destroyed_node_count = {destroyed}",
                    f"destroyed_node_fraction = {fraction:.2f}",
                ],
                "evidence": {
                    "source": "summary_statistics",
                    "counts": {
                        "destroyed_node_count": destroyed,
                        "destroyed_node_fraction": fraction,
                    },
                },
                "related_entities": [{"kind": "scenario", "id": scenario_id}],
            }
        )

    closed = stats.get("route_status_counts", {}).get("CLOSED", 0)
    if closed:
        structured.append(
            {
                "insight_id": "routes-closed",
                "category": "network_state",
                "severity": "high" if closed >= 3 else "medium",
                "headline": f"{closed} routes closed at run end",
                "detail": "Closed routes may block primary logistics paths.",
                "action": "Review Blue reroute traces and validate alternate OPEN paths.",
                "reasoning_steps": [
                    f"summary_statistics.route_status_counts.CLOSED = {closed}",
                ],
                "evidence": {
                    "source": "summary_statistics",
                    "counts": {"closed_routes": closed},
                },
                "related_entities": [],
            }
        )

    for corridor in corridor_risks[:2]:
        composite = corridor.get("metrics", {}).get("composite_risk_score", 0)
        if composite < 35:
            continue
        structured.append(
            {
                "insight_id": f"corridor-{corridor['entity_id']}",
                "category": "corridor_risk",
                "severity": corridor.get("severity", "medium"),
                "headline": corridor["summary"],
                "detail": corridor.get("recommendation") or corridor["summary"],
                "action": corridor.get("recommendation"),
                "reasoning_steps": corridor.get("reasoning_steps", []),
                "evidence": corridor.get("evidence", {}),
                "related_entities": [
                    {"kind": "corridor", "id": corridor["entity_id"]},
                ],
            }
        )

    for highlight in critical_highlights[:3]:
        structured.append(
            {
                "insight_id": f"{highlight.get('insight_type', 'finding')}-{highlight['entity_id']}",
                "category": highlight.get("insight_type", "finding"),
                "severity": highlight.get("severity", "medium"),
                "headline": highlight["summary"],
                "detail": highlight.get("recommendation") or highlight["summary"],
                "action": highlight.get("recommendation"),
                "reasoning_steps": highlight.get("reasoning_steps", []),
                "evidence": highlight.get("evidence", {}),
                "related_entities": [
                    {
                        "kind": highlight.get("entity_kind", "unknown"),
                        "id": highlight["entity_id"],
                    }
                ],
            }
        )

    for pattern in red_analysis.get("patterns", [])[:2]:
        structured.append(
            {
                "insight_id": f"red-{pattern.get('pattern_id', 'pattern')}",
                "category": "red_pattern",
                "severity": pattern.get("severity", "medium"),
                "headline": pattern["summary"],
                "detail": pattern["summary"],
                "action": (
                    f"Compare against alternate Red pacing — pattern '{pattern.get('pattern_id')}' "
                    "may shift under different cooldown/budget settings."
                ),
                "reasoning_steps": pattern.get("reasoning_steps", []),
                "evidence": pattern.get("evidence", {}),
                "related_entities": [
                    {
                        "kind": "red_pattern",
                        "id": pattern.get("pattern_id", "unknown"),
                    }
                ],
            }
        )

    if not structured:
        structured.append(
            {
                "insight_id": "stable-network",
                "category": "network_state",
                "severity": "low",
                "headline": "Network remained largely operational with limited Red pressure",
                "detail": "No critical corridor or node risks exceeded reporting thresholds.",
                "action": "Consider longer tick count or faster Red pacing for stress comparison.",
                "reasoning_steps": ["No critical/high findings in ranked vulnerability or corridor lists."],
                "evidence": {"source": "analytics.thresholds"},
                "related_entities": [],
            }
        )

    return structured[:10]


def _structured_to_key_insights(structured: list[dict[str, Any]]) -> list[str]:
    """Backward-compatible string bullets from structured insights."""
    return [item["headline"] for item in structured[:8]]


def _build_insight_context(bundle: dict[str, Any], stats: dict[str, Any]) -> dict[str, Any]:
    nodes = bundle["network_state"]["nodes"]
    routes = bundle["network_state"]["routes"]
    red_traces = sum(1 for t in bundle["audit_traces"] if t.get("agent_side") == "RED")
    return {
        "scenario_id": bundle["run"]["scenario_id"],
        "ticks_executed": bundle["execution"]["ticks_executed"],
        "seed": bundle["execution"]["seed"],
        "network_size": {
            "node_count": len(nodes),
            "route_count": len(routes),
        },
        "end_state": {
            "node_status_counts": stats.get("node_status_counts", {}),
            "route_status_counts": stats.get("route_status_counts", {}),
            "destroyed_node_fraction": stats.get("destroyed_node_fraction", 0.0),
        },
        "activity": {
            "audit_trace_count": len(bundle["audit_traces"]),
            "red_trace_count": red_traces,
            "event_count": len(bundle["simulation_events"]),
        },
    }


def _build_recommended_focus_areas(
    *,
    critical_highlights: list[dict[str, Any]],
    corridor_risks: list[dict[str, Any]],
    node_risks: list[dict[str, Any]],
    red_analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    """Derive analyst focus areas from ranked findings."""
    areas: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _append(
        *,
        priority: int,
        area: str,
        entity_kind: str,
        entity_id: str,
        rationale: str,
        evidence: dict[str, Any],
        action: str | None = None,
    ) -> None:
        key = f"{entity_kind}:{entity_id}"
        if key in seen:
            return
        seen.add(key)
        areas.append(
            {
                "priority": priority,
                "area": area,
                "entity_kind": entity_kind,
                "entity_id": entity_id,
                "rationale": rationale,
                "recommended_action": action,
                "evidence": evidence,
            }
        )

    for highlight in critical_highlights[:3]:
        _append(
            priority=1,
            area=highlight.get("entity_name", highlight["entity_id"]),
            entity_kind=highlight.get("entity_kind", "unknown"),
            entity_id=highlight["entity_id"],
            rationale=highlight["summary"],
            evidence=highlight.get("evidence", {}),
            action=highlight.get("recommendation"),
        )

    for corridor in corridor_risks[:2]:
        if corridor["metrics"]["composite_risk_score"] >= 40:
            _append(
                priority=2,
                area=corridor.get("entity_name", corridor["entity_id"]),
                entity_kind="corridor",
                entity_id=corridor["entity_id"],
                rationale=f"Elevated corridor risk — {corridor['summary']}",
                evidence=corridor.get("evidence", {}),
                action=corridor.get("recommendation"),
            )

    for node in node_risks[:2]:
        if node["metrics"]["risk_score"] >= 45:
            _append(
                priority=3,
                area=node.get("entity_name", node["entity_id"]),
                entity_kind="node",
                entity_id=node["entity_id"],
                rationale=f"High-exposure node — {node['summary']}",
                evidence=node.get("evidence", {}),
                action=node.get("recommendation"),
            )

    for pattern in red_analysis.get("patterns", []):
        if pattern.get("pattern_id") in {"disruption_zone_timing", "route_focus"}:
            metrics = pattern.get("metrics", {})
            entity_id = metrics.get("corridor") or metrics.get("target_id", "red-activity")
            _append(
                priority=4,
                area=str(entity_id).replace("_", " ").title(),
                entity_kind="red_pattern",
                entity_id=str(entity_id),
                rationale=pattern["summary"],
                evidence=pattern.get("evidence", {}),
                action=(
                    f"Run what-if pacing study targeting {entity_id}."
                ),
            )

    areas.sort(key=lambda item: item["priority"])
    return areas[:6]


def generate_insights_report(bundle: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a complete, explainable insights report from an ADR-009 run bundle.

    Schema v1.1 adds structured_insights, actionable_recommendations, insight_context,
    and reasoning_steps on findings. ``key_insights`` remains for backward compatibility.
    """
    run = bundle["run"]
    execution = bundle["execution"]
    stats = bundle["summary_statistics"]

    bottlenecks = detect_bottlenecks(bundle)
    vulnerabilities = detect_vulnerabilities(bundle)
    node_risks = score_node_risks(bundle)
    route_risks = score_route_risks(bundle)
    corridor_risks = score_corridor_risks(bundle)
    red_analysis = analyze_red_patterns(bundle)

    critical_highlights = _build_critical_highlights(
        bottlenecks=bottlenecks,
        vulnerabilities=vulnerabilities,
        route_risks=route_risks,
        corridor_risks=corridor_risks,
    )

    structured_insights = _build_structured_insights(
        stats=stats,
        critical_highlights=critical_highlights,
        corridor_risks=corridor_risks,
        red_analysis=red_analysis,
        scenario_id=run["scenario_id"],
    )
    key_insights = _structured_to_key_insights(structured_insights)

    recommended_focus_areas = _build_recommended_focus_areas(
        critical_highlights=critical_highlights,
        corridor_risks=corridor_risks,
        node_risks=node_risks,
        red_analysis=red_analysis,
    )

    partial_report = {
        "findings": {
            "bottlenecks": bottlenecks,
            "vulnerabilities": vulnerabilities,
            "node_risks": node_risks,
            "route_risks": route_risks,
            "corridor_risks": corridor_risks,
            "red_patterns": red_analysis["patterns"],
            "critical_highlights": critical_highlights,
        },
        "recommended_focus_areas": recommended_focus_areas,
        "summary_statistics": stats,
        "scenario_id": run["scenario_id"],
        "run_id": run["run_id"],
    }
    actionable_recommendations = build_actionable_recommendations(partial_report)

    return {
        "schema_version": INSIGHTS_SCHEMA_VERSION,
        "run_id": run["run_id"],
        "scenario_id": run["scenario_id"],
        "label": execution.get("label"),
        "seed": execution["seed"],
        "ticks_executed": execution["ticks_executed"],
        "generated_from": {
            "export_schema_version": bundle.get("export_schema_version"),
            "audit_trace_count": len(bundle["audit_traces"]),
            "event_count": len(bundle["simulation_events"]),
            "analytics_module": "adsl.analytics",
        },
        "insight_context": _build_insight_context(bundle, stats),
        "key_insights": key_insights,
        "structured_insights": structured_insights,
        "actionable_recommendations": actionable_recommendations,
        "recommended_focus_areas": recommended_focus_areas,
        "findings": partial_report["findings"],
        "red_behavior_summary": red_analysis["summary"],
        "red_behavior_metrics": red_analysis["metrics"],
        "summary_statistics": stats,
    }