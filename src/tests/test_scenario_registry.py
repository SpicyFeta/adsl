# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for scenario registry (ADR-009)."""

from pathlib import Path

import pytest

from adsl.simulation.loader import load_scenario_package
from adsl.simulation.registry import (
    list_scenario_ids,
    load_scenario_registry,
    resolve_scenario_path,
)

SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"


def test_registry_lists_all_scenarios() -> None:
    ids = list_scenario_ids(SYNTHETIC_DIR)
    assert "kessari-strait-v1" in ids
    assert "island-chokepoint-v2" in ids
    assert "alpine-valley-v3" in ids
    assert "continental-grid-scale-v4" in ids
    assert "continental-mega-scale-v5" in ids


def test_resolve_scenario_path_v2() -> None:
    path = resolve_scenario_path("island-chokepoint-v2", synthetic_dir=SYNTHETIC_DIR)
    assert path.name == "logistics_scenario_v2.json"
    package = load_scenario_package(path)
    assert package.scenario.scenario_id == "island-chokepoint-v2"


def test_resolve_unknown_scenario_raises() -> None:
    with pytest.raises(KeyError, match="Unknown scenario"):
        resolve_scenario_path("nonexistent-scenario", synthetic_dir=SYNTHETIC_DIR)


def test_resolve_scenario_path_v3() -> None:
    path = resolve_scenario_path("alpine-valley-v3", synthetic_dir=SYNTHETIC_DIR)
    assert path.name == "logistics_scenario_v3.json"
    package = load_scenario_package(path)
    assert package.scenario.scenario_id == "alpine-valley-v3"


def test_load_scenario_registry_returns_mapping() -> None:
    registry = load_scenario_registry(SYNTHETIC_DIR)
    assert registry["kessari-strait-v1"] == "logistics_scenario_v1.json"
    assert registry["island-chokepoint-v2"] == "logistics_scenario_v2.json"
    assert registry["alpine-valley-v3"] == "logistics_scenario_v3.json"
    assert registry["continental-grid-scale-v4"] == "logistics_scenario_scale.json"