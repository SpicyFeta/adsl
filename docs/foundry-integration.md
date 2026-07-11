# Palantir Foundry Integration

**Increment 12** — Optional dataset import/export and Ontology sync via a modular Foundry layer (ADR-011). The simulation engine has **zero** Foundry imports.

---

## Architecture

```
simulation/                 (Palantir-agnostic)
    ▼
ontology/integration.py     (ADR-006 mappers)
    ▼
foundry/                    (ADR-011 dataset + HTTP adapter)
    ├── config.py           Activation gate + env parsing
    ├── client.py           Local or HTTP adapter selection
    ├── scenario_import.py  Import / publish scenarios
    ├── results_export.py   Export runs, traces, annotations
    └── lineage.py          Provenance on every record
    ▼
Palantir Foundry (datasets + Ontology REST)
```

---

## Activation Gate

Live HTTP mode requires **all** of:

| Variable | Purpose |
|----------|---------|
| `ADSL_FOUNDRY_ENABLED=true` | Master switch |
| `FOUNDRY_URL` | Foundry instance base URL (HTTPS) |
| `FOUNDRY_TOKEN` | API bearer token (env only — never commit) |

Optional dataset RIDs:

| Variable | Purpose |
|----------|---------|
| `FOUNDRY_SCENARIO_DATASET_RID` | Import scenario packages |
| `FOUNDRY_RESULTS_DATASET_RID` | Export simulation results |
| `ONTOLOGY_RID` | Ontology object writes |
| `ADSL_ONTOLOGY_SYNC_ENABLED=true` | Enable Ontology sync path |

When the gate fails, ADSL uses **local filesystem datasets** under `data/foundry/datasets/` (CI-safe, no network).

Check status:

```bash
python scripts/foundry_status.py
python scripts/foundry_status.py --json
```

---

## Authentication & Security

- Tokens are read from environment variables only.
- Live adapter requires HTTPS (`ssl.create_default_context()`).
- Default CI runs offline — no credentials required.
- Live integration tests use `pytest -m live_foundry` (not run in default CI).
- Rollback: unset `ADSL_FOUNDRY_ENABLED` — simulation and exports continue locally.

---

## Dataset Record Format

Each Foundry dataset record is a JSON object (JSONL in local mode):

| `record_type` | Direction | Content |
|---------------|-----------|---------|
| `adsl_scenario_package` | Import | Full `ADSL_ScenarioPackage` |
| `adsl_simulation_run` | Export | Run metadata + summary statistics |
| `adsl_network_snapshot` | Export | End-state nodes/routes |
| `adsl_audit_trace` | Export | One immutable trace per record |
| `adsl_annotations` | Export | Team annotations (optional) |
| `adsl_insights` | Export | Automated insights (optional) |
| `adsl_lineage` | Both | Provenance summary |

Every record includes a `lineage` block:

```json
{
  "lineage_schema_version": "1.0",
  "lineage_id": "<uuid>",
  "source_system": "ADSL_PHASE3",
  "operation": "simulation_export",
  "recorded_at": "2026-07-08T12:00:00+00:00",
  "parent_dataset_rid": "ri.foundry.main.dataset....",
  "parent_run_id": "<run_id>",
  "scenario_id": "island-chokepoint-v2"
}
```

Full schema reference: [integration/foundry-dataset-schema.json](integration/foundry-dataset-schema.json)

---

## Import Scenarios from Foundry

### Publish a local scenario (offline or live)

```bash
python scripts/foundry_import.py publish --scenario island-chokepoint-v2
python scripts/foundry_import.py publish --scenario-path data/synthetic/logistics_scenario_v3.json
```

### Import into ADSL

```bash
python scripts/foundry_import.py import --scenario-id island-chokepoint-v2
# Writes: data/foundry/imported/island-chokepoint-v2__foundry.json

# Run simulation from imported file
python scripts/run_simulation.py --dataset data/foundry/imported/island-chokepoint-v2__foundry.json --ticks 50
```

### Python API

```python
from adsl.foundry import import_scenario_from_foundry, publish_scenario_to_foundry

package, record = import_scenario_from_foundry("alpine-valley-v3")
print(record["lineage"]["lineage_id"])
```

---

## Export Results to Foundry

### From existing ADR-009 export

```bash
python scripts/export_run.py --scenario alpine-valley-v3 --ticks 50 --export-dir exports

python scripts/foundry_export.py --from-export exports/<run_id>
python scripts/foundry_export.py --from-export exports/<run_id> --dry-run
python scripts/foundry_export.py --from-export exports/<run_id> --no-ontology
```

### Live run + export in one step

```bash
python scripts/foundry_export.py --scenario island-chokepoint-v2 --seed 42 --ticks 50
```

### Inspect records without writing

```bash
python scripts/foundry_export.py --from-export exports/<run_id> --records-only
```

Exports include audit traces (append-only, original `trace_id` preserved), network snapshot, annotations, and insights when present in the ADR-009 bundle.

---

## Ontology Sync

When `ADSL_ONTOLOGY_SYNC_ENABLED=true` and the Foundry gate passes, `export_run_to_foundry_dataset()` also writes Ontology objects via the HTTP adapter (ADR-006 mappers, ADR-007 client).

Object write policy (unchanged):

| Object type | Mode |
|-------------|------|
| `ADSL_AuditTrace` | Append-only |
| `ADSL_SimulationEvent` | Append-only |
| `ADSL_LogisticsNode` | Upsert |
| `ADSL_LogisticsRoute` | Upsert |
| `ADSL_SimulationRun` | Upsert |

---

## Local Development (No Foundry)

Example scenarios are pre-published under `data/foundry/datasets/scenarios/`:

```bash
python scripts/foundry_import.py import --scenario-id island-chokepoint-v2
python scripts/foundry_export.py --scenario island-chokepoint-v2 --ticks 10
# Results append to data/foundry/datasets/results/records.jsonl
```

---

## Limitations (v1)

| Limitation | Notes |
|------------|-------|
| No real-time bidirectional sync | Batch import/export only |
| No official Palantir SDK package | REST adapter per stakeholder alignment |
| No automatic schema transformation | Records use ADSL-native shapes |
| Not all Ontology object types | Six ADR-006 types only |
| No multi-tenant access control | Token scope is operator responsibility |
| HTTP paths are conventions | Confirm with platform team before production |
| Read Ontology returns null on 404 | No retry/backoff in v1 |

---

## Verification

```bash
python -m pytest src/tests/test_foundry.py -v
python scripts/foundry_status.py
python scripts/foundry_import.py publish --scenario alpine-valley-v3
python scripts/foundry_export.py --scenario island-chokepoint-v2 --ticks 5 --dry-run
```