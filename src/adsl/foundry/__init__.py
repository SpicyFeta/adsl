# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Palantir Foundry dataset integration (ADR-011). Optional — decoupled from simulation engine."""

from adsl.foundry.client import FoundryClient, get_foundry_client
from adsl.foundry.config import FoundryConfig
from adsl.foundry.lineage import build_lineage_metadata
from adsl.foundry.results_export import export_run_to_foundry_dataset
from adsl.foundry.results_export import build_foundry_export_records
from adsl.foundry.scenario_import import (
    build_scenario_dataset_record,
    import_scenario_from_foundry,
    publish_scenario_to_foundry,
)

__all__ = [
    "FoundryConfig",
    "FoundryClient",
    "get_foundry_client",
    "build_lineage_metadata",
    "build_scenario_dataset_record",
    "build_foundry_export_records",
    "import_scenario_from_foundry",
    "publish_scenario_to_foundry",
    "export_run_to_foundry_dataset",
]