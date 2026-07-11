# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Workshop session management for multi-user collaboration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from adsl.collaboration.schema import (
    COLLAB_SCHEMA_VERSION,
    RUNS_DIR,
    SESSION_FILENAME,
    SHARED_SCENARIOS_DIR,
)

DEFAULT_SESSIONS_ROOT = Path(__file__).resolve().parents[3] / "data" / "collaboration" / "sessions"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _session_path(session_root: Path) -> Path:
    return session_root / SESSION_FILENAME


def create_session(
    name: str,
    *,
    description: str = "",
    facilitator: str | None = None,
    sessions_root: Path | None = None,
) -> dict[str, Any]:
    """Create a new workshop session directory and manifest."""
    root = sessions_root or DEFAULT_SESSIONS_ROOT
    session_id = str(uuid4())
    session_root = root / session_id
    session_root.mkdir(parents=True, exist_ok=True)
    (session_root / SHARED_SCENARIOS_DIR).mkdir(exist_ok=True)
    (session_root / RUNS_DIR).mkdir(exist_ok=True)

    participants: list[dict[str, Any]] = []
    if facilitator:
        participants.append(
            {
                "participant_id": str(uuid4()),
                "display_name": facilitator,
                "role": "facilitator",
                "joined_at": _utc_now_iso(),
            }
        )

    session = {
        "schema_version": COLLAB_SCHEMA_VERSION,
        "session_id": session_id,
        "name": name,
        "description": description,
        "created_at": _utc_now_iso(),
        "updated_at": _utc_now_iso(),
        "participants": participants,
        "scenario_refs": [],
        "run_refs": [],
        "activity_log": [
            {
                "timestamp": _utc_now_iso(),
                "actor": facilitator or "system",
                "action": "session_created",
                "details": {"name": name},
            }
        ],
    }
    save_session(session, session_root=session_root)
    session["_session_root"] = str(session_root)
    return session


def load_session(session_root: Path) -> dict[str, Any]:
    """Load a session manifest from its directory."""
    path = _session_path(session_root)
    if not path.exists():
        raise FileNotFoundError(f"Session manifest not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != COLLAB_SCHEMA_VERSION:
        raise ValueError(f"Unsupported session schema: {data.get('schema_version')}")
    return data


def save_session(session: dict[str, Any], *, session_root: Path) -> Path:
    """Persist session manifest to disk."""
    session = {key: value for key, value in session.items() if not key.startswith("_")}
    session["updated_at"] = _utc_now_iso()
    path = _session_path(session_root)
    path.write_text(json.dumps(session, indent=2), encoding="utf-8")
    return path


def add_participant(
    session: dict[str, Any],
    *,
    display_name: str,
    role: str = "analyst",
    session_root: Path,
) -> dict[str, Any]:
    """Register a participant on the workshop session."""
    participant = {
        "participant_id": str(uuid4()),
        "display_name": display_name,
        "role": role,
        "joined_at": _utc_now_iso(),
    }
    session["participants"].append(participant)
    session.setdefault("activity_log", []).append(
        {
            "timestamp": _utc_now_iso(),
            "actor": display_name,
            "action": "participant_joined",
            "details": {"role": role},
        }
    )
    save_session(session, session_root=session_root)
    return participant


def link_scenario_to_session(
    session: dict[str, Any],
    *,
    scenario_id: str,
    version_id: str,
    version_label: str,
    shared_path: str,
    author: str,
    session_root: Path,
) -> None:
    """Record a shared scenario reference on the session."""
    ref = {
        "scenario_id": scenario_id,
        "version_id": version_id,
        "version_label": version_label,
        "shared_path": shared_path,
        "linked_at": _utc_now_iso(),
        "linked_by": author,
    }
    session["scenario_refs"] = [
        existing
        for existing in session.get("scenario_refs", [])
        if existing.get("version_id") != version_id
    ]
    session["scenario_refs"].append(ref)
    session.setdefault("activity_log", []).append(
        {
            "timestamp": _utc_now_iso(),
            "actor": author,
            "action": "scenario_linked",
            "details": {"scenario_id": scenario_id, "version_label": version_label},
        }
    )
    save_session(session, session_root=session_root)


def link_run_to_session(
    session: dict[str, Any],
    *,
    run_id: str,
    scenario_id: str,
    export_path: str,
    label: str | None,
    author: str,
    session_root: Path,
) -> None:
    """Record a simulation run export on the session."""
    ref = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "export_path": export_path,
        "label": label,
        "linked_at": _utc_now_iso(),
        "linked_by": author,
    }
    session["run_refs"] = [
        existing for existing in session.get("run_refs", []) if existing.get("run_id") != run_id
    ]
    session["run_refs"].append(ref)
    session.setdefault("activity_log", []).append(
        {
            "timestamp": _utc_now_iso(),
            "actor": author,
            "action": "run_linked",
            "details": {"run_id": run_id, "scenario_id": scenario_id},
        }
    )
    save_session(session, session_root=session_root)


def list_sessions(sessions_root: Path | None = None) -> list[dict[str, Any]]:
    """List all workshop sessions under the sessions root."""
    root = sessions_root or DEFAULT_SESSIONS_ROOT
    if not root.exists():
        return []
    sessions: list[dict[str, Any]] = []
    for child in sorted(root.iterdir()):
        manifest = child / SESSION_FILENAME
        if child.is_dir() and manifest.exists():
            data = load_session(child)
            sessions.append(
                {
                    "session_id": data["session_id"],
                    "name": data["name"],
                    "created_at": data["created_at"],
                    "participant_count": len(data.get("participants", [])),
                    "scenario_count": len(data.get("scenario_refs", [])),
                    "run_count": len(data.get("run_refs", [])),
                    "session_root": str(child),
                }
            )
    return sessions