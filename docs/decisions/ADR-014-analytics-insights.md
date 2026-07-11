# ADR-014: Explainable Analytics & Insights

**Status:** Accepted  
**Date:** 2026-07-08  
**Increment:** Phase 3 Increment 13 (extends Increment 9)

---

## Context

Analysts need automated interpretation of ADR-009 run bundles — bottlenecks, risks, Red patterns, and what-if comparisons — without manual trace review. Increment 9 delivered the core module; Increment 13 formalizes the schema, focus-area recommendations, and dashboard exposure.

All analytics must remain **rule-based and explainable** (no ML/black-box models).

---

## Decision

1. **Read-only analytics layer** — `adsl.analytics` consumes `run_bundle.json` only; never mutates simulation state.

2. **Heuristic scoring** — Nodes, routes, and corridors scored 0–100 using transparent rules (status, metadata, Red pressure, topology).

3. **Evidence contract** — Every finding includes `evidence` with `source`, `trace_ids`, `entity_ids`, `ticks`, and `counts`.

4. **Report schema** — `INSIGHTS_SCHEMA_VERSION = "1.0"` with `key_insights`, `recommended_focus_areas`, and categorized `findings`.

5. **What-if comparison** — `compare_what_if()` diffs metrics and insight-level changes across ≥2 runs.

6. **Optional integration** — Export bundles include `insights.json`; dashboard serves `/api/insights/{run_id}`. Simulation engine has zero analytics imports.

7. **CLI entry points** — `scripts/analyze_run.py`, `scripts/compare_runs.py --what-if`, and installed aliases `adsl-analyze`, `adsl-compare`.

---

## Consequences

- Analysts get ranked risks and focus areas without reading every audit trace.
- All scores are auditable — analysts can follow `trace_ids` to raw data.
- No runtime simulation overhead (post-run analysis only).
- Heuristics may not capture domain-specific doctrine without future ADR scope.

---

## Out of Scope

- Machine learning / predictive modeling
- Real-time per-tick analytics during simulation
- Advanced visualization beyond dashboard text panels