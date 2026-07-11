# ADSL Phase 3 — Scoping Document

**Status:** Approved — Phase 3 active; Increment 1 complete  
**Date:** 2026-07-08  
**Last updated:** 2026-07-08 (Increment 1 delivered; stakeholder alignment package issued)  
**Basis:** Phase 2 closure (`docs/phase2-handover.md`), Foundation Chain Status Update v2.5, ADR-001–009, demo playbook (`docs/demo-playbook.md`)

---

## Executive Summary

ADSL Phase 2 delivered a workshop-ready contested-logistics platform: two scenarios, export bundles, hardening v2, deconfliction, SDK skeleton, and 46 passing tests. **Live Palantir Foundry SDK integration remains deferred** — preparation complete (ADR-007 Proposed), activation blocked on stakeholder credentials.

Phase 3 extends ADSL toward **live platform integration** (when credentials arrive), **richer demonstration and analyst value**, and **optional mechanics depth** — while preserving Phase 1/2 non-negotiables: auditability, explainability, modularity, ADR-governed design, and data-gated increment delivery.

Phase 3 scoping is **approved**. **Increment 1** (Red Agent Variety + Playbook Validation) is **complete** — see [`phase3-increment1-completion.md`](phase3-increment1-completion.md), [`phase3-increment1-playbook-validation.md`](phase3-increment1-playbook-validation.md), and [ADR-010](decisions/ADR-010-red-agent-variety.md) (Accepted). **Next Track A candidate:** Increment 2 (Additional Scenario), pending PM authorization. **Track B** remains blocked on Foundry credentials.

**Approved increment ordering:**

| Order | Increment | Track | Status |
|-------|-----------|-------|--------|
| **1** | Red Agent Variety + Playbook Validation | A | **Complete** — see `phase3-increment1-completion.md` |
| 2 | Additional Scenario | A | **Complete** — see `phase3-increment2-completion.md` |
| 3 | Live Foundry SDK Activation | B | Planned — when credentials arrive |
| 4 | Analyst Workflows | A | **Complete** — see `phase3-increment4-completion.md` |
| 5 | Demo Surface | A/B | Conditional — demo format decision |
| 6 | Visualization Layer | A | **Complete** — see `phase3-increment6-completion.md` |
| 7 | Documentation & Positioning | A | **Complete** — see `phase3-increment7-completion.md` |
| 8 | Advanced Mechanics | A | Optional — PM-gated |

**Two parallel tracks are defined:**

| Track | Dependency | Can start now? |
|-------|------------|----------------|
| **Track A — Credential-independent** | PM approval only | **Yes** (after v2.5 alignment) |
| **Track B — Foundry activation** | Credentials, schema manifest, ADR-007 acceptance | **No** — blocked on stakeholders |

---

## Proposed Phase 3 Goals

Aligned with Foundation Chain Status Update v2.5 recommendations:

| Goal | Phase 3 intent |
|------|----------------|
| **Complete live Palantir integration** | Activate ADR-007; real Ontology writes when credentials present; schema validation; gated live smoke test |
| **Sustain workshop readiness** | Playbook Parts 1–4 validated (engineering proxy); independent facilitator sign-off pending |
| **Extend simulation depth (bounded)** | Red agent variety **delivered** (ADR-010); optional multi-level hardening; no doctrine/scale without explicit ADR |
| **Expand scenario library (disciplined)** | One scenario per increment with acceptance tests and registry entry |
| **Improve analyst workflows** | Multi-run comparison, trend metrics, batch export (lower priority) |
| **Optional demo surface** | Workshop UI or Foundry-native presentation — only after stakeholder demo-format decision |
| **Maintain auditability & modularity** | ADR-003 trace contract unchanged; engine remains Palantir-agnostic; custom agent framework retained |
| **Preserve honesty boundaries** | No claim of live integration until Foundry object visibility verified; RL1/RL6 unchanged |

---

## Potential Feature Areas (Grouped by Priority)

### P0 — Highest leverage (credential-dependent)

| ID | Feature area | Description | External dependency |
|----|--------------|-------------|---------------------|
| P3-F01 | **Live Ontology SDK activation** | Wire `sdk_client.py` live paths; add SDK to `pyproject.toml`; implement append/upsert per ADR-006/007 | **Foundry credentials**, schema manifest, PM acceptance of ADR-007 |
| P3-F02 | **Ontology schema validation** | `validate_ontology_payload.py` against stakeholder schema manifest; fail fast before live writes | Schema manifest from platform team |
| P3-F03 | **Live integration smoke test** | Gated `pytest -m live_foundry`; verify object visibility in Foundry; rollback test | Foundry environment, network egress |

**v2.5 proposed success metrics (first live sync — ratification pending):**
1. `validate_ontology_payload.py` passes against schema manifest
2. `pytest -m live_foundry` passes in gated environment
3. ≥ 1 `ADSL_AuditTrace` and ≥ 1 `ADSL_SimulationRun` visible in Foundry Ontology
4. Rollback verified via `ADSL_ONTOLOGY_SYNC_ENABLED=false`

---

### P1 — High value (no Foundry dependency)

| ID | Feature area | Description | External dependency |
|----|--------------|-------------|---------------------|
| P3-F04 | **Additional synthetic scenario(s)** | Third+ scenario; one per increment; defined degradation curve and acceptance tests | PM approval of scenario concept |
| P3-F05 | **Red agent variety** | Per-agent cooldown, strike budget, target rotation (P2-F07 deferred) | **Delivered** — ADR-010 Accepted; Inc 1 complete |
| P3-F06 | **Demo playbook validation** | Independent facilitator executes playbook; document friction points | **Partial** — engineering proxy PASS; independent facilitator pending |
| P3-F07 | **Multi-run aggregation** | Compare runs by seed/scenario; trend summaries; batch export directory | None (engineering) |
| P3-F08 | **Export schema v1.1** | Optional export enhancements (comparison metadata, run lineage) if analyst need confirmed | Stakeholder feedback on export consumption |

---

### P2 — Conditional (stakeholder decision required)

| ID | Feature area | Description | Blocker |
|----|--------------|-------------|---------|
| P3-F09 | **Workshop UI / dashboard** | Lightweight web or static dashboard for run visualization | Demo format decision (CLI/export vs UI vs Foundry Workshop app) |
| P3-F10 | **Foundry Workshop app integration** | Native Foundry presentation layer | Foundry credentials + platform team guidance |
| P3-F11 | **Per-tick trace streaming** | Live Foundry feed during simulation ticks | Live SDK active + workshop requirement confirmed |
| P3-F12 | **Multi-level hardening** | `harden_level > 1`, decay, stacking rules | ADR amendment; gameplay balance review |

---

### P3 — Out of scope unless explicitly opened by PM + stakeholder ADR

| Area | Rationale |
|------|-----------|
| Doctrine modeling | Requires scoped ADR and subject-matter stakeholder input; not justified by Phase 2 evidence alone |
| Theater-scale simulation | Beyond ADSL bounded logistics scope |
| Physics / high-fidelity dynamics | Phase 1/2 intentional boundary |
| Ontology read for scenario seeding | Write-first policy; deferred since Phase 1 |
| LangChain, CrewAI, AutoGen, or external agent frameworks | ADR-002 prohibition |
| Foundation Chain tooling changes | Separate Aether track; no ADSL scope bleed per v2.5 |
| Classified / air-gapped deployment hardening | Operations concern; document assumptions only |

---

## Dependencies

### External (Stakeholder-provided)

| Dependency | Owner | Required for | Status |
|------------|-------|--------------|--------|
| `FOUNDRY_URL` | IT / Platform | P3-F01–F03 (Track B) | **Not configured** |
| `FOUNDRY_TOKEN` | IT / Platform | P3-F01–F03 | **Not configured** |
| `ONTOLOGY_RID` | Platform team | P3-F01–F03 | **Not configured** |
| Ontology schema manifest | Platform team | P3-F02 | **Not delivered** |
| SDK package name + pinned version | Engineering + Platform | P3-F01 | **TBD** |
| Network egress to Foundry | Operations | P3-F03 | **Unknown** |
| Demo format decision | Stakeholders / PM | P3-F09, P3-F10 | **Unresolved** |
| Phase 3 priority ranking | PM / Stakeholders | Increment ordering | **Unresolved** |
| Doctrine/scale in/out of scope (6–9 months) | PM / Stakeholders | P3 doctrine items | **Unresolved** |

### Internal (Engineering)

| Dependency | Required for |
|------------|--------------|
| Phase 2 codebase stable (tagged or documented baseline) | All increments |
| ADR-007 acceptance before live SDK code | Track B only |
| ADR amendment before Red variety or hardening scope expansion | P3-F05, P3-F12 |
| CI remains offline by default (no live Foundry in default `pytest`) | All increments |
| Module boundaries preserved (`ontology/` vs `simulation/` vs `export/`) | All increments |
| Demo playbook available for validation | P3-F06 |

### What can start without external dependencies

| Work | Prerequisites |
|------|---------------|
| Additional scenario (P3-F04) | PM-approved scenario brief + acceptance criteria |
| Red agent variety (P3-F05) | **Complete** — no further work unless PM opens Inc 6 |
| Multi-run aggregation (P3-F07) | PM approval of increment plan |
| Export schema v1.1 (P3-F08) | Stakeholder confirmation that v1.0 exports are insufficient |
| Demo playbook validation (P3-F06) | Independent facilitator assigned |
| Golden trace / regression expansion | Part of any mechanics increment |

### What requires Foundry credentials

| Work | Cannot start until |
|------|-------------------|
| SDK package addition to `pyproject.toml` | Credentials + ADR-007 accepted |
| Live `read_object()` / `write_object()` | Credentials + SDK wired |
| `validate_ontology_payload.py` against live schema | Schema manifest delivered |
| `pytest -m live_foundry` | Gated Foundry environment |
| Foundry Workshop app (P3-F10) | Live SDK + platform guidance |

---

## High-Level Increments (Suggested Grouping)

Phase 3 follows the same gated increment model as Phase 2: locked plan, success criteria, PM approval before implementation. Increments may run in parallel only when module boundaries are respected and PM explicitly authorizes parallel tracks.

### Increment 1 — Red Agent Variety + Playbook Validation (Track A) — **COMPLETE**

**Status:** Complete — 2026-07-08 — see [`phase3-increment1-completion.md`](phase3-increment1-completion.md)  
**Policy:** [ADR-010](decisions/ADR-010-red-agent-variety.md) (**Accepted**)  
**Duration:** Delivered within estimate  
**Dependency:** None (Foundry-independent)  
**Features:** P3-F05 (Red variety), P3-F06 (light playbook validation)

P3-F07 (multi-run compare) **removed from Inc 1 scope** — deferred to Increment 4.

| Deliverable | Outcome |
|-------------|---------|
| Red agent pacing | `red_pacing.py` — strike cooldown (default 3 ticks); optional strike budget; target rotation |
| ADR-010 | **Accepted** — pacing gates in `red_interdiction.py`; metadata in orchestration context |
| Playbook validation | Parts 1–4 PASS in ~5 min (engineering proxy); independent facilitator still recommended |
| Tests | **58 passed**, **92% coverage**; golden fixtures for cooldown and budget exhaustion |
| Regression | Both scenarios COMPLETED at 100 ticks; ADR-008 deconfliction unchanged |

**Increment 1 results (kessari-strait-v1, 100 ticks, seed=42):**

| Metric | Phase 2 baseline | Inc 1 result |
|--------|------------------|--------------|
| `ATTACK_ROUTE` traces | 7 | 36 |
| Distinct route targets | ~5 | 5 |
| ADR-010 pacing holds | — | 100 |

R4 passed via distinct targets ≥ baseline and measurable pacing holds — not via attack count reduction. Cooldown increases route rotation across patrol corridors rather than reducing total strikes on stress scenarios.

**Lessons for subsequent increments:**

- Track A delivery model (locked plan → ADR acceptance → implementation → completion note) remains effective without Foundry dependency.
- Inc 2 (additional scenario) is validated as the right next Track A step while credentials remain pending.
- Independent facilitator sign-off for P3-F06 should be pursued before Phase 3 exit; engineering proxy is sufficient for Inc 1 closure only.
- Red variety scope per ADR-010 is sufficient for workshop demos; per-target cooldown and modality rotation remain out of scope unless PM opens via ADR amendment.

---

### Increment 2 — Additional Scenario (Track A)

**Duration estimate:** 2–3 weeks  
**Dependency:** PM-approved scenario concept  
**Features:** P3-F04

| Deliverable | Detail |
|-------------|--------|
| `logistics_scenario_v3.json` (or named variant) | Distinct topology/stress profile from v1 and v2 |
| Registry entry | `scenario_registry.json` update |
| Acceptance tests | 100-tick end-state metrics; golden trace baseline |
| Export compatibility | ADR-009 bundle works without schema break |

**Success criteria (draft):**
- [ ] Third scenario runnable via `--scenario`
- [ ] Defined end-state metrics met at 100 ticks (documented in scenario brief)
- [ ] Regression suite includes v3 scenario
- [ ] One scenario only — no batching

---

### Increment 3 — Live Foundry SDK Activation (Track B)

**Duration estimate:** 3–4 weeks  
**Dependency:** **Foundry credentials, schema manifest, ADR-007 acceptance**  
**Features:** P3-F01, P3-F02, P3-F03

| Deliverable | Detail |
|-------------|--------|
| ADR-007 accepted | Status change from Proposed |
| SDK in `pyproject.toml` | Pinned version |
| Live `sdk_client.py` | Read/write/batch paths |
| `validate_ontology_payload.py` | Schema manifest validation |
| Gated live test | `pytest -m live_foundry` |
| `source_system` | `ADSL_PHASE3` or retained `ADSL_PHASE2` per ADR decision |

**Success criteria (draft — align with v2.5):**
- [ ] Payload validation passes before any live write
- [ ] ≥ 1 successful end-to-end run with sync enabled and objects visible in Foundry
- [ ] Rollback verified (`ADSL_ONTOLOGY_SYNC_ENABLED=false`)
- [ ] Default CI remains offline; live test manual/gated only
- [ ] Engine still has zero direct SDK imports

**Note:** This increment should **preempt or run in parallel** with lower-priority Track A work when credentials arrive. PM must explicitly authorize Track B opening.

---

### Increment 4 — Analyst Workflows (Track A)

**Duration estimate:** 2–3 weeks  
**Dependency:** Stakeholder confirmation that export v1.0 is insufficient  
**Features:** P3-F07, P3-F08 (optional)

| Deliverable | Detail |
|-------------|--------|
| Multi-run comparison CLI or script | Compare seeds/scenarios; summary table |
| Batch export | Directory of ADR-009 bundles for workshop sets |
| Export schema v1.1 (if needed) | ADR-009 amendment |

**Success criteria (draft):**
- [ ] Compare ≥ 2 runs on same scenario with diff summary
- [ ] Batch export produces valid bundles per ADR-009 (or v1.1)
- [ ] Documentation for analyst consumption path

---

### Increment 5 — Demo Surface (Track A or B — conditional)

**Duration estimate:** 3–5 weeks  
**Dependency:** **Demo format stakeholder decision**  
**Features:** P3-F09 and/or P3-F10

| Option | Description |
|--------|-------------|
| A — Lightweight dashboard | Static or local web UI reading export bundles |
| B — Foundry Workshop app | Requires Track B complete |
| C — Export-only (no increment) | Continue CLI + ADR-009; defer UI |

**Success criteria:** Defined per chosen option at increment lock-in. Not scoping implementation detail here.

---

### Increment 6 — Advanced Mechanics (Track A — optional, PM-gated)

**Duration estimate:** 2–3 weeks  
**Dependency:** PM reprioritization; ADR amendment  
**Features:** P3-F12 (multi-level hardening), extended deconfliction rules

**Note:** Lower priority than P3-F04, P3-F05, Track B. Open only if workshop feedback identifies hardening ceiling as limiting.

---

## Risks and Considerations

### RL1/RL6 and substrate honesty

- ADSL Phase 3 implementation will remain **human-mediated PM directive execution** — not autonomous constitutional delegation.
- Live SDK activation does **not** resolve RL1/RL6 or native `spawn_subagent` gaps.
- Documentation must continue to distinguish: preparation vs activation, placeholder vs live sync, application delivery vs Foundation Chain governance.
- Phase 3 handover must include explicit limitations surface analogous to Phase 1/2 handover documents.

### Scope control

- **One scenario per increment** — no batch scenario delivery.
- **No parallel Track A + Track B** without PM authorization and separate module ownership.
- Red variety and hardening extensions require **ADR amendments** before code — not optional.
- Doctrine, theater-scale, and physics remain **out of scope** unless PM opens with stakeholder ADR.

### Live Palantir deferral carry-forward

- Phase 2 preparation (skeleton, ADR-007 Proposed) is **not** Phase 3 completion.
- Workshop demos remain **offline** (CLI + ADR-009 exports) until Increment 3 succeeds.
- Overclaiming integration during Phase 3 Track A work would violate v2.5 honesty boundaries.

### Integration with Foundation Chain

| Aspect | Consideration |
|--------|---------------|
| Governance rhythm | ADSL Phase 3 increments use PM directives and locked plans — analogous to Foundation Chain increment discipline but **separate codebase and ADRs** |
| Tooling bleed | Foundation Chain distillation helpers and Phase 5 scaffolding are **not** embedded in ADSL runtime |
| Expansion bar | ADSL Phase 2 success does **not** justify Foundation Chain tooling expansion |
| Routine cycles | Foundation Chain routine cycles may continue in parallel as lowest-risk self-governance activity |
| v2.5 framework | Data-gated principle applies to both tracks independently |

### Technical risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Foundry credentials further delayed | High | Proceed Track A; maintain offline demo path |
| Ontology schema mismatch at activation | Medium | P3-F02 validation before writes; early schema review |
| Red variety complexity creep | Medium | ADR lock scope; golden traces; no multi-hop pathfinding |
| UI increment without format decision | Medium | Increment 5 blocked until stakeholder choice |
| Test flakiness with live Foundry | Medium | Gated test only; CI offline |
| Parallel increment merge conflicts | Low | Module boundaries: `ontology/` vs `simulation/` vs `export/` |

---

## Approved Increment Ordering (PM Decision 2026-07-08)

**First increment:** **Increment 1 — Red Agent Variety + Playbook Validation (Track A)** — **COMPLETE**

| Decision | Resolution |
|----------|------------|
| Phase 3 scoping | **Approved** |
| First increment | **Inc 1 complete** (Red variety + playbook validation) |
| P3-F05 Red variety | **Delivered** via ADR-010 |
| P3-F07 multi-run | **Deferred** to Inc 4 |
| Playbook validation | Engineering proxy PASS; independent facilitator pending |
| Next increment | **Inc 2** (Additional Scenario) — PM authorization pending |
| Track B preempt | When credentials arrive, Inc 3 may preempt Inc 2/4 with PM authorization |

**Completed plan:** [`phase3-increment1-plan.md`](phase3-increment1-plan.md) · [`phase3-increment1-completion.md`](phase3-increment1-completion.md)

**Remaining increments** proceed in table order (2 → 3 when unblocked → 4 → 5 conditional → 6 optional) unless PM reprioritizes at stakeholder alignment.

---

## Open Questions (Stakeholder / PM Input Required)

### Foundry and platform

1. **When will `FOUNDRY_URL`, `FOUNDRY_TOKEN`, and `ONTOLOGY_RID` be delivered?** Is there a committed date or formal deferral?
2. **Who owns the Ontology schema manifest** and what is the delivery timeline for `docs/integration/ontology-schema-manifest.json`?
3. **Which Palantir Ontology SDK package and version** should ADSL pin for Python 3.11+?
4. **Is network egress to Foundry** confirmed from dev/CI environments?
5. **Are the v2.5 proposed live sync success metrics acceptable** or should they be amended before Increment 3 lock-in?

### Phase 3 prioritization

6. ~~**Confirm Phase 3 increment ordering**~~ — **Resolved:** Inc 1 complete; default next is Inc 2 (scenario) unless credentials preempt with Inc 3.
7. **Is doctrine modeling in or out of scope** for the next 6–9 months?
8. **Is theater-scale or physics simulation explicitly out of scope** for Phase 3?

### Demo and workshop

9. **What is the chosen demo format?** CLI + export only, Foundry Workshop app, lightweight dashboard, or hybrid?
10. **Will an independent facilitator validate the demo playbook?** Engineering proxy PASS (Inc 1); non-author facilitator assignment still open.
11. **Do stakeholders need multi-run comparison** (P3-F07) or is ADR-009 v1.0 export sufficient for analyst workflows?
12. **Is per-tick trace streaming to Foundry** a workshop requirement, or is batch-at-run-end acceptable indefinitely?

### Mechanics and agents

13. ~~**Should P2-F07 Red variety enter Phase 3**~~ — **Resolved and delivered:** Inc 1 complete via ADR-010 (cooldown, optional budget, target rotation).
14. **Is multi-level hardening (`harden_level > 1`)** a stakeholder priority, or is ADR-008 Inc 3 scope sufficient?
15. **Are there specific scenario concepts** (geography, chokepoint type, force mix) for a third synthetic dataset?

### Governance

16. ~~**PM approval process for Phase 3**~~ — **Resolved:** Per-increment approval (Phase 2 precedent); Inc 1 complete; **Inc 2+ requires separate PM directive**.
17. **Parallel Track A + Track B** — if credentials arrive mid-Phase 3, may Live SDK increment run parallel to Track A work?
18. **Foundation Chain routine cycles** — continue at current cadence while ADSL Phase 3 proceeds?

---

## Phase 3 Exit Criteria (Draft — for PM ratification)

Phase 3 is **complete** when agreed subsets are met per PM-signed increment plan (not all items mandatory unless PM specifies):

| Criterion | Measure |
|-----------|---------|
| Live sync (if Track B authorized) | ≥ 1 successful Foundry-visible run; validation script passes; rollback verified |
| Workshop readiness | Demo playbook independently validated; ≥ 2 scenarios demo-viable at 100 ticks |
| Agent depth (if Inc 1 delivered) | **Met** — Red variety documented and tested; golden traces updated |
| Auditability | 100% agent decisions produce `ADSL_AuditTrace`; no trace mutability |
| Modularity | Simulation engine has zero direct Palantir SDK imports |
| Tests | All tests pass; coverage ≥ Phase 2 baseline (92%) |
| Documentation | ADR(s) for new policies; `phase3-handover.md`; honesty limitations explicit |
| Honesty | No overclaim on live integration, RL1/RL6, or UI scope |

---

## Relationship to Prior Documents

| Document | Role |
|----------|------|
| [Foundation_Chain_Status_Update_v2.5.md](../Foundation_Chain_Status_Update_v2.5.md) | Strategic authority for Phase 3 priorities and honesty boundaries |
| [phase3-increment1-plan.md](phase3-increment1-plan.md) | Increment 1 locked plan (complete) |
| [phase3-increment1-completion.md](phase3-increment1-completion.md) | Increment 1 delivery outcomes |
| [phase3-increment1-playbook-validation.md](phase3-increment1-playbook-validation.md) | Playbook validation report |
| [current-state-summary.md](current-state-summary.md) | Stakeholder current-state briefing |
| [stakeholder-alignment-agenda.md](stakeholder-alignment-agenda.md) | Proposed alignment meeting agenda |
| [ADR-010](decisions/ADR-010-red-agent-variety.md) | Red variety policy (**Accepted**) |
| [phase2-handover.md](phase2-handover.md) | Baseline delivered vs remaining |
| [phase2-planning.md](phase2-planning.md) | Precedent for increment structure and gating |
| [demo-playbook.md](demo-playbook.md) | Inc 1 playbook validation subject |
| [decisions/README.md](decisions/README.md) | ADR index |
| [ADR-007](decisions/ADR-007-live-palantir-sdk-integration.md) | Track B architecture (not yet Accepted) |

---

## Increment 1 Outcomes — Scoping Adjustments

Based on Increment 1 delivery, the following scoping adjustments are recorded (no scope expansion):

| Area | Adjustment |
|------|------------|
| P3-F05 Red variety | **Closed** — delivered per ADR-010; no further Red pacing work unless PM opens Inc 6 |
| P3-F06 Playbook validation | **Partially closed** — engineering proxy sufficient for Inc 1; independent facilitator remains open question |
| Inc 2 recommendation | **Unchanged** — additional scenario remains recommended next Track A increment |
| Inc 3 (Track B) | **Unchanged** — still highest platform leverage; blocked on credentials; may preempt Inc 2 when unblocked with PM authorization |
| Inc 4 multi-run | **Unchanged** — deferred; stakeholder need confirmation still required |
| Inc 5 demo surface | **Unchanged** — blocked on demo format decision |
| Test baseline | **Updated** — Phase 3 baseline is now **58 tests**, **92% coverage** (was 46 tests at Inc 1 lock-in) |

---

## Next Step

**Increment 1 is complete.** Awaiting:

1. **Stakeholder alignment meeting** per [`stakeholder-alignment-agenda.md`](stakeholder-alignment-agenda.md) — Foundry timeline, priorities, demo format, live sync metrics.
2. **PM authorization** for Increment 2 (Additional Scenario) or explicit reprioritization (e.g., Track B preempt when credentials arrive).
3. **Independent facilitator assignment** for full playbook sign-off (organizational).
4. **Foundry credential delivery** — required before Increment 3 lock-in and ADR-007 acceptance.

Do **not** begin Increment 2 implementation, activate Track B, or expand Red variety scope without explicit PM directive.

---

*Phase 3 scoping approved. Increment 1 complete. Stakeholder alignment package issued.*