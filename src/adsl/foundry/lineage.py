# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Data lineage metadata for Foundry import/export (ADR-011)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

SOURCE_SYSTEM = "ADSL_PHASE3"
LINEAGE_SCHEMA_VERSION = "1.0"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_lineage_metadata(
    *,
    operation: str,
    parent_dataset_rid: str | None = None,
    parent_run_id: str | None = None,
    scenario_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build immutable lineage block attached to every Foundry dataset record."""
    lineage: dict[str, Any] = {
        "lineage_schema_version": LINEAGE_SCHEMA_VERSION,
        "lineage_id": str(uuid4()),
        "source_system": SOURCE_SYSTEM,
        "operation": operation,
        "recorded_at": _utc_now_iso(),
    }
    if parent_dataset_rid:
        lineage["parent_dataset_rid"] = parent_dataset_rid
    if parent_run_id:
        lineage["parent_run_id"] = parent_run_id
    if scenario_id:
        lineage["scenario_id"] = scenario_id
    if extra:
        lineage.update(extra)
    return lineage