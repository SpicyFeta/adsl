# ADR-009: Run Export Bundle and Executive Summary Contract

**Status:** Accepted  
**Date:** 2026-07-08  
**Deciders:** ADSL Engineering Team, Project Management  
**Phase:** Phase 2 — Increment 1 (Demo Foundation)

---

## Context

ADSL Phase 1 produced simulation outputs via CLI stdout and structured `structlog` JSON logs. Phase 2 Increment 1 requires **workshop-ready artifacts** that stakeholders can consume without re-running the simulation or parsing raw logs.

Phase 1 already defines canonical Pydantic models (`ADSL_SimulationRun`, `ADSL_AuditTrace`, `SimulationEvent`, etc.) and Ontology mapping payloads (ADR-006). Phase 2 needs a stable, versioned **export contract** for bundling run artifacts into portable files.

This ADR defines the export bundle schema, file layout, executive summary format, and CLI integration — without coupling exports to live Palantir Foundry sync.

---

## Decision

ADSL Phase 2 Increment 1 adopts a **run export bundle** produced by `scripts/export_run.py` and optionally via `scripts/run_simulation.py --export-dir`.

### 1. Export schema version

- Constant: `EXPORT_SCHEMA_VERSION = "1.0"`
- Recorded in bundle metadata as `export_schema_version`
- Breaking changes require a new schema version and ADR amendment

### 2. Bundle directory layout

Each export writes to a directory named `{run_id}/` under the user-specified export root:

```
{export_dir}/
└── {run_id}/
    ├── manifest.json           # Bundle index and schema metadata
    ├── run_bundle.json         # Complete machine-readable bundle
    ├── audit_traces.jsonl      # One ADSL_AuditTrace per line (optional convenience)
    ├── simulation_events.jsonl # One SimulationEvent per line (optional convenience)
    └── executive_summary.md    # Human-readable workshop summary
```

### 3. `manifest.json` (required fields)

| Field | Type | Description |
|-------|------|-------------|
| `export_schema_version` | string | `"1.0"` |
| `source_system` | string | `"ADSL_PHASE2"` |
| `exported_at` | ISO-8601 UTC | Export timestamp |
| `run_id` | string | Simulation run identifier |
| `scenario_id` | string | Scenario identifier |
| `files` | object | Map of logical name → filename |

### 4. `run_bundle.json` (required top-level keys)

| Key | Content |
|-----|---------|
| `export_schema_version` | Schema version string |
| `source_system` | `"ADSL_PHASE2"` |
| `exported_at` | ISO-8601 UTC timestamp |
| `run` | Serialized `ADSL_SimulationRun` |
| `scenario` | Serialized `ADSL_Scenario` (definition, not live package) |
| `execution` | `{ "ticks_executed", "seed", "dataset_path" }` |
| `network_state` | `{ "nodes": [...], "routes": [...] }` end-of-run state |
| `audit_traces` | Array of serialized `ADSL_AuditTrace` |
| `simulation_events` | Array of serialized `SimulationEvent` |
| `ontology_payload` | Output of `build_run_sync_payload()` per ADR-006 |
| `summary_statistics` | Aggregated counts (traces by side/action/category, node/route statuses) |

All serialized models use Pydantic `model_dump(mode="json")` for JSON compatibility.

### 5. Executive summary (`executive_summary.md`)

Auto-generated Markdown with the following sections (no manual editing required):

1. **Title** — scenario name, run ID, export timestamp
2. **Run Overview** — status, ticks, seed, trace/event counts
3. **Network State** — node and route status breakdown
4. **Agent Activity** — audit trace counts by side, action, category
5. **Key Outcomes** — last N actionable events (default 8)
6. **Ontology Payload** — object counts per category
7. **Provenance** — `source_system`, schema version, dataset path

### 6. CLI integration

| Flag | Script | Behaviour |
|------|--------|-----------|
| `--export-dir PATH` | `run_simulation.py`, `export_run.py` | Write bundle after run |
| `--scenario ID` | both | Resolve dataset via scenario registry |
| `--quiet-logs` | both | Suppress structlog JSON stdout |

`--dataset` remains supported and overrides `--scenario` when both provided.

### 7. Scenario registry

Scenarios are registered in `data/synthetic/scenario_registry.json`:

```json
{
  "kessari-strait-v1": "logistics_scenario_v1.json",
  "island-chokepoint-v2": "logistics_scenario_v2.json"
}
```

Resolution via `adsl.simulation.registry.resolve_scenario_path()`.

### 8. Module boundaries

| Component | Location |
|-----------|----------|
| Export logic (pure, testable) | `src/adsl/export/bundle.py` |
| Executive summary builder | `src/adsl/export/summary.py` |
| Scenario registry | `src/adsl/simulation/registry.py` |
| CLI export runner | `scripts/export_run.py` |

Simulation engine and Ontology mappers are **not** modified for export; export reads engine state post-run.

### 9. Immutability and auditability

- Export is a **read-only snapshot** of a completed run; it does not mutate traces or events.
- Audit traces in the bundle match engine memory exactly (no filtering beyond serialization).
- `ontology_payload` is included for workshop handoff even when live sync is disabled.

---

## Rationale

### 1. Workshop readiness

Stakeholders need portable artifacts for Foundry ingestion, briefings, and archival without CLI expertise.

### 2. Separation of concerns

Export logic is isolated from simulation and Ontology sync, enabling offline testing and CI validation.

### 3. JSON + JSONL dual format

`run_bundle.json` is self-contained; JSONL files support streaming tools and large trace sets.

### 4. Versioned contract

`export_schema_version` enables forward-compatible consumers and explicit breaking-change governance.

### 5. Reuse of Phase 1 models

No parallel schema; Pydantic models remain the single source of truth.

---

## Consequences

### Positive

- One-command workshop artifact generation.
- Testable export schema without network dependencies.
- Executive summary suitable for non-technical audiences.

### Negative / Trade-offs

- Large bundles for 100-tick runs (~1,100 traces); acceptable for Phase 2 demos.
- No incremental/streaming export during simulation (batch at run end).
- HTML export deferred; Markdown only in Increment 1.

### Neutral

- GeoJSON map overlays out of scope for Increment 1.
- Export directory is user-managed; not committed to repository.

---

## Compliance Rules

1. Export bundles must include all keys in §4 unless an ADR amendment says otherwise.
2. `executive_summary.md` must be generated automatically from run data.
3. Export must not require Palantir credentials or live sync.
4. Phase 1 tests must continue to pass after export integration.

---

## References

- ADR-003: AuditTrace System and Explainability Contract
- ADR-006: Palantir Integration Architecture and Sync Policy
- `docs/phase2-planning.md` — Increment 1 scope