# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Batch export utilities for analyst workflows."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adsl.export.bundle import EXPORT_SCHEMA_VERSION, SOURCE_SYSTEM, export_run_bundle
from adsl.export.compare import compare_runs, format_comparison_markdown
from adsl.export.runner import RunResult, RunSpec, execute_run

BATCH_SCHEMA_VERSION = "1.0"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def batch_export_runs(
    specs: list[RunSpec],
    export_dir: str | Path,
    *,
    synthetic_dir: Path | None = None,
    quiet_logs: bool = True,
    workers: int = 1,
    scale_mode: bool = False,
) -> dict[str, Any]:
    """
    Execute multiple runs and export ADR-009 bundles plus a batch manifest.

    Layout:
      {export_dir}/
        batch_manifest.json
        comparison_summary.md
        {run_id}/  (per-run ADR-009 bundle)
    """
    if not specs:
        raise ValueError("batch_export_runs requires at least one RunSpec")

    if workers > 1:
        from adsl.performance.parallel import parallel_batch_export_runs

        return parallel_batch_export_runs(
            specs,
            export_dir,
            synthetic_dir=synthetic_dir,
            quiet_logs=quiet_logs,
            max_workers=workers,
            scale_mode=scale_mode,
        )

    export_root = Path(export_dir)
    export_root.mkdir(parents=True, exist_ok=True)

    results: list[RunResult] = []
    for spec in specs:
        _, result = execute_run(
            spec,
            synthetic_dir=synthetic_dir,
            quiet_logs=quiet_logs,
            scale_mode=scale_mode,
        )
        export_path = export_run_bundle(result.bundle, export_root)
        results.append(result)

    bundles = [result.bundle for result in results]
    comparison = compare_runs(bundles) if len(bundles) >= 2 else None

    manifest: dict[str, Any] = {
        "batch_schema_version": BATCH_SCHEMA_VERSION,
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "source_system": SOURCE_SYSTEM,
        "exported_at": _utc_now_iso(),
        "run_count": len(results),
        "runs": [
            {
                "run_id": result.bundle["run"]["run_id"],
                "label": result.spec.label,
                "scenario_id": result.bundle["run"]["scenario_id"],
                "seed": result.bundle["execution"]["seed"],
                "ticks_executed": result.bundle["execution"]["ticks_executed"],
                "export_path": str(
                    export_root / result.bundle["run"]["run_id"]
                ),
                "red_pacing_overrides": result.spec.red_pacing_overrides or None,
            }
            for result in results
        ],
    }
    if comparison is not None:
        manifest["comparison"] = comparison

    (export_root / "batch_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    if comparison is not None:
        (export_root / "comparison_summary.md").write_text(
            format_comparison_markdown(comparison),
            encoding="utf-8",
        )

    return manifest