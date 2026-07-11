# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for Palantir Foundry dataset integration (ADR-011)."""

import json
from pathlib import Path

import pytest

from adsl.collaboration.annotations import add_annotation
from adsl.export.bundle import export_run_bundle
from adsl.export.runner import RunSpec, execute_run, load_run_bundle_from_export
from adsl.foundry import (
    FoundryClient,
    FoundryConfig,
    build_foundry_export_records,
    build_scenario_dataset_record,
    export_run_to_foundry_dataset,
    import_scenario_from_foundry,
    publish_scenario_to_foundry,
)
from adsl.foundry.lineage import LINEAGE_SCHEMA_VERSION, SOURCE_SYSTEM
from adsl.simulation.registry import resolve_scenario_path

SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"


@pytest.fixture
def local_foundry_root(tmp_path: Path) -> Path:
    return tmp_path / "datasets"


@pytest.fixture
def foundry_client(local_foundry_root: Path) -> FoundryClient:
    config = FoundryConfig(
        foundry_url=None,
        foundry_token=None,
        ontology_rid=None,
        scenario_dataset_rid=None,
        results_dataset_rid=None,
        foundry_enabled=False,
        ontology_sync_enabled=False,
        local_datasets_root=str(local_foundry_root),
    )
    return FoundryClient(config)


def test_build_scenario_dataset_record_includes_lineage() -> None:
    path = resolve_scenario_path("island-chokepoint-v2", synthetic_dir=SYNTHETIC_DIR)
    from adsl.simulation.loader import load_scenario_package

    package = load_scenario_package(path)
    record = build_scenario_dataset_record(package)

    assert record["record_type"] == "adsl_scenario_package"
    assert record["scenario_id"] == "island-chokepoint-v2"
    assert record["lineage"]["source_system"] == SOURCE_SYSTEM
    assert record["lineage"]["lineage_schema_version"] == LINEAGE_SCHEMA_VERSION


def test_publish_and_import_scenario_roundtrip(foundry_client: FoundryClient) -> None:
    path = resolve_scenario_path("alpine-valley-v3", synthetic_dir=SYNTHETIC_DIR)
    publish_result = publish_scenario_to_foundry(path, client=foundry_client)
    assert publish_result["scenario_id"] == "alpine-valley-v3"

    package, source_record = import_scenario_from_foundry(
        "alpine-valley-v3",
        client=foundry_client,
    )
    assert package.scenario.scenario_id == "alpine-valley-v3"
    assert source_record["lineage"]["lineage_id"] == publish_result["lineage_id"]


def test_import_missing_scenario_raises(foundry_client: FoundryClient) -> None:
    with pytest.raises(KeyError, match="not found"):
        import_scenario_from_foundry("nonexistent-scenario", client=foundry_client)


def test_build_foundry_export_records_structure() -> None:
    spec = RunSpec(scenario_id="island-chokepoint-v2", seed=7, ticks=5, label="foundry-test")
    _, result = execute_run(spec, synthetic_dir=SYNTHETIC_DIR)
    records = build_foundry_export_records(result.bundle)

    types = {record["record_type"] for record in records}
    assert "adsl_simulation_run" in types
    assert "adsl_network_snapshot" in types
    assert "adsl_audit_trace" in types
    assert "adsl_lineage" in types
    assert sum(1 for record in records if record["record_type"] == "adsl_audit_trace") == len(
        result.bundle["audit_traces"]
    )


def test_export_includes_annotations_and_insights(tmp_path: Path) -> None:
    spec = RunSpec(scenario_id="island-chokepoint-v2", seed=3, ticks=3)
    _, result = execute_run(spec, synthetic_dir=SYNTHETIC_DIR)
    export_dir = export_run_bundle(result.bundle, tmp_path)

    add_annotation(export_dir, author="Analyst", text="Workshop note.", target_kind="run")
    records = build_foundry_export_records(result.bundle, export_dir=export_dir)
    types = {record["record_type"] for record in records}
    assert "adsl_annotations" in types
    assert "adsl_insights" in types


def test_export_run_to_local_dataset(foundry_client: FoundryClient) -> None:
    spec = RunSpec(scenario_id="island-chokepoint-v2", seed=11, ticks=4)
    _, result = execute_run(spec, synthetic_dir=SYNTHETIC_DIR)

    export_result = export_run_to_foundry_dataset(result.bundle, client=foundry_client)
    assert export_result["records_exported"] > 0
    assert export_result["audit_traces_exported"] == len(result.bundle["audit_traces"])
    assert export_result["lineage_id"]

    records_path = (
        Path(foundry_client.config.local_datasets_root) / "results" / "records.jsonl"
    )
    assert records_path.exists()
    lines = [line for line in records_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == export_result["records_exported"]


def test_foundry_config_local_mode_by_default(monkeypatch) -> None:
    monkeypatch.delenv("ADSL_FOUNDRY_ENABLED", raising=False)
    config = FoundryConfig.from_env()
    assert config.is_live_ready() is False
    summary = config.validate()
    assert summary["mode"] == "local_filesystem"


def test_foundry_config_live_ready_with_credentials(monkeypatch) -> None:
    monkeypatch.setenv("ADSL_FOUNDRY_ENABLED", "true")
    monkeypatch.setenv("FOUNDRY_URL", "https://foundry.example.com")
    monkeypatch.setenv("FOUNDRY_TOKEN", "test-token")

    config = FoundryConfig.from_env()
    assert config.is_live_ready() is True
    assert config.validate()["mode"] == "live_http"


def test_example_local_scenarios_dataset_readable() -> None:
    """Committed example data under data/foundry/datasets/scenarios."""
    scenarios_path = (
        Path(__file__).resolve().parents[2] / "data" / "foundry" / "datasets" / "scenarios"
    )
    records_file = scenarios_path / "records.jsonl"
    if not records_file.exists():
        pytest.skip("Example Foundry scenarios dataset not generated")

    config = FoundryConfig(
        foundry_url=None,
        foundry_token=None,
        ontology_rid=None,
        scenario_dataset_rid=None,
        results_dataset_rid=None,
        foundry_enabled=False,
        ontology_sync_enabled=False,
        local_datasets_root=str(scenarios_path.parent),
    )
    client = FoundryClient(config)
    package, _ = import_scenario_from_foundry("island-chokepoint-v2", client=client)
    assert package.scenario.scenario_id == "island-chokepoint-v2"


def test_load_bundle_from_export_for_foundry_export(tmp_path: Path, foundry_client: FoundryClient) -> None:
    spec = RunSpec(scenario_id="alpine-valley-v3", seed=1, ticks=2)
    _, result = execute_run(spec, synthetic_dir=SYNTHETIC_DIR)
    export_dir = export_run_bundle(result.bundle, tmp_path)
    bundle = load_run_bundle_from_export(export_dir)

    export_result = export_run_to_foundry_dataset(
        bundle,
        client=foundry_client,
        export_dir=export_dir,
    )
    assert export_result["insights_exported"] == 1