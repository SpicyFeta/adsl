# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Formatters for analytics insight reports."""

from __future__ import annotations

from typing import Any


def format_insights_summary(report: dict[str, Any]) -> str:
    """Render a short plain-text summary of key insights."""
    lines = [
        f"ADSL Insights — {report['scenario_id']} (seed {report['seed']})",
        f"Run: {report['run_id']}",
        "",
        "Key insights:",
    ]
    for index, insight in enumerate(report["key_insights"], start=1):
        lines.append(f"  {index}. {insight}")

    highlights = report["findings"]["critical_highlights"]
    if highlights:
        lines.extend(["", "Critical highlights:"])
        for item in highlights:
            lines.append(f"  • [{item['severity']}] {item['summary']}")

    focus = report.get("recommended_focus_areas", [])
    if focus:
        lines.extend(["", "Recommended focus areas:"])
        for item in focus:
            action = item.get("recommended_action")
            suffix = f" → {action}" if action else ""
            lines.append(f"  → {item['area']}: {item['rationale']}{suffix}")

    recs = report.get("actionable_recommendations", [])
    if recs:
        lines.extend(["", "Top recommendations:"])
        for item in recs[:5]:
            lines.append(f"  [{item['priority']}] {item['action']}")

    return "\n".join(lines)


def _format_finding_section(title: str, findings: list[dict[str, Any]]) -> list[str]:
    if not findings:
        return [f"## {title}", "", "_None detected._", ""]
    lines = [f"## {title}", ""]
    for item in findings:
        lines.append(f"### {item.get('entity_name', item.get('entity_id'))} — {item['severity']}")
        lines.append("")
        lines.append(item["summary"])
        metrics = item.get("metrics", {})
        if metrics:
            metric_str = ", ".join(f"{key}={value}" for key, value in metrics.items())
            lines.append(f"- Metrics: {metric_str}")
        evidence = item.get("evidence", {})
        if evidence.get("trace_ids"):
            lines.append(f"- Trace IDs: `{', '.join(evidence['trace_ids'][:3])}` …")
        if evidence.get("entity_ids"):
            lines.append(f"- Entities: `{', '.join(evidence['entity_ids'])}`")
        reasoning = item.get("reasoning_steps") or evidence.get("reasoning_steps")
        if reasoning:
            lines.append("- Reasoning:")
            for step in reasoning[:4]:
                lines.append(f"  - {step}")
        if item.get("recommendation"):
            lines.append(f"- **Action:** {item['recommendation']}")
        lines.append("")
    return lines


def format_insights_markdown(report: dict[str, Any]) -> str:
    """Render a full Markdown insight report with evidence references."""
    lines = [
        f"# ADSL Analytics Insights — {report['scenario_id']}",
        "",
        f"**Run ID:** `{report['run_id']}`  ",
        f"**Seed:** {report['seed']}  ",
        f"**Ticks:** {report['ticks_executed']}  ",
        f"**Schema:** {report['schema_version']}",
        "",
        "## Executive Summary",
        "",
    ]
    for insight in report["key_insights"]:
        lines.append(f"- {insight}")

    focus = report.get("recommended_focus_areas", [])
    if focus:
        lines.extend(["", "## Recommended Focus Areas", ""])
        for item in focus:
            action = item.get("recommended_action")
            action_text = f" *Action: {action}*" if action else ""
            lines.append(f"- **{item['area']}** — {item['rationale']}{action_text}")

    structured = report.get("structured_insights", [])
    if structured:
        lines.extend(["", "## Structured Insights", ""])
        for item in structured[:6]:
            lines.append(f"### {item['headline']} ({item['severity']})")
            lines.append("")
            if item.get("action"):
                lines.append(f"**Recommended action:** {item['action']}")
            for step in item.get("reasoning_steps", [])[:4]:
                lines.append(f"- {step}")
            lines.append("")

    recs = report.get("actionable_recommendations", [])
    if recs:
        lines.extend(["", "## Actionable Recommendations", ""])
        for item in recs:
            lines.append(
                f"{item['priority']}. **{item['action']}** — {item.get('rationale', '')}"
            )

    context = report.get("insight_context")
    if context:
        lines.extend(
            [
                "",
                "## Run Context",
                "",
                f"- Nodes: {context['network_size']['node_count']} | "
                f"Routes: {context['network_size']['route_count']}",
                f"- Red traces: {context['activity']['red_trace_count']}",
                f"- Destroyed node fraction: {context['end_state'].get('destroyed_node_fraction', 0):.0%}",
                "",
            ]
        )

    lines.extend(
        [
            "",
            "## Red Behavior",
            "",
            report["red_behavior_summary"],
            "",
            f"Metrics: `{report['red_behavior_metrics']}`",
            "",
        ]
    )

    findings = report["findings"]
    lines.extend(_format_finding_section("Critical Highlights", findings["critical_highlights"]))
    lines.extend(_format_finding_section("Bottlenecks", findings["bottlenecks"]))
    lines.extend(_format_finding_section("Vulnerabilities", findings["vulnerabilities"]))
    lines.extend(_format_finding_section("Node Risk", findings.get("node_risks", [])))
    lines.extend(_format_finding_section("Route Risk", findings["route_risks"]))
    lines.extend(_format_finding_section("Corridor Risk", findings["corridor_risks"]))
    lines.extend(_format_finding_section("Red Patterns", findings["red_patterns"]))

    lines.extend(
        [
            "## Provenance",
            "",
            f"- Source audit traces: {report['generated_from']['audit_trace_count']}",
            f"- Export schema: `{report['generated_from']['export_schema_version']}`",
            "- All findings include `evidence` blocks traceable to raw bundle data.",
            "",
        ]
    )
    return "\n".join(lines)


def format_what_if_markdown(comparison: dict[str, Any]) -> str:
    """Render what-if comparison as Markdown."""
    metric = comparison["metric_comparison"]
    lines = [
        "# ADSL What-If Comparison",
        "",
        f"**Runs:** {metric['run_count']} | **Same scenario:** {metric['same_scenario']}",
        "",
        "## Metric Comparison",
        "",
        "| Label | Destroyed | ATTACK_ROUTE | NO_ACTION | CLOSED |",
        "|-------|-----------|--------------|-----------|--------|",
    ]

    for row in metric["metrics"]:
        label = row.get("label") or row["run_id"][:12]
        lines.append(
            f"| {label} | {row['destroyed_node_count']} | "
            f"{row['attack_route_count']} | {row['no_action_count']} | "
            f"{row['closed_route_count']} |"
        )

    for block in comparison["what_if_deltas"]:
        lines.extend(
            [
                "",
                f"## What-If: {block['compare_label']} vs {block['baseline_label']}",
                "",
            ]
        )
        if block.get("comparison_narrative"):
            lines.append(block["comparison_narrative"])
            lines.append("")
        if not block["insight_deltas"]:
            lines.append("_No significant insight-level changes detected._")
        else:
            for change in block["insight_deltas"]:
                action = f" → {change['action']}" if change.get("action") else ""
                lines.append(f"- **{change['change_type']}:** {change['summary']}{action}")

    cross_run = comparison.get("cross_run_patterns", [])
    if cross_run:
        lines.extend(["", "## Cross-Run Patterns", ""])
        for pattern in cross_run:
            lines.append(
                f"- **{pattern['pattern_id']}** ({pattern['occurrence_count']}/"
                f"{pattern['run_count']} runs): {pattern['summary']}"
            )

    structured = comparison.get("actionable_recommendations", [])
    if structured:
        lines.extend(["", "## Structured Recommendations", ""])
        for item in structured:
            lines.append(f"- [{item['priority']}] {item['action']}")

    if comparison["recommendations"]:
        lines.extend(["", "## Recommendations", ""])
        for rec in comparison["recommendations"]:
            lines.append(f"- {rec}")

    return "\n".join(lines)