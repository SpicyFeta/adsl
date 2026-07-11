# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""End-to-end tests for ADSL Phase 1 contested logistics simulation."""

from pathlib import Path

from adsl.models import SimulationStatus
from adsl.ontology.integration import build_run_sync_payload
from adsl.simulation.engine import SimulationEngine
from adsl.simulation.loader import load_scenario_package

DATASET_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "synthetic" / "logistics_scenario_v1.json"
)
E2E_TICKS = 50
E2E_SEED = 42


def test_kessari_strait_simulation_end_to_end() -> None:
    """Run the full Kessari Strait scenario and verify core outputs."""
    package = load_scenario_package(DATASET_PATH)
    agent_count = len(package.red_force_elements) + len(package.blue_force_elements)

    engine = SimulationEngine(max_ticks=E2E_TICKS, seed=E2E_SEED)
    run = engine.run_scenario(package)

    assert run is not None
    assert run.scenario_id == "kessari-strait-v1"
    assert run.status == SimulationStatus.COMPLETED
    assert run.current_tick == E2E_TICKS - 1
    assert run.seed == E2E_SEED
    assert run.started_at is not None
    assert run.completed_at is not None

    expected_traces = E2E_TICKS * agent_count
    assert len(engine.audit_traces) == expected_traces
    assert len(run.audit_trace_ids) == expected_traces
    assert all(trace.run_id == run.run_id for trace in engine.audit_traces)

    assert len(engine.events) > 0
    assert len(engine.nodes) == len(package.scenario.nodes)
    assert len(engine.routes) == len(package.scenario.routes)

    payload = build_run_sync_payload(
        run=run,
        nodes=engine.nodes,
        routes=engine.routes,
        audit_traces=engine.audit_traces,
        events=engine.events,
        scenario_package=package,
    )

    assert len(payload["bootstrap"]) == (
        len(package.scenario.nodes)
        + len(package.scenario.routes)
        + len(package.blue_force_elements)
        + len(package.red_force_elements)
    )
    assert len(payload["simulation_run"]) == 1
    assert len(payload["audit_traces"]) == expected_traces
    assert len(payload["simulation_events"]) == len(engine.events)
    assert payload["simulation_run"][0]["primary_key"] == run.run_id