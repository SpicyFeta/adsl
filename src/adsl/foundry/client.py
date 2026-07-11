# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Foundry client — selects local or HTTP adapter (ADR-011)."""

from __future__ import annotations

from typing import Any

from adsl.foundry.adapters.http import HttpDatasetAdapter
from adsl.foundry.adapters.local import LocalDatasetAdapter
from adsl.foundry.config import FoundryConfig

DEFAULT_SCENARIO_DATASET = "local:scenarios"
DEFAULT_RESULTS_DATASET = "local:results"


class FoundryClient:
    """Unified client for Foundry dataset read/write operations."""

    def __init__(self, config: FoundryConfig) -> None:
        self._config = config
        self._local = LocalDatasetAdapter(config.local_datasets_root)
        self._http: HttpDatasetAdapter | None = None
        if config.is_live_ready():
            self._http = HttpDatasetAdapter(config)

    @classmethod
    def from_env(cls) -> FoundryClient:
        return cls(FoundryConfig.from_env())

    @property
    def config(self) -> FoundryConfig:
        return self._config

    def validate(self) -> dict[str, Any]:
        return self._config.validate()

    def _resolve_dataset_key(self, dataset_rid: str | None, default_local: str) -> str:
        if dataset_rid:
            return dataset_rid
        return default_local

    def read_dataset_records(
        self,
        dataset_rid: str | None = None,
        *,
        record_type: str | None = None,
        default_local: str = DEFAULT_SCENARIO_DATASET,
    ) -> list[dict[str, Any]]:
        key = self._resolve_dataset_key(dataset_rid, default_local)
        if self._http is not None and key.startswith("ri."):
            return self._http.read_records(key, record_type=record_type)
        return self._local.read_records(key, record_type=record_type)

    def write_dataset_records(
        self,
        records: list[dict[str, Any]],
        dataset_rid: str | None = None,
        *,
        append: bool = True,
        default_local: str = DEFAULT_RESULTS_DATASET,
    ) -> dict[str, Any]:
        key = self._resolve_dataset_key(dataset_rid, default_local)
        if self._http is not None and key.startswith("ri."):
            return self._http.write_records(key, records, append=append)
        return self._local.write_records(key, records, append=append)

    def write_ontology_object(self, payload: dict[str, Any]) -> str:
        if self._http is not None and self._config.ontology_sync_enabled:
            return self._http.write_ontology_object(payload)
        object_type = payload.get("object_type", "Unknown")
        primary_key = payload.get("primary_key", "unknown")
        return f"ri.ontology.main.object.{object_type}.{primary_key}"

    def write_ontology_objects_batch(self, payloads: list[dict[str, Any]]) -> list[str]:
        if self._http is not None and self._config.ontology_sync_enabled:
            return self._http.write_ontology_objects_batch(payloads)
        return [self.write_ontology_object(payload) for payload in payloads]

    def read_ontology_object(
        self,
        object_type: str,
        primary_key: str,
    ) -> dict[str, Any] | None:
        if self._http is not None and self._config.ontology_sync_enabled:
            return self._http.read_ontology_object(object_type, primary_key)
        return None


def get_foundry_client() -> FoundryClient:
    return FoundryClient.from_env()