# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Parallel batch execution for multi-run analyst workloads."""

from __future__ import annotations

import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adsl.export.batch import BATCH_SCHEMA_VERSION
from adsl.export.bundle import EXPORT_SCHEMA_VERSION, SOURCE_SYSTEM, export_run_bundle
from adsl.export.compare import compare_runs, format_comparison_markdown
from adsl.export.runner import RunResult, RunSpec, execute_run

DEFAULT_MAX_WORKERS = max(1, (os.cpu_count() or 2) - 1)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _execute_run_worker(
    spec: RunSpec,
    synthetic_dir: str | None,
    quiet_logs: bool,
    scale_mode: bool,
) -> RunResult:
    """Process-pool worker: execute one run and return the result."""
    base = Path(synthetic_dir) if synthetic_dir else None
    _, result = execute_run(
        spec,
        synthetic_dir=base,
        quiet_logs=quiet_logs,
        scale_mode=scale_mode,
    )
    return result


def parallel_batch_export_runs(
    specs: list[RunSpec],
    export_dir: str | Path,
    *,
    synthetic_dir: Path | None = None,
    quiet_logs: bool = True,
    max_workers: int | None = None,
    scale_mode: bool = False,
) -> dict[str, Any]:
    """
    Execute multiple runs in parallel and export ADR-009 bundles.

    Uses a process pool to bypass the GIL for CPU-bound simulation loops.
    Export and manifest assembly happen in the parent process after workers finish.
    """
    if not specs:
        raise ValueError("parallel_batch_export_runs requires at least one RunSpec")

    export_root = Path(export_dir)
    export_root.mkdir(parents=True, exist_ok=True)
    workers = max_workers or DEFAULT_MAX_WORKERS
    workers = min(workers, len(specs))
    synthetic_str = str(synthetic_dir) if synthetic_dir else None

    results: list[RunResult] = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                _execute_run_worker,
                spec,
                synthetic_str,
                quiet_logs,
                scale_mode,
            ): spec
            for spec in specs
        }
        for future in as_completed(futures):
            results.append(future.result())

    spec_order = {spec.display_label(): index for index, spec in enumerate(specs)}
    results.sort(key=lambda item: spec_order.get(item.spec.display_label(), 0))

    for result in results:
        export_run_bundle(result.bundle, export_root)

    bundles = [result.bundle for result in results]
    comparison = compare_runs(bundles) if len(bundles) >= 2 else None

    manifest: dict[str, Any] = {
        "batch_schema_version": BATCH_SCHEMA_VERSION,
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "source_system": SOURCE_SYSTEM,
        "exported_at": _utc_now_iso(),
        "run_count": len(results),
        "parallel_workers": workers,
        "runs": [
            {
                "run_id": result.bundle["run"]["run_id"],
                "label": result.spec.label,
                "scenario_id": result.bundle["run"]["scenario_id"],
                "seed": result.bundle["execution"]["seed"],
                "ticks_executed": result.bundle["execution"]["ticks_executed"],
                "export_path": str(export_root / result.bundle["run"]["run_id"]),
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