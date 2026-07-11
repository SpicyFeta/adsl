# ADSL Phase 3 — Increment 2 Locked Plan

**Status:** In progress  
**Date:** 2026-07-08  
**Track:** A (credential-independent)  
**Feature:** P3-F04 (Additional synthetic scenario)

---

## Scenario Concept

**ID:** `alpine-valley-v3`  
**Name:** Meridian Alpine Valley Dual-Corridor  
**Topology:** `alpine_dual_corridor` — inland alpine network with parallel north-ridge and south-ridge supply corridors converging at a central valley depot.

Distinct from:
- `kessari-strait-v1` — coastal stress test with heavy node destruction
- `island-chokepoint-v2` — island chokepoint with mainland ferry corridors

Workshop intent: demonstrate **dual-corridor route contestation** and Red pacing rotation across parallel passes without network collapse.

---

## Success Criteria

| ID | Criterion | Measure |
|----|-----------|---------|
| S1 | Registry entry | `alpine-valley-v3` maps to `logistics_scenario_v3.json` in `scenario_registry.json` |
| S2 | Runnable via CLI | `--scenario alpine-valley-v3` completes 100 ticks (seed=42) with status `COMPLETED` |
| S3 | Topology distinct | `metadata.topology == "alpine_dual_corridor"`; 11 nodes, 16 routes |
| S4 | Auditability | `len(audit_traces) == 100 × agent_count` (11 agents) |
| S5 | Workshop degradation | Node destruction < 40% at 100 ticks; ≥ 2 route statuses (OPEN/CLOSED/CONTESTED) |
| S6 | Mechanics compatibility | Hardening v2, deconfliction, ADR-010 Red pacing pass on v3 |
| S7 | Export compatibility | ADR-009 bundle exports without schema break |
| S8 | Regression | All existing tests pass; coverage ≥ 92% |

---

## Deliverables

| # | Deliverable |
|---|-------------|
| D1 | `data/synthetic/logistics_scenario_v3.json` |
| D2 | `scenario_registry.json` update |
| D3 | `src/tests/test_scenario_v3.py` acceptance tests |
| D4 | Regression updates (`test_scenario_registry.py`, `test_mechanics_regression.py`, `test_red_variety.py`, `test_export_bundle.py`) |
| D5 | README and demo-playbook updates |
| D6 | `docs/phase3-increment2-completion.md` |