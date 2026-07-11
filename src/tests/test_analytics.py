# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for Phase 3 analytics and insights (Increments 9 + 13)."""

import json
from pathlib import Path

import pytest

from adsl.analytics import (
    compare_what_if,
    format_insights_markdown,
    format_insights_summary,
    generate_insights_report,
)
from adsl.analytics.bottlenecks import detect_bottlenecks, detect_vulnerabilities
from adsl.analytics.format import format_what_if_markdown
from adsl.analytics.red_patterns import analyze_red_patterns
from adsl.analytics.risk import score_corridor_risks, score_node_risks, score_route_risks
from adsl.export.bundle import export_run_bundle
from adsl.export.runner import RunSpec, execute_run

SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"


@pytest.fixture
def alpine_bundle() -> dict:
    spec = RunSpec(scenario_id="alpine-valley-v3", seed=42, ticks=50, label="analytics-test")
    _, result = execute_run(spec, synthetic_dir=SYNTHETIC_DIR)
    return result.bundle


def test_generate_insights_report_structure(alpine_bundle: dict) -> None:
    report = generate_insights_report(alpine_bundle)

    assert report["schema_version"] == "1.1"
    assert report["run_id"] == alpine_bundle["run"]["run_id"]
    assert report["scenario_id"] == "alpine-valley-v3"
    assert len(report["key_insights"]) >= 1
    assert len(report["structured_insights"]) >= 1
    assert "insight_context" in report
    assert "actionable_recommendations" in report
    assert "bottlenecks" in report["findings"]
    assert "node_risks" in report["findings"]
    assert "corridor_risks" in report["findings"]
    assert "red_patterns" in report["findings"]
    assert "recommended_focus_areas" in report


def test_insights_include_traceable_evidence(alpine_bundle: dict) -> None:
    report = generate_insights_report(alpine_bundle)

    for highlight in report["findings"]["critical_highlights"]:
        assert "evidence" in highlight
        assert "source" in highlight["evidence"]

    for route in report["findings"]["route_risks"]:
        assert route["metrics"]["risk_score"] >= 0
        assert "evidence" in route
        if route["metrics"]["risk_score"] >= 45:
            assert route.get("reasoning_steps")


def test_detect_bottlenecks_finds_chokepoints(alpine_bundle: dict) -> None:
    bottlenecks = detect_bottlenecks(alpine_bundle)
    assert bottlenecks
    assert any(item["metrics"].get("degree", 0) >= 1 for item in bottlenecks)


def test_score_corridor_risks_groups_by_metadata(alpine_bundle: dict) -> None:
    corridors = score_corridor_risks(alpine_bundle)
    corridor_ids = {item["entity_id"] for item in corridors}
    assert "north_ridge" in corridor_ids or "south_ridge" in corridor_ids


def test_analyze_red_patterns_detects_activity(alpine_bundle: dict) -> None:
    analysis = analyze_red_patterns(alpine_bundle)
    assert analysis["metrics"]["red_trace_count"] > 0
    assert analysis["metrics"]["actions_by_type"]["ATTACK_ROUTE"] > 0


def test_compare_what_if_pacing_scenarios() -> None:
    fast = RunSpec(
        scenario_id="alpine-valley-v3",
        seed=42,
        ticks=50,
        label="fast",
        red_pacing_overrides={
            "RED-NORTH-01": {"strike_cooldown_ticks": 1},
            "RED-SOUTH-01": {"strike_cooldown_ticks": 1},
        },
    )
    slow = RunSpec(
        scenario_id="alpine-valley-v3",
        seed=42,
        ticks=50,
        label="slow",
        red_pacing_overrides={
            "RED-NORTH-01": {"strike_cooldown_ticks": 8},
            "RED-SOUTH-01": {"strike_cooldown_ticks": 8},
        },
    )
    _, fast_result = execute_run(fast, synthetic_dir=SYNTHETIC_DIR)
    _, slow_result = execute_run(slow, synthetic_dir=SYNTHETIC_DIR)

    comparison = compare_what_if([fast_result.bundle, slow_result.bundle])
    assert comparison["metric_comparison"]["run_count"] == 2
    assert len(comparison["what_if_deltas"]) == 1
    assert comparison["run_insights"][0]["label"] == "fast"


def test_compare_what_if_requires_two_bundles(alpine_bundle: dict) -> None:
    with pytest.raises(ValueError, match="at least two"):
        compare_what_if([alpine_bundle])


def test_format_insights_markdown_includes_sections(alpine_bundle: dict) -> None:
    report = generate_insights_report(alpine_bundle)
    md = format_insights_markdown(report)
    assert "# ADSL Analytics Insights" in md
    assert "## Executive Summary" in md
    assert "## Provenance" in md


def test_format_insights_summary_is_concise(alpine_bundle: dict) -> None:
    report = generate_insights_report(alpine_bundle)
    summary = format_insights_summary(report)
    assert "Key insights:" in summary
    assert report["run_id"] in summary


def test_format_what_if_markdown() -> None:
    fast = RunSpec("alpine-valley-v3", seed=42, ticks=30, label="a")
    slow = RunSpec("alpine-valley-v3", seed=42, ticks=30, label="b")
    _, a = execute_run(fast, synthetic_dir=SYNTHETIC_DIR)
    _, b = execute_run(slow, synthetic_dir=SYNTHETIC_DIR)
    comparison = compare_what_if([a.bundle, b.bundle])
    md = format_what_if_markdown(comparison)
    assert "# ADSL What-If Comparison" in md


def test_export_includes_insights_files(alpine_bundle: dict, tmp_path: Path) -> None:
    export_dir = export_run_bundle(alpine_bundle, tmp_path)
    insights_json = export_dir / "insights.json"
    insights_md = export_dir / "insights_report.md"

    assert insights_json.exists()
    assert insights_md.exists()
    report = json.loads(insights_json.read_text(encoding="utf-8"))
    assert report["schema_version"] == "1.1"
    assert "key_insights" in report
    assert "structured_insights" in report


def test_score_node_risks_exposes_risk_score(alpine_bundle: dict) -> None:
    node_risks = score_node_risks(alpine_bundle)
    for item in node_risks:
        assert item["insight_type"] == "node_risk"
        assert "risk_score" in item["metrics"]
        assert item["metrics"]["risk_score"] == item["metrics"]["vulnerability_score"]


def test_recommended_focus_areas_have_evidence(alpine_bundle: dict) -> None:
    report = generate_insights_report(alpine_bundle)
    for area in report["recommended_focus_areas"]:
        assert "area" in area
        assert "rationale" in area
        assert "evidence" in area


def test_red_timing_disruption_pattern(alpine_bundle: dict) -> None:
    analysis = analyze_red_patterns(alpine_bundle)
    pattern_ids = {p["pattern_id"] for p in analysis["patterns"]}
    assert analysis["metrics"]["red_trace_count"] > 0
    assert pattern_ids  # at least one pattern detected


def test_structured_insights_have_reasoning(alpine_bundle: dict) -> None:
    report = generate_insights_report(alpine_bundle)
    for item in report["structured_insights"]:
        assert "headline" in item
        assert "severity" in item
        assert "reasoning_steps" in item


def test_actionable_recommendations_are_specific(alpine_bundle: dict) -> None:
    report = generate_insights_report(alpine_bundle)
    for rec in report["actionable_recommendations"]:
        assert "action" in rec
        assert "rationale" in rec
        assert "evidence" in rec
        assert rec["priority"] >= 1


def test_compare_what_if_cross_run_patterns() -> None:
    fast = RunSpec("alpine-valley-v3", seed=42, ticks=50, label="fast")
    slow = RunSpec("alpine-valley-v3", seed=42, ticks=50, label="slow")
    _, a = execute_run(fast, synthetic_dir=SYNTHETIC_DIR)
    _, b = execute_run(slow, synthetic_dir=SYNTHETIC_DIR)
    comparison = compare_what_if([a.bundle, b.bundle])
    assert comparison["schema_version"] == "1.1"
    assert "cross_run_patterns" in comparison
    assert "actionable_recommendations" in comparison
    block = comparison["what_if_deltas"][0]
    assert "comparison_narrative" in block


def test_detect_cross_run_patterns_module(alpine_bundle: dict) -> None:
    from adsl.analytics.cross_run import detect_cross_run_patterns

    report = generate_insights_report(alpine_bundle)
    patterns = detect_cross_run_patterns([report, report])
    assert patterns
    assert patterns[0]["occurrence_count"] == 2


def test_format_includes_recommendations_section(alpine_bundle: dict) -> None:
    report = generate_insights_report(alpine_bundle)
    md = format_insights_markdown(report)
    if report["actionable_recommendations"]:
        assert "## Actionable Recommendations" in md


def test_vulnerabilities_and_route_risks_ranked(alpine_bundle: dict) -> None:
    vulns = detect_vulnerabilities(alpine_bundle)
    risks = score_route_risks(alpine_bundle)
    if len(vulns) >= 2:
        assert (
            vulns[0]["metrics"]["vulnerability_score"]
            >= vulns[1]["metrics"]["vulnerability_score"]
        )
    if len(risks) >= 2:
        assert risks[0]["metrics"]["risk_score"] >= risks[1]["metrics"]["risk_score"]