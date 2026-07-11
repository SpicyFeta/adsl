#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Import ADSL scenario packages from Palantir Foundry datasets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from adsl.foundry import (  # noqa: E402
    FoundryClient,
    import_scenario_from_foundry,
    publish_scenario_to_foundry,
)
from adsl.simulation.registry import resolve_scenario_path  # noqa: E402

SYNTHETIC_DIR = PROJECT_ROOT / "data" / "synthetic"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "foundry" / "imported"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import or publish ADSL scenarios via Foundry datasets (ADR-011)."
    )
    parser.add_argument("--json", action="store_true", help="Output structured JSON.")
    parser.add_argument(
        "--dataset-rid",
        help="Foundry dataset RID (default: local:scenarios or FOUNDRY_SCENARIO_DATASET_RID).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Directory for imported scenario JSON (default: {DEFAULT_OUTPUT}).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    imp = sub.add_parser("import", help="Import a scenario from a Foundry dataset.")
    imp.add_argument("--scenario-id", required=True, help="Scenario ID to import.")

    pub = sub.add_parser("publish", help="Publish a local scenario to a Foundry dataset.")
    pub.add_argument("--scenario", help="Scenario ID from registry.")
    pub.add_argument("--scenario-path", type=Path, help="Direct path to scenario JSON.")
    pub.add_argument(
        "--no-append",
        action="store_true",
        help="Overwrite dataset records instead of appending.",
    )

    return parser.parse_args()


def _cmd_import(args: argparse.Namespace) -> int:
    client = FoundryClient.from_env()
    package, record = import_scenario_from_foundry(
        args.scenario_id,
        dataset_rid=args.dataset_rid,
        client=client,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"{package.scenario.scenario_id}__foundry.json"
    output_path.write_text(
        json.dumps(package.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )

    result = {
        "scenario_id": package.scenario.scenario_id,
        "output_path": str(output_path),
        "lineage": record.get("lineage"),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Imported {result['scenario_id']} -> {result['output_path']}")
        print(f"  Lineage ID: {result['lineage']['lineage_id']}")
    return 0


def _cmd_publish(args: argparse.Namespace) -> int:
    if args.scenario_path:
        scenario_path = args.scenario_path
    elif args.scenario:
        scenario_path = resolve_scenario_path(args.scenario, synthetic_dir=SYNTHETIC_DIR)
    else:
        raise ValueError("Provide --scenario or --scenario-path.")

    client = FoundryClient.from_env()
    result = publish_scenario_to_foundry(
        scenario_path,
        dataset_rid=args.dataset_rid,
        client=client,
        append=not args.no_append,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Published {result['scenario_id']} to Foundry dataset")
        print(f"  Lineage ID: {result['lineage_id']}")
        print(f"  Write: {result['dataset_write']}")
    return 0


def main() -> int:
    args = _parse_args()
    try:
        if args.command == "import":
            return _cmd_import(args)
        if args.command == "publish":
            return _cmd_publish(args)
        raise ValueError(f"Unknown command: {args.command}")
    except (ValueError, KeyError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())