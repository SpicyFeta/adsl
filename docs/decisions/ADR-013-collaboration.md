# ADR-013: File-Based Collaboration for Workshops

**Status:** Accepted  
**Date:** 2026-07-08  
**Increment:** Phase 3 Increment 11

---

## Context

Team workshops require multiple analysts to work from the same scenarios, compare runs, and capture shared observations. ADSL is offline-first with ADR-009 export bundles as the primary artifact. Real-time collaborative editing (multi-user live scenario mutation) is explicitly out of scope per the capabilities matrix.

Increment 11 must support basic collaboration workflows without introducing server infrastructure or coupling to the simulation engine.

---

## Decision

1. **Session directories** — Workshop state lives under `data/collaboration/sessions/{session_id}/` with a `session.json` manifest tracking participants, scenario refs, run refs, and an activity log.

2. **Scenario sharing** — Scenarios are exported as self-contained share manifests in `shared_scenarios/` with content fingerprints and version labels. Import writes a plain `ADSL_ScenarioPackage` JSON for local simulation.

3. **Version history** — `scenario_history.json` records append-only version entries with optional `parent_version_id` for lineage.

4. **Run linking** — ADR-009 exports are copied into `runs/{run_id}/` (or referenced by path when `--no-copy` is used) and registered on the session manifest.

5. **Annotations** — Comments attach to run export directories as `annotations.json` with `target_kind` in `{run, node, route, insight, scenario}`. Initialized on ADR-009 export; surfaced via dashboard `/api/annotations/{run_id}`.

6. **CLI surface** — `scripts/collab_workshop.py` provides subcommands for session, scenario, run, and annotation workflows.

---

## Consequences

### Positive

- Zero server dependency; teams share folders via existing IT mechanisms.
- Annotations co-locate with ADR-009 exports for audit traceability.
- Scenario versioning supports workshop iteration without registry mutation.
- Simulation engine remains unchanged (ADR-002 compliance).

### Negative / Limits

- No live sync — users must manually refresh or re-copy session folders.
- No authZ — session directories are trust-on-share.
- Annotation conflicts possible if two users edit the same `annotations.json` concurrently (last-write-wins).

---

## Alternatives Considered

| Alternative | Rejected because |
|-------------|------------------|
| Real-time WebSocket sync | Out of roadmap; adds ops burden |
| Git-only workflow | Too technical for non-author workshop participants |
| Annotations in separate DB | Breaks ADR-009 bundle portability |
| Foundry as collaboration hub | Credentials and stakeholder decision pending (ADR-007) |

---

## Compliance

- Collaboration module must not import simulation engine internals beyond `load_scenario_package`.
- Annotations schema version tracked via `COLLAB_SCHEMA_VERSION`.
- Export manifest must list `annotations.json` when present (ADR-009 extension).