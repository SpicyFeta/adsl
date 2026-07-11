# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Scenario registry for ADSL synthetic datasets (ADR-009)."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_SYNTHETIC_DIR = Path(__file__).resolve().parents[3] / "data" / "synthetic"
REGISTRY_FILENAME = "scenario_registry.json"


def _registry_path(synthetic_dir: Path | None = None) -> Path:
    base = synthetic_dir or DEFAULT_SYNTHETIC_DIR
    return base / REGISTRY_FILENAME


def load_scenario_registry(synthetic_dir: Path | None = None) -> dict[str, str]:
    """Load scenario_id → dataset filename mapping."""
    path = _registry_path(synthetic_dir)
    if not path.exists():
        raise FileNotFoundError(f"Scenario registry not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Scenario registry must be a JSON object.")
    return {str(key): str(value) for key, value in data.items()}


def resolve_scenario_path(
    scenario_id: str,
    *,
    synthetic_dir: Path | None = None,
) -> Path:
    """Resolve a scenario ID to an absolute dataset path."""
    registry = load_scenario_registry(synthetic_dir)
    if scenario_id not in registry:
        known = ", ".join(sorted(registry))
        raise KeyError(f"Unknown scenario '{scenario_id}'. Known scenarios: {known}")
    base = synthetic_dir or DEFAULT_SYNTHETIC_DIR
    path = base / registry[scenario_id]
    if not path.exists():
        raise FileNotFoundError(f"Scenario dataset not found for '{scenario_id}': {path}")
    return path


def list_scenario_ids(synthetic_dir: Path | None = None) -> list[str]:
    """Return registered scenario IDs sorted alphabetically."""
    return sorted(load_scenario_registry(synthetic_dir))