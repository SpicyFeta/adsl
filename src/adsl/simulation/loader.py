# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Scenario dataset loading utilities."""

from __future__ import annotations

import json
from pathlib import Path

from adsl.models import ADSL_ScenarioPackage


def load_scenario_package(path: str | Path) -> ADSL_ScenarioPackage:
    """Load and validate a scenario package from a JSON dataset file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ADSL_ScenarioPackage.model_validate(data)