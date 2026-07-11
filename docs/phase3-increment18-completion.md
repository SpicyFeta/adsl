# Phase 3 Increment 18 — Deeper Analytics & Insights (Complete)

**Date:** 2026-07-08  
**Status:** Complete  
**Directive:** Advance analytics from good to more sophisticated, contextual, and actionable insights.

---

## Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| Enhanced insight generation | `analytics/report.py`, `bottlenecks.py`, `risk.py`, `red_patterns.py` | ✅ |
| Reasoning & score breakdowns | `analytics/reasoning.py` | ✅ |
| Actionable recommendations | `analytics/recommendations.py` | ✅ |
| Cross-run pattern detection | `analytics/cross_run.py` | ✅ |
| Deeper what-if comparison | `analytics/what_if.py` (v1.1) | ✅ |
| Insights schema v1.1 | `INSIGHTS_SCHEMA_VERSION = "1.1"` | ✅ |
| Dashboard overlay enrichment | `viz/transform.py` | ✅ |
| CLI output improvements | `compare_runs.py`, formatters | ✅ |
| Tests | `test_analytics.py` (+6 tests) | ✅ |
| Documentation | `analytics-insights.md` | ✅ |

---

## Success Criteria

| Criterion | Evidence |
|-----------|----------|
| More specific, contextual insights | `structured_insights`, `recommendation` per finding, `actionable_recommendations` |
| Clear reasoning for risks | `reasoning_steps` on findings and evidence blocks |
| Cross-run pattern detection | `cross_run_patterns` in `compare_what_if` output |
| Stronger what-if | Node/corridor risk deltas, Red pattern changes, `comparison_narrative` |
| Traceability preserved | All new fields include `evidence` with `trace_ids`, `reasoning_steps` |
| Acceptable performance | 20 analytics tests pass; no engine changes |

---

## Schema v1.1 Additions

| Field | Purpose |
|-------|---------|
| `structured_insights` | Rich objects: headline, action, reasoning_steps, evidence |
| `actionable_recommendations` | Prioritized analyst actions with targets |
| `insight_context` | Network size, end-state, activity summary |
| `reasoning_steps` | Per-finding explainability (also in `evidence`) |
| `recommendation` | Per-finding suggested action |
| `contributing_factors` | Route risk score decomposition |

What-if schema v1.1 adds: `cross_run_patterns`, `actionable_recommendations`, `comparison_narrative`, `node_risk_shift` deltas.

---

## Verification

```bash
python -m pytest src/tests/test_analytics.py -v
python scripts/analyze_run.py --scenario alpine-valley-v3 --ticks 50 --markdown
python scripts/compare_runs.py --specs data/analyst/pacing_compare.json --what-if --markdown
```

---

## Out of Scope (unchanged)

- Machine learning / predictive modeling
- Real-time per-tick analytics
- New visualization engine for insights
- Core simulation engine changes