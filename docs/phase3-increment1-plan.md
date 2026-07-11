# ADSL Phase 3 — Increment 1 Locked Plan

**Status:** Complete — implementation delivered 2026-07-08  
**Date:** 2026-07-08  
**Track:** A (credential-independent)  
**Features:** P3-F05 (Red agent variety), P3-F06 (light playbook validation)  
**Policy:** ADR-010 (Proposed — draft complete; acceptance required before implementation)

---

## Summary

Increment 1 delivers **bounded Red agent variety mechanics** to reduce repetitive long-run strike behavior and conducts **light independent validation** of the existing workshop demo playbook. No Foundry credentials, engine orchestration changes, or export schema changes are required.

**Implementation must not begin** until PM issues an explicit implementation directive after reviewing this locked plan and ADR-010.

---

## Duration and Dependencies

| Item | Value |
|------|-------|
| Duration estimate | 2–3 weeks |
| External dependencies | None (Foundry-independent) |
| Internal dependencies | Phase 2 stable baseline; ADR-010 accepted before code |
| Parallel work | Track B (Live SDK) **not** authorized in Inc 1 |

---

## Deliverables

| # | Deliverable | Owner | Notes |
|---|-------------|-------|-------|
| D1 | ADR-010 accepted | Engineering + PM | Red variety policy — draft complete |
| D2 | Red variety module or agent updates | Engineering | Scoped per ADR-010; primarily `red_interdiction.py` |
| D3 | Force element metadata conventions | Engineering | Optional per-element `strike_cooldown_ticks`, `strike_budget` |
| D4 | Audit trace updates | Engineering | Reasoning cites ADR-010 when cooldown/budget affects decision |
| D5 | Unit and golden trace tests | Engineering | Deterministic pacing assertions |
| D6 | Regression on v1 + v2 scenarios | Engineering | 100-tick runs; no test count regression |
| D7 | Playbook validation report | Facilitator + PM | `docs/phase3-increment1-playbook-validation.md` (template below) |
| D8 | Increment 1 completion note | Engineering | Brief summary for Phase 3 handover inputs |

---

## Scope — Red Agent Variety Mechanics (In Scope)

Per ADR-010 (high-level). Implementation details deferred to implementation phase.

### In scope

| Mechanic | Description |
|----------|-------------|
| **Strike cooldown** | After a Red agent applies `ATTACK_ROUTE` or `ATTACK_NODE`, that agent cannot authorize the same action type against any target for `cooldown_ticks` (default: 3). Agent may still `NO_ACTION` with trace explaining hold. |
| **Per-run strike budget** | Optional `metadata.strike_budget` on `ADSL_ForceElement` (integer, default: unlimited). Each applied attack decrements budget; at zero, agent holds with auditable `NO_ACTION`. |
| **Target rotation preference** | Extend existing `_engaged_targets` deprioritization: recently struck targets (within cooldown window) receive zero utility; encourages alternation among patrol routes. |
| **Readiness interaction** | Existing `readiness` multiplier unchanged; cooldown and budget gate before utility scoring. |
| **Role coverage** | `STRIKE` (route attacks) and `FIRE_SUPPORT` (node attacks); `RECONNAISSANCE` unchanged. |
| **Trace contract** | All holds due to cooldown/budget produce `NO_ACTION` traces citing ADR-010 with evidence fields (`cooldown_remaining`, `strike_budget_remaining`). |
| **Determinism** | Cooldown and budget state derived from tick count and agent action history — reproducible golden traces. |

### Out of scope (Increment 1)

| Item | Rationale |
|------|-----------|
| Engine / deconfliction changes | ADR-008 unchanged; variety is agent-side gating only |
| Blue agent changes | Inc 1 is Red-focused |
| New scenarios | Increment 2 |
| Multi-run aggregation | Increment 4 |
| Modality rotation or new action types | Beyond P2-F07 bounded scope |
| Doctrine modeling | Phase 3 P3 out-of-scope |
| Live SDK / Ontology changes | Track B |
| Demo playbook rewrite | Light validation only; fixes limited to README/troubleshooting if blocking |

### Default parameters (locked for Inc 1)

| Parameter | Default | Override |
|-----------|---------|----------|
| `strike_cooldown_ticks` | 3 | Per force element `metadata.strike_cooldown_ticks` |
| `strike_budget` | None (unlimited) | Per force element `metadata.strike_budget` (integer) |
| Cooldown scope | Per agent, all targets | Not per-target cooldown in Inc 1 |

---

## Scope — Light Playbook Validation (In Scope)

Validation of existing `docs/demo-playbook.md` — **not** a new playbook or UI.

### In scope

| Activity | Detail |
|----------|--------|
| Facilitator | One person **not** the primary ADSL implementer |
| Parts executed | **Parts 1–4** (required): setup, v1 stress run, v2 workshop run, export bundle + artifact inspection |
| Parts optional | Parts 5–6 (mechanics narrative, Palantir status) — facilitator may skip if time-constrained |
| Time target | Complete Parts 1–4 in **≤ 30 minutes** |
| Environment | Clean machine or fresh venv per playbook prerequisites |
| Output | Completed validation report with checklist, elapsed time, friction log |

### Validation checklist (required pass items)

- [ ] `pip install -e ".[dev]"` succeeds from project root
- [ ] `python -m pytest -q` reports 46 passed (baseline at Inc 1 lock-in)
- [ ] `kessari-strait-v1` 100-tick run completes with `COMPLETED`
- [ ] `island-chokepoint-v2` 100-tick run completes with `COMPLETED`
- [ ] `export_run.py` produces valid bundle under `exports/<run_id>/`
- [ ] `manifest.json` shows `export_schema_version: "1.0"` and `source_system: "ADSL_PHASE2"`
- [ ] `executive_summary.md` readable without code knowledge

### Out of scope (playbook validation)

| Item | Rationale |
|------|-----------|
| Independent facilitator scheduling | PM/organizational responsibility |
| Foundry or live sync demonstration | Track B not active |
| Stakeholder audience feedback | Future workshop event |
| Automated playbook runner | Manual execution only for Inc 1 |
| Export schema changes | Not required for validation pass |

### Friction severity classification

| Severity | Definition | Inc 1 response |
|----------|------------|----------------|
| **Blocker** | Cannot complete Parts 1–4 without author assistance | Document; fix README/troubleshooting in Inc 1 if trivial |
| **Minor** | Slows facilitator but completable | Document only |
| **Cosmetic** | Wording or output formatting | Document only; defer playbook edit |

---

## Success Criteria

Increment 1 is **complete** when all criteria below are met:

### Red variety (engineering)

| # | Criterion | Measure |
|---|-----------|---------|
| R1 | ADR-010 accepted | PM sign-off; status Accepted |
| R2 | Cooldown enforced | Given STRIKE agent attacks at tick T, agent does not emit `ATTACK_ROUTE` at ticks T+1..T+cooldown-1 (default cooldown=3); may emit `NO_ACTION` with ADR-010 trace |
| R3 | Strike budget enforced | Given `strike_budget=2`, agent emits at most 2 applied attacks per run; subsequent decisions are `NO_ACTION` with budget evidence |
| R4 | Measurable pacing improvement | On `kessari-strait-v1`, 100 ticks, seed=42: `ATTACK_ROUTE` count **≤ Phase 2 baseline (7)** OR distinct route targets struck **≥ Phase 2 baseline** — at least one metric improved, documented in completion note |
| R5 | Golden traces | At least one golden trace fixture for cooldown hold and one for budget exhaustion |
| R6 | Regression | All Phase 2 tests pass; total test count ≥ 46; coverage ≥ 92% |
| R7 | Scenarios | `kessari-strait-v1` and `island-chokepoint-v2` both complete 100-tick runs with `COMPLETED` |
| R8 | Auditability | 100% agent decisions still produce `ADSL_AuditTrace`; no silent decisions |
| R9 | Modularity | No engine orchestration change; no Palantir SDK imports added |
| R10 | Deconfliction compatibility | ADR-008 suppression behavior unchanged; variety gates apply before action selection |

### Playbook validation (process)

| # | Criterion | Measure |
|---|-----------|---------|
| P1 | Independent execution | Validation report signed by non-author facilitator |
| P2 | Time target | Parts 1–4 completed in ≤ 30 minutes **or** blockers documented with severity |
| P3 | Checklist | All required checklist items pass **or** blockers documented |
| P4 | Report filed | `docs/phase3-increment1-playbook-validation.md` committed |

### Increment exit

| # | Criterion | Measure |
|---|-----------|---------|
| E1 | No scope creep | No scenarios, UI, SDK, or doctrine work merged under Inc 1 |
| E2 | PM sign-off | Increment 1 completion acknowledged before Increment 2 opens |

---

## Phase 2 Baseline (Reference for R4)

From Phase 2 final regression (`kessari-strait-v1`, 100 ticks, seed=42):

| Metric | Value |
|--------|-------|
| `ATTACK_ROUTE` traces | 7 |
| `ATTACK_NODE` traces | 15 |
| `NO_ACTION` traces (Red) | Majority of Red turns at saturation |

R4 requires documented improvement in strike pacing metrics vs this baseline.

---

## Implementation Sequence (Post-Approval Only)

When PM authorizes implementation:

1. Accept ADR-010
2. Implement cooldown and budget state in Red agent (agent-side only)
3. Update audit traces per ADR-010
4. Add unit tests and golden traces
5. Run regression; verify R4 metrics
6. Conduct playbook validation in parallel (organizational track)
7. File validation report and increment completion note

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Cooldown makes Red too passive | Default cooldown=3; tune via metadata; R4 metric gate |
| Budget breaks scenario balance | Budget optional per element; default unlimited |
| Playbook validation delayed | Engineering completion not blocked; P1–P4 required for Inc 1 exit |
| Interaction with ADR-008 suppression | Variety is pre-decision gating; deconfliction unchanged |

---

## Related Documents

- [ADR-010](decisions/ADR-010-red-agent-variety.md) — policy (Proposed)
- [phase3-scoping.md](phase3-scoping.md) — Phase 3 approved ordering
- [demo-playbook.md](demo-playbook.md) — validation subject
- [ADR-004](decisions/ADR-004-simulation-orchestration-policy.md) — orchestration unchanged
- [ADR-008](decisions/ADR-008-hardening-deconfliction.md) — deconfliction unchanged

---

*Locked by PM directive 2026-07-08. Implementation forbidden until explicit PM implementation approval.*