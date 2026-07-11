# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Foundry integration configuration (ADR-011)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class FoundryConfig:
    """Configuration for Palantir Foundry dataset and Ontology connectivity."""

    foundry_url: str | None
    foundry_token: str | None
    ontology_rid: str | None
    scenario_dataset_rid: str | None
    results_dataset_rid: str | None
    foundry_enabled: bool
    ontology_sync_enabled: bool
    local_datasets_root: str

    @classmethod
    def from_env(cls) -> FoundryConfig:
        return cls(
            foundry_url=os.getenv("FOUNDRY_URL"),
            foundry_token=os.getenv("FOUNDRY_TOKEN"),
            ontology_rid=os.getenv("ONTOLOGY_RID"),
            scenario_dataset_rid=os.getenv("FOUNDRY_SCENARIO_DATASET_RID"),
            results_dataset_rid=os.getenv("FOUNDRY_RESULTS_DATASET_RID"),
            foundry_enabled=_env_bool("ADSL_FOUNDRY_ENABLED"),
            ontology_sync_enabled=_env_bool("ADSL_ONTOLOGY_SYNC_ENABLED"),
            local_datasets_root=os.getenv(
                "ADSL_FOUNDRY_LOCAL_DATASETS_ROOT",
                "data/foundry/datasets",
            ),
        )

    def missing_credentials(self) -> list[str]:
        missing: list[str] = []
        if not self.foundry_url:
            missing.append("FOUNDRY_URL")
        if not self.foundry_token:
            missing.append("FOUNDRY_TOKEN")
        return missing

    def missing_ontology_credentials(self) -> list[str]:
        missing = self.missing_credentials()
        if not self.ontology_rid:
            missing.append("ONTOLOGY_RID")
        return missing

    def is_live_ready(self) -> bool:
        """True when live Foundry HTTP adapter may be used."""
        if not self.foundry_enabled:
            return False
        return not self.missing_credentials()

    def validate(self) -> dict:
        return {
            "foundry_enabled": self.foundry_enabled,
            "ontology_sync_enabled": self.ontology_sync_enabled,
            "live_ready": self.is_live_ready(),
            "missing_credentials": self.missing_credentials(),
            "scenario_dataset_rid": self.scenario_dataset_rid,
            "results_dataset_rid": self.results_dataset_rid,
            "ontology_rid": self.ontology_rid,
            "mode": "live_http" if self.is_live_ready() else "local_filesystem",
            "local_datasets_root": self.local_datasets_root,
        }