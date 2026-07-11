# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Annotations and comments on simulation run results."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from adsl.collaboration.schema import ANNOTATIONS_FILENAME, COLLAB_SCHEMA_VERSION

VALID_TARGET_KINDS = {"run", "node", "route", "insight", "scenario"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _annotations_path(export_run_dir: Path) -> Path:
    return export_run_dir / ANNOTATIONS_FILENAME


def load_annotations(export_run_dir: Path) -> dict[str, Any]:
    """Load annotations for a run export directory."""
    path = _annotations_path(export_run_dir)
    if not path.exists():
        run_id = export_run_dir.name
        manifest_path = export_run_dir / "manifest.json"
        if manifest_path.exists():
            run_id = json.loads(manifest_path.read_text(encoding="utf-8")).get("run_id", run_id)
        return {
            "schema_version": COLLAB_SCHEMA_VERSION,
            "run_id": run_id,
            "annotations": [],
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != COLLAB_SCHEMA_VERSION:
        raise ValueError(f"Unsupported annotations schema: {data.get('schema_version')}")
    return data


def save_annotations(data: dict[str, Any], *, export_run_dir: Path) -> Path:
    path = _annotations_path(export_run_dir)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def add_annotation(
    export_run_dir: Path,
    *,
    author: str,
    text: str,
    target_kind: str = "run",
    target_id: str | None = None,
    simulation_tick: int | None = None,
) -> dict[str, Any]:
    """Add a comment annotation to a run export."""
    if target_kind not in VALID_TARGET_KINDS:
        raise ValueError(f"target_kind must be one of {sorted(VALID_TARGET_KINDS)}")

    data = load_annotations(export_run_dir)
    annotation = {
        "annotation_id": str(uuid4()),
        "author": author,
        "created_at": _utc_now_iso(),
        "text": text,
        "target_kind": target_kind,
        "target_id": target_id,
        "simulation_tick": simulation_tick,
    }
    data["annotations"].append(annotation)
    save_annotations(data, export_run_dir=export_run_dir)
    return annotation


def list_annotations(
    export_run_dir: Path,
    *,
    target_kind: str | None = None,
    author: str | None = None,
) -> list[dict[str, Any]]:
    """List annotations with optional filters."""
    data = load_annotations(export_run_dir)
    results = data.get("annotations", [])
    if target_kind:
        results = [item for item in results if item.get("target_kind") == target_kind]
    if author:
        results = [item for item in results if item.get("author") == author]
    return results