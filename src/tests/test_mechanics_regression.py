# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Regression tests for Phase 2 mechanics on v1 and v2 scenarios."""

from pathlib import Path

from adsl.models import SimulationStatus
from adsl.simulation.engine import SimulationEngine
from adsl.simulation.loader import load_scenario_package
from adsl.simulation.registry import resolve_scenario_path

SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"


def test_kessari_v1_regression_after_mechanics_v2() -> None:
    path = resolve_scenario_path("kessari-strait-v1", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    agent_count = len(package.red_force_elements) + len(package.blue_force_elements)

    engine = SimulationEngine(max_ticks=50, seed=42, quiet_logs=True)
    run = engine.run_scenario(package)

    assert run.status == SimulationStatus.COMPLETED
    assert len(engine.audit_traces) == 50 * agent_count
    assert len(engine.events) > 0


def test_island_chokepoint_v2_regression_after_mechanics_v2() -> None:
    path = resolve_scenario_path("island-chokepoint-v2", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    agent_count = len(package.red_force_elements) + len(package.blue_force_elements)

    engine = SimulationEngine(max_ticks=100, seed=42, quiet_logs=True)
    run = engine.run_scenario(package)

    assert run.status == SimulationStatus.COMPLETED
    assert len(engine.audit_traces) == 100 * agent_count

    destroyed = sum(
        1 for node in engine.nodes if node.status.value == "DESTROYED"
    )
    assert destroyed / len(engine.nodes) < 0.5


def test_alpine_valley_v3_regression_after_mechanics_v2() -> None:
    path = resolve_scenario_path("alpine-valley-v3", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    agent_count = len(package.red_force_elements) + len(package.blue_force_elements)

    engine = SimulationEngine(max_ticks=100, seed=42, quiet_logs=True)
    run = engine.run_scenario(package)

    assert run.status == SimulationStatus.COMPLETED
    assert len(engine.audit_traces) == 100 * agent_count
    assert len(engine.events) > 0