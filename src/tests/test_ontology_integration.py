# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for Palantir Ontology integration layer."""

from pathlib import Path

from adsl.models import AgentSide, DecisionCategory, ActionType
from adsl.ontology.integration import (
    ONTOLOGY_OBJECT_TYPES,
    build_run_sync_payload,
    map_audit_trace_to_ontology,
    map_logistics_node_to_ontology,
    sync_run_to_ontology,
    write_ontology_object,
)
from adsl.simulation.engine import SimulationEngine
from adsl.simulation.loader import load_scenario_package

DATASET_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "synthetic" / "logistics_scenario_v1.json"
)


def test_map_logistics_node_includes_ontology_fields() -> None:
    package = load_scenario_package(DATASET_PATH)
    node = package.scenario.nodes[0]
    payload = map_logistics_node_to_ontology(node)

    assert payload["object_type"] == ONTOLOGY_OBJECT_TYPES["logistics_node"]
    assert payload["primary_key"] == node.node_id
    assert payload["properties"]["source_system"] == "ADSL_PHASE1"
    assert payload["properties"]["node_type"] == node.node_type.value


def test_build_run_sync_payload_contains_all_categories() -> None:
    package = load_scenario_package(DATASET_PATH)
    engine = SimulationEngine(max_ticks=2, seed=1)
    run = engine.run_scenario(package)

    payload = build_run_sync_payload(
        run=run,
        nodes=engine.nodes,
        routes=engine.routes,
        audit_traces=engine.audit_traces,
        events=engine.events,
        scenario_package=package,
    )

    assert payload["bootstrap"]
    assert payload["simulation_run"]
    assert payload["audit_traces"]
    assert payload["simulation_events"]
    assert len(payload["audit_traces"]) == len(engine.audit_traces)


def test_sync_run_offline_returns_no_writes(monkeypatch) -> None:
    monkeypatch.delenv("ADSL_ONTOLOGY_SYNC_ENABLED", raising=False)
    package = load_scenario_package(DATASET_PATH)
    engine = SimulationEngine(max_ticks=1, seed=0)
    run = engine.run_scenario(package)

    result = sync_run_to_ontology(
        run=run,
        nodes=engine.nodes,
        routes=engine.routes,
        audit_traces=engine.audit_traces,
        events=engine.events,
    )

    assert result["sync_enabled"] is False
    assert result["written_rids"] == []


def test_write_ontology_object_placeholder_returns_rid() -> None:
    payload = map_audit_trace_to_ontology(
        __import__("adsl.models", fromlist=["ADSL_AuditTrace"]).ADSL_AuditTrace(
            run_id="run-1",
            agent_id="agent-1",
            agent_side=AgentSide.RED,
            simulation_tick=0,
            decision_category=DecisionCategory.NO_ACTION,
            inputs_considered={"tick": 0},
            reasoning_steps=[
                __import__(
                    "adsl.models", fromlist=["ADSL_ReasoningStep"]
                ).ADSL_ReasoningStep(step_index=0, description="Test.")
            ],
            action_type=ActionType.NO_ACTION,
            action_summary="No action",
        )
    )
    rid = write_ontology_object(payload)
    assert rid.startswith("ri.ontology.main.object.")