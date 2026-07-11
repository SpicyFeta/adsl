#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Launch the ADSL visualization dashboard for exported simulation runs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from adsl.viz.discovery import discover_runs  # noqa: E402
from adsl.viz.server import serve_dashboard  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch the ADSL web visualization dashboard (ADR-009 exports)."
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=PROJECT_ROOT / "exports",
        help="Directory containing run export bundles or a batch manifest.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8765, help="Bind port (default 8765).")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open a browser tab automatically.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    export_dir = args.export_dir.resolve()

    if not export_dir.exists():
        print(f"Export directory not found: {export_dir}", file=sys.stderr)
        return 1

    try:
        runs = discover_runs(export_dir)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not runs:
        print(
            f"No ADR-009 runs found under {export_dir}. "
            "Export a run first, e.g.:\n"
            "  python scripts/export_run.py --scenario island-chokepoint-v2 "
            "--ticks 100 --export-dir exports --quiet-logs",
            file=sys.stderr,
        )
        return 1

    print(f"Discovered {len(runs)} run(s) for visualization.")
    serve_dashboard(
        export_dir,
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())