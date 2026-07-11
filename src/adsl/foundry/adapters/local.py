# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Local filesystem adapter mimicking Foundry dataset layout (offline CI)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATASET_SCHEMA_VERSION = "1.0"


class LocalDatasetAdapter:
    """Read/write dataset records as JSONL under a local directory."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def _dataset_dir(self, dataset_key: str) -> Path:
        # Support alias keys like "local:scenarios" or raw RIDs mapped to folder names
        folder = dataset_key.removeprefix("local:")
        if folder.startswith("ri."):
            folder = folder.split(".")[-1]
        path = self._root / folder
        path.mkdir(parents=True, exist_ok=True)
        return path

    def read_records(
        self,
        dataset_key: str,
        *,
        record_type: str | None = None,
    ) -> list[dict[str, Any]]:
        records_path = self._dataset_dir(dataset_key) / "records.jsonl"
        if not records_path.exists():
            return []

        records: list[dict[str, Any]] = []
        for line in records_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record_type is None or record.get("record_type") == record_type:
                records.append(record)
        return records

    def write_records(
        self,
        dataset_key: str,
        records: list[dict[str, Any]],
        *,
        append: bool = True,
    ) -> dict[str, Any]:
        dataset_dir = self._dataset_dir(dataset_key)
        records_path = dataset_dir / "records.jsonl"
        manifest_path = dataset_dir / "manifest.json"

        mode = "a" if append and records_path.exists() else "w"
        with records_path.open(mode, encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record))
                handle.write("\n")

        existing_count = 0
        if records_path.exists():
            existing_count = sum(
                1 for line in records_path.read_text(encoding="utf-8").splitlines() if line.strip()
            )

        manifest = {
            "dataset_schema_version": DATASET_SCHEMA_VERSION,
            "dataset_key": dataset_key,
            "record_count": existing_count,
            "storage": "local_filesystem",
            "path": str(records_path),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        return {
            "dataset_key": dataset_key,
            "records_written": len(records),
            "total_records": existing_count,
            "path": str(dataset_dir),
        }