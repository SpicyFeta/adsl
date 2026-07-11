# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Multi-run comparison utilities for analyst workflows."""

from __future__ import annotations

from typing import Any


def extract_run_metrics(bundle: dict[str, Any]) -> dict[str, Any]:
    """Extract comparable metrics from an ADR-009 run bundle."""
    run = bundle["run"]
    stats = bundle["summary_statistics"]
    execution = bundle["execution"]
    by_action = stats.get("audit_traces_by_action", {})

    return {
        "run_id": run["run_id"],
        "label": execution.get("label"),
        "scenario_id": run["scenario_id"],
        "seed": execution["seed"],
        "ticks_executed": execution["ticks_executed"],
        "status": run["status"],
        "audit_trace_count": len(bundle["audit_traces"]),
        "event_count": len(bundle["simulation_events"]),
        "destroyed_node_count": stats["destroyed_node_count"],
        "destroyed_node_fraction": stats["destroyed_node_fraction"],
        "node_status_counts": stats["node_status_counts"],
        "route_status_counts": stats["route_status_counts"],
        "closed_route_count": stats["route_status_counts"].get("CLOSED", 0),
        "attack_route_count": by_action.get("ATTACK_ROUTE", 0),
        "no_action_count": by_action.get("NO_ACTION", 0),
        "harden_count": by_action.get("HARDEN", 0),
        "reroute_count": by_action.get("REROUTE", 0),
        "red_pacing_overrides": execution.get("red_pacing_overrides"),
    }


def compare_runs(bundles: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare two or more run bundles and produce a structured summary."""
    if len(bundles) < 2:
        raise ValueError("compare_runs requires at least two run bundles")

    metrics = [extract_run_metrics(bundle) for bundle in bundles]
    scenario_ids = {m["scenario_id"] for m in metrics}
    same_scenario = len(scenario_ids) == 1

    deltas: list[dict[str, Any]] = []
    if same_scenario:
        baseline = metrics[0]
        for other in metrics[1:]:
            deltas.append(
                {
                    "baseline_label": baseline.get("label") or baseline["run_id"],
                    "compare_label": other.get("label") or other["run_id"],
                    "destroyed_node_count_delta": (
                        other["destroyed_node_count"] - baseline["destroyed_node_count"]
                    ),
                    "attack_route_count_delta": (
                        other["attack_route_count"] - baseline["attack_route_count"]
                    ),
                    "no_action_count_delta": (
                        other["no_action_count"] - baseline["no_action_count"]
                    ),
                    "closed_route_count_delta": (
                        other["closed_route_count"] - baseline["closed_route_count"]
                    ),
                }
            )

    return {
        "run_count": len(metrics),
        "same_scenario": same_scenario,
        "scenario_ids": sorted(scenario_ids),
        "metrics": metrics,
        "deltas": deltas,
    }


def format_comparison_table(comparison: dict[str, Any]) -> str:
    """Render a human-readable comparison table for terminal output."""
    lines = [
        "ADSL Multi-Run Comparison",
        "=" * 72,
        f"Runs: {comparison['run_count']} | Same scenario: {comparison['same_scenario']}",
        "",
        f"{'Label':<20} {'Scenario':<22} {'Seed':>5} {'Destroyed':>10} "
        f"{'AtkRoute':>9} {'NoAction':>9} {'ClosedRt':>9}",
        "-" * 72,
    ]

    for metric in comparison["metrics"]:
        label = metric.get("label") or metric["run_id"][:18]
        lines.append(
            f"{label:<20} {metric['scenario_id']:<22} {metric['seed']:>5} "
            f"{metric['destroyed_node_count']:>10} "
            f"{metric['attack_route_count']:>9} "
            f"{metric['no_action_count']:>9} "
            f"{metric['closed_route_count']:>9}"
        )

    if comparison["deltas"]:
        lines.extend(["", "Deltas (vs first run):", "-" * 72])
        for delta in comparison["deltas"]:
            lines.append(
                f"  {delta['compare_label']} vs {delta['baseline_label']}: "
                f"destroyed {delta['destroyed_node_count_delta']:+d}, "
                f"ATTACK_ROUTE {delta['attack_route_count_delta']:+d}, "
                f"NO_ACTION {delta['no_action_count_delta']:+d}, "
                f"CLOSED routes {delta['closed_route_count_delta']:+d}"
            )

    return "\n".join(lines)


def format_comparison_markdown(comparison: dict[str, Any]) -> str:
    """Render comparison as Markdown for batch manifests and reports."""
    lines = [
        "# ADSL Multi-Run Comparison",
        "",
        f"**Runs compared:** {comparison['run_count']}  ",
        f"**Same scenario:** {comparison['same_scenario']}  ",
        f"**Scenarios:** {', '.join(comparison['scenario_ids'])}",
        "",
        "## Run Metrics",
        "",
        "| Label | Scenario | Seed | Destroyed | ATTACK_ROUTE | NO_ACTION | CLOSED routes |",
        "|-------|----------|------|-----------|--------------|-----------|---------------|",
    ]

    for metric in comparison["metrics"]:
        label = metric.get("label") or metric["run_id"][:12]
        lines.append(
            f"| {label} | {metric['scenario_id']} | {metric['seed']} | "
            f"{metric['destroyed_node_count']} | {metric['attack_route_count']} | "
            f"{metric['no_action_count']} | {metric['closed_route_count']} |"
        )

    if comparison["deltas"]:
        lines.extend(
            [
                "",
                "## Deltas (vs first run)",
                "",
                "| Compare | Baseline | Δ Destroyed | Δ ATTACK_ROUTE | Δ NO_ACTION | Δ CLOSED |",
                "|---------|----------|-------------|----------------|-------------|----------|",
            ]
        )
        for delta in comparison["deltas"]:
            lines.append(
                f"| {delta['compare_label']} | {delta['baseline_label']} | "
                f"{delta['destroyed_node_count_delta']:+d} | "
                f"{delta['attack_route_count_delta']:+d} | "
                f"{delta['no_action_count_delta']:+d} | "
                f"{delta['closed_route_count_delta']:+d} |"
            )

    return "\n".join(lines)