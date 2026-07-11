# ADSL Phase 2 — Handover

**Date:** 2026-07-08  
**Status:** Phase 2 complete (with Increment 2 live SDK deferred)  
**Next milestone:** v2.5 strategic review

---

## Executive Summary

Phase 2 extended ADSL from a single-scenario MVP into a **workshop-ready contested-logistics simulation** with multi-scenario support, export bundles, hardened route mechanics, and same-tick action deconfliction. Live Palantir Foundry SDK integration was **prepared but not activated** — awaiting stakeholder credentials and PM approval per ADR-007.

| Metric | Phase 1 exit | Phase 2 exit |
|--------|--------------|--------------|
| Tests | 23 passed | **46 passed** |
| Coverage | ~91% | **92%** |
| Scenarios | 1 (Kessari Strait) | **2** (v1 + island chokepoint v2) |
| ADRs | ADR-001–006 (accepted) | ADR-007 (proposed), ADR-008–009 (accepted) |
| Export bundles | None | ADR-009 workshop bundles |
| Simulation mechanics | Phase 1 hardening (metadata only) | Hardening v2 + deconfliction (ADR-008) |

---

## What Was Delivered

### Increment 1 — Demo Foundation

| Deliverable | Path / detail |
|-------------|---------------|
| Scenario v2 | `data/synthetic/logistics_scenario_v2.json` — island chokepoint, 12 nodes, 18 routes |
| Scenario registry | `data/synthetic/scenario_registry.json` — `kessari-strait-v1`, `island-chokepoint-v2` |
| Export module | `src/adsl/export/bundle.py`, `summary.py` |
| Export CLI | `scripts/export_run.py` |
| CLI flags | `--scenario`, `--export-dir`, `--quiet-logs` on `run_simulation.py` |
| ADR-009 | Run export bundle and executive summary contract (accepted) |

### Increment 2 — Live Palantir Ontology Integration (Preparation Only)

| Deliverable | Status |
|-------------|--------|
| ADR-007 draft | Proposed — architecture, credential requirements, activation gates |
| SDK skeleton | `src/adsl/ontology/sdk_client.py` — placeholder methods, `is_live_ready()` always `False` |
| Integration wiring | `integration.py` delegates to `get_sdk_client()` |
| SDK in `pyproject.toml` | **Not added** |
| Live SDK calls | **Not implemented** |
| `validate_ontology_payload.py` | Deferred to activation |

**Activation gate:** `ADSL_ONTOLOGY_SYNC_ENABLED=true` plus `FOUNDRY_URL`, `FOUNDRY_TOKEN`, `ONTOLOGY_RID`, and live-ready client.

### Increment 3 — Simulation Mechanics v2

| Deliverable | Path / detail |
|-------------|---------------|
| Hardening v2 | `src/adsl/simulation/hardening.py` — `harden_level=1` absorbs first route attack |
| Deconfliction | `src/adsl/simulation/deconfliction.py` — same-tick target registry, `ACTION_SUPPRESSED` events |
| Engine integration | `src/adsl/simulation/engine.py` |
| Agent updates | Blue/Red traces cite ADR-008 |
| ADR-008 | Hardening and deconfliction policy (accepted) |
| Tests | Unit, golden trace, regression on v1 + v2 |

### Increment 4 — Phase 2 Closure

| Deliverable | Path |
|-------------|------|
| Handover document | `docs/phase2-handover.md` (this file) |
| Demo playbook | `docs/demo-playbook.md` |
| README Phase 2 section | `README.md` |
| ADR index | `docs/decisions/README.md` |
| v2.5 review inputs | `Foundation_Chain_Status_Update_v2.5.md` |

---

## How to Run

### Prerequisites

- Python 3.11+
- Dependencies: `pip install -e ".[dev]"` or `uv sync --extra dev`

### Quick commands

```bash
# List scenarios
python scripts/run_simulation.py --scenario kessari-strait-v1 --ticks 50 --quiet-logs

# Workshop scenario (slower degradation)
python scripts/run_simulation.py --scenario island-chokepoint-v2 --ticks 100 --quiet-logs

# Export workshop bundle (ADR-009)
python scripts/export_run.py --scenario island-chokepoint-v2 --ticks 100 --export-dir exports --quiet-logs

# Run all tests
python -m pytest
```

### CLI options (Phase 2)

| Flag | Default | Description |
|------|---------|-------------|
| `--scenario` | `kessari-strait-v1` | Scenario ID from registry |
| `--dataset` | — | Direct path to scenario JSON (overrides `--scenario`) |
| `--ticks` | `50` | Tick count (max 100) |
| `--seed` | `42` | Random seed |
| `--export-dir` | off | Write ADR-009 export bundle after run |
| `--quiet-logs` | off | Suppress structlog JSON during simulation |
| `--sync-ontology` | off | Placeholder Ontology sync (not live SDK) |

---

## Final Regression Results (2026-07-08)

### Test suite

```
46 passed in ~2s
Coverage: 92% (1086 statements, 85 missed)
```

### 100-tick runs (seed=42)

| Scenario | Status | Traces | Events | Nodes (end) | Routes (end) |
|----------|--------|--------|--------|-------------|--------------|
| `kessari-strait-v1` | COMPLETED | 1,100 | 2,505 | 8 DESTROYED, 1 OPERATIONAL, 1 DEGRADED | 10 OPEN, 6 CLOSED, 2 CONTESTED |
| `island-chokepoint-v2` | COMPLETED | 1,100 | 2,404 | **12 OPERATIONAL** (0% destroyed) | 9 OPEN, 9 CLOSED |

Scenario v2 demonstrates the intended workshop-friendly degradation curve: route contestation without node destruction at 100 ticks.

---

## Known Limitations

| Limitation | Detail | Phase 3 candidate |
|------------|--------|-------------------|
| **Live Foundry SDK** | Placeholder sync only; ADR-007 proposed, not activated | Inc 2 activation when credentials arrive |
| **No workshop UI** | CLI + export bundles + executive summary markdown | Dashboard or Foundry Workshop app |
| **Batch sync** | Traces/events batched at run end | Per-tick streaming sync (optional) |
| **Single absorption layer** | `harden_level=1` max in Inc 3 | Multi-level hardening, decay |
| **Red variety deferred** | No per-agent cooldown/strike budget (P2-F07) | Agent variety mechanics |
| **Schema validation** | No live Ontology schema manifest | `validate_ontology_payload.py` at Inc 2 activation |
| **Simplified dynamics** | No doctrine, physics, theater-scale | Scoped doctrine modeling |
| **Credentials unset** | `FOUNDRY_URL`, `FOUNDRY_TOKEN`, `ONTOLOGY_RID` not configured | Stakeholder delivery |

These boundaries are intentional and documented in ADR-006, ADR-007, and ADR-008.

---

## Phase 2 Exit Criteria Assessment

| Criterion | Status | Notes |
|-----------|--------|-------|
| Multi-scenario CLI | **Met** | Registry + 2 scenarios |
| Hardening v2 | **Met** | ADR-008 accepted, tested |
| Deconfliction | **Met** | `ACTION_SUPPRESSED` events, golden traces |
| Workshop export | **Met** | ADR-009 bundle + executive summary |
| Auditability | **Met** | 100% agent decisions produce traces |
| Modularity | **Met** | Engine has zero Palantir SDK imports |
| Tests | **Met** | 46 passed, 92% coverage (≥ Phase 1 baseline) |
| Documentation | **Met** | Handover, playbook, ADR index, README |
| Live sync | **Deferred** | Inc 2 prep complete; credentials pending PM/stakeholder sign-off |

---

## Delivered vs. Remaining for Phase 3

### Delivered in Phase 2

- Multi-scenario support with registry resolver
- Workshop export bundles (JSON, JSONL, executive summary)
- Hardening v2 with attack absorption
- Same-tick action deconfliction with full audit trail
- SDK client skeleton and ADR-007 activation architecture
- Golden trace and regression test matrix
- Demo playbook for non-author workshop execution

### Remaining for Phase 3 (recommended priorities)

1. **Live Foundry SDK activation** (highest leverage) — wire `sdk_client.py`, add SDK dependency, schema validation, gated live integration test. Blocked on credentials.
2. **Workshop UI or Foundry-native demo surface** — reduce CLI dependency for stakeholder audiences.
3. **Additional scenarios** — one at a time with acceptance criteria; geography/doctrine variants.
4. **Red agent variety** — cooldowns, strike budgets, modality rotation (P2-F07 deferred).
5. **Multi-run aggregation** — compare runs, trend metrics, batch export.
6. **Doctrine modeling** — only with explicit stakeholder scope and ADR.

Do **not** open doctrine, theater-scale, or physics modeling without v2.5 stakeholder prioritization.

---

## Architecture Decision Records

| ADR | Title | Status | Phase |
|-----|-------|--------|-------|
| ADR-001 | Python Language Selection | Accepted | 1 |
| ADR-002 | Custom Agent System | Accepted | 1 |
| ADR-003 | AuditTrace System | Accepted | 1 |
| ADR-004 | Simulation Orchestration Policy | Accepted | 1 |
| ADR-005 | Blue Adaptation Policy | Accepted | 1 |
| ADR-006 | Palantir Integration Architecture | Accepted | 1 |
| ADR-007 | Live Palantir Ontology SDK Integration | **Proposed** | 2 (prep) |
| ADR-008 | Hardening v2 and Deconfliction | Accepted | 2 |
| ADR-009 | Run Export Bundle Contract | Accepted | 2 |

Full index: [`docs/decisions/README.md`](decisions/README.md)

---

## Readiness for v2.5 Strategic Review

Phase 2 is **complete and ready** for the v2.5 strategic review, with live SDK explicitly deferred.

### Demonstrated capabilities

- Two synthetic scenarios runnable via CLI with registry
- Workshop export bundles consumable without re-running simulation
- Hardening v2 materially affects attack outcomes with auditable absorption
- Same-tick conflicts resolved deterministically with suppression events
- Offline CI stable (46 tests, no Foundry network calls)
- SDK activation path documented with clear credential checklist

### Review topics for stakeholders

1. **Foundry activation** — credential delivery timeline, schema manifest, SDK package pin
2. **Demo format** — CLI + export vs. workshop UI vs. Foundry Workshop app
3. **Phase 3 priority ranking** — live SDK vs. UI vs. scenarios vs. doctrine
4. **Success metrics** — acceptance criteria for first live sync run
5. **Red variety / advanced mechanics** — whether P2-F07 should enter Phase 3

### Related documents

- [Demo playbook](demo-playbook.md)
- [Phase 2 planning](phase2-planning.md)
- [Phase 1 handover](phase1-handover.md)
- [v2.5 strategic review inputs](../Foundation_Chain_Status_Update_v2.5.md)
- [ADR index](decisions/README.md)
- [README](../README.md)

---

## Key Source Paths

```
src/adsl/
├── agents/           # Red interdiction, Blue logistics (ADR-008 traces)
├── simulation/       # Engine, hardening, deconfliction, registry
├── ontology/         # integration.py, sdk_client.py (skeleton)
├── export/           # bundle.py, summary.py (ADR-009)
└── models.py         # ACTION_SUPPRESSED event type

data/synthetic/
├── logistics_scenario_v1.json
├── logistics_scenario_v2.json
└── scenario_registry.json

scripts/
├── run_simulation.py
└── export_run.py

docs/
├── phase2-handover.md
├── demo-playbook.md
└── decisions/        # ADR-001–009
```