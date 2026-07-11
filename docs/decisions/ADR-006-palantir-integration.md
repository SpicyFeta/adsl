# ADR-006: Palantir Integration Architecture and Sync Policy

**Status:** Proposed  
**Date:** 2026-07-08  
**Deciders:** ADSL Engineering Team, Project Management  
**Phase:** Phase 1 — Contested Logistics Stress Test MVP

---

## Context

ADSL Phase 1 must integrate with Palantir's Ontology to demonstrate that simulation outputs—logistics networks, agent decisions, and audit traces—are consumable by defense and intelligence platforms. ADR-001 selected Python partly for Palantir Ontology SDK support. ADR-003 defined `ADSL_AuditTrace` as the canonical explainability artifact. ADR-004 and ADR-005 established simulation orchestration and Blue adaptation policies whose outputs must be externally visible.

Phase 1 requires a **clean integration boundary** in `src/adsl/ontology/` that:

- Maps ADSL Pydantic models to Ontology object types.
- Defines when and how data is synchronized.
- Uses the official Palantir Ontology SDK (not custom REST hacks).
- Remains testable without a live Foundry instance during development.

This ADR defines the high-level integration architecture and sync policy. Live SDK client wiring and credentials are Phase 1 scaffolding with placeholder read/write functions until Foundry environment details are provided by stakeholders.

---

## Decision

ADSL Phase 1 adopts a **write-oriented Ontology integration layer** in `src/adsl/ontology/integration.py` with the following architecture.

### 1. Integration boundary

```
SimulationEngine
    │
    ├── produces ADSL_SimulationRun, ADSL_AuditTrace, SimulationEvent
    ├── mutates ADSL_LogisticsNode, ADSL_LogisticsRoute state
    │
    ▼
OntologyMapper (pure functions)
    │  map_*_to_ontology() → dict payloads
    ▼
OntologySync (placeholder read/write in Phase 1)
    │  write_ontology_object() / write_ontology_objects()
    ▼
Palantir Foundry Ontology (via official SDK — future connection)
```

- **Mapping** is pure and side-effect free (unit-testable).
- **Sync** is isolated behind placeholder functions that will wrap the Palantir Ontology SDK.
- Simulation engine code does not import Palantir SDK directly.

### 2. Ontology object type mapping (Phase 1)

| ADSL model | Ontology object type | Primary key |
|------------|---------------------|-------------|
| `ADSL_LogisticsNode` | `ADSL_LogisticsNode` | `node_id` |
| `ADSL_LogisticsRoute` | `ADSL_LogisticsRoute` | `route_id` |
| `ADSL_AuditTrace` | `ADSL_AuditTrace` | `trace_id` |
| `ADSL_SimulationRun` | `ADSL_SimulationRun` | `run_id` |
| `ADSL_ForceElement` | `ADSL_ForceElement` | `element_id` |
| `SimulationEvent` | `ADSL_SimulationEvent` | `event_id` |

All mapped payloads include:

- `adsl_schema_version` — model or trace schema version for forward compatibility
- `source_system` — constant `"ADSL_PHASE1"`
- `mapped_at` — UTC timestamp of mapping (not simulation time)

### 3. Sync policy (Phase 1)

| Phase | When | Objects | Mode |
|-------|------|---------|------|
| **Bootstrap** | Before tick loop (run start) | Scenario nodes, routes, force elements | Upsert (placeholder) |
| **Per decision** | After each agent decision (optional in Phase 1) | `ADSL_AuditTrace` | Append-only insert |
| **Per event** | Deferred batch in Phase 1 | `ADSL_SimulationEvent` | Append-only insert |
| **Run complete** | After simulation ends | `ADSL_SimulationRun`, final node/route state, trace batch, event batch | Upsert run; upsert network state |

**Default Phase 1 CLI behaviour** (`scripts/run_simulation.py`):

1. Run simulation locally.
2. Print human-readable summary to stdout.
3. Build Ontology payload batch via `build_run_sync_payload()`.
4. Do **not** call live Foundry write unless `ADSL_ONTOLOGY_SYNC_ENABLED=true`.

**Append-only rule for audit artifacts:** `ADSL_AuditTrace` and `ADSL_SimulationEvent` are never updated or deleted once written. Corrections require new records with new IDs.

**Upsert rule for network state:** Nodes and routes reflect latest simulation state at run completion.

### 4. Read policy (Phase 1)

- `read_ontology_object()` is a **placeholder** returning `None`.
- Phase 1 simulation is self-contained from synthetic JSON datasets.
- Future phases may read Ontology state to seed simulations or validate sync.

### 5. Configuration (environment variables)

| Variable | Purpose | Phase 1 default |
|----------|---------|-----------------|
| `FOUNDRY_URL` | Foundry instance URL | Unset (offline) |
| `FOUNDRY_TOKEN` | API token | Unset |
| `ONTOLOGY_RID` | Ontology resource identifier | Unset |
| `ADSL_ONTOLOGY_SYNC_ENABLED` | Gate live writes | `false` |

Credentials must not be committed to the repository. Use `.env` locally (gitignored).

### 6. SDK usage constraint

Per project charter: integration **must** use the official Palantir Ontology SDK when live sync is enabled. Placeholder functions document the intended SDK call sites; swapping placeholders for SDK calls must not change mapper signatures or sync policy.

---

## Rationale

### 1. Separation of concerns

Pure mappers keep Ontology field evolution independent of simulation logic. The engine remains Palantir-agnostic.

### 2. Auditability alignment

Append-only trace and event sync matches ADR-003 immutability expectations and defense audit requirements.

### 3. Offline development

Placeholder write functions allow full simulation and mapping development without Foundry credentials—critical for incremental Phase 1 delivery.

### 4. Batch-friendly completion sync

Deferring event batch write until run end reduces SDK call volume for MVP demonstrations while preserving complete run records.

### 5. Palantir consumer clarity

Stable object type names mirroring ADSL models reduce ETL ambiguity for Ontology consumers and workshop developers.

---

## Consequences

### Positive

- Clear contract for Ontology object shapes and sync timing.
- CLI script can demonstrate end-to-end payload generation.
- Unit tests validate mappings without Foundry connectivity.
- Future SDK wiring is a contained change in `integration.py`.

### Negative / Trade-offs

- Placeholder writes do not validate against live Ontology schema constraints.
- No real-time streaming of traces to Foundry during simulation in Phase 1.
- Upsert semantics for nodes/routes are simplified (no conflict resolution across parallel runs).
- Read path unimplemented; no Ontology-driven scenario loading yet.

### Neutral

- Ontology link types (e.g., trace → run, route → node) are embedded as property fields in Phase 1; explicit Ontology relations may be added later.
- SDK package not added to `pyproject.toml` until credentials and ontology schema are confirmed (avoids unused heavy dependency during offline dev).

---

## Alternatives Considered

| Alternative | Reason Not Selected (Phase 1) |
|-------------|-------------------------------|
| **Direct REST to Foundry APIs** | Violates project requirement for official Ontology SDK |
| **Inline SDK calls in SimulationEngine** | Couples simulation to Palantir; harder to test and audit |
| **CSV export only (no Ontology)** | Fails Phase 1 Palantir integration goal |
| **Real-time trace streaming** | Adds complexity; batch at run end sufficient for MVP demo |
| **Bidirectional sync (read + write)** | Read not needed for synthetic dataset-driven Phase 1 |

---

## Compliance Rules

1. All Ontology mapping logic lives in `src/adsl/ontology/integration.py`.
2. Mappers must accept ADSL Pydantic models and return JSON-serializable dicts.
3. `ADSL_AuditTrace` sync must be append-only.
4. Simulation engine must not depend on Palantir SDK imports.
5. Live sync gated by `ADSL_ONTOLOGY_SYNC_ENABLED`.
6. Secrets only via environment variables; never in source control.
7. Object type names must match the table in §2 unless amended by ADR.

---

## Phase 1 Limitations (Explicit)

- Placeholder `read_ontology_object()` / `write_ontology_object()` — no network I/O.
- No Ontology schema validation against live Foundry.
- No link-type graph navigation in SDK.
- No multi-run aggregation or workshop UI.
- No classified network / air-gapped deployment guidance (deferred to operations).

---

## Implementation Map

| Component | Location |
|-----------|----------|
| Ontology mappers and sync placeholders | `src/adsl/ontology/integration.py` |
| CLI run + summary | `scripts/run_simulation.py` |
| Environment template | `.env.example` |
| Integration tests | `src/tests/test_ontology_integration.py` |

---

## References

- ADR-001: Python 3.11+ as Primary Implementation Language
- ADR-003: AuditTrace System and Explainability Contract
- ADR-004: Simulation Orchestration Policy
- ADR-005: Blue Adaptation Policy
- [Palantir Ontology SDK overview](https://www.palantir.com/docs/foundry/ontology-sdk/overview/)
- `data/synthetic/logistics_scenario_v1.json`