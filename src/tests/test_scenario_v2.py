# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for island chokepoint scenario v2 (Phase 2 Increment 1)."""

from pathlib import Path

from adsl.models import NodeStatus, SimulationStatus
from adsl.simulation.engine import SimulationEngine
from adsl.simulation.registry import resolve_scenario_path
from adsl.simulation.loader import load_scenario_package

SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"
V2_TICKS = 100
V2_SEED = 42


def test_island_chokepoint_v2_loads() -> None:
    path = resolve_scenario_path("island-chokepoint-v2", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    assert package.scenario.scenario_id == "island-chokepoint-v2"
    assert len(package.scenario.nodes) == 12
    assert len(package.scenario.routes) == 18
    assert len(package.blue_force_elements) == 7
    assert len(package.red_force_elements) == 4


def test_island_chokepoint_v2_100_tick_demo_profile() -> None:
    """Scenario v2 should sustain demos with <50% node destruction at 100 ticks."""
    path = resolve_scenario_path("island-chokepoint-v2", synthetic_dir=SYNTHETIC_DIR)
    package = load_scenario_package(path)
    agent_count = len(package.red_force_elements) + len(package.blue_force_elements)

    engine = SimulationEngine(max_ticks=V2_TICKS, seed=V2_SEED, quiet_logs=True)
    run = engine.run_scenario(package)

    assert run is not None
    assert run.status == SimulationStatus.COMPLETED
    assert run.current_tick == V2_TICKS - 1
    assert len(engine.audit_traces) == V2_TICKS * agent_count

    destroyed = sum(1 for node in engine.nodes if node.status == NodeStatus.DESTROYED)
    destruction_fraction = destroyed / len(engine.nodes)
    assert destruction_fraction < 0.5, (
        f"Expected <50% node destruction; got {destroyed}/{len(engine.nodes)} "
        f"({destruction_fraction:.1%})"
    )