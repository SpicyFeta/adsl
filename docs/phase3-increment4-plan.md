# ADSL Phase 3 — Increment 4 Locked Plan

**Status:** In progress  
**Date:** 2026-07-08  
**Track:** A (credential-independent)  
**Features:** P3-F07 (multi-run aggregation), batch export

---

## Success Criteria

| ID | Criterion | Measure |
|----|-----------|---------|
| S1 | Multi-run comparison | Compare ≥ 2 runs (seeds, scenarios, or Red pacing) with diff summary |
| S2 | Batch export | Multiple simulations exported; each bundle valid per ADR-009 |
| S3 | Batch manifest | `batch_manifest.json` indexes runs and embeds comparison summary |
| S4 | Red pacing overrides | Runtime metadata overrides without editing scenario JSON |
| S5 | Auditability | Each run retains full audit traces; no trace mutability |
| S6 | Mechanics compatibility | Hardening v2, deconfliction, ADR-010 unchanged |
| S7 | Documentation | README + analyst usage path documented |
| S8 | Regression | All tests pass; coverage ≥ 92% |

---

## Deliverables

| # | Deliverable |
|---|-------------|
| D1 | `src/adsl/export/runner.py` — RunSpec, execute_run |
| D2 | `src/adsl/export/compare.py` — metrics extraction, comparison |
| D3 | `src/adsl/export/batch.py` — batch export + manifest |
| D4 | `scripts/compare_runs.py` — CLI comparison |
| D5 | `scripts/batch_export.py` — CLI batch export |
| D6 | `src/tests/test_analyst_workflows.py` |
| D7 | README + completion note |