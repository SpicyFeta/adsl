# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for Phase 3 Increment 11 collaboration features."""

import json
from pathlib import Path

import pytest

from adsl.collaboration.annotations import add_annotation, list_annotations, load_annotations
from adsl.collaboration.format import format_annotations_markdown, format_session_summary
from adsl.collaboration.scenario_share import (
    export_shared_scenario,
    import_shared_scenario,
    resolve_latest_shared_scenario,
)
from adsl.collaboration.session import (
    add_participant,
    create_session,
    link_run_to_session,
    list_sessions,
    load_session,
)
from adsl.collaboration.versioning import append_scenario_version, load_version_history
from adsl.collaboration.workflows import annotate_run_in_session, register_run_export
from adsl.export.bundle import export_run_bundle
from adsl.export.runner import RunSpec, execute_run
from adsl.simulation.registry import resolve_scenario_path

SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"


@pytest.fixture
def session_root(tmp_path: Path) -> Path:
    session = create_session(
        "Test Workshop",
        description="Collaboration test session",
        facilitator="Lead Analyst",
        sessions_root=tmp_path,
    )
    return Path(session["_session_root"])


@pytest.fixture
def alpine_export(tmp_path: Path) -> Path:
    spec = RunSpec(scenario_id="alpine-valley-v3", seed=42, ticks=10, label="collab-test")
    _, result = execute_run(spec, synthetic_dir=SYNTHETIC_DIR)
    return export_run_bundle(result.bundle, tmp_path)


def test_create_session_structure(session_root: Path) -> None:
    session = load_session(session_root)
    assert session["schema_version"] == "1.0"
    assert session["name"] == "Test Workshop"
    assert len(session["participants"]) == 1
    assert session["participants"][0]["role"] == "facilitator"
    assert (session_root / "shared_scenarios").is_dir()
    assert (session_root / "runs").is_dir()


def test_add_participant_updates_session(session_root: Path) -> None:
    session = load_session(session_root)
    participant = add_participant(
        session,
        display_name="Blue SME",
        role="reviewer",
        session_root=session_root,
    )
    updated = load_session(session_root)
    assert participant["display_name"] == "Blue SME"
    assert len(updated["participants"]) == 2
    assert updated["activity_log"][-1]["action"] == "participant_joined"


def test_list_sessions(session_root: Path, tmp_path: Path) -> None:
    sessions = list_sessions(tmp_path)
    assert len(sessions) == 1
    assert sessions[0]["name"] == "Test Workshop"
    assert sessions[0]["participant_count"] == 1


def test_export_shared_scenario_and_version_history(session_root: Path) -> None:
    scenario_path = resolve_scenario_path("island-chokepoint-v2", synthetic_dir=SYNTHETIC_DIR)
    result = export_shared_scenario(
        scenario_path,
        session_root,
        author="Lead Analyst",
        version_label="workshop-baseline",
        changelog="Initial share",
    )

    assert result["scenario_id"] == "island-chokepoint-v2"
    assert Path(result["shared_path"]).exists()

    history = load_version_history(session_root)
    versions = history["scenarios"]["island-chokepoint-v2"]
    assert len(versions) == 1
    assert versions[0]["version_id"] == result["version_id"]
    assert versions[0]["version_label"] == "workshop-baseline"

    session = load_session(session_root)
    assert len(session["scenario_refs"]) == 1
    assert session["scenario_refs"][0]["version_id"] == result["version_id"]


def test_scenario_version_lineage(session_root: Path) -> None:
    scenario_path = resolve_scenario_path("alpine-valley-v3", synthetic_dir=SYNTHETIC_DIR)
    first = export_shared_scenario(
        scenario_path,
        session_root,
        author="Analyst A",
        version_label="v1",
    )
    second = export_shared_scenario(
        scenario_path,
        session_root,
        author="Analyst B",
        version_label="v2",
        parent_version_id=first["version_id"],
    )

    history = load_version_history(session_root)
    versions = history["scenarios"]["alpine-valley-v3"]
    assert len(versions) == 2
    assert versions[1]["parent_version_id"] == first["version_id"]
    assert second["version_id"] != first["version_id"]

    latest = resolve_latest_shared_scenario(session_root, "alpine-valley-v3")
    assert latest is not None
    assert latest.name.endswith(".json")


def test_import_shared_scenario(session_root: Path, tmp_path: Path) -> None:
    scenario_path = resolve_scenario_path("island-chokepoint-v2", synthetic_dir=SYNTHETIC_DIR)
    export_shared_scenario(
        scenario_path,
        session_root,
        author="Lead Analyst",
        version_label="import-test",
    )
    shared_path = resolve_latest_shared_scenario(session_root, "island-chokepoint-v2")
    assert shared_path is not None

    output_path = import_shared_scenario(shared_path, output_dir=tmp_path / "imported")
    package = json.loads(output_path.read_text(encoding="utf-8"))
    assert package["scenario"]["scenario_id"] == "island-chokepoint-v2"


def test_register_run_export_copies_and_links(
    session_root: Path,
    alpine_export: Path,
) -> None:
    result = register_run_export(
        session_root,
        alpine_export,
        author="Lead Analyst",
        label="baseline-run",
    )

    session = load_session(session_root)
    assert len(session["run_refs"]) == 1
    assert session["run_refs"][0]["run_id"] == result["run_id"]
    assert (session_root / result["export_path"]).is_dir()
    assert (session_root / result["export_path"] / "manifest.json").exists()


def test_annotate_run_in_session(session_root: Path, alpine_export: Path) -> None:
    linked = register_run_export(session_root, alpine_export, author="Lead Analyst")
    annotation = annotate_run_in_session(
        session_root,
        linked["run_id"],
        author="Blue SME",
        text="North ridge corridor shows sustained contestation.",
        target_kind="route",
        target_id="ROUTE-NORTH-01",
        simulation_tick=25,
    )

    assert annotation["author"] == "Blue SME"
    export_dir = session_root / linked["export_path"]
    stored = list_annotations(export_dir, target_kind="route")
    assert len(stored) == 1
    assert stored[0]["text"] == annotation["text"]


def test_add_annotation_on_export_dir(alpine_export: Path) -> None:
    add_annotation(
        alpine_export,
        author="Analyst",
        text="Workshop note on node pressure.",
        target_kind="node",
        target_id="NODE-01",
    )
    doc = load_annotations(alpine_export)
    assert len(doc["annotations"]) == 1
    assert doc["annotations"][0]["target_kind"] == "node"


def test_append_scenario_version_with_explicit_id(session_root: Path) -> None:
    entry = append_scenario_version(
        session_root=session_root,
        scenario_id="test-scenario",
        version_label="manual",
        author="Tester",
        shared_path="shared_scenarios/test.json",
        version_id="fixed-version-id",
    )
    history = load_version_history(session_root)
    assert history["scenarios"]["test-scenario"][0]["version_id"] == "fixed-version-id"
    assert entry["version_id"] == "fixed-version-id"


def test_format_session_summary(session_root: Path) -> None:
    session = load_session(session_root)
    summary = format_session_summary(session)
    assert "Test Workshop" in summary
    assert "Lead Analyst" in summary


def test_format_annotations_markdown(alpine_export: Path) -> None:
    add_annotation(alpine_export, author="A", text="Note one.")
    doc = load_annotations(alpine_export)
    md = format_annotations_markdown(doc)
    assert "Run Annotations" in md
    assert "Note one." in md