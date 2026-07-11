# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Lightweight HTTP server for the ADSL visualization dashboard."""

from __future__ import annotations

import json
import mimetypes
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from adsl.export.runner import load_run_bundle_from_export
from adsl.viz.discovery import discover_runs
from adsl.analytics.report import generate_insights_report
from adsl.collaboration.annotations import load_annotations
from adsl.viz.compare import build_viz_comparison
from adsl.viz.transform import build_viz_payload

DASHBOARD_DIR = Path(__file__).resolve().parents[3] / "viz" / "dashboard"


class DashboardHandler(BaseHTTPRequestHandler):
    export_root: Path = Path("exports")
    dashboard_dir: Path = DASHBOARD_DIR

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(404, "Not found")
            return
        content_type, _ = mimetypes.guess_type(str(path))
        content_type = content_type or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/runs":
            try:
                runs = discover_runs(self.export_root)
                self._send_json({"export_root": str(self.export_root), "runs": runs})
            except FileNotFoundError as exc:
                self._send_json({"error": str(exc)}, status=404)
            return

        if path.startswith("/api/viz/"):
            run_id = path.removeprefix("/api/viz/").strip("/")
            try:
                runs = discover_runs(self.export_root)
                match = next((run for run in runs if run["run_id"] == run_id), None)
                if match is None:
                    self._send_json({"error": f"Run not found: {run_id}"}, status=404)
                    return
                bundle = load_run_bundle_from_export(Path(match["export_path"]))
                self._send_json(build_viz_payload(bundle))
            except (FileNotFoundError, json.JSONDecodeError) as exc:
                self._send_json({"error": str(exc)}, status=404)
            return

        if path.startswith("/api/insights/"):
            run_id = path.removeprefix("/api/insights/").strip("/")
            try:
                runs = discover_runs(self.export_root)
                match = next((run for run in runs if run["run_id"] == run_id), None)
                if match is None:
                    self._send_json({"error": f"Run not found: {run_id}"}, status=404)
                    return
                export_path = Path(match["export_path"])
                insights_path = export_path / "insights.json"
                if insights_path.exists():
                    report = json.loads(insights_path.read_text(encoding="utf-8"))
                else:
                    bundle = load_run_bundle_from_export(export_path)
                    report = generate_insights_report(bundle)
                self._send_json(report)
            except (FileNotFoundError, json.JSONDecodeError) as exc:
                self._send_json({"error": str(exc)}, status=404)
            return

        if path == "/api/compare":
            query = parse_qs(parsed.query)
            baseline_id = (query.get("baseline") or [None])[0]
            compare_id = (query.get("compare") or [None])[0]
            if not baseline_id or not compare_id:
                self._send_json(
                    {"error": "Provide baseline and compare query parameters."},
                    status=400,
                )
                return
            try:
                runs = discover_runs(self.export_root)
                baseline_match = next(
                    (run for run in runs if run["run_id"] == baseline_id),
                    None,
                )
                compare_match = next(
                    (run for run in runs if run["run_id"] == compare_id),
                    None,
                )
                if baseline_match is None or compare_match is None:
                    self._send_json({"error": "One or both runs not found."}, status=404)
                    return
                baseline_bundle = load_run_bundle_from_export(Path(baseline_match["export_path"]))
                compare_bundle = load_run_bundle_from_export(Path(compare_match["export_path"]))
                self._send_json(build_viz_comparison(baseline_bundle, compare_bundle))
            except (FileNotFoundError, json.JSONDecodeError) as exc:
                self._send_json({"error": str(exc)}, status=404)
            return

        if path.startswith("/api/annotations/"):
            run_id = path.removeprefix("/api/annotations/").strip("/")
            try:
                runs = discover_runs(self.export_root)
                match = next((run for run in runs if run["run_id"] == run_id), None)
                if match is None:
                    self._send_json({"error": f"Run not found: {run_id}"}, status=404)
                    return
                export_path = Path(match["export_path"])
                self._send_json(load_annotations(export_path))
            except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
                self._send_json({"error": str(exc)}, status=404)
            return

        if path == "/" or path == "":
            return self._send_file(self.dashboard_dir / "index.html")

        static_path = self.dashboard_dir / path.lstrip("/")
        if static_path.exists():
            return self._send_file(static_path)

        self.send_error(404, "Not found")


def create_server(
    export_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> ThreadingHTTPServer:
    export_root = export_root.resolve()
    handler = type(
        "ConfiguredDashboardHandler",
        (DashboardHandler,),
        {"export_root": export_root, "dashboard_dir": DASHBOARD_DIR},
    )
    return ThreadingHTTPServer((host, port), handler)


def serve_dashboard(
    export_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
) -> None:
    """Start the visualization dashboard HTTP server (blocking)."""
    server = create_server(export_root, host=host, port=port)
    url = f"http://{host}:{port}/"
    print(f"ADSL Visualization Dashboard")
    print(f"Export root: {export_root.resolve()}")
    print(f"Serving at:  {url}")
    print("Press Ctrl+C to stop.")

    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()