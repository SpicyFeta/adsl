# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for Phase 3 Increment 4 analyst workflows."""

import json
from pathlib import Path

import pytest

from adsl.export.batch import BATCH_SCHEMA_VERSION, batch_export_runs
from adsl.export.bundle import EXPORT_SCHEMA_VERSION
from adsl.export.compare import (
    compare_runs,
    extract_run_metrics,
    format_comparison_table,
)
from adsl.export.runner import RunSpec, apply_red_pacing_overrides, execute_run
from adsl.simulation.loader import load_scenario_package
from adsl.simulation.registry import resolve_scenario_path

SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"


def test_execute_run_produces_valid_bundle() -> None:
    spec = RunSpec(scenario_id="alpine-valley-v3", seed=42, ticks=20, label="test-run")
    _, result = execute_run(spec, synthetic_dir=SYNTHETIC_DIR)

    assert result.bundle["run"]["scenario_id"] == "alpine-valley-v3"
    assert result.bundle["execution"]["seed"] == 42
    assert result.bundle["execution"]["label"] == "test-run"
    assert result.bundle["export_schema_version"] == EXPORT_SCHEMA_VERSION
    assert len(result.bundle["audit_traces"]) > 0


def test_red_pacing_overrides_change_attack_profile() -> None:
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

    fast_attacks = extract_run_metrics(fast_result.bundle)["attack_route_count"]
    slow_attacks = extract_run_metrics(slow_result.bundle)["attack_route_count"]
    slow_no_action = extract_run_metrics(slow_result.bundle)["no_action_count"]
    fast_no_action = extract_run_metrics(fast_result.bundle)["no_action_count"]

    assert fast_attacks >= slow_attacks
    assert slow_no_action >= fast_no_action


def test_apply_red_pacing_overrides_patches_metadata() -> None:
    path = resolve_scenario_path("alpine-valley-v3", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    patched = apply_red_pacing_overrides(
        package,
        {"RED-NORTH-01": {"strike_cooldown_ticks": 5}},
    )
    north = next(
        element for element in patched.red_force_elements if element.element_id == "RED-NORTH-01"
    )
    assert north.metadata["strike_cooldown_ticks"] == 5


def test_compare_runs_same_scenario_produces_deltas() -> None:
    specs = [
        RunSpec(scenario_id="alpine-valley-v3", seed=42, ticks=30, label="seed-42"),
        RunSpec(scenario_id="alpine-valley-v3", seed=99, ticks=30, label="seed-99"),
    ]
    bundles = [execute_run(spec, synthetic_dir=SYNTHETIC_DIR)[1].bundle for spec in specs]

    comparison = compare_runs(bundles)
    assert comparison["same_scenario"] is True
    assert comparison["run_count"] == 2
    assert len(comparison["deltas"]) == 1
    assert "attack_route_count_delta" in comparison["deltas"][0]

    table = format_comparison_table(comparison)
    assert "seed-42" in table
    assert "seed-99" in table


def test_compare_runs_requires_two_bundles() -> None:
    spec = RunSpec(scenario_id="island-chokepoint-v2", seed=42, ticks=10)
    _, result = execute_run(spec, synthetic_dir=SYNTHETIC_DIR)
    with pytest.raises(ValueError, match="at least two"):
        compare_runs([result.bundle])


def test_batch_export_writes_manifest_and_valid_bundles(tmp_path: Path) -> None:
    specs = [
        RunSpec(scenario_id="alpine-valley-v3", seed=42, ticks=15, label="a"),
        RunSpec(scenario_id="alpine-valley-v3", seed=7, ticks=15, label="b"),
    ]
    manifest = batch_export_runs(specs, tmp_path, synthetic_dir=SYNTHETIC_DIR)

    assert manifest["batch_schema_version"] == BATCH_SCHEMA_VERSION
    assert manifest["run_count"] == 2
    assert (tmp_path / "batch_manifest.json").exists()
    assert (tmp_path / "comparison_summary.md").exists()

    for run_entry in manifest["runs"]:
        run_dir = Path(run_entry["export_path"])
        assert (run_dir / "manifest.json").exists()
        assert (run_dir / "run_bundle.json").exists()
        assert (run_dir / "audit_traces.jsonl").exists()
        assert (run_dir / "executive_summary.md").exists()

        bundle = json.loads((run_dir / "run_bundle.json").read_text(encoding="utf-8"))
        assert bundle["export_schema_version"] == EXPORT_SCHEMA_VERSION

    comparison = manifest["comparison"]
    assert comparison is not None
    assert comparison["run_count"] == 2