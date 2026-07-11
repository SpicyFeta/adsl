# Phase 3 Increment 12 — Live Data Integration (Foundry) (Complete)

**Date:** 2026-07-08  
**Status:** Complete  
**Directive:** Enable optional Palantir Foundry dataset import/export with lineage and auditability.

---

## Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| Foundry integration module | `src/adsl/foundry/` | ✅ |
| Local + HTTP adapters | `adapters/local.py`, `adapters/http.py` | ✅ |
| Scenario import / publish | `scenario_import.py` | ✅ |
| Results export + lineage | `results_export.py`, `lineage.py` | ✅ |
| SDK client wiring | `ontology/sdk_client.py` → Foundry HTTP | ✅ |
| CLI — status | `scripts/foundry_status.py` | ✅ |
| CLI — import/publish | `scripts/foundry_import.py` | ✅ |
| CLI — export | `scripts/foundry_export.py` | ✅ |
| Example datasets | `data/foundry/datasets/scenarios/` | ✅ |
| Dataset schema reference | `docs/integration/foundry-dataset-schema.json` | ✅ |
| ADR-011 | `docs/decisions/ADR-011-foundry-dataset-integration.md` | ✅ |
| Documentation | `docs/foundry-integration.md` | ✅ |
| Tests | `src/tests/test_foundry.py` | ✅ |

---

## Success Criteria

| Criterion | Evidence |
|-----------|----------|
| Read scenario data from Foundry dataset | `import_scenario_from_foundry`, local + HTTP adapters |
| Write simulation outputs to Foundry | `export_run_to_foundry_dataset` with traces, metrics, annotations |
| Modular / optional integration | Engine has zero Foundry imports; local mode default |
| Setup documentation | `foundry-integration.md`, env gate table |
| Traceability | `lineage` block on every record; `lineage_id` in export result |

---

## Verification

```bash
python -m pytest src/tests/test_foundry.py -v
python scripts/foundry_status.py
python scripts/foundry_import.py import --scenario-id island-chokepoint-v2
python scripts/foundry_export.py --scenario island-chokepoint-v2 --ticks 10
```

---

## Out of Scope (unchanged)

- Real-time bidirectional synchronization
- Official Palantir SDK package dependency
- Full Ontology object type coverage
- Multi-tenant enterprise access control
- Foundry Workshop application