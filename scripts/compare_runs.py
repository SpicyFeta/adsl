#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Compare multiple ADSL simulation runs (live execution or existing exports)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from adsl.analytics.what_if import compare_what_if  # noqa: E402
from adsl.analytics.format import format_what_if_markdown  # noqa: E402
from adsl.export.compare import compare_runs, format_comparison_markdown, format_comparison_table  # noqa: E402
from adsl.export.runner import RunSpec, execute_run, load_run_bundle_from_export  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two or more ADSL simulation runs."
    )
    parser.add_argument(
        "--specs",
        type=Path,
        help="JSON file with a list of run specifications.",
    )
    parser.add_argument(
        "--from-exports",
        type=Path,
        help="Directory containing one or more ADR-009 run export subdirectories.",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        default=[],
        help="Scenario ID (repeat for multiple runs). Pair with --seed and --label.",
    )
    parser.add_argument(
        "--seed",
        action="append",
        type=int,
        default=[],
        help="Random seed per run (repeat; defaults to 42 when omitted).",
    )
    parser.add_argument(
        "--label",
        action="append",
        default=[],
        help="Optional label per run.",
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=50,
        help="Ticks for live runs (default 50).",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Output Markdown instead of a terminal table.",
    )
    parser.add_argument(
        "--quiet-logs",
        action="store_true",
        help="Suppress structlog JSON during live runs.",
    )
    parser.add_argument(
        "--what-if",
        action="store_true",
        help="Include insight-level what-if analysis (requires --markdown for full report).",
    )
    return parser.parse_args()


def _load_specs_from_json(path: Path, default_ticks: int) -> list[RunSpec]:
    data = json.loads(path.read_text(encoding="utf-8"))
    ticks = data.get("ticks", default_ticks)
    runs = data["runs"]
    specs: list[RunSpec] = []
    for entry in runs:
        pacing = entry.get("red_pacing") or entry.get("red_pacing_overrides") or {}
        specs.append(
            RunSpec(
                scenario_id=entry["scenario"],
                seed=entry.get("seed", 42),
                ticks=entry.get("ticks", ticks),
                label=entry.get("label"),
                red_pacing_overrides=pacing,
            )
        )
    return specs


def _build_specs_from_cli(args: argparse.Namespace) -> list[RunSpec]:
    if not args.scenario:
        return []
    specs: list[RunSpec] = []
    for index, scenario_id in enumerate(args.scenario):
        seed = args.seed[index] if index < len(args.seed) else 42
        label = args.label[index] if index < len(args.label) else None
        specs.append(
            RunSpec(
                scenario_id=scenario_id,
                seed=seed,
                ticks=args.ticks,
                label=label,
            )
        )
    return specs


def _load_bundles_from_exports(export_root: Path) -> list[dict]:
    bundles: list[dict] = []
    for child in sorted(export_root.iterdir()):
        if child.is_dir() and (child / "run_bundle.json").exists():
            bundles.append(load_run_bundle_from_export(child))
    if len(bundles) < 2:
        raise ValueError(
            f"Expected at least two export directories under {export_root}"
        )
    return bundles


def main() -> int:
    args = _parse_args()
    bundles: list[dict] = []

    try:
        if args.from_exports is not None:
            bundles = _load_bundles_from_exports(args.from_exports)
        else:
            specs: list[RunSpec] = []
            if args.specs is not None:
                specs = _load_specs_from_json(args.specs, args.ticks)
            specs.extend(_build_specs_from_cli(args))

            if len(specs) < 2:
                print(
                    "Provide at least two runs via --scenario (repeat), --specs, "
                    "or --from-exports.",
                    file=sys.stderr,
                )
                return 1

            for spec in specs:
                _, result = execute_run(spec, quiet_logs=args.quiet_logs)
                bundles.append(result.bundle)
    except (ValueError, FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.what_if:
        comparison = compare_what_if(bundles)
        if args.markdown:
            print(format_what_if_markdown(comparison))
        else:
            metric = comparison["metric_comparison"]
            print(format_comparison_table(metric))
            print()
            print("What-If Insight Changes")
            print("=" * 72)
            for block in comparison["what_if_deltas"]:
                print(f"\n{block['compare_label']} vs {block['baseline_label']}:")
                if not block["key_insight_changes"]:
                    print("  (no significant insight-level changes)")
                else:
                    for change in block["key_insight_changes"]:
                        print(f"  • {change}")
            for pattern in comparison.get("cross_run_patterns", [])[:3]:
                print(f"  • [cross-run] {pattern['summary']}")
            structured = comparison.get("actionable_recommendations", [])
            if structured:
                print("\nStructured recommendations:")
                for rec in structured[:6]:
                    print(f"  [{rec['priority']}] {rec['action']}")
            elif comparison["recommendations"]:
                print("\nRecommendations:")
                for rec in comparison["recommendations"]:
                    print(f"  • {rec}")
    else:
        comparison = compare_runs(bundles)
        if args.markdown:
            print(format_comparison_markdown(comparison))
        else:
            print(format_comparison_table(comparison))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())