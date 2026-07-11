# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Scenario version history tracking for collaborative workshops."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from adsl.collaboration.schema import COLLAB_SCHEMA_VERSION, VERSION_HISTORY_FILENAME


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _history_path(session_root: Path) -> Path:
    return session_root / VERSION_HISTORY_FILENAME


def load_version_history(session_root: Path) -> dict[str, Any]:
    """Load scenario version history for a session."""
    path = _history_path(session_root)
    if not path.exists():
        return {"schema_version": COLLAB_SCHEMA_VERSION, "scenarios": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != COLLAB_SCHEMA_VERSION:
        raise ValueError(f"Unsupported version history schema: {data.get('schema_version')}")
    return data


def save_version_history(history: dict[str, Any], *, session_root: Path) -> Path:
    path = _history_path(session_root)
    path.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return path


def append_scenario_version(
    *,
    session_root: Path,
    scenario_id: str,
    version_label: str,
    author: str,
    shared_path: str,
    changelog: str = "",
    parent_version_id: str | None = None,
    version_id: str | None = None,
) -> dict[str, Any]:
    """Append a version entry to scenario history."""
    history = load_version_history(session_root)
    version_entry = {
        "version_id": version_id or str(uuid4()),
        "version_label": version_label,
        "author": author,
        "exported_at": _utc_now_iso(),
        "shared_path": shared_path,
        "changelog": changelog,
        "parent_version_id": parent_version_id,
    }

    scenarios = history.setdefault("scenarios", {})
    versions = scenarios.setdefault(scenario_id, [])
    versions.append(version_entry)
    save_version_history(history, session_root=session_root)
    return version_entry