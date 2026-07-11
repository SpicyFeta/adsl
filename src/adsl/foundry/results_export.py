# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Export simulation results to Foundry datasets (ADR-011)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adsl.foundry.client import FoundryClient, get_foundry_client
from adsl.foundry.lineage import build_lineage_metadata
from adsl.models import ADSL_ScenarioPackage

DATASET_SCHEMA_VERSION = "1.0"
RECORD_TYPE_ANNOTATIONS = "adsl_annotations"
RECORD_TYPE_INSIGHTS = "adsl_insights"


def _run_record(bundle: dict[str, Any], lineage: dict[str, Any]) -> dict[str, Any]:
    run = bundle["run"]
    stats = bundle["summary_statistics"]
    return {
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "record_type": "adsl_simulation_run",
        "run_id": run["run_id"],
        "scenario_id": run["scenario_id"],
        "lineage": lineage,
        "payload": {
            "run": run,
            "execution": bundle["execution"],
            "summary_statistics": stats,
            "export_schema_version": bundle["export_schema_version"],
        },
    }


def _network_record(bundle: dict[str, Any], lineage: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "record_type": "adsl_network_snapshot",
        "run_id": bundle["run"]["run_id"],
        "lineage": lineage,
        "payload": bundle["network_state"],
    }


def _trace_records(bundle: dict[str, Any], lineage: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for trace in bundle["audit_traces"]:
        trace_lineage = {
            **lineage,
            "trace_id": trace["trace_id"],
            "operation": "audit_trace_export",
        }
        records.append(
            {
                "dataset_schema_version": DATASET_SCHEMA_VERSION,
                "record_type": "adsl_audit_trace",
                "run_id": bundle["run"]["run_id"],
                "trace_id": trace["trace_id"],
                "lineage": trace_lineage,
                "payload": trace,
            }
        )
    return records


def _optional_export_artifacts(
    export_dir: Path | None,
    bundle: dict[str, Any],
    lineage: dict[str, Any],
) -> list[dict[str, Any]]:
    """Include annotations and insights from an ADR-009 export directory when present."""
    if export_dir is None or not export_dir.is_dir():
        return []

    records: list[dict[str, Any]] = []
    run_id = bundle["run"]["run_id"]

    annotations_path = export_dir / "annotations.json"
    if annotations_path.exists():
        annotations_doc = json.loads(annotations_path.read_text(encoding="utf-8"))
        records.append(
            {
                "dataset_schema_version": DATASET_SCHEMA_VERSION,
                "record_type": RECORD_TYPE_ANNOTATIONS,
                "run_id": run_id,
                "lineage": {**lineage, "operation": "annotations_export"},
                "payload": annotations_doc,
            }
        )

    insights_path = export_dir / "insights.json"
    if insights_path.exists():
        insights_doc = json.loads(insights_path.read_text(encoding="utf-8"))
        records.append(
            {
                "dataset_schema_version": DATASET_SCHEMA_VERSION,
                "record_type": RECORD_TYPE_INSIGHTS,
                "run_id": run_id,
                "lineage": {**lineage, "operation": "insights_export"},
                "payload": insights_doc,
            }
        )

    return records


def build_foundry_export_records(
    bundle: dict[str, Any],
    *,
    parent_dataset_rid: str | None = None,
    scenario_package: ADSL_ScenarioPackage | None = None,
    export_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Build Foundry dataset records from an ADR-009 run bundle."""
    run_id = bundle["run"]["run_id"]
    scenario_id = bundle["run"]["scenario_id"]
    lineage = build_lineage_metadata(
        operation="simulation_export",
        parent_dataset_rid=parent_dataset_rid,
        parent_run_id=run_id,
        scenario_id=scenario_id,
        extra={
            "audit_trace_count": len(bundle["audit_traces"]),
            "event_count": len(bundle["simulation_events"]),
        },
    )

    records: list[dict[str, Any]] = [
        _run_record(bundle, lineage),
        _network_record(bundle, lineage),
    ]
    records.extend(_trace_records(bundle, lineage))
    records.extend(_optional_export_artifacts(export_dir, bundle, lineage))

    records.append(
        {
            "dataset_schema_version": DATASET_SCHEMA_VERSION,
            "record_type": "adsl_lineage",
            "run_id": run_id,
            "lineage": lineage,
            "payload": {
                "scenario_id": scenario_id,
                "source_system": lineage["source_system"],
                "operation": lineage["operation"],
                "recorded_at": lineage["recorded_at"],
            },
        }
    )
    return records


def export_run_to_foundry_dataset(
    bundle: dict[str, Any],
    *,
    dataset_rid: str | None = None,
    client: FoundryClient | None = None,
    append: bool = True,
    export_dir: Path | None = None,
) -> dict[str, Any]:
    """Write simulation results to a Foundry dataset with lineage."""
    foundry = client or get_foundry_client()
    records = build_foundry_export_records(
        bundle,
        parent_dataset_rid=dataset_rid or foundry.config.results_dataset_rid,
        export_dir=export_dir,
    )
    write_result = foundry.write_dataset_records(
        records,
        dataset_rid,
        append=append,
    )

    ontology_rids: list[str] = []
    if foundry.config.ontology_sync_enabled and foundry.config.is_live_ready():
        from adsl.ontology.integration import build_run_sync_payload, write_ontology_objects

        payload = build_run_sync_payload(
            run=_bundle_to_run(bundle),
            nodes=_bundle_nodes(bundle),
            routes=_bundle_routes(bundle),
            audit_traces=_bundle_traces(bundle),
            events=_bundle_events(bundle),
        )
        all_payloads: list[dict[str, Any]] = []
        for key in ("bootstrap", "simulation_run", "logistics_nodes", "logistics_routes"):
            all_payloads.extend(payload[key])
        all_payloads.extend(payload["audit_traces"])
        all_payloads.extend(payload["simulation_events"])
        ontology_rids = write_ontology_objects(all_payloads)

    return {
        "dataset_write": write_result,
        "records_exported": len(records),
        "audit_traces_exported": sum(
            1 for record in records if record["record_type"] == "adsl_audit_trace"
        ),
        "annotations_exported": sum(
            1 for record in records if record["record_type"] == RECORD_TYPE_ANNOTATIONS
        ),
        "insights_exported": sum(
            1 for record in records if record["record_type"] == RECORD_TYPE_INSIGHTS
        ),
        "lineage_id": records[-1]["lineage"]["lineage_id"],
        "ontology_objects_written": len(ontology_rids),
        "ontology_rids": ontology_rids,
    }


def _bundle_to_run(bundle: dict[str, Any]):
    from adsl.models import ADSL_SimulationRun

    return ADSL_SimulationRun.model_validate(bundle["run"])


def _bundle_nodes(bundle: dict[str, Any]):
    from adsl.models import ADSL_LogisticsNode

    return [ADSL_LogisticsNode.model_validate(node) for node in bundle["network_state"]["nodes"]]


def _bundle_routes(bundle: dict[str, Any]):
    from adsl.models import ADSL_LogisticsRoute

    return [ADSL_LogisticsRoute.model_validate(route) for route in bundle["network_state"]["routes"]]


def _bundle_traces(bundle: dict[str, Any]):
    from adsl.models import ADSL_AuditTrace

    return [ADSL_AuditTrace.model_validate(trace) for trace in bundle["audit_traces"]]


def _bundle_events(bundle: dict[str, Any]):
    from adsl.models import SimulationEvent

    return [SimulationEvent.model_validate(event) for event in bundle["simulation_events"]]