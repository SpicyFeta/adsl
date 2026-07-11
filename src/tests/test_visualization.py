# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for Phase 3 visualization layer."""

import json
from pathlib import Path

from adsl.export.runner import load_run_bundle_from_export
from adsl.viz.discovery import discover_runs
from adsl.export.runner import RunSpec, execute_run
from adsl.viz.compare import build_viz_comparison
from adsl.viz.transform import VIZ_SCHEMA_VERSION, build_viz_payload

SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"

EXPORTS_DIR = Path(__file__).resolve().parents[2] / "exports"


def _first_export_dir() -> Path:
    for child in EXPORTS_DIR.iterdir():
        if child.is_dir() and (child / "run_bundle.json").exists():
            return child
    raise FileNotFoundError("No export directory with run_bundle.json found")


def test_build_viz_payload_from_export() -> None:
    export_dir = _first_export_dir()
    bundle = load_run_bundle_from_export(export_dir)
    payload = build_viz_payload(bundle)

    assert payload["schema_version"] == VIZ_SCHEMA_VERSION
    assert payload["run_id"] == bundle["run"]["run_id"]
    assert len(payload["nodes"]) == len(bundle["network_state"]["nodes"])
    assert len(payload["routes"]) == len(bundle["network_state"]["routes"])
    assert "metrics" in payload
    assert "red_activity" in payload
    assert payload["bounds"]["min_lat"] <= payload["bounds"]["max_lat"]


def test_viz_nodes_have_status_colors() -> None:
    export_dir = _first_export_dir()
    bundle = load_run_bundle_from_export(export_dir)
    payload = build_viz_payload(bundle)

    for node in payload["nodes"]:
        assert "color" in node
        assert node["status"] in {"OPERATIONAL", "DEGRADED", "DESTROYED"}
        assert "is_bottleneck" in node


def test_viz_routes_distinguish_status() -> None:
    export_dir = _first_export_dir()
    bundle = load_run_bundle_from_export(export_dir)
    payload = build_viz_payload(bundle)

    statuses = {route["status"] for route in payload["routes"]}
    assert statuses.issubset({"OPEN", "CONTESTED", "CLOSED"})
    for route in payload["routes"]:
        assert "color" in route
        assert route["is_contested"] == (route["status"] == "CONTESTED")


def test_discover_runs_finds_exports() -> None:
    if not EXPORTS_DIR.exists():
        return
    runs = discover_runs(EXPORTS_DIR)
    assert len(runs) >= 1
    assert "run_id" in runs[0]
    assert "scenario_id" in runs[0]


def test_viz_payload_includes_analytics_overlay() -> None:
    export_dir = _first_export_dir()
    bundle = load_run_bundle_from_export(export_dir)
    payload = build_viz_payload(bundle)

    assert "analytics_overlay" in payload
    assert "recommended_focus_areas" in payload["analytics_overlay"]
    assert "top_route_risks" in payload["analytics_overlay"]

    for node in payload["nodes"]:
        assert "risk_score" in node
        assert "risk_severity" in node
        assert "is_focus_area" in node

    for route in payload["routes"]:
        assert "risk_score" in route
        assert "risk_severity" in route


def test_build_viz_comparison_detects_deltas() -> None:
    fast = RunSpec(
        scenario_id="alpine-valley-v3",
        seed=42,
        ticks=30,
        label="fast",
        red_pacing_overrides={
            "RED-NORTH-01": {"strike_cooldown_ticks": 1},
            "RED-SOUTH-01": {"strike_cooldown_ticks": 1},
        },
    )
    slow = RunSpec(
        scenario_id="alpine-valley-v3",
        seed=42,
        ticks=30,
        label="slow",
        red_pacing_overrides={
            "RED-NORTH-01": {"strike_cooldown_ticks": 8},
            "RED-SOUTH-01": {"strike_cooldown_ticks": 8},
        },
    )
    _, fast_result = execute_run(fast, synthetic_dir=SYNTHETIC_DIR)
    _, slow_result = execute_run(slow, synthetic_dir=SYNTHETIC_DIR)

    comparison = build_viz_comparison(fast_result.bundle, slow_result.bundle)
    assert comparison["schema_version"] == VIZ_SCHEMA_VERSION
    assert "metric_deltas" in comparison
    assert "node_diffs" in comparison
    assert "route_diffs" in comparison
    assert comparison["baseline"]["run_id"] == fast_result.bundle["run"]["run_id"]


def test_red_activity_aggregated_from_traces() -> None:
    export_dir = _first_export_dir()
    bundle = load_run_bundle_from_export(export_dir)
    payload = build_viz_payload(bundle)

    assert "by_action" in payload["red_activity"]
    assert payload["metrics"]["attack_route_count"] >= 0