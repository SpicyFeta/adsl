# Phase 3 Increment 1 — Demo Playbook Validation Report

**Date:** 2026-07-08  
**Facilitator:** Engineering validation run (proxy for independent facilitator)  
**Playbook:** `docs/demo-playbook.md` Parts 1–4  
**Environment:** Windows 10, Python 3.14.3, project root `adsl-phase1`

---

## Summary

| Item | Result |
|------|--------|
| Parts executed | 1–4 (required) |
| Elapsed time (Parts 1–4) | ~5 minutes |
| Overall result | **PASS** |
| Blockers | None |

**Note:** This report documents an engineering-executed validation checklist per Increment 1 scope. A future independent non-author facilitator run is still recommended for full P1 sign-off per the locked plan.

---

## Checklist

| # | Item | Result |
|---|------|--------|
| 1 | `pip install -e ".[dev]"` succeeds | PASS (pre-existing environment) |
| 2 | `python -m pytest -q` — 58 passed (Inc 1 baseline) | PASS |
| 3 | `kessari-strait-v1` 100-tick run `COMPLETED` | PASS |
| 4 | `island-chokepoint-v2` 100-tick run `COMPLETED` | PASS |
| 5 | `export_run.py` produces bundle under `exports/<run_id>/` | PASS |
| 6 | `manifest.json` — `export_schema_version: "1.0"`, `source_system: "ADSL_PHASE2"` | PASS |
| 7 | `executive_summary.md` readable without code knowledge | PASS |

---

## Commands Executed

```bash
python -m pytest src/tests -q
python scripts/run_simulation.py --scenario kessari-strait-v1 --ticks 100 --seed 42 --quiet-logs
python scripts/run_simulation.py --scenario island-chokepoint-v2 --ticks 100 --seed 42 --quiet-logs
python scripts/export_run.py --scenario island-chokepoint-v2 --ticks 100 --seed 42 --export-dir exports --quiet-logs
```

**Export path validated:** `exports/3e56a9da-e1c5-4464-b9fc-8f0b927a5c0f/`

---

## Friction Log

| Severity | Item | Notes |
|----------|------|-------|
| Minor | Test count changed | Playbook references 46 tests; Inc 1 adds 12 tests (58 total). README/playbook updated. |
| Cosmetic | Windows path display | Export path uses backslashes on Windows; playbook shows both Windows and Unix examples. |
| None | Blockers | All Parts 1–4 completable without author assistance |

---

## Part 5–6 (Optional)

Not executed in this validation run. ADR-010 pacing mechanics can be demonstrated via audit trace `ADR-010` reasoning steps after Inc 1 implementation.

---

## Conclusion

Demo playbook Parts 1–4 remain executable well under the 30-minute target. No blocking friction identified. Minor documentation updates applied for test count and ADR-010 demo notes.