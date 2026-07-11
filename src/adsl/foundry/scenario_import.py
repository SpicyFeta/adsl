# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Import ADSL scenario packages from Foundry datasets (ADR-011)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adsl.foundry.client import DEFAULT_SCENARIO_DATASET, FoundryClient, get_foundry_client
from adsl.foundry.lineage import build_lineage_metadata
from adsl.models import ADSL_ScenarioPackage
from adsl.simulation.loader import load_scenario_package

DATASET_SCHEMA_VERSION = "1.0"
RECORD_TYPE_SCENARIO = "adsl_scenario_package"


def build_scenario_dataset_record(
    package: ADSL_ScenarioPackage,
    *,
    parent_dataset_rid: str | None = None,
) -> dict[str, Any]:
    """Wrap a scenario package as a Foundry dataset record."""
    return {
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "record_type": RECORD_TYPE_SCENARIO,
        "scenario_id": package.scenario.scenario_id,
        "lineage": build_lineage_metadata(
            operation="scenario_publish",
            parent_dataset_rid=parent_dataset_rid,
            scenario_id=package.scenario.scenario_id,
        ),
        "payload": package.model_dump(mode="json"),
    }


def parse_scenario_record(record: dict[str, Any]) -> ADSL_ScenarioPackage:
    """Parse a Foundry dataset record into a validated scenario package."""
    if record.get("record_type") != RECORD_TYPE_SCENARIO:
        raise ValueError(
            f"Expected record_type={RECORD_TYPE_SCENARIO!r}, got {record.get('record_type')!r}"
        )
    payload = record.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("Scenario record missing payload object")
    return ADSL_ScenarioPackage.model_validate(payload)


def import_scenario_from_foundry(
    scenario_id: str,
    *,
    dataset_rid: str | None = None,
    client: FoundryClient | None = None,
) -> tuple[ADSL_ScenarioPackage, dict[str, Any]]:
    """
    Import a scenario package from a Foundry dataset by scenario_id.

    Returns the validated package and the source record (including lineage).
    """
    foundry = client or get_foundry_client()
    records = foundry.read_dataset_records(
        dataset_rid,
        record_type=RECORD_TYPE_SCENARIO,
    )

    for record in records:
        if record.get("scenario_id") == scenario_id:
            return parse_scenario_record(record), record

    raise KeyError(
        f"Scenario {scenario_id!r} not found in dataset "
        f"{dataset_rid or 'local:scenarios'}"
    )


def import_scenario_from_local_file(path: str | Path) -> ADSL_ScenarioPackage:
    """Load scenario directly from local JSON (non-Foundry path)."""
    return load_scenario_package(path)


def publish_scenario_to_foundry(
    scenario_path: str | Path,
    *,
    dataset_rid: str | None = None,
    client: FoundryClient | None = None,
    append: bool = True,
) -> dict[str, Any]:
    """Publish a local scenario package to a Foundry scenario dataset."""
    foundry = client or get_foundry_client()
    package = load_scenario_package(scenario_path)
    record = build_scenario_dataset_record(
        package,
        parent_dataset_rid=dataset_rid or foundry.config.scenario_dataset_rid,
    )
    write_result = foundry.write_dataset_records(
        [record],
        dataset_rid,
        append=append,
        default_local=DEFAULT_SCENARIO_DATASET,
    )
    return {
        "scenario_id": package.scenario.scenario_id,
        "lineage_id": record["lineage"]["lineage_id"],
        "dataset_write": write_result,
    }