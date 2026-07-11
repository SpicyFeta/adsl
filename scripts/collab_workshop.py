#!/usr/bin/env python3

# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Workshop collaboration CLI — sessions, scenario sharing, run linking, annotations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from adsl.collaboration.annotations import add_annotation, list_annotations, load_annotations  # noqa: E402
from adsl.collaboration.format import format_annotations_markdown, format_session_summary  # noqa: E402
from adsl.collaboration.scenario_share import (  # noqa: E402
    export_shared_scenario,
    import_shared_scenario,
    resolve_latest_shared_scenario,
)
from adsl.collaboration.session import (  # noqa: E402
    DEFAULT_SESSIONS_ROOT,
    add_participant,
    create_session,
    list_sessions,
    load_session,
)
from adsl.collaboration.versioning import load_version_history  # noqa: E402
from adsl.collaboration.workflows import annotate_run_in_session, register_run_export  # noqa: E402
from adsl.simulation.registry import resolve_scenario_path  # noqa: E402

SYNTHETIC_DIR = PROJECT_ROOT / "data" / "synthetic"


def _resolve_session_root(args: argparse.Namespace) -> Path:
    if args.session:
        path = Path(args.session)
        if path.is_dir() and (path / "session.json").exists():
            return path
        candidate = DEFAULT_SESSIONS_ROOT / args.session
        if candidate.is_dir():
            return candidate
        raise FileNotFoundError(f"Session not found: {args.session}")
    raise ValueError("--session is required for this command")


def _cmd_session_create(args: argparse.Namespace) -> int:
    session = create_session(
        args.name,
        description=args.description or "",
        facilitator=args.facilitator,
        sessions_root=Path(args.sessions_root) if args.sessions_root else None,
    )
    if args.json:
        print(json.dumps(session, indent=2))
    else:
        print(format_session_summary(session))
        print(f"\nSession root: {session['_session_root']}")
    return 0


def _cmd_session_list(args: argparse.Namespace) -> int:
    root = Path(args.sessions_root) if args.sessions_root else DEFAULT_SESSIONS_ROOT
    sessions = list_sessions(root)
    if args.json:
        print(json.dumps(sessions, indent=2))
    else:
        if not sessions:
            print("No workshop sessions found.")
            return 0
        for item in sessions:
            print(
                f"{item['name']} · {item['session_id'][:8]}… · "
                f"{item['participant_count']} participants · "
                f"{item['scenario_count']} scenarios · {item['run_count']} runs"
            )
            print(f"  {item['session_root']}")
    return 0


def _cmd_session_show(args: argparse.Namespace) -> int:
    session_root = _resolve_session_root(args)
    session = load_session(session_root)
    if args.json:
        print(json.dumps(session, indent=2))
    else:
        print(format_session_summary(session))
    return 0


def _cmd_participant_add(args: argparse.Namespace) -> int:
    session_root = _resolve_session_root(args)
    session = load_session(session_root)
    participant = add_participant(
        session,
        display_name=args.name,
        role=args.role,
        session_root=session_root,
    )
    if args.json:
        print(json.dumps(participant, indent=2))
    else:
        print(f"Added participant: {participant['display_name']} ({participant['role']})")
    return 0


def _cmd_scenario_share(args: argparse.Namespace) -> int:
    session_root = _resolve_session_root(args)
    scenario_path = (
        Path(args.scenario_path)
        if args.scenario_path
        else resolve_scenario_path(args.scenario, synthetic_dir=SYNTHETIC_DIR)
    )
    result = export_shared_scenario(
        scenario_path,
        session_root,
        author=args.author,
        version_label=args.label,
        changelog=args.changelog or "",
        parent_version_id=args.parent_version,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"Shared {result['scenario_id']} as '{result['version_label']}' "
            f"(version {result['version_id'][:8]}…)"
        )
        print(f"  Path: {result['shared_path']}")
        print(f"  Fingerprint: {result['content_fingerprint']}")
    return 0


def _cmd_scenario_import(args: argparse.Namespace) -> int:
    session_root = _resolve_session_root(args)
    if args.latest:
        shared_path = resolve_latest_shared_scenario(session_root, args.scenario)
        if shared_path is None:
            raise FileNotFoundError(f"No shared versions for scenario {args.scenario}")
    else:
        shared_path = Path(args.shared_path)

    output_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / "data" / "collaboration" / "imported"
    output_path = import_shared_scenario(
        shared_path,
        output_dir=output_dir,
        overwrite=args.overwrite,
    )
    if args.json:
        print(json.dumps({"output_path": str(output_path)}, indent=2))
    else:
        print(f"Imported scenario to {output_path}")
    return 0


def _cmd_scenario_history(args: argparse.Namespace) -> int:
    session_root = _resolve_session_root(args)
    history = load_version_history(session_root)
    if args.scenario:
        versions = history.get("scenarios", {}).get(args.scenario, [])
        payload = {"scenario_id": args.scenario, "versions": versions}
    else:
        payload = history
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        scenarios = payload.get("scenarios", payload)
        if isinstance(scenarios, dict):
            for scenario_id, versions in scenarios.items():
                print(f"\n{scenario_id} ({len(versions)} versions)")
                for version in versions:
                    print(
                        f"  - {version['version_label']} by {version['author']} "
                        f"({version['version_id'][:8]}…)"
                    )
        else:
            print("No version history.")
    return 0


def _cmd_run_link(args: argparse.Namespace) -> int:
    session_root = _resolve_session_root(args)
    export_dir = Path(args.export_dir)
    result = register_run_export(
        session_root,
        export_dir,
        author=args.author,
        label=args.label,
        copy_into_session=not args.no_copy,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Linked run {result['run_id']} ({result['scenario_id']})")
        print(f"  Export path: {result['export_path']}")
    return 0


def _cmd_annotate_add(args: argparse.Namespace) -> int:
    session_root = _resolve_session_root(args)
    annotation = annotate_run_in_session(
        session_root,
        args.run_id,
        author=args.author,
        text=args.text,
        target_kind=args.target_kind,
        target_id=args.target_id,
        simulation_tick=args.tick,
    )
    if args.json:
        print(json.dumps(annotation, indent=2))
    else:
        print(f"Annotation added by {annotation['author']}: {annotation['text']}")
    return 0


def _cmd_annotate_list(args: argparse.Namespace) -> int:
    if args.export_dir:
        export_dir = Path(args.export_dir)
    else:
        session_root = _resolve_session_root(args)
        session = load_session(session_root)
        match = next(
            (ref for ref in session.get("run_refs", []) if ref["run_id"] == args.run_id),
            None,
        )
        if match is None:
            raise KeyError(f"Run {args.run_id} not registered in session")
        export_dir = session_root / match["export_path"]

    annotations = list_annotations(
        export_dir,
        target_kind=args.target_kind,
        author=args.author_filter,
    )
    if args.markdown:
        doc = load_annotations(export_dir)
        doc["annotations"] = annotations
        print(format_annotations_markdown(doc))
    elif args.json:
        print(json.dumps(annotations, indent=2))
    else:
        if not annotations:
            print("No annotations.")
            return 0
        for item in annotations:
            tick = f" tick={item['simulation_tick']}" if item.get("simulation_tick") is not None else ""
            print(
                f"- {item['author']} · {item['target_kind']}/{item.get('target_id') or '—'}"
                f"{tick}: {item['text']}"
            )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ADSL workshop collaboration — sessions, sharing, annotations."
    )
    parser.add_argument(
        "--sessions-root",
        type=Path,
        help=f"Override sessions root (default: {DEFAULT_SESSIONS_ROOT})",
    )
    parser.add_argument("--json", action="store_true", help="Output structured JSON.")

    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("session-create", help="Create a new workshop session.")
    create.add_argument("name", help="Session display name.")
    create.add_argument("--description", help="Optional session description.")
    create.add_argument("--facilitator", help="Facilitator display name.")
    create.set_defaults(handler=_cmd_session_create)

    listing = sub.add_parser("session-list", help="List workshop sessions.")
    listing.set_defaults(handler=_cmd_session_list)

    show = sub.add_parser("session-show", help="Show session details.")
    show.add_argument("--session", required=True, help="Session ID or path.")
    show.set_defaults(handler=_cmd_session_show)

    participant = sub.add_parser("participant-add", help="Add a participant.")
    participant.add_argument("--session", required=True, help="Session ID or path.")
    participant.add_argument("name", help="Participant display name.")
    participant.add_argument("--role", default="analyst", help="Role (default: analyst).")
    participant.set_defaults(handler=_cmd_participant_add)

    share = sub.add_parser("scenario-share", help="Export a scenario into the session.")
    share.add_argument("--session", required=True, help="Session ID or path.")
    share.add_argument("--scenario", help="Scenario ID from registry.")
    share.add_argument("--scenario-path", type=Path, help="Direct path to scenario JSON.")
    share.add_argument("--label", required=True, help="Version label (e.g. workshop-v1).")
    share.add_argument("--author", required=True, help="Author display name.")
    share.add_argument("--changelog", help="Optional changelog note.")
    share.add_argument("--parent-version", help="Parent version ID for lineage.")
    share.set_defaults(handler=_cmd_scenario_share)

    imp = sub.add_parser("scenario-import", help="Import a shared scenario from session.")
    imp.add_argument("--session", required=True, help="Session ID or path.")
    imp.add_argument("--scenario", help="Scenario ID (use with --latest).")
    imp.add_argument("--latest", action="store_true", help="Import latest shared version.")
    imp.add_argument("--shared-path", type=Path, help="Path to shared manifest JSON.")
    imp.add_argument("--output-dir", type=Path, help="Output directory for imported package.")
    imp.add_argument("--overwrite", action="store_true", help="Overwrite existing import.")
    imp.set_defaults(handler=_cmd_scenario_import)

    history = sub.add_parser("scenario-history", help="Show scenario version history.")
    history.add_argument("--session", required=True, help="Session ID or path.")
    history.add_argument("--scenario", help="Filter to one scenario ID.")
    history.set_defaults(handler=_cmd_scenario_history)

    link = sub.add_parser("run-link", help="Link an ADR-009 export to the session.")
    link.add_argument("--session", required=True, help="Session ID or path.")
    link.add_argument("--export-dir", required=True, type=Path, help="ADR-009 export directory.")
    link.add_argument("--author", required=True, help="Author display name.")
    link.add_argument("--label", help="Optional run label.")
    link.add_argument("--no-copy", action="store_true", help="Reference export path without copying.")
    link.set_defaults(handler=_cmd_run_link)

    ann_add = sub.add_parser("annotate-add", help="Add annotation to a linked run.")
    ann_add.add_argument("--session", required=True, help="Session ID or path.")
    ann_add.add_argument("--run-id", required=True, help="Run ID to annotate.")
    ann_add.add_argument("--author", required=True, help="Author display name.")
    ann_add.add_argument("--text", required=True, help="Annotation text.")
    ann_add.add_argument(
        "--target-kind",
        default="run",
        choices=["run", "node", "route", "insight", "scenario"],
        help="Annotation target kind.",
    )
    ann_add.add_argument("--target-id", help="Target entity ID.")
    ann_add.add_argument("--tick", type=int, help="Simulation tick reference.")
    ann_add.set_defaults(handler=_cmd_annotate_add)

    ann_list = sub.add_parser("annotate-list", help="List annotations for a run.")
    ann_list.add_argument("--run-id", required=True, help="Run ID.")
    ann_list.add_argument("--session", help="Session ID or path.")
    ann_list.add_argument("--export-dir", type=Path, help="Direct export directory path.")
    ann_list.add_argument("--target-kind", help="Filter by target kind.")
    ann_list.add_argument("--author-filter", help="Filter by author.")
    ann_list.add_argument("--markdown", action="store_true", help="Render as Markdown.")
    ann_list.set_defaults(handler=_cmd_annotate_list)

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except (ValueError, FileNotFoundError, KeyError, FileExistsError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())