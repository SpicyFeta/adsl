#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Report Foundry integration configuration and readiness."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from adsl.foundry import FoundryClient  # noqa: E402
from adsl.ontology.sdk_client import OntologySdkClient  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ADSL Foundry integration status.")
    parser.add_argument("--json", action="store_true", help="Output structured JSON.")
    args = parser.parse_args()

    foundry = FoundryClient.from_env()
    ontology = OntologySdkClient.from_env()
    report = {
        "foundry": foundry.validate(),
        "ontology": ontology.validate_config(),
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        f = report["foundry"]
        o = report["ontology"]
        print("ADSL Foundry Integration Status")
        print(f"  Mode:              {f['mode']}")
        print(f"  Foundry enabled:   {f['foundry_enabled']}")
        print(f"  Live ready:        {f['live_ready']}")
        print(f"  Scenario dataset:  {f['scenario_dataset_rid'] or 'local:scenarios'}")
        print(f"  Results dataset:   {f['results_dataset_rid'] or 'local:results'}")
        print(f"  Local datasets:    {f['local_datasets_root']}")
        if f["missing_credentials"]:
            print(f"  Missing creds:     {', '.join(f['missing_credentials'])}")
        print()
        print("Ontology Sync")
        print(f"  Sync enabled:      {o['sync_enabled']}")
        print(f"  Live ready:        {o['live_ready']}")
        print(f"  Mode:              {o['mode']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())