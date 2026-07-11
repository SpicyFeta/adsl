# Phase 3 Increment 13 — Advanced Analytics & Insights (Complete)

**Date:** 2026-07-08  
**Status:** Complete  
**Directive:** Automated analytics and insight generation from simulation results.

> **Note:** Core analytics were delivered in Increment 9. Increment 13 validates success criteria, adds node risk scoring, Red timing/disruption patterns, recommended focus areas, CLI aliases, dashboard panels, and formalizes ADR-014.

---

## Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| Analytics module | `src/adsl/analytics/` | ✅ |
| Node risk scoring | `risk.score_node_risks()` | ✅ |
| Red timing/disruption zones | `red_patterns.disruption_zone_timing` | ✅ |
| Recommended focus areas | `report.recommended_focus_areas` | ✅ |
| Single-run CLI | `scripts/analyze_run.py`, `adsl-analyze` | ✅ |
| What-if comparison | `scripts/compare_runs.py --what-if`, `adsl-compare` | ✅ |
| Export integration | `insights.json`, `insights_report.md` | ✅ |
| Dashboard API + UI | `/api/insights/{run_id}`, focus areas + node risk panels | ✅ |
| ADR-014 | `docs/decisions/ADR-014-analytics-insights.md` | ✅ |
| Documentation | `docs/analytics-insights.md` (updated) | ✅ |
| Tests | `src/tests/test_analytics.py` (16 tests) | ✅ |

---

## Success Criteria

| Criterion | Evidence |
|-----------|----------|
| Rank critical bottlenecks and high-risk routes/nodes | `critical_highlights`, `node_risks`, `route_risks`, `corridor_risks` |
| Compare multiple runs with clear differences | `compare_what_if()` + `--what-if` CLI |
| Understandable automated summaries | `key_insights`, `recommended_focus_areas` |
| Traceable to source data | `evidence` blocks on every finding |
| CLI + dashboard access | `adsl-analyze`, `adsl-compare`, insights panel |

---

## Verification

```bash
python -m pytest src/tests/test_analytics.py -v
python scripts/analyze_run.py --scenario alpine-valley-v3 --ticks 50
python scripts/compare_runs.py --specs data/analyst/pacing_compare.json --what-if
python scripts/launch_dashboard.py --export-dir exports
```

---

## Out of Scope (unchanged)

- Machine learning / predictive modeling
- Real-time analytics during simulation
- Advanced insight visualizations