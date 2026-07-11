# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for simulation engine and synthetic scenario dataset."""

from pathlib import Path

import pytest

from adsl.models import AgentSide, SimulationEventType, SimulationStatus
from adsl.simulation.engine import DEFAULT_MAX_TICKS, SimulationEngine
from adsl.simulation.loader import load_scenario_package

DATASET_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "synthetic" / "logistics_scenario_v1.json"
)


def test_scenario_dataset_loads_and_validates() -> None:
    package = load_scenario_package(DATASET_PATH)
    assert package.scenario.scenario_id == "kessari-strait-v1"
    assert len(package.scenario.nodes) == 10
    assert len(package.scenario.routes) == 18
    assert len(package.blue_force_elements) == 7
    assert len(package.red_force_elements) == 4


def test_engine_runs_scenario_with_placeholder_agents() -> None:
    package = load_scenario_package(DATASET_PATH)
    engine = SimulationEngine(max_ticks=3, seed=42)
    run = engine.run_scenario(package)

    assert run.status == SimulationStatus.COMPLETED
    assert run.current_tick == 2
    expected_traces = 3 * (len(package.red_force_elements) + len(package.blue_force_elements))
    assert len(engine.audit_traces) == expected_traces
    assert len(run.audit_trace_ids) == expected_traces


def test_red_agents_act_before_blue_each_tick() -> None:
    package = load_scenario_package(DATASET_PATH)
    engine = SimulationEngine(max_ticks=1, seed=1)
    engine.run_scenario(package)

    decision_events = [
        event
        for event in engine.events
        if event.event_type == SimulationEventType.AGENT_DECISION
    ]
    sides = [event.agent_side for event in decision_events]
    red_count = len(package.red_force_elements)
    assert sides[:red_count] == [AgentSide.RED] * red_count
    assert sides[red_count:] == [AgentSide.BLUE] * len(package.blue_force_elements)


def test_engine_rejects_excessive_tick_count() -> None:
    with pytest.raises(ValueError, match="at most"):
        SimulationEngine(max_ticks=DEFAULT_MAX_TICKS + 1)