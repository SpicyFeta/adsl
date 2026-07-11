# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""HTTP adapter for live Palantir Foundry dataset and Ontology APIs (ADR-011)."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any

from adsl.foundry.config import FoundryConfig


class FoundryHttpError(RuntimeError):
    """Raised when a Foundry HTTP request fails."""


class HttpDatasetAdapter:
    """
    Live Foundry HTTP adapter.

    Uses Foundry REST conventions documented for stakeholder alignment.
    Dataset paths: /api/v1/datasets/{rid}/records
    Ontology paths: /api/v1/ontologies/{ontology_rid}/objects
    """

    def __init__(self, config: FoundryConfig) -> None:
        if not config.is_live_ready():
            raise FoundryHttpError(
                "HTTP adapter requires ADSL_FOUNDRY_ENABLED=true and credentials."
            )
        self._config = config
        self._base_url = config.foundry_url.rstrip("/")  # type: ignore[union-attr]

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._config.foundry_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict | list | None = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=data,
            headers=self._headers(),
            method=method,
        )
        context = ssl.create_default_context()
        try:
            with urllib.request.urlopen(request, context=context, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise FoundryHttpError(
                f"Foundry HTTP {exc.code} for {method} {path}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise FoundryHttpError(f"Foundry connection error for {url}: {exc}") from exc

    def read_records(
        self,
        dataset_rid: str,
        *,
        record_type: str | None = None,
    ) -> list[dict[str, Any]]:
        path = f"/api/v1/datasets/{dataset_rid}/records"
        if record_type:
            path += f"?record_type={record_type}"
        payload = self._request("GET", path)
        if isinstance(payload, list):
            return payload
        return payload.get("records", [])

    def write_records(
        self,
        dataset_rid: str,
        records: list[dict[str, Any]],
        *,
        append: bool = True,
    ) -> dict[str, Any]:
        path = f"/api/v1/datasets/{dataset_rid}/records"
        body = {"records": records, "append": append}
        result = self._request("POST", path, body=body)
        return {
            "dataset_rid": dataset_rid,
            "records_written": len(records),
            "response": result,
        }

    def write_ontology_object(self, payload: dict[str, Any]) -> str:
        ontology_rid = self._config.ontology_rid
        object_type = payload["object_type"]
        path = f"/api/v1/ontologies/{ontology_rid}/objects/{object_type}"
        result = self._request("POST", path, body=payload)
        return result.get("rid") or result.get("primaryKey") or payload["primary_key"]

    def write_ontology_objects_batch(self, payloads: list[dict[str, Any]]) -> list[str]:
        return [self.write_ontology_object(payload) for payload in payloads]

    def read_ontology_object(
        self,
        object_type: str,
        primary_key: str,
    ) -> dict[str, Any] | None:
        ontology_rid = self._config.ontology_rid
        path = f"/api/v1/ontologies/{ontology_rid}/objects/{object_type}/{primary_key}"
        try:
            return self._request("GET", path)
        except FoundryHttpError:
            return None