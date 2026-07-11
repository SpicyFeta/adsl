# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Formatters for collaboration session summaries."""

from __future__ import annotations

from typing import Any


def format_session_summary(session: dict[str, Any]) -> str:
    """Render a human-readable workshop session summary."""
    lines = [
        f"# Workshop Session — {session['name']}",
        "",
        f"**Session ID:** `{session['session_id']}`  ",
        f"**Created:** {session['created_at']}  ",
        f"**Updated:** {session.get('updated_at', '—')}",
        "",
    ]
    if session.get("description"):
        lines.extend([session["description"], ""])

    lines.append("## Participants")
    for participant in session.get("participants", []):
        lines.append(
            f"- {participant['display_name']} ({participant.get('role', 'analyst')})"
        )
    if not session.get("participants"):
        lines.append("- _(none registered)_")

    lines.extend(["", "## Shared Scenarios"])
    for ref in session.get("scenario_refs", []):
        lines.append(
            f"- `{ref['scenario_id']}` — {ref.get('version_label', '?')} "
            f"by {ref.get('linked_by', '?')}"
        )
    if not session.get("scenario_refs"):
        lines.append("- _(none linked)_")

    lines.extend(["", "## Linked Runs"])
    for ref in session.get("run_refs", []):
        label = ref.get("label") or ref["run_id"][:12]
        lines.append(f"- {label} · {ref['scenario_id']} · `{ref['run_id']}`")
    if not session.get("run_refs"):
        lines.append("- _(none linked)_")

    recent = session.get("activity_log", [])[-5:]
    if recent:
        lines.extend(["", "## Recent Activity"])
        for entry in recent:
            lines.append(
                f"- {entry['timestamp']} · {entry.get('actor', '?')}: "
                f"{entry.get('action', '?')}"
            )

    return "\n".join(lines)


def format_annotations_markdown(annotations_doc: dict[str, Any]) -> str:
    """Render run annotations as Markdown."""
    lines = [
        f"# Run Annotations — `{annotations_doc.get('run_id', '?')}`",
        "",
    ]
    for item in annotations_doc.get("annotations", []):
        target = item.get("target_kind", "run")
        target_id = item.get("target_id") or "—"
        tick = item.get("simulation_tick")
        tick_str = f" tick {tick}" if tick is not None else ""
        lines.append(
            f"- **{item['author']}** ({item['created_at']}) · "
            f"{target}/{target_id}{tick_str}: {item['text']}"
        )
    if not annotations_doc.get("annotations"):
        lines.append("_No annotations yet._")
    return "\n".join(lines)