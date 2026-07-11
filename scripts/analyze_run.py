#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Generate automated analytics insights from ADSL simulation runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from adsl.analytics import (  # noqa: E402
    generate_insights_report,
    format_insights_markdown,
    format_insights_summary,
)
from adsl.export.runner import RunSpec, execute_run, load_run_bundle_from_export  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate explainable analytics insights from ADSL runs."
    )
    parser.add_argument("--scenario", help="Scenario ID for a live run.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42).")
    parser.add_argument("--ticks", type=int, default=50, help="Ticks for live runs (default 50).")
    parser.add_argument("--label", help="Optional label for live runs.")
    parser.add_argument(
        "--from-export",
        type=Path,
        help="Load run_bundle.json from an ADR-009 export directory.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON instead of text summary.",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Output full Markdown report.",
    )
    parser.add_argument(
        "--write",
        type=Path,
        help="Write report to file (extension determines format: .json / .md / .txt).",
    )
    parser.add_argument(
        "--verbose-logs",
        action="store_true",
        help="Show structlog JSON during live runs (quiet by default).",
    )
    return parser.parse_args()


def _load_bundle(args: argparse.Namespace) -> dict:
    if args.from_export is not None:
        return load_run_bundle_from_export(args.from_export)

    if not args.scenario:
        raise ValueError("Provide --scenario for a live run or --from-export for an export.")

    spec = RunSpec(
        scenario_id=args.scenario,
        seed=args.seed,
        ticks=args.ticks,
        label=args.label,
    )
    _, result = execute_run(spec, quiet_logs=not args.verbose_logs)
    return result.bundle


def main() -> int:
    args = _parse_args()
    try:
        bundle = _load_bundle(args)
        report = generate_insights_report(bundle)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.markdown:
        output = format_insights_markdown(report)
    elif args.json:
        output = json.dumps(report, indent=2)
    else:
        output = format_insights_summary(report)

    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(output, encoding="utf-8")
        print(f"Wrote insights to {args.write}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())