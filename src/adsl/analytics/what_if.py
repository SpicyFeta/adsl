# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""What-if comparison between multiple simulation runs."""

from __future__ import annotations

from typing import Any

from adsl.analytics.cross_run import detect_cross_run_patterns
from adsl.analytics.evidence import make_evidence
from adsl.analytics.report import generate_insights_report
from adsl.export.compare import compare_runs, extract_run_metrics

WHAT_IF_SCHEMA_VERSION = "1.1"


def _entity_risk_lookup(
    report: dict[str, Any],
    *,
    kind: str,
    score_key: str,
    findings_key: str,
) -> dict[str, float]:
    return {
        item["entity_id"]: item.get("metrics", {}).get(score_key, 0.0)
        for item in report["findings"].get(findings_key, [])
        if item.get("entity_kind") == kind or findings_key != "node_risks"
    }


def _insight_delta(
    baseline_report: dict[str, Any],
    compare_report: dict[str, Any],
) -> list[dict[str, Any]]:
    """Compare key insight dimensions between two runs with entity-level risk deltas."""
    deltas: list[dict[str, Any]] = []

    baseline_critical = {
        item["entity_id"]: item
        for item in baseline_report["findings"]["critical_highlights"]
    }
    compare_critical = {
        item["entity_id"]: item
        for item in compare_report["findings"]["critical_highlights"]
    }

    new_risks = set(compare_critical) - set(baseline_critical)
    resolved_risks = set(baseline_critical) - set(compare_critical)

    for entity_id in sorted(new_risks):
        item = compare_critical[entity_id]
        deltas.append(
            {
                "change_type": "new_risk",
                "entity_id": entity_id,
                "entity_kind": item.get("entity_kind"),
                "severity": item.get("severity"),
                "summary": f"New critical highlight: {item['summary']}",
                "action": item.get("recommendation"),
                "reasoning_steps": item.get("reasoning_steps", []),
                "evidence": item.get("evidence"),
            }
        )

    for entity_id in sorted(resolved_risks):
        item = baseline_critical[entity_id]
        deltas.append(
            {
                "change_type": "resolved_risk",
                "entity_id": entity_id,
                "entity_kind": item.get("entity_kind"),
                "severity": "low",
                "summary": f"No longer critical vs baseline: {item['summary']}",
                "action": "Confirm mitigation holds if pacing or seed changes.",
                "reasoning_steps": [
                    "Entity present in baseline critical_highlights but absent in compare run.",
                ],
                "evidence": item.get("evidence"),
            }
        )

    baseline_corridors = _entity_risk_lookup(
        baseline_report, kind="corridor", score_key="composite_risk_score", findings_key="corridor_risks"
    )
    compare_corridors = _entity_risk_lookup(
        compare_report, kind="corridor", score_key="composite_risk_score", findings_key="corridor_risks"
    )

    for corridor_id in sorted(set(baseline_corridors) | set(compare_corridors)):
        base_score = baseline_corridors.get(corridor_id, 0.0)
        compare_score = compare_corridors.get(corridor_id, 0.0)
        delta = compare_score - base_score
        if abs(delta) < 5.0:
            continue
        direction = "increased" if delta > 0 else "decreased"
        action = (
            f"Investigate Red pacing or Blue hardening on corridor '{corridor_id}' — "
            f"risk {direction} {abs(delta):.0f} points."
            if delta > 0
            else f"Corridor '{corridor_id}' improved — validate whether change is durable across seeds."
        )
        deltas.append(
            {
                "change_type": "corridor_risk_shift",
                "entity_id": corridor_id,
                "entity_kind": "corridor",
                "severity": "high" if abs(delta) >= 15 else "medium",
                "summary": (
                    f"Corridor '{corridor_id}' risk {direction} by {abs(delta):.1f} points "
                    f"({base_score:.1f} → {compare_score:.1f})."
                ),
                "action": action,
                "reasoning_steps": [
                    f"Baseline composite_risk_score: {base_score:.1f}",
                    f"Compare composite_risk_score: {compare_score:.1f}",
                    f"Delta: {delta:+.1f}",
                ],
                "metrics": {
                    "baseline_score": base_score,
                    "compare_score": compare_score,
                    "delta": round(delta, 1),
                },
                "evidence": make_evidence(
                    source="insights.corridor_risks",
                    entity_ids=[corridor_id],
                    counts={
                        "baseline_score": base_score,
                        "compare_score": compare_score,
                        "delta": round(delta, 1),
                    },
                    reasoning_steps=[
                        f"Baseline composite_risk_score: {base_score:.1f}",
                        f"Compare composite_risk_score: {compare_score:.1f}",
                    ],
                ),
            }
        )

    baseline_nodes = _entity_risk_lookup(
        baseline_report, kind="node", score_key="risk_score", findings_key="node_risks"
    )
    compare_nodes = _entity_risk_lookup(
        compare_report, kind="node", score_key="risk_score", findings_key="node_risks"
    )
    for node_id in sorted(set(baseline_nodes) | set(compare_nodes)):
        base_score = baseline_nodes.get(node_id, 0.0)
        compare_score = compare_nodes.get(node_id, 0.0)
        delta = compare_score - base_score
        if abs(delta) < 8.0:
            continue
        direction = "increased" if delta > 0 else "decreased"
        deltas.append(
            {
                "change_type": "node_risk_shift",
                "entity_id": node_id,
                "entity_kind": "node",
                "severity": "high" if abs(delta) >= 20 else "medium",
                "summary": (
                    f"Node '{node_id}' risk {direction} by {abs(delta):.1f} points "
                    f"({base_score:.1f} → {compare_score:.1f})."
                ),
                "action": (
                    f"Review Red node targeting and Blue reallocation at {node_id}."
                    if delta > 0
                    else f"Node {node_id} exposure reduced — document effective Blue response."
                ),
                "metrics": {
                    "baseline_score": base_score,
                    "compare_score": compare_score,
                    "delta": round(delta, 1),
                },
                "evidence": make_evidence(
                    source="insights.node_risks",
                    entity_ids=[node_id],
                    counts={"baseline_score": base_score, "compare_score": compare_score},
                ),
            }
        )

    baseline_patterns = {
        p["pattern_id"]: p for p in baseline_report["findings"].get("red_patterns", [])
    }
    compare_patterns = {
        p["pattern_id"]: p for p in compare_report["findings"].get("red_patterns", [])
    }
    for pattern_id in sorted(set(baseline_patterns) | set(compare_patterns)):
        if pattern_id in baseline_patterns and pattern_id in compare_patterns:
            continue
        if pattern_id in compare_patterns:
            pattern = compare_patterns[pattern_id]
            deltas.append(
                {
                    "change_type": "new_red_pattern",
                    "entity_id": pattern_id,
                    "entity_kind": "red_pattern",
                    "severity": pattern.get("severity", "medium"),
                    "summary": f"New Red pattern vs baseline: {pattern['summary']}",
                    "action": "Run additional seeds to confirm pattern stability.",
                    "evidence": pattern.get("evidence"),
                }
            )
        else:
            pattern = baseline_patterns[pattern_id]
            deltas.append(
                {
                    "change_type": "absent_red_pattern",
                    "entity_id": pattern_id,
                    "entity_kind": "red_pattern",
                    "severity": "low",
                    "summary": f"Red pattern no longer detected vs baseline: {pattern['summary']}",
                    "evidence": pattern.get("evidence"),
                }
            )

    return deltas


def _build_comparison_narrative(
    *,
    baseline_label: str,
    compare_label: str,
    insight_deltas: list[dict[str, Any]],
    metric_comparison: dict[str, Any],
) -> str:
    if not insight_deltas:
        return (
            f"Comparing '{compare_label}' to baseline '{baseline_label}': "
            "no significant insight-level shifts detected (thresholds: corridor ±5, node ±8)."
        )

    increases = [d for d in insight_deltas if d.get("metrics", {}).get("delta", 0) > 0]
    new_risks = [d for d in insight_deltas if d["change_type"] == "new_risk"]
    parts = [
        f"'{compare_label}' vs baseline '{baseline_label}': "
        f"{len(insight_deltas)} insight-level change(s)."
    ]
    if new_risks:
        parts.append(f"{len(new_risks)} new critical highlight(s).")
    if increases:
        parts.append(f"{len(increases)} entity risk score increase(s).")

    baseline_metrics = metric_comparison["metrics"][0]
    compare_metrics = metric_comparison["metrics"][1]
    attack_delta = compare_metrics.get("attack_route_count", 0) - baseline_metrics.get(
        "attack_route_count", 0
    )
    if attack_delta:
        parts.append(f"Red ATTACK_ROUTE count changed by {attack_delta:+d}.")
    return " ".join(parts)


def _structured_recommendations(
    what_if_deltas: list[dict[str, Any]],
    *,
    baseline_label: str,
    compare_label: str,
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    priority = 1
    for change in what_if_deltas:
        action = change.get("action")
        if not action:
            continue
        if change["change_type"] in {"corridor_risk_shift", "node_risk_shift", "new_risk"}:
            metrics = change.get("metrics", {})
            if change["change_type"] == "corridor_risk_shift" and metrics.get("delta", 0) <= 5:
                continue
            recommendations.append(
                {
                    "priority": priority,
                    "recommendation_id": f"whatif-{change['change_type']}-{change['entity_id']}",
                    "action": action,
                    "rationale": change["summary"],
                    "target_entity_kind": change.get("entity_kind"),
                    "target_entity_id": change["entity_id"],
                    "compare_context": f"{compare_label} vs {baseline_label}",
                    "evidence": change.get("evidence", {}),
                    "reasoning_steps": change.get("reasoning_steps", []),
                }
            )
            priority += 1
        if priority > 8:
            break
    return recommendations


def compare_what_if(
    bundles: list[dict[str, Any]],
    *,
    baseline_index: int = 0,
) -> dict[str, Any]:
    """
    Compare multiple runs with metric deltas, insight-level what-if analysis,
    cross-run recurring patterns, and structured recommendations.

    The first bundle (or ``baseline_index``) is the baseline for deltas.
    """
    if len(bundles) < 2:
        raise ValueError("compare_what_if requires at least two run bundles")
    if baseline_index < 0 or baseline_index >= len(bundles):
        raise ValueError(f"baseline_index {baseline_index} out of range")

    metric_comparison = compare_runs(bundles)
    reports = [generate_insights_report(bundle) for bundle in bundles]
    baseline_report = reports[baseline_index]
    cross_run_patterns = detect_cross_run_patterns(reports)

    what_if_deltas: list[dict[str, Any]] = []
    baseline_label = (
        metric_comparison["metrics"][baseline_index].get("label")
        or metric_comparison["metrics"][baseline_index]["run_id"]
    )

    all_structured_recommendations: list[dict[str, Any]] = []

    for index, report in enumerate(reports):
        if index == baseline_index:
            continue
        compare_label = (
            metric_comparison["metrics"][index].get("label")
            or metric_comparison["metrics"][index]["run_id"]
        )
        insight_deltas = _insight_delta(baseline_report, report)
        narrative = _build_comparison_narrative(
            baseline_label=baseline_label,
            compare_label=compare_label,
            insight_deltas=insight_deltas,
            metric_comparison={
                "metrics": [
                    metric_comparison["metrics"][baseline_index],
                    metric_comparison["metrics"][index],
                ]
            },
        )
        structured_recs = _structured_recommendations(
            insight_deltas,
            baseline_label=baseline_label,
            compare_label=compare_label,
        )
        all_structured_recommendations.extend(structured_recs)

        block = {
            "baseline_label": baseline_label,
            "compare_label": compare_label,
            "baseline_run_id": baseline_report["run_id"],
            "compare_run_id": report["run_id"],
            "comparison_narrative": narrative,
            "insight_deltas": insight_deltas,
            "key_insight_changes": [d["summary"] for d in insight_deltas[:8]],
            "structured_recommendations": structured_recs,
        }
        what_if_deltas.append(block)

    recommendations: list[str] = []
    for rec in all_structured_recommendations[:8]:
        recommendations.append(rec["action"])
    for pattern in cross_run_patterns[:3]:
        recommendations.append(
            f"Persistent pattern: {pattern['summary']}"
        )

    return {
        "schema_version": WHAT_IF_SCHEMA_VERSION,
        "baseline_index": baseline_index,
        "metric_comparison": metric_comparison,
        "run_insights": [
            {
                "run_id": report["run_id"],
                "label": report.get("label"),
                "scenario_id": report.get("scenario_id"),
                "key_insights": report["key_insights"],
                "structured_insights": report.get("structured_insights", [])[:5],
                "critical_count": len(report["findings"]["critical_highlights"]),
                "recommendation_count": len(report.get("actionable_recommendations", [])),
            }
            for report in reports
        ],
        "what_if_deltas": what_if_deltas,
        "cross_run_patterns": cross_run_patterns,
        "recommendations": recommendations[:10],
        "actionable_recommendations": all_structured_recommendations[:10],
    }