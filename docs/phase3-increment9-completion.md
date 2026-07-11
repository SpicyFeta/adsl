# Phase 3 Increment 9 — Advanced Analytics & Insights (Complete)

**Date:** 2026-07-08  
**Status:** Complete  
**Directive:** Automated analysis capabilities generating actionable insights from simulation results.

---

## Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| Analytics module | `src/adsl/analytics/` | ✅ |
| Single-run CLI | `scripts/analyze_run.py` | ✅ |
| What-if comparison | `scripts/compare_runs.py --what-if` | ✅ |
| Export integration | `insights.json`, `insights_report.md` in ADR-009 bundles | ✅ |
| Dashboard API + UI | `/api/insights/{run_id}`, insights panel | ✅ |
| Documentation | `docs/analytics-insights.md` | ✅ |
| Tests | `src/tests/test_analytics.py` | ✅ |

---

## Success Criteria

| Criterion | Evidence |
|-----------|----------|
| Automatically highlight critical nodes, routes, and risks | `critical_highlights`, `route_risks`, `corridor_risks` in insight reports |
| Insights clear, actionable, well-documented | `key_insights` bullets + `docs/analytics-insights.md` with examples |
| Compare multiple runs and understand differences | `compare_what_if()` + `--what-if` CLI with metric and insight deltas |
| Explainable and traceable to raw data | `evidence` blocks on every finding with trace/entity IDs |

---

## Module Structure

```
src/adsl/analytics/
├── __init__.py
├── evidence.py       # Traceable evidence references
├── bottlenecks.py    # Bottleneck + vulnerability detection
├── risk.py           # Route and corridor risk scoring
├── red_patterns.py   # Red agent behavior patterns
├── what_if.py        # Multi-run what-if comparison
├── report.py         # Report orchestrator
└── format.py         # Markdown / text formatters
```

---

## Integration Points

- **Export:** `export_run_bundle()` writes `insights.json` and `insights_report.md`
- **Dashboard:** `DashboardHandler` serves `/api/insights/{run_id}`
- **Analyst workflows:** Extends Increment 4 `compare_runs` with insight-level deltas

---

## Verification

```bash
python -m pytest src/tests/test_analytics.py -v
python scripts/analyze_run.py --scenario alpine-valley-v3 --ticks 50
python scripts/compare_runs.py --specs data/analyst/pacing_compare.json --what-if
```

---

## Next Steps (Optional)

- Persist insight history across batch exports in `batch_manifest.json`
- ADR for insight schema versioning if external consumers adopt `insights.json`
- Foundry dataset sync for insight objects (Track B, credentials-dependent)