# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Run export bundle builder (ADR-009)."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adsl.analytics import generate_insights_report
from adsl.analytics.format import format_insights_markdown
from adsl.collaboration.annotations import load_annotations, save_annotations
from adsl.export.summary import build_executive_summary
from adsl.models import (
    ADSL_AuditTrace,
    ADSL_LogisticsNode,
    ADSL_LogisticsRoute,
    ADSL_Scenario,
    ADSL_ScenarioPackage,
    ADSL_SimulationRun,
    SimulationEvent,
)
from adsl.ontology.integration import build_run_sync_payload

EXPORT_SCHEMA_VERSION = "1.0"
SOURCE_SYSTEM = "ADSL_PHASE2"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compute_summary_statistics(
    *,
    audit_traces: list[ADSL_AuditTrace],
    nodes: list[ADSL_LogisticsNode],
    routes: list[ADSL_LogisticsRoute],
) -> dict[str, Any]:
    return {
        "audit_traces_by_side": dict(Counter(t.agent_side.value for t in audit_traces)),
        "audit_traces_by_action": dict(Counter(t.action_type.value for t in audit_traces)),
        "audit_traces_by_category": dict(
            Counter(t.decision_category.value for t in audit_traces)
        ),
        "node_status_counts": dict(Counter(n.status.value for n in nodes)),
        "route_status_counts": dict(Counter(r.status.value for r in routes)),
        "destroyed_node_count": sum(
            1 for node in nodes if node.status.value == "DESTROYED"
        ),
        "destroyed_node_fraction": (
            sum(1 for node in nodes if node.status.value == "DESTROYED") / len(nodes)
            if nodes
            else 0.0
        ),
    }


def build_run_bundle(
    *,
    run: ADSL_SimulationRun,
    scenario: ADSL_Scenario,
    nodes: list[ADSL_LogisticsNode],
    routes: list[ADSL_LogisticsRoute],
    audit_traces: list[ADSL_AuditTrace],
    events: list[SimulationEvent],
    scenario_package: ADSL_ScenarioPackage,
    dataset_path: str | Path,
    ticks_executed: int,
) -> dict[str, Any]:
    """Build the complete run bundle dict per ADR-009."""
    exported_at = _utc_now_iso()
    ontology_payload = build_run_sync_payload(
        run=run,
        nodes=nodes,
        routes=routes,
        audit_traces=audit_traces,
        events=events,
        scenario_package=scenario_package,
    )
    summary_statistics = _compute_summary_statistics(
        audit_traces=audit_traces,
        nodes=nodes,
        routes=routes,
    )

    return {
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "source_system": SOURCE_SYSTEM,
        "exported_at": exported_at,
        "run": run.model_dump(mode="json"),
        "scenario": scenario.model_dump(mode="json"),
        "execution": {
            "ticks_executed": ticks_executed,
            "seed": run.seed,
            "dataset_path": str(dataset_path),
        },
        "network_state": {
            "nodes": [node.model_dump(mode="json") for node in nodes],
            "routes": [route.model_dump(mode="json") for route in routes],
        },
        "audit_traces": [trace.model_dump(mode="json") for trace in audit_traces],
        "simulation_events": [event.model_dump(mode="json") for event in events],
        "ontology_payload": ontology_payload,
        "summary_statistics": summary_statistics,
    }


def export_run_bundle(
    bundle: dict[str, Any],
    export_dir: str | Path,
) -> Path:
    """
    Write export bundle files to {export_dir}/{run_id}/ per ADR-009.

    Returns the run-specific export directory path.
    """
    run_id = bundle["run"]["run_id"]
    run_export_dir = Path(export_dir) / run_id
    run_export_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "source_system": SOURCE_SYSTEM,
        "exported_at": bundle["exported_at"],
        "run_id": run_id,
        "scenario_id": bundle["run"]["scenario_id"],
        "files": {
            "run_bundle": "run_bundle.json",
            "audit_traces": "audit_traces.jsonl",
            "simulation_events": "simulation_events.jsonl",
            "executive_summary": "executive_summary.md",
            "insights": "insights.json",
            "insights_report": "insights_report.md",
            "annotations": "annotations.json",
        },
    }

    (run_export_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    (run_export_dir / "run_bundle.json").write_text(
        json.dumps(bundle, indent=2),
        encoding="utf-8",
    )

    with (run_export_dir / "audit_traces.jsonl").open("w", encoding="utf-8") as handle:
        for trace in bundle["audit_traces"]:
            handle.write(json.dumps(trace))
            handle.write("\n")

    with (run_export_dir / "simulation_events.jsonl").open("w", encoding="utf-8") as handle:
        for event in bundle["simulation_events"]:
            handle.write(json.dumps(event))
            handle.write("\n")

    summary_md = build_executive_summary(bundle)
    (run_export_dir / "executive_summary.md").write_text(summary_md, encoding="utf-8")

    insights_report = generate_insights_report(bundle)
    (run_export_dir / "insights.json").write_text(
        json.dumps(insights_report, indent=2),
        encoding="utf-8",
    )
    (run_export_dir / "insights_report.md").write_text(
        format_insights_markdown(insights_report),
        encoding="utf-8",
    )

    annotations_doc = load_annotations(run_export_dir)
    save_annotations(annotations_doc, export_run_dir=run_export_dir)

    return run_export_dir