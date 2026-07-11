# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Shareable scenario export and import for team collaboration."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from adsl.collaboration.schema import COLLAB_SCHEMA_VERSION, SHARED_SCENARIOS_DIR
from adsl.collaboration.session import link_scenario_to_session, load_session
from adsl.collaboration.versioning import append_scenario_version, load_version_history
from adsl.simulation.loader import load_scenario_package

SHARE_SCHEMA_VERSION = "1.0"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _content_fingerprint(package_dict: dict[str, Any]) -> str:
    canonical = json.dumps(package_dict, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def export_shared_scenario(
    scenario_path: Path,
    session_root: Path,
    *,
    author: str,
    version_label: str,
    changelog: str = "",
    parent_version_id: str | None = None,
) -> dict[str, Any]:
    """
    Export a scenario package into a session's shared_scenarios directory.

    Returns the share manifest including version_id and fingerprint.
    """
    package = load_scenario_package(scenario_path)
    content = package.model_dump(mode="json")
    scenario_id = package.scenario.scenario_id

    share_dir = session_root / SHARED_SCENARIOS_DIR
    share_dir.mkdir(parents=True, exist_ok=True)

    version_id = str(uuid4())
    filename = f"{scenario_id}__{version_label.replace(' ', '_')}__{version_id[:8]}.json"
    shared_path = share_dir / filename

    share_manifest = {
        "share_schema_version": SHARE_SCHEMA_VERSION,
        "collab_schema_version": COLLAB_SCHEMA_VERSION,
        "version_id": version_id,
        "parent_version_id": parent_version_id,
        "scenario_id": scenario_id,
        "version_label": version_label,
        "author": author,
        "changelog": changelog,
        "exported_at": _utc_now_iso(),
        "source_path": str(scenario_path),
        "content_fingerprint": _content_fingerprint(content),
        "scenario_package": content,
    }
    shared_path.write_text(json.dumps(share_manifest, indent=2), encoding="utf-8")

    version_entry = append_scenario_version(
        session_root=session_root,
        scenario_id=scenario_id,
        version_label=version_label,
        author=author,
        shared_path=str(shared_path.relative_to(session_root)),
        changelog=changelog,
        parent_version_id=parent_version_id,
        version_id=version_id,
    )

    session = load_session(session_root)
    link_scenario_to_session(
        session,
        scenario_id=scenario_id,
        version_id=version_entry["version_id"],
        version_label=version_label,
        shared_path=str(shared_path.relative_to(session_root)),
        author=author,
        session_root=session_root,
    )

    return {
        "version_id": version_id,
        "scenario_id": scenario_id,
        "version_label": version_label,
        "shared_path": str(shared_path),
        "content_fingerprint": share_manifest["content_fingerprint"],
    }


def import_shared_scenario(
    shared_manifest_path: Path,
    *,
    output_dir: Path,
    overwrite: bool = False,
) -> Path:
    """
    Import a shared scenario manifest into a local scenarios directory.

    Writes a plain ADSL_ScenarioPackage JSON suitable for simulation runs.
    """
    data = json.loads(shared_manifest_path.read_text(encoding="utf-8"))
    if data.get("share_schema_version") != SHARE_SCHEMA_VERSION:
        raise ValueError(f"Unsupported share schema: {data.get('share_schema_version')}")

    scenario_id = data["scenario_id"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{scenario_id}__imported.json"
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Scenario already imported at {output_path}")

    package = data["scenario_package"]
    load_scenario_package_from_dict(package)  # validate
    output_path.write_text(json.dumps(package, indent=2), encoding="utf-8")
    return output_path


def load_scenario_package_from_dict(data: dict[str, Any]):
    """Validate scenario package dict (helper to avoid circular imports in tests)."""
    from adsl.models import ADSL_ScenarioPackage

    return ADSL_ScenarioPackage.model_validate(data)


def resolve_latest_shared_scenario(
    session_root: Path,
    scenario_id: str,
) -> Path | None:
    """Return the path to the latest shared scenario version for a scenario_id."""
    history = load_version_history(session_root)
    versions = history.get("scenarios", {}).get(scenario_id, [])
    if not versions:
        return None
    latest = versions[-1]
    return session_root / latest["shared_path"]