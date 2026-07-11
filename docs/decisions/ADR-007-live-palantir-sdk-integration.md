# ADR-007: Live Palantir Ontology SDK Integration

**Status:** Proposed (Draft — Increment 2 preparation)  
**Date:** 2026-07-08  
**Deciders:** ADSL Engineering Team, Project Management  
**Phase:** Phase 2 — Increment 2 (Live Palantir Ontology Integration)

---

## Context

ADR-006 established a write-oriented Ontology integration layer with pure mappers and placeholder read/write functions in `src/adsl/ontology/integration.py`. Phase 2 Increment 1 delivered workshop export bundles (ADR-009) that include Ontology payload snapshots offline.

Increment 2 requires **live Palantir Foundry connectivity** using the official Ontology SDK, while preserving ADR-006 mapper signatures, append-only audit sync policy, and offline CI behaviour.

This ADR defines the live SDK architecture, credential requirements, schema validation policy, and activation gates. **Live SDK calls are not implemented in the preparation phase** — only `src/adsl/ontology/sdk_client.py` skeleton and integration wiring contracts are delivered pending stakeholder credentials and PM approval.

---

## Decision

ADSL Phase 2 Increment 2 adopts a **layered Ontology client architecture**:

```
SimulationEngine (unchanged — no SDK imports)
    ▼
integration.py (mappers + sync policy — ADR-006)
    ▼
sdk_client.py (connection, auth, SDK adapter — ADR-007)
    ▼
Palantir Ontology SDK (official package — added in Inc 2 activation)
    ▼
Palantir Foundry Ontology
```

### 1. Activation gate

Live SDK I/O occurs **only when all conditions are true**:

| Condition | Variable / check |
|-----------|------------------|
| Sync explicitly enabled | `ADSL_ONTOLOGY_SYNC_ENABLED=true` |
| Foundry URL present | `FOUNDRY_URL` |
| API token present | `FOUNDRY_TOKEN` |
| Ontology RID present | `ONTOLOGY_RID` |
| Client reports live-ready | `OntologySdkClient.is_live_ready() == True` |

If any condition fails, `integration.py` falls back to **offline placeholder behaviour** (synthetic RIDs, zero network I/O) per ADR-006.

### 2. SDK client module (`sdk_client.py`)

| Method | Phase 2 preparation | Increment 2 activation |
|--------|---------------------|------------------------|
| `from_env()` | Parse and validate env config | Same |
| `is_live_ready()` | Returns `False` (no SDK package) | Returns `True` when SDK wired + credentials valid |
| `validate_config()` | Returns missing credential list | Same |
| `read_object()` | Raises `OntologySdkNotActiveError` | SDK `get` call |
| `write_object()` | Returns synthetic RID via placeholder path | SDK upsert/insert per object policy |
| `write_objects_batch()` | Placeholder batch | SDK batch write |

### 3. Object write policy (unchanged from ADR-006)

| Object type | Mode |
|-------------|------|
| `ADSL_AuditTrace` | Append-only insert |
| `ADSL_SimulationEvent` | Append-only insert |
| `ADSL_LogisticsNode` | Upsert at run complete |
| `ADSL_LogisticsRoute` | Upsert at run complete |
| `ADSL_SimulationRun` | Upsert at run complete |
| `ADSL_ForceElement` | Upsert at bootstrap |

### 4. Schema validation (Increment 2)

Before live writes, `scripts/validate_ontology_payload.py` will:

1. Build payload via `build_run_sync_payload()`.
2. Validate required properties per object type against stakeholder schema manifest.
3. Fail fast with actionable errors before SDK calls.

Schema manifest location (TBD with platform team): `docs/integration/ontology-schema-manifest.json`.

### 5. Credential and schema requirements (stakeholder)

| Requirement | Owner | Status |
|-------------|-------|--------|
| `FOUNDRY_URL` — Foundry instance base URL | IT / Platform | **Required before activation** |
| `FOUNDRY_TOKEN` — API token or service account token | IT / Platform | **Required before activation** |
| `ONTOLOGY_RID` — Target ontology resource identifier | Platform team | **Required before activation** |
| Object type names match ADR-006 table | Platform team | **Confirm** |
| Property schema per object type | Platform team | **Required for validation script** |
| Network egress to Foundry from dev/CI environment | Operations | **Confirm** |
| SDK package name and pinned version | Engineering + Platform | **TBD at activation** |

### 6. `source_system` versioning

Live sync payloads will use `source_system: "ADSL_PHASE2"` in mapper metadata (ADR-009 export already uses this convention). Phase 1 `"ADSL_PHASE1"` values remain valid for historical records.

### 7. Rollback

Set `ADSL_ONTOLOGY_SYNC_ENABLED=false` (or unset) to immediately disable all live SDK I/O. Mappers and simulation engine require no changes.

### 8. CI policy

- Default `pytest` suite: **offline only** (no Foundry network calls).
- Optional manual/gated live integration test: `pytest -m live_foundry` (not enabled in preparation phase).

---

## Rationale

### 1. Preserves ADR-006 boundaries

Mappers stay pure; SDK complexity isolated in `sdk_client.py`.

### 2. Safe incremental activation

Skeleton client + env validation allows preparation without credentials or SDK dependency.

### 3. Dual-mode operation

Workshop demos continue offline via export bundles (ADR-009) when Foundry is unavailable.

### 4. Defense audit alignment

Append-only trace/event policy unchanged for live sync.

---

## Consequences

### Positive

- Clear activation checklist for stakeholders.
- Contained SDK swap without engine changes.
- Offline CI remains stable.

### Negative / Trade-offs

- Preparation phase does not validate against live Ontology schema.
- Two code paths (placeholder vs live) until activation complete.

### Neutral

- Read path remains deferred (write-first policy unchanged).

---

## Implementation Status (Preparation Phase)

| Item | Status |
|------|--------|
| ADR-007 draft | Proposed |
| `sdk_client.py` skeleton | Delivered (placeholder methods only) |
| SDK in `pyproject.toml` | **Not added** (awaiting activation approval) |
| Live SDK calls | **Not implemented** |
| `validate_ontology_payload.py` | Deferred to activation |
| `integration.py` wiring to skeleton | Delivered (delegates when sync enabled; placeholder path active) |

---

## Compliance Rules

1. Simulation engine must not import Palantir SDK.
2. Mapper signatures must not change from ADR-006.
3. Live sync gated by `ADSL_ONTOLOGY_SYNC_ENABLED` plus credential presence.
4. No secrets in source control.

---

## References

- ADR-006: Palantir Integration Architecture and Sync Policy
- ADR-009: Run Export Bundle and Executive Summary Contract
- [Palantir Ontology SDK overview](https://www.palantir.com/docs/foundry/ontology-sdk/overview/)
- `.env.example`