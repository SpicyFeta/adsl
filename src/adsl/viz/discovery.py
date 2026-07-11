# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Discover simulation runs available for visualization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def discover_runs(export_root: Path) -> list[dict[str, Any]]:
    """
    Discover runs under an export directory.

    Supports:
    - Per-run ADR-009 directories containing run_bundle.json
    - Batch manifests (batch_manifest.json) at the export root
    """
    export_root = Path(export_root)
    if not export_root.exists():
        raise FileNotFoundError(f"Export directory not found: {export_root}")

    runs: list[dict[str, Any]] = []
    batch_manifest = export_root / "batch_manifest.json"
    if batch_manifest.exists():
        manifest = json.loads(batch_manifest.read_text(encoding="utf-8"))
        for entry in manifest.get("runs", []):
            runs.append(
                {
                    "run_id": entry["run_id"],
                    "label": entry.get("label"),
                    "scenario_id": entry["scenario_id"],
                    "seed": entry.get("seed"),
                    "export_path": entry.get("export_path")
                    or str(export_root / entry["run_id"]),
                }
            )
        return runs

    for child in sorted(export_root.iterdir()):
        if child.is_dir() and (child / "run_bundle.json").exists():
            manifest_path = child / "manifest.json"
            label = None
            scenario_id = None
            seed = None
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                scenario_id = manifest.get("scenario_id")
            bundle = json.loads((child / "run_bundle.json").read_text(encoding="utf-8"))
            run = bundle["run"]
            execution = bundle["execution"]
            runs.append(
                {
                    "run_id": run["run_id"],
                    "label": execution.get("label"),
                    "scenario_id": scenario_id or run["scenario_id"],
                    "seed": execution.get("seed"),
                    "export_path": str(child),
                }
            )

    return runs