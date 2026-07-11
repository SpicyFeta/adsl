# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for run export bundle (ADR-009)."""

import json
from pathlib import Path

from adsl.export.bundle import EXPORT_SCHEMA_VERSION, build_run_bundle, export_run_bundle
from adsl.simulation.engine import SimulationEngine
from adsl.simulation.loader import load_scenario_package
from adsl.simulation.registry import resolve_scenario_path

SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"


def test_build_run_bundle_contains_required_keys(tmp_path: Path) -> None:
    dataset = resolve_scenario_path("kessari-strait-v1", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(dataset)
    engine = SimulationEngine(max_ticks=2, seed=7, quiet_logs=True)
    run = engine.run_scenario(package)

    bundle = build_run_bundle(
        run=run,
        scenario=package.scenario,
        nodes=engine.nodes,
        routes=engine.routes,
        audit_traces=engine.audit_traces,
        events=engine.events,
        scenario_package=package,
        dataset_path=dataset,
        ticks_executed=run.current_tick + 1,
    )

    required_keys = {
        "export_schema_version",
        "source_system",
        "exported_at",
        "run",
        "scenario",
        "execution",
        "network_state",
        "audit_traces",
        "simulation_events",
        "ontology_payload",
        "summary_statistics",
    }
    assert required_keys.issubset(bundle.keys())
    assert bundle["export_schema_version"] == EXPORT_SCHEMA_VERSION
    assert bundle["ontology_payload"]["audit_traces"]
    assert bundle["network_state"]["nodes"]
    assert bundle["network_state"]["routes"]


def test_export_run_bundle_writes_all_files(tmp_path: Path) -> None:
    dataset = resolve_scenario_path("island-chokepoint-v2", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(dataset)
    engine = SimulationEngine(max_ticks=1, seed=1, quiet_logs=True)
    run = engine.run_scenario(package)

    bundle = build_run_bundle(
        run=run,
        scenario=package.scenario,
        nodes=engine.nodes,
        routes=engine.routes,
        audit_traces=engine.audit_traces,
        events=engine.events,
        scenario_package=package,
        dataset_path=dataset,
        ticks_executed=run.current_tick + 1,
    )
    export_path = export_run_bundle(bundle, tmp_path)

    assert export_path.is_dir()
    assert (export_path / "manifest.json").exists()
    assert (export_path / "run_bundle.json").exists()
    assert (export_path / "audit_traces.jsonl").exists()
    assert (export_path / "simulation_events.jsonl").exists()
    assert (export_path / "executive_summary.md").exists()
    assert (export_path / "insights.json").exists()
    assert (export_path / "insights_report.md").exists()
    assert (export_path / "annotations.json").exists()

    manifest = json.loads((export_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["files"]["annotations"] == "annotations.json"
    assert manifest["run_id"] == run.run_id
    assert manifest["scenario_id"] == "island-chokepoint-v2"

    summary = (export_path / "executive_summary.md").read_text(encoding="utf-8")
    assert "Executive Summary" in summary
    assert run.run_id in summary
    assert "## Ontology Payload" in summary

    run_bundle = json.loads((export_path / "run_bundle.json").read_text(encoding="utf-8"))
    assert run_bundle["run"]["run_id"] == run.run_id
    assert len(run_bundle["audit_traces"]) == len(engine.audit_traces)


def test_export_run_bundle_v3_scenario(tmp_path: Path) -> None:
    dataset = resolve_scenario_path("alpine-valley-v3", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(dataset)
    engine = SimulationEngine(max_ticks=2, seed=42, quiet_logs=True)
    run = engine.run_scenario(package)

    bundle = build_run_bundle(
        run=run,
        scenario=package.scenario,
        nodes=engine.nodes,
        routes=engine.routes,
        audit_traces=engine.audit_traces,
        events=engine.events,
        scenario_package=package,
        dataset_path=dataset,
        ticks_executed=run.current_tick + 1,
    )
    export_path = export_run_bundle(bundle, tmp_path)

    manifest = json.loads((export_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["scenario_id"] == "alpine-valley-v3"