# ADR-011: Foundry Dataset Integration (Import / Export)

**Status:** Accepted  
**Date:** 2026-07-08  
**Deciders:** ADSL Engineering Team, Project Management  
**Phase:** Phase 3 — Increment 8 (Live Data Integration)

---

## Context

ADR-006/007 defined Ontology object mapping and SDK client architecture with write-first policy. Increment 8 extends integration to **Foundry datasets** for:

1. **Importing** scenario configuration from Foundry-managed datasets
2. **Exporting** simulation results (including audit traces) back to Foundry datasets
3. Maintaining **data lineage** for defense audit requirements

The simulation engine must remain Palantir-agnostic (zero Foundry imports in `simulation/`).

---

## Decision

### 1. Module boundary

```
simulation/          (no Foundry imports)
    ▼
ontology/integration.py   (mappers — ADR-006)
    ▼
foundry/             (dataset + HTTP adapter — ADR-011)
    ├── client.py
    ├── scenario_import.py
    ├── results_export.py
    └── lineage.py
    ▼
Foundry (datasets + Ontology via shared credentials)
```

### 2. Activation gate

| Condition | Variable |
|-----------|----------|
| Foundry integration enabled | `ADSL_FOUNDRY_ENABLED=true` |
| Instance URL | `FOUNDRY_URL` |
| API token | `FOUNDRY_TOKEN` |
| Scenario dataset RID (import) | `FOUNDRY_SCENARIO_DATASET_RID` |
| Results dataset RID (export) | `FOUNDRY_RESULTS_DATASET_RID` |
| Ontology RID (object sync) | `ONTOLOGY_RID` |

When gate fails, **local adapter** reads/writes under `data/foundry/datasets/` for offline development.

### 3. Dataset record formats

| Record type | Direction | Content |
|-------------|-----------|---------|
| `adsl_scenario_package` | Import | Full `ADSL_ScenarioPackage` JSON + lineage |
| `adsl_simulation_run` | Export | Run metadata + metrics |
| `adsl_audit_trace` | Export | One record per trace (append-only lineage) |
| `adsl_network_snapshot` | Export | End-state nodes/routes |
| `adsl_lineage` | Both | Provenance metadata |

### 4. Lineage policy

Every import/export record includes:
- `source_system`, `operation`, `timestamp`, `parent_run_id` / `parent_dataset_rid`
- Immutable audit traces exported with original `trace_id` — no mutation

### 5. Security

- Tokens via environment only — never in source control
- HTTPS required for live HTTP adapter
- Default CI remains offline (local adapter only)
- Gated live tests: `pytest -m live_foundry`

### 6. ADR-007 activation (Increment 8)

ADR-007 moves to **Accepted**. `OntologySdkClient.is_live_ready()` returns `True` when Foundry gate passes and HTTP adapter is configured. Ontology writes delegate to `foundry` HTTP layer (no Palantir SDK package required for dataset/Ontology REST paths in Inc 8).

---

## Consequences

- Engine independence preserved
- Dual-mode: local datasets for CI; live when credentials present
- Dataset and Ontology paths share credential validation