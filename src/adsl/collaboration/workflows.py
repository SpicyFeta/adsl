# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""High-level collaboration workflows combining session, export, and annotation steps."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from adsl.collaboration.annotations import add_annotation, load_annotations
from adsl.collaboration.session import link_run_to_session, load_session
from adsl.collaboration.schema import RUNS_DIR


def register_run_export(
    session_root: Path,
    export_run_dir: Path,
    *,
    author: str,
    label: str | None = None,
    copy_into_session: bool = True,
) -> dict[str, Any]:
    """
    Link an ADR-009 export directory to a workshop session.

    Optionally copies the export into the session ``runs/`` folder for sharing.
    """
    manifest_path = export_run_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json not found in {export_run_dir}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_id = manifest["run_id"]
    scenario_id = manifest["scenario_id"]

    if copy_into_session:
        target_dir = session_root / RUNS_DIR / run_id
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(export_run_dir, target_dir)
        export_path = str(target_dir.relative_to(session_root))
    else:
        export_path = str(export_run_dir)

    session = load_session(session_root)
    link_run_to_session(
        session,
        run_id=run_id,
        scenario_id=scenario_id,
        export_path=export_path,
        label=label,
        author=author,
        session_root=session_root,
    )

    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "export_path": export_path,
        "annotations": load_annotations(
            session_root / export_path if copy_into_session else export_run_dir
        ),
    }


def annotate_run_in_session(
    session_root: Path,
    run_id: str,
    *,
    author: str,
    text: str,
    target_kind: str = "run",
    target_id: str | None = None,
    simulation_tick: int | None = None,
) -> dict[str, Any]:
    """Add an annotation to a run registered in the session."""
    session = load_session(session_root)
    match = next(
        (ref for ref in session.get("run_refs", []) if ref["run_id"] == run_id),
        None,
    )
    if match is None:
        raise KeyError(f"Run {run_id} not registered in session {session['session_id']}")

    export_dir = session_root / match["export_path"]
    return add_annotation(
        export_dir,
        author=author,
        text=text,
        target_kind=target_kind,
        target_id=target_id,
        simulation_tick=simulation_tick,
    )