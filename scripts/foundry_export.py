#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Export ADSL simulation results to Palantir Foundry datasets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from adsl.export.runner import RunSpec, execute_run, load_run_bundle_from_export  # noqa: E402
from adsl.foundry import (  # noqa: E402
    FoundryClient,
    build_foundry_export_records,
    export_run_to_foundry_dataset,
)

SYNTHETIC_DIR = PROJECT_ROOT / "data" / "synthetic"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export ADSL simulation results to Foundry datasets (ADR-011)."
    )
    parser.add_argument("--json", action="store_true", help="Output structured JSON.")
    parser.add_argument(
        "--dataset-rid",
        help="Foundry results dataset RID (default: local:results or env).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build export records without writing to dataset.",
    )
    parser.add_argument(
        "--no-ontology",
        action="store_true",
        help="Skip Ontology object sync even when enabled.",
    )
    parser.add_argument(
        "--verbose-logs",
        action="store_true",
        help="Show structlog JSON during live runs.",
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--from-export", type=Path, help="ADR-009 export directory.")
    source.add_argument("--scenario", help="Run scenario live then export.")
    source.add_argument("--records-only", action="store_true", help="With --from-export, print records.")

    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ticks", type=int, default=50)
    parser.add_argument("--label", help="Optional run label for live runs.")
    return parser.parse_args()


def _load_bundle(args: argparse.Namespace) -> tuple[dict, Path | None]:
    if args.from_export is not None:
        return load_run_bundle_from_export(args.from_export), args.from_export
    if not args.scenario:
        raise ValueError("Provide --scenario for a live run.")

    spec = RunSpec(
        scenario_id=args.scenario,
        seed=args.seed,
        ticks=args.ticks,
        label=args.label,
    )
    _, result = execute_run(spec, synthetic_dir=SYNTHETIC_DIR, quiet_logs=not args.verbose_logs)
    return result.bundle, None


def main() -> int:
    args = _parse_args()
    try:
        bundle, export_dir = _load_bundle(args)
        client = FoundryClient.from_env()

        if args.records_only and args.from_export:
            records = build_foundry_export_records(
                bundle,
                parent_dataset_rid=args.dataset_rid or client.config.results_dataset_rid,
                export_dir=export_dir,
            )
            print(json.dumps(records, indent=2))
            return 0

        if args.dry_run:
            records = build_foundry_export_records(
                bundle,
                parent_dataset_rid=args.dataset_rid or client.config.results_dataset_rid,
                export_dir=export_dir,
            )
            result = {
                "dry_run": True,
                "records_built": len(records),
                "record_types": sorted({record["record_type"] for record in records}),
                "run_id": bundle["run"]["run_id"],
            }
        else:
            if args.no_ontology:
                import os

                os.environ["ADSL_ONTOLOGY_SYNC_ENABLED"] = "false"
                client = FoundryClient.from_env()

            result = export_run_to_foundry_dataset(
                bundle,
                dataset_rid=args.dataset_rid,
                client=client,
                export_dir=export_dir,
            )

        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            if result.get("dry_run"):
                print(f"Dry run: {result['records_built']} records for {result['run_id']}")
                print(f"  Types: {', '.join(result['record_types'])}")
            else:
                write = result["dataset_write"]
                print(f"Exported run {bundle['run']['run_id']}")
                print(f"  Records: {result['records_exported']}")
                print(f"  Audit traces: {result['audit_traces_exported']}")
                print(f"  Lineage ID: {result['lineage_id']}")
                print(f"  Dataset write: {write}")
                if result["ontology_objects_written"]:
                    print(f"  Ontology objects: {result['ontology_objects_written']}")
        return 0
    except (ValueError, FileNotFoundError, RuntimeError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())