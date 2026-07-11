# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for Phase 3 Increment 10 scale and performance."""

import json
from pathlib import Path

import pytest

from adsl.export.batch import batch_export_runs
from adsl.export.runner import RunSpec, execute_run
from adsl.performance.benchmark import (
    benchmark_run,
    check_regression,
    load_baselines,
)
from adsl.performance.config import DEFAULT_MAX_TICKS, SCALE_MAX_TICKS
from adsl.performance.network_index import NetworkIndex
from adsl.simulation.engine import SimulationEngine
from adsl.simulation.loader import load_scenario_package
from adsl.simulation.registry import resolve_scenario_path

SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"
BASELINES_PATH = Path(__file__).resolve().parents[2] / "data" / "performance" / "baselines.json"


def test_scale_scenario_loads() -> None:
    path = resolve_scenario_path("continental-grid-scale-v4", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    assert package.scenario.scenario_id == "continental-grid-scale-v4"
    assert len(package.scenario.nodes) >= 15
    assert len(package.red_force_elements) >= 6
    assert len(package.blue_force_elements) >= 9


def test_scale_mode_allows_extended_ticks() -> None:
    package = load_scenario_package(
        resolve_scenario_path("continental-mega-scale-v5", synthetic_dir=SYNTHETIC_DIR)
    )
    engine = SimulationEngine(max_ticks=300, seed=42, quiet_logs=True, scale_mode=True)
    run = engine.run_scenario(package)
    assert run.status.value == "COMPLETED"
    assert run.current_tick == 299


def test_default_mode_rejects_ticks_above_cap() -> None:
    with pytest.raises(ValueError, match=str(DEFAULT_MAX_TICKS)):
        SimulationEngine(max_ticks=DEFAULT_MAX_TICKS + 1)


def test_scale_mode_rejects_ticks_above_scale_cap() -> None:
    with pytest.raises(ValueError, match=str(SCALE_MAX_TICKS)):
        SimulationEngine(max_ticks=SCALE_MAX_TICKS + 1, scale_mode=True)


def test_network_index_lookup() -> None:
    path = resolve_scenario_path("alpine-valley-v3", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    index = NetworkIndex(package.scenario.nodes, package.scenario.routes)
    node = package.scenario.nodes[0]
    route = package.scenario.routes[0]
    assert index.get_node(node.node_id) is node
    assert index.get_route(route.route_id) is route
    assert index.get_node("missing") is None


def test_benchmark_run_returns_metrics() -> None:
    spec = RunSpec(scenario_id="island-chokepoint-v2", seed=42, ticks=20)
    result = benchmark_run(spec, synthetic_dir=SYNTHETIC_DIR)
    assert result.scenario_id == "island-chokepoint-v2"
    assert result.ticks == 20
    assert result.elapsed_seconds > 0
    assert result.ticks_per_second > 0
    assert result.audit_trace_count > 0


def test_regression_check_uses_baselines() -> None:
    baselines = load_baselines(BASELINES_PATH)
    spec = RunSpec(scenario_id="alpine-valley-v3", seed=42, ticks=100)
    result = benchmark_run(spec, synthetic_dir=SYNTHETIC_DIR)
    violations = check_regression(result, baselines, factor=100.0)
    assert violations == []


def test_parallel_batch_export(tmp_path: Path) -> None:
    specs = [
        RunSpec(scenario_id="island-chokepoint-v2", seed=42, ticks=5, label="a"),
        RunSpec(scenario_id="island-chokepoint-v2", seed=43, ticks=5, label="b"),
    ]
    manifest = batch_export_runs(
        specs,
        tmp_path,
        synthetic_dir=SYNTHETIC_DIR,
        workers=2,
        quiet_logs=True,
    )
    assert manifest["run_count"] == 2
    assert manifest.get("parallel_workers") == 2
    assert (tmp_path / "batch_manifest.json").exists()
    for run_entry in manifest["runs"]:
        export_path = Path(run_entry["export_path"])
        assert (export_path / "run_bundle.json").exists()


def test_optimized_engine_preserves_determinism() -> None:
    spec = RunSpec(scenario_id="alpine-valley-v3", seed=7, ticks=30)
    _, first = execute_run(spec, synthetic_dir=SYNTHETIC_DIR)
    _, second = execute_run(spec, synthetic_dir=SYNTHETIC_DIR)
    assert first.bundle["summary_statistics"] == second.bundle["summary_statistics"]


def test_mega_scale_scenario_loads() -> None:
    path = resolve_scenario_path("continental-mega-scale-v5", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    assert package.scenario.scenario_id == "continental-mega-scale-v5"
    assert len(package.scenario.nodes) >= 30
    agent_count = len(package.red_force_elements) + len(package.blue_force_elements)
    assert agent_count >= 30


def test_registry_includes_scale_scenarios() -> None:
    assert (
        resolve_scenario_path("continental-grid-scale-v4", synthetic_dir=SYNTHETIC_DIR).name
        == "logistics_scenario_scale.json"
    )
    assert (
        resolve_scenario_path("continental-mega-scale-v5", synthetic_dir=SYNTHETIC_DIR).name
        == "logistics_scenario_mega.json"
    )


def test_baselines_file_schema() -> None:
    data = json.loads(BASELINES_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert "benchmarks" in data
    assert len(data["benchmarks"]) >= 4


def test_before_after_comparison_file() -> None:
    path = Path(__file__).resolve().parents[2] / "data" / "performance" / "before_after.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    mega = next(
        row for row in data["comparisons"] if row["scenario_id"] == "continental-mega-scale-v5"
    )
    assert mega["after_inc16_engine"]["audit_traces"] == 7200


def test_observation_cache_reuse_with_dirty_invalidation() -> None:
    from adsl.simulation.observation_cache import build_side_observation_cache
    from adsl.models import AgentSide

    path = resolve_scenario_path("alpine-valley-v3", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    engine = SimulationEngine(max_ticks=5, seed=42, quiet_logs=True)
    engine._initialize_run(package.scenario)
    engine._initialize_state(package)
    engine._initialize_agents(package)

    cache_a = build_side_observation_cache(AgentSide.RED, engine._nodes, engine._routes)
    cache_b = build_side_observation_cache(AgentSide.RED, engine._nodes, engine._routes)
    assert cache_a.visible_nodes is not cache_b.visible_nodes
    assert cache_a.nodes_by_id == cache_b.nodes_by_id


def test_network_index_open_alternates() -> None:
    path = resolve_scenario_path("alpine-valley-v3", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    index = NetworkIndex(package.scenario.nodes, package.scenario.routes)
    route = package.scenario.routes[0]
    alternates = index.open_alternates_for_route(route)
    assert all(item.route_id != route.route_id for item in alternates)


def test_benchmark_engine_only_mode() -> None:
    from adsl.performance.benchmark import benchmark_engine_run

    spec = RunSpec(scenario_id="island-chokepoint-v2", seed=42, ticks=20)
    result = benchmark_engine_run(spec, synthetic_dir=SYNTHETIC_DIR)
    assert result.elapsed_seconds > 0
    assert result.audit_trace_count > 0


def test_profile_run_returns_hotspots() -> None:
    from adsl.performance.profiler import profile_run

    spec = RunSpec(scenario_id="island-chokepoint-v2", seed=42, ticks=10)
    report = profile_run(spec, synthetic_dir=SYNTHETIC_DIR)
    assert report.elapsed_seconds > 0
    assert report.hotspot_summary.startswith("Primary hotspots:")