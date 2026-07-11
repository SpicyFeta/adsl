# Phase 3 Increment 4 — Completion Note

**Date:** 2026-07-08  
**Increment:** Analyst Workflows (Track A)  
**Features:** P3-F07 multi-run comparison, batch export

---

## Delivered

| Deliverable | Path |
|-------------|------|
| Run execution API | `src/adsl/export/runner.py` — `RunSpec`, `execute_run`, Red pacing overrides |
| Comparison API | `src/adsl/export/compare.py` — metrics, deltas, table/Markdown output |
| Batch export API | `src/adsl/export/batch.py` — `batch_export_runs`, `batch_manifest.json` |
| Compare CLI | `scripts/compare_runs.py` |
| Batch export CLI | `scripts/batch_export.py` |
| Example spec files | `data/analyst/example_batch.json`, `data/analyst/pacing_compare.json` |
| Tests | `src/tests/test_analyst_workflows.py` (6 tests) |

---

## Analyst Usage

**Compare live runs:**

```bash
python scripts/compare_runs.py \
  --scenario alpine-valley-v3 --seed 42 --label baseline \
  --scenario alpine-valley-v3 --seed 99 --label alt-seed \
  --ticks 50 --quiet-logs
```

**Batch export with comparison:**

```bash
python scripts/batch_export.py \
  --specs data/analyst/example_batch.json \
  --export-dir exports/workshop-batch --quiet-logs
```

**Compare existing exports:**

```bash
python scripts/compare_runs.py --from-exports exports/workshop-batch
```

---

## Success Criteria

| ID | Status |
|----|--------|
| S1 Multi-run comparison | Met |
| S2 Batch export (ADR-009 per run) | Met |
| S3 Batch manifest | Met |
| S4 Red pacing overrides | Met |
| S5 Auditability | Met — full traces per run |
| S6 Mechanics compatibility | Met — no engine changes |
| S7 Documentation | Met — README, demo-playbook |
| S8 Regression + coverage | Met — 70 passed, 93% |