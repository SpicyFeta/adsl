# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""HTTP server tests for visualization dashboard."""

import json
import threading
from http.client import HTTPConnection
from pathlib import Path

from adsl.viz.server import create_server

EXPORTS_DIR = Path(__file__).resolve().parents[2] / "exports"


def _get_free_port_server(export_root: Path):
    server = create_server(export_root, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_api_runs_endpoint() -> None:
    if not EXPORTS_DIR.exists():
        return

    server, _thread = _get_free_port_server(EXPORTS_DIR)
    host, port = server.server_address

    try:
        conn = HTTPConnection(host, port, timeout=5)
        conn.request("GET", "/api/runs")
        response = conn.getresponse()
        assert response.status == 200
        data = json.loads(response.read().decode("utf-8"))
        assert "runs" in data
        assert len(data["runs"]) >= 1
        conn.close()
    finally:
        server.shutdown()


def test_api_viz_endpoint() -> None:
    if not EXPORTS_DIR.exists():
        return

    server, _thread = _get_free_port_server(EXPORTS_DIR)
    host, port = server.server_address

    try:
        conn = HTTPConnection(host, port, timeout=5)
        conn.request("GET", "/api/runs")
        runs = json.loads(conn.getresponse().read().decode("utf-8"))["runs"]
        run_id = runs[0]["run_id"]

        conn.request("GET", f"/api/viz/{run_id}")
        response = conn.getresponse()
        assert response.status == 200
        payload = json.loads(response.read().decode("utf-8"))
        assert payload["run_id"] == run_id
        assert "nodes" in payload
        assert "routes" in payload
        conn.close()
    finally:
        server.shutdown()


def test_api_insights_endpoint() -> None:
    if not EXPORTS_DIR.exists():
        return

    server, _thread = _get_free_port_server(EXPORTS_DIR)
    host, port = server.server_address

    try:
        conn = HTTPConnection(host, port, timeout=5)
        conn.request("GET", "/api/runs")
        runs = json.loads(conn.getresponse().read().decode("utf-8"))["runs"]
        run_id = runs[0]["run_id"]

        conn.request("GET", f"/api/insights/{run_id}")
        response = conn.getresponse()
        assert response.status == 200
        report = json.loads(response.read().decode("utf-8"))
        assert report["run_id"] == run_id
        assert "key_insights" in report
        assert "findings" in report
        conn.close()
    finally:
        server.shutdown()


def test_api_annotations_endpoint() -> None:
    if not EXPORTS_DIR.exists():
        return

    server, _thread = _get_free_port_server(EXPORTS_DIR)
    host, port = server.server_address

    try:
        conn = HTTPConnection(host, port, timeout=5)
        conn.request("GET", "/api/runs")
        runs = json.loads(conn.getresponse().read().decode("utf-8"))["runs"]
        run_id = runs[0]["run_id"]

        conn.request("GET", f"/api/annotations/{run_id}")
        response = conn.getresponse()
        assert response.status == 200
        doc = json.loads(response.read().decode("utf-8"))
        assert doc["run_id"] == run_id
        assert "annotations" in doc
        conn.close()
    finally:
        server.shutdown()


def test_api_compare_endpoint() -> None:
    if not EXPORTS_DIR.exists():
        return

    server, _thread = _get_free_port_server(EXPORTS_DIR)
    host, port = server.server_address

    try:
        conn = HTTPConnection(host, port, timeout=5)
        conn.request("GET", "/api/runs")
        runs = json.loads(conn.getresponse().read().decode("utf-8"))["runs"]
        if len(runs) < 2:
            conn.close()
            return

        baseline = runs[0]["run_id"]
        compare = runs[1]["run_id"]
        conn.request("GET", f"/api/compare?baseline={baseline}&compare={compare}")
        response = conn.getresponse()
        assert response.status == 200
        data = json.loads(response.read().decode("utf-8"))
        assert data["baseline"]["run_id"] == baseline
        assert data["compare"]["run_id"] == compare
        assert "metric_deltas" in data
        conn.close()
    finally:
        server.shutdown()


def test_dashboard_index_served() -> None:
    if not EXPORTS_DIR.exists():
        return

    server, _thread = _get_free_port_server(EXPORTS_DIR)
    host, port = server.server_address

    try:
        conn = HTTPConnection(host, port, timeout=5)
        conn.request("GET", "/")
        response = conn.getresponse()
        assert response.status == 200
        body = response.read().decode("utf-8")
        assert "ADSL Simulation Dashboard" in body
        conn.close()
    finally:
        server.shutdown()