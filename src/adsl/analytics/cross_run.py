# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Cross-run pattern detection across multiple simulation runs."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from adsl.analytics.evidence import make_evidence


_RECURRING_THRESHOLDS = {
    "bottleneck": 0.5,
    "vulnerability": 45.0,
    "node_risk": 45.0,
    "route_risk": 45.0,
    "corridor_risk": 40.0,
    "critical_highlight": 0.0,
}


def _entity_key(kind: str, entity_id: str) -> str:
    return f"{kind}:{entity_id}"


def _collect_entities_from_report(
    report: dict[str, Any],
    *,
    run_label: str,
) -> dict[str, dict[str, Any]]:
    """Map entity keys to occurrence metadata for one run's insights."""
    entities: dict[str, dict[str, Any]] = {}
    findings = report.get("findings", {})

    for item in findings.get("bottlenecks", []):
        key = _entity_key("node", item["entity_id"])
        entities[key] = {
            "entity_kind": "node",
            "entity_id": item["entity_id"],
            "entity_name": item.get("entity_name", item["entity_id"]),
            "insight_types": ["bottleneck"],
            "severity": item.get("severity", "medium"),
            "summary": item["summary"],
            "evidence": item.get("evidence"),
            "run_label": run_label,
        }

    for item in findings.get("vulnerabilities", []):
        score = item.get("metrics", {}).get("vulnerability_score", 0)
        if score < _RECURRING_THRESHOLDS["vulnerability"]:
            continue
        key = _entity_key("node", item["entity_id"])
        entry = entities.setdefault(
            key,
            {
                "entity_kind": "node",
                "entity_id": item["entity_id"],
                "entity_name": item.get("entity_name", item["entity_id"]),
                "insight_types": [],
                "severity": item.get("severity"),
                "summary": item["summary"],
                "evidence": item.get("evidence"),
                "run_label": run_label,
            },
        )
        entry["insight_types"].append("vulnerability")

    for item in findings.get("node_risks", []):
        score = item.get("metrics", {}).get("risk_score", 0)
        if score < _RECURRING_THRESHOLDS["node_risk"]:
            continue
        key = _entity_key("node", item["entity_id"])
        entry = entities.setdefault(
            key,
            {
                "entity_kind": "node",
                "entity_id": item["entity_id"],
                "entity_name": item.get("entity_name", item["entity_id"]),
                "insight_types": [],
                "severity": item.get("severity"),
                "summary": item["summary"],
                "evidence": item.get("evidence"),
                "run_label": run_label,
            },
        )
        entry["insight_types"].append("node_risk")

    for item in findings.get("route_risks", []):
        score = item.get("metrics", {}).get("risk_score", 0)
        if score < _RECURRING_THRESHOLDS["route_risk"]:
            continue
        key = _entity_key("route", item["entity_id"])
        entities[key] = {
            "entity_kind": "route",
            "entity_id": item["entity_id"],
            "entity_name": item.get("entity_name", item["entity_id"]),
            "insight_types": ["route_risk"],
            "severity": item.get("severity"),
            "summary": item["summary"],
            "evidence": item.get("evidence"),
            "run_label": run_label,
        }

    for item in findings.get("corridor_risks", []):
        score = item.get("metrics", {}).get("composite_risk_score", 0)
        if score < _RECURRING_THRESHOLDS["corridor_risk"]:
            continue
        key = _entity_key("corridor", item["entity_id"])
        entities[key] = {
            "entity_kind": "corridor",
            "entity_id": item["entity_id"],
            "entity_name": item.get("entity_name", item["entity_id"]),
            "insight_types": ["corridor_risk"],
            "severity": item.get("severity"),
            "summary": item["summary"],
            "evidence": item.get("evidence"),
            "run_label": run_label,
        }

    for item in findings.get("critical_highlights", []):
        kind = item.get("entity_kind", "unknown")
        key = _entity_key(kind, item["entity_id"])
        entities[key] = {
            "entity_kind": kind,
            "entity_id": item["entity_id"],
            "entity_name": item.get("entity_name", item["entity_id"]),
            "insight_types": ["critical_highlight"],
            "severity": item.get("severity"),
            "summary": item["summary"],
            "evidence": item.get("evidence"),
            "run_label": run_label,
        }

    return entities


def detect_cross_run_patterns(
    reports: list[dict[str, Any]],
    *,
    min_occurrence_ratio: float = 0.5,
) -> list[dict[str, Any]]:
    """
    Identify entities flagged as risks or bottlenecks across multiple runs.

    ``min_occurrence_ratio`` defaults to 0.5 — entity must appear in at least
    half of compared runs (minimum 2 runs required).
    """
    if len(reports) < 2:
        return []

    occurrence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for report in reports:
        label = report.get("label") or report.get("run_id", "run")
        for key, meta in _collect_entities_from_report(report, run_label=label).items():
            occurrence[key].append(meta)

    min_count = max(2, int(len(reports) * min_occurrence_ratio + 0.999))
    patterns: list[dict[str, Any]] = []

    for key, hits in sorted(occurrence.items()):
        if len(hits) < min_count:
            continue
        first = hits[0]
        insight_types = sorted({t for hit in hits for t in hit.get("insight_types", [])})
        run_labels = [hit["run_label"] for hit in hits]
        pattern_id = "recurring_risk" if "critical_highlight" in insight_types else "recurring_exposure"

        if "bottleneck" in insight_types:
            pattern_id = "recurring_bottleneck"

        patterns.append(
            {
                "pattern_id": pattern_id,
                "entity_kind": first["entity_kind"],
                "entity_id": first["entity_id"],
                "entity_name": first.get("entity_name", first["entity_id"]),
                "occurrence_count": len(hits),
                "run_count": len(reports),
                "run_labels": run_labels,
                "insight_types": insight_types,
                "severity": max(
                    (hit.get("severity", "low") for hit in hits),
                    key=lambda s: {"critical": 3, "high": 2, "medium": 1, "low": 0}.get(s, 0),
                ),
                "summary": (
                    f"{first.get('entity_name', first['entity_id'])} flagged in "
                    f"{len(hits)}/{len(reports)} runs "
                    f"({', '.join(insight_types)}) — persistent analyst attention warranted."
                ),
                "evidence": make_evidence(
                    source="cross_run.insights",
                    entity_ids=[first["entity_id"]],
                    details={
                        "run_labels": run_labels,
                        "insight_types": insight_types,
                        "sample_summaries": [hit["summary"] for hit in hits[:3]],
                    },
                ),
            }
        )

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    patterns.sort(
        key=lambda item: (
            severity_rank.get(item.get("severity", "low"), 9),
            -item["occurrence_count"],
        )
    )
    return patterns