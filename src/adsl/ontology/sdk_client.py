# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""
Palantir Ontology client adapter (ADR-007 / ADR-011).

Live I/O delegates to the Foundry HTTP adapter when the activation gate passes.
No Palantir SDK package is required for dataset or Ontology REST paths.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


class OntologySdkNotActiveError(RuntimeError):
    """Raised when live SDK operations are requested but not yet activated."""


@dataclass(frozen=True)
class OntologySdkConfig:
    """Configuration for Palantir Foundry Ontology connectivity."""

    foundry_url: str | None
    foundry_token: str | None
    ontology_rid: str | None
    sync_enabled: bool

    @classmethod
    def from_env(cls) -> OntologySdkConfig:
        sync_enabled = os.getenv("ADSL_ONTOLOGY_SYNC_ENABLED", "false").lower() in {
            "1",
            "true",
            "yes",
        }
        return cls(
            foundry_url=os.getenv("FOUNDRY_URL"),
            foundry_token=os.getenv("FOUNDRY_TOKEN"),
            ontology_rid=os.getenv("ONTOLOGY_RID"),
            sync_enabled=sync_enabled,
        )

    def missing_credentials(self) -> list[str]:
        missing: list[str] = []
        if not self.foundry_url:
            missing.append("FOUNDRY_URL")
        if not self.foundry_token:
            missing.append("FOUNDRY_TOKEN")
        if not self.ontology_rid:
            missing.append("ONTOLOGY_RID")
        return missing


class OntologySdkClient:
    """
    Adapter for the official Palantir Ontology SDK.

    Preparation phase: placeholder methods only. `is_live_ready()` returns False.
    """

    def __init__(self, config: OntologySdkConfig) -> None:
        self._config = config

    @classmethod
    def from_env(cls) -> OntologySdkClient:
        return cls(OntologySdkConfig.from_env())

    def is_live_ready(self) -> bool:
        """Return True when live Foundry HTTP adapter may be used (ADR-011 gate)."""
        if not self._config.sync_enabled:
            return False
        if self._config.missing_credentials():
            return False
        from adsl.foundry.config import FoundryConfig

        return FoundryConfig.from_env().is_live_ready()

    def validate_config(self) -> dict[str, Any]:
        """Return configuration validation summary for diagnostics."""
        missing = self._config.missing_credentials()
        mode = "live_http" if self.is_live_ready() else "offline_placeholder"
        return {
            "sync_enabled": self._config.sync_enabled,
            "live_ready": self.is_live_ready(),
            "missing_credentials": missing,
            "sdk_package_installed": False,
            "mode": mode,
        }

    def read_object(self, object_type: str, primary_key: str) -> dict[str, Any] | None:
        """
        Read an object from the Palantir Ontology.

        Preparation phase: not active. Returns None when sync is disabled;
        raises OntologySdkNotActiveError when sync enabled but live SDK not wired.
        """
        if not self._config.sync_enabled:
            return None
        if self.is_live_ready():
            from adsl.foundry.client import get_foundry_client

            return get_foundry_client().read_ontology_object(object_type, primary_key)
        raise OntologySdkNotActiveError(
            "Live Ontology read requires ADSL_FOUNDRY_ENABLED=true and credentials."
        )

    def write_object(self, payload: dict[str, Any]) -> str:
        """
        Write a single object to the Palantir Ontology.

        Preparation phase: returns synthetic RID (same contract as ADR-006 placeholder).
        Live SDK path will replace this method body at Increment 2 activation.
        """
        if self.is_live_ready():
            from adsl.foundry.client import get_foundry_client

            return get_foundry_client().write_ontology_object(payload)
        object_type = payload.get("object_type", "Unknown")
        primary_key = payload.get("primary_key", "unknown")
        return f"ri.ontology.main.object.{object_type}.{primary_key}"

    def write_objects_batch(self, payloads: list[dict[str, Any]]) -> list[str]:
        """Batch write placeholder. Live SDK batching deferred to activation."""
        return [self.write_object(payload) for payload in payloads]


def get_sdk_client() -> OntologySdkClient:
    """Return a process-wide SDK client configured from environment."""
    return OntologySdkClient.from_env()