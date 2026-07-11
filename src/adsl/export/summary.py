# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Executive summary generator for run export bundles (ADR-009)."""

from __future__ import annotations

from typing import Any


def build_executive_summary(bundle: dict[str, Any], *, key_events_limit: int = 8) -> str:
    """Generate Markdown executive summary from a run bundle."""
    run = bundle["run"]
    scenario = bundle["scenario"]
    stats = bundle["summary_statistics"]
    execution = bundle["execution"]
    ontology = bundle["ontology_payload"]

    lines: list[str] = [
        f"# ADSL Executive Summary — {scenario['name']}",
        "",
        f"**Run ID:** `{run['run_id']}`  ",
        f"**Exported:** {bundle['exported_at']}  ",
        f"**Schema:** {bundle['export_schema_version']}",
        "",
        "## Run Overview",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Status | {run['status']} |",
        f"| Scenario | {run['scenario_id']} |",
        f"| Ticks executed | {execution['ticks_executed']} |",
        f"| Seed | {execution['seed']} |",
        f"| Audit traces | {len(bundle['audit_traces'])} |",
        f"| Simulation events | {len(bundle['simulation_events'])} |",
        f"| Dataset | `{execution['dataset_path']}` |",
        "",
        "## Network State (End of Run)",
        "",
        f"**Nodes:** {stats['node_status_counts']}  ",
        f"**Routes:** {stats['route_status_counts']}  ",
        f"**Destroyed nodes:** {stats['destroyed_node_count']} "
        f"({stats['destroyed_node_fraction']:.1%} of network)",
        "",
        "## Agent Activity",
        "",
        f"- **By side:** {stats['audit_traces_by_side']}",
        f"- **By action:** {stats['audit_traces_by_action']}",
        f"- **By category:** {stats['audit_traces_by_category']}",
        "",
        "## Key Outcomes",
        "",
    ]

    actionable = [
        event
        for event in bundle["simulation_events"]
        if event["event_type"] in {"AGENT_DECISION", "ACTION_RECORDED"}
    ]
    for event in actionable[-key_events_limit:]:
        side = event.get("agent_side") or "-"
        agent = event.get("agent_id") or "-"
        tick = event["simulation_tick"]
        event_type = event["event_type"]
        payload = event.get("payload", {})
        if event_type == "AGENT_DECISION":
            detail = (
                f"{payload.get('action_type')} — {payload.get('action_summary', '')}"
            )
        else:
            detail = (
                f"{payload.get('action_type')} target={payload.get('target_id')} "
                f"applied={payload.get('applied')}"
            )
        lines.append(f"- Tick {tick} | {side} | {agent} | {detail}")

    if not actionable:
        lines.append("- No actionable events recorded.")

    lines.extend(
        [
            "",
            "## Ontology Payload",
            "",
        ]
    )
    for key, items in ontology.items():
        lines.append(f"- `{key}`: {len(items)} objects")

    lines.extend(
        [
            "",
            "## Provenance",
            "",
            f"- Source system: `{bundle['source_system']}`",
            f"- Export schema: `{bundle['export_schema_version']}`",
            f"- Ontology mapping: ADR-006 (offline payload snapshot)",
            "",
        ]
    )

    return "\n".join(lines)