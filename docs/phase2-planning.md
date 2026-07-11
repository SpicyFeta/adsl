# ADSL Phase 2 — Planning Document

**Status:** Proposed — awaiting PM approval  
**Date:** 2026-07-08  
**Basis:** Phase 1 completion (`docs/phase1-handover.md`, `docs/phase1-completion.md`), ADR-001–006, Foundation Chain Status Update v2.4, PM Phase 2 goals directive

---

## Executive Summary

ADSL Phase 1 delivered a verified contested-logistics MVP: custom Red/Blue agents, tick-based simulation, immutable audit traces, Palantir Ontology mapping (placeholder sync), CLI runner, and 23 passing tests. Phase 2 extends that foundation toward **live platform integration**, **richer demonstration value**, and **more realistic simulation mechanics** — while preserving the non-negotiables from Phase 1: auditability, explainability, modularity, and ADR-governed design.

Phase 2 is organized into **four gated increments**. Increment 1 can begin immediately (no external credentials). Increment 2 (live Foundry SDK) is **blocked on stakeholder dependencies** and should not start until credentials and Ontology schema are confirmed. Simulation enhancements and workshop exports are sequenced to deliver demo value in parallel where dependencies allow.

**Recommendation for first approved increment:** **Increment 1 — Workshop exports + Scenario v2** (lowest risk, unblocks stakeholder demos while Foundry prerequisites are resolved).

---

## Phase 2 Goals (Aligned with PM Directive)

| Goal | Phase 2 intent |
|------|----------------|
| Live Palantir Ontology integration | Replace placeholder sync with official Ontology SDK; validate writes against live schema |
| Additional synthetic scenarios | Reduce demo saturation; support varied Red/Blue behavior over longer runs |
| Improved simulation features | Hardening that affects attack outcomes; basic action deconfliction; richer network dynamics |
| Workshop/demo readiness | Structured export formats, run bundles, executive summaries for non-CLI audiences |
| Maintain auditability & modularity | ADR-003 trace contract unchanged; engine remains Palantir-agnostic; custom agent framework retained |

---

## Proposed Scope

### In Scope (Phase 2)

| ID | Feature area | Description |
|----|--------------|-------------|
| P2-F01 | **Live Ontology SDK** | SDK client in `src/adsl/ontology/`; env-based auth; upsert/append per ADR-006 policy |
| P2-F02 | **Ontology schema validation** | Pre-flight payload check against stakeholder-provided schema or SDK type definitions |
| P2-F03 | **Scenario v2** | Second synthetic dataset (different topology/stress profile; e.g., island chokepoint or hub-spoke variant) |
| P2-F04 | **Scenario registry** | Loader discovers scenarios by manifest; CLI `--scenario` selector |
| P2-F05 | **Hardening mechanics v2** | Hardened routes resist degradation (e.g., first attack → remain CONTESTED; metadata tracks harden level) |
| P2-F06 | **Basic deconfliction** | Engine resolves conflicting actions same tick (priority rules; audit events for suppressed actions) |
| P2-F07 | **Red variety** | Cooldowns, target de-duplication, or role-based strike pacing to reduce repetitive 100-tick behavior |
| P2-F08 | **Run export bundle** | JSON/JSONL export: run summary, traces, events, final network state, Ontology payload snapshot |
| P2-F09 | **Executive summary generator** | Markdown/HTML one-pager from run artifacts for workshop handoff |
| P2-F10 | **Quiet/demo CLI mode** | `--quiet-logs` suppresses structlog JSON; preserves human summary |
| P2-F11 | **ADR-007+** | Phase 2 decisions documented before implementation (SDK wiring, hardening semantics, export contract) |
| P2-F12 | **Test expansion** | Integration tests with SDK mock/fixture; scenario v2 e2e; export schema validation tests |

### Out of Scope (Phase 2)

- Workshop UI / web dashboard (export files only; consume in Foundry or external tools)
- Theater-scale or physics-based simulation
- Doctrine modeling beyond extended hardening/deconfliction rules
- LangChain, CrewAI, AutoGen, or external agent frameworks
- Ontology **read** for scenario seeding (write-first; read deferred to Phase 3)
- Real-time trace streaming to Foundry during ticks (batch-at-run-end retained unless PM reprioritizes)
- Classified/air-gapped deployment hardening (operations concern; document assumptions only)
- Foundation Chain tooling changes (separate Aether track per v2.4)

---

## Prioritized Feature Backlog

### P0 — Must have (Phase 2 exit criteria)

1. **P2-F01 Live Ontology SDK** — real writes when `ADSL_ONTOLOGY_SYNC_ENABLED=true` and credentials present
2. **P2-F08 Run export bundle** — reproducible artifact for workshops
3. **P2-F03 Scenario v2** — at least one additional demo-viable scenario
4. **P2-F05 Hardening mechanics v2** — hardening materially affects attack outcomes (ADR-005 gap closed)
5. **P2-F11 ADRs** — ADR-007 (SDK integration), ADR-008 (hardening/deconfliction), ADR-009 (export contract)

### P1 — Should have

6. **P2-F06 Basic deconfliction** — same-tick conflict resolution with audit trail
7. **P2-F09 Executive summary generator** — workshop one-pager
8. **P2-F04 Scenario registry** — multi-scenario CLI without hardcoded paths
9. **P2-F02 Schema validation** — fail fast before live writes
10. **P2-F10 Quiet/demo CLI mode**

### P2 — Nice to have (if capacity permits)

11. **P2-F07 Red variety** — pacing/cooldowns for long runs
12. **P2-F12 Extended test matrix** — SDK contract tests, export golden files
13. **Optional per-tick trace sync** — only if workshop requires live Foundry feed

---

## Proposed Increments (Gated Delivery)

Phase 2 follows the data-gated principle from Foundation Chain Status Update v2.4: each increment has a locked plan, success criteria, and PM approval before implementation.

### Increment 1 — Demo Foundation (no Foundry dependency)

**Duration estimate:** 2–3 weeks  
**Features:** P2-F03, P2-F04, P2-F08, P2-F09, P2-F10, ADR-009 (export contract)

| Deliverable | Detail |
|-------------|--------|
| `logistics_scenario_v2.json` | New topology; designed for 50–100 tick demos without early network saturation |
| `scripts/export_run.py` | Export run bundle (JSON/JSONL + summary markdown) |
| CLI updates | `--scenario`, `--export-dir`, `--quiet-logs` |
| Tests | Scenario v2 load test; export schema test; e2e on v2 scenario |

**Success criteria:**
- [ ] Scenario v2 loads and runs 100 ticks with &lt; 50% node destruction (design target)
- [ ] Export bundle contains: run metadata, audit traces, events, network state, Ontology payload dict
- [ ] Executive summary markdown generated without manual editing
- [ ] All Phase 1 tests still pass; ≥ 3 new tests for export/scenario v2
- [ ] ADR-009 accepted

**Dependencies:** None external.

---

### Increment 2 — Live Palantir Ontology Integration

**Duration estimate:** 3–4 weeks (after dependencies satisfied)  
**Features:** P2-F01, P2-F02, ADR-007 (SDK integration)

| Deliverable | Detail |
|-------------|--------|
| SDK package in `pyproject.toml` | Official Palantir Ontology SDK (version TBD with stakeholders) |
| `src/adsl/ontology/sdk_client.py` | Connection, auth, write paths; swappable behind existing `integration.py` interface |
| Replace placeholders | `read_ontology_object` / `write_ontology_object` call SDK when enabled |
| `scripts/validate_ontology_payload.py` | Pre-flight validation against schema |
| `.env` contract | Documented `FOUNDRY_URL`, `FOUNDRY_TOKEN`, `ONTOLOGY_RID` |
| Tests | SDK mock layer for CI; optional live integration test (manual/gated) |

**Success criteria:**
- [ ] With valid credentials, 50-tick run syncs all six object types to Foundry without error
- [ ] Append-only traces/events verified (no update/delete of audit artifacts)
- [ ] Offline mode unchanged: sync disabled → zero network I/O, tests pass
- [ ] Mapper signatures unchanged (ADR-006 compliance)
- [ ] ADR-007 accepted
- [ ] Rollback documented: disable sync via env var

**Dependencies:** See Dependencies section — **hard gate**.

---

### Increment 3 — Simulation Mechanics v2

**Duration estimate:** 2–3 weeks  
**Features:** P2-F05, P2-F06, P2-F07 (P2 if time), ADR-008

| Deliverable | Detail |
|-------------|--------|
| Hardening v2 | Hardened routes: first `ATTACK_ROUTE` → no status change (or CONTESTED only); second attack applies normal degradation; `metadata.harden_level` |
| Deconfliction | Engine tick queue: duplicate targets same tick → priority order (Red before Blue; lexicographic tie-break); `SimulationEvent` type `ACTION_SUPPRESSED` |
| Red variety (P2) | Per-agent target cooldown or strike budget metadata |
| Blue/Red agent updates | Audit traces cite new rules (P7+ if needed) |
| Tests | Golden traces for hardening/deconfliction; regression on Phase 1 scenarios |

**Success criteria:**
- [ ] Hardened route survives first attack in same run; second attack degrades per rules
- [ ] Deconfliction produces auditable suppressed-action events
- [ ] Kessari v1 and scenario v2 both pass e2e with new mechanics
- [ ] No LangChain/external frameworks introduced
- [ ] ADR-008 accepted

**Dependencies:** Increment 1 scenario v2 recommended for demo validation; not blocking.

---

### Increment 4 — Phase 2 Closure & Workshop Readiness

**Duration estimate:** 1–2 weeks  
**Features:** Integration hardening, documentation, Phase 2 handover

| Deliverable | Detail |
|-------------|--------|
| `docs/phase2-handover.md` | Delivery summary, limitations, Phase 3 candidates |
| README Phase 2 section | Quick start with export + live sync |
| Demo playbook | Step-by-step workshop script (CLI → export → Foundry) |
| Full regression | 100-tick runs on v1 + v2 scenarios; live sync smoke test |
| ADR index update | ADR-007–009 recorded |

**Success criteria:**
- [ ] Demo playbook executable by non-author in &lt; 30 minutes
- [ ] All tests pass; coverage ≥ Phase 1 baseline (~91%)
- [ ] Phase 2 handover approved by PM
- [ ] v2.5 strategic review inputs prepared

**Dependencies:** Increments 1–3 complete (or Inc 2 waived if Foundry blocked, with explicit documented deferral).

---

## High-Level Timeline

| Increment | Est. duration | Earliest start | Blocker |
|-----------|---------------|----------------|---------|
| Inc 1 — Demo Foundation | 2–3 weeks | Immediately | PM approval of this plan |
| Inc 2 — Live Foundry SDK | 3–4 weeks | After Inc 1 + dependencies | Credentials + schema |
| Inc 3 — Simulation Mechanics | 2–3 weeks | After Inc 1 (parallel with Inc 2 if staffed) | None |
| Inc 4 — Closure | 1–2 weeks | After Inc 1–3 | — |

**Total Phase 2 estimate:** 8–12 weeks (sequential); 6–9 weeks with Inc 2 and Inc 3 parallelized.

```
Week 1–3:   [ Inc 1: Scenario v2 + Exports ]
Week 2–5:   [ Inc 3: Hardening + Deconfliction ]  (parallel track)
Week 3–7:   [ Inc 2: Foundry SDK ]                (starts when credentials arrive)
Week 8–9:   [ Inc 4: Closure + Demo playbook ]
```

---

## Dependencies

### External (Stakeholder-provided)

| Dependency | Owner | Required for | Status |
|------------|-------|--------------|--------|
| Foundry instance URL | Stakeholders / IT | Inc 2 | **Not configured** |
| API token / service account | Stakeholders / IT | Inc 2 | **Not configured** |
| Ontology RID | Platform team | Inc 2 | **Not configured** |
| Ontology object type definitions | Platform team | Inc 2 schema validation | **Assumed match ADR-006 names** — must confirm |
| Property schema per object type | Platform team | Inc 2 | **Not validated** |
| SDK package name + version | Engineering + Platform | Inc 2 | **TBD** (Python Ontology SDK) |
| Network access to Foundry | Operations | Inc 2 live tests | **Unknown** |

### Internal (Engineering)

| Dependency | Required for |
|------------|--------------|
| Phase 1 codebase stable (tagged release) | All increments |
| ADR-007 drafted before Inc 2 code | Inc 2 |
| ADR-008 drafted before Inc 3 code | Inc 3 |
| Export directory contract (ADR-009) | Inc 1 |
| CI continues offline (no live Foundry in default pytest) | All increments |

### Assumptions

- Phase 1 ADR-006 object type names and primary keys remain valid in stakeholder Ontology.
- `source_system` may upgrade from `ADSL_PHASE1` to `ADSL_PHASE2` with backward-compatible mapping (ADR-007 decision).
- Workshop consumers can ingest JSON/JSONL exports without a custom ADSL UI.

---

## Success Criteria (Phase 2 Exit)

Phase 2 is **complete** when all of the following are met (or explicitly deferred with PM sign-off):

| Criterion | Measure |
|-----------|---------|
| Live sync | ≥ 1 successful end-to-end run with Ontology sync enabled and objects visible in Foundry |
| Multi-scenario | ≥ 2 synthetic scenarios runnable via CLI |
| Hardening | Documented rules where hardening affects attack outcomes; tested |
| Deconfliction | Conflicting same-tick actions resolved with audit events |
| Workshop export | Export bundle + executive summary producible in one command |
| Auditability | 100% agent decisions still produce `ADSL_AuditTrace`; no trace mutability |
| Modularity | Simulation engine has zero direct Palantir SDK imports |
| Tests | All tests pass; no regression vs Phase 1 exit (23 tests minimum; target ≥ 30) |
| Documentation | ADR-007–009 accepted; phase2-handover.md complete |
| Honesty | Limitations documented (no overclaim on RL1/RL6, live sync scope, or UI) |

---

## Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Foundry credentials delayed | High | Blocks Inc 2 | Proceed Inc 1 + Inc 3 first; export bundles enable offline workshop demos |
| Ontology schema mismatch | Medium | High | Pre-flight validation script; early schema review workshop with platform team |
| SDK API breaking changes | Medium | Medium | Pin SDK version; adapter layer in `sdk_client.py`; mapper signatures frozen |
| Hardening/deconfliction complexity creep | Medium | Medium | ADR-008 locked scope; golden trace tests; no multi-hop pathfinding |
| Demo saturation on v1 scenario | High (known) | Low | Scenario v2 designed with slower degradation curve |
| Secret leakage in repo | Low | Critical | `.env` gitignored; CI uses mocks only; document token rotation |
| Test flakiness with live Foundry | Medium | Low | Live sync test manual/gated; CI stays offline |
| Parallel Inc 2/Inc 3 merge conflicts | Medium | Low | Module boundaries: `ontology/` vs `simulation/`; separate PRs |
| Overclaiming Palantir integration | Medium | High | Maintain placeholder path; ADR-007 explicit about read/sync limits |
| Foundation Chain / ADSL scope bleed | Low | Medium | Separate increments, ADRs, and handover docs per v2.4 guidance |

---

## Integration with the Broader Aether Ecosystem

ADSL sits as the **application-layer contested-logistics simulation** within the broader Aether program. Phase 2 integration points:

### Relationship to Foundation Chain

| Aspect | Integration |
|--------|-------------|
| Governance | Phase 2 increments use locked plans and PM directives analogous to Foundation Chain increment discipline |
| Data-gated expansion | v2.4 framework applies: no Inc 2 without credentials evidence; no scope creep without ADR |
| RL1/RL6 honesty | ADSL remains human-mediated PM-directed implementation; no claim of autonomous constitutional gates |
| Documentation rhythm | Phase 2 handover mirrors `phase1-handover.md`; optional Summary of Operational Learnings per increment |
| Tooling | Foundation Chain distillation helpers and Phase 5 scaffolding are **not** embedded in ADSL runtime; separate concern |

### Relationship to Palantir / Foundry

| Aspect | Integration |
|--------|-------------|
| Ontology object types | Six ADSL types (ADR-006) consumed by workshop pipelines |
| Export → Foundry | Phase 2 export bundle is ingestible if SDK sync unavailable |
| Audit traces | Align with defense explainability requirements; append-only sync policy preserved |
| `source_system` | Identifies ADSL provenance for Ontology lineage |

### Relationship to Future Aether Capabilities

| Future capability | Phase 2 positioning |
|-------------------|---------------------|
| Native subagent spawning (RL1/RL6) | Not in scope; ADSL agents remain custom Python classes |
| Multi-run aggregation | Export format designed for downstream aggregation (run_id keyed) |
| Workshop UI | Phase 2 exports feed external UI; no embedded dashboard |
| Doctrine modeling | Phase 3+; Phase 2 hardening/deconfliction are stepping stones only |

### Recommended Aether Coordination

1. **v2.5 strategic review** — present Phase 2 plan approval and Inc 1 results.
2. **Platform team sync** — schedule Ontology schema review before Inc 2 kickoff.
3. **Parallel tracks** — Foundation Chain routine cycles continue independently per v2.4.
4. **Version tagging** — tag `adsl-phase1-complete` before Phase 2 Inc 1 merge.

---

## Architecture Principles (Carried Forward)

1. **Engine is Palantir-agnostic** — SDK only in `src/adsl/ontology/`.
2. **Mappers are pure** — no side effects; unit-testable without Foundry.
3. **Audit traces are immutable** — append-only Ontology sync for traces/events.
4. **Custom agents only** — perceive → decide → act; no external agent frameworks.
5. **ADR before code** — each increment opens with ADR proposal; implementation after acceptance.
6. **Offline-first CI** — default test suite runs without network or credentials.

---

## Open Questions for PM (Pre-Approval)

1. **Increment order:** Approve Inc 1 (exports + scenario v2) first while Foundry dependencies are resolved, or wait for credentials and lead with Inc 2?
2. **Scenario v2 theme:** Island chokepoint, hub-spoke resupply, or PM-specified geography?
3. **Foundry access timeline:** When will `FOUNDRY_URL`, token, and `ONTOLOGY_RID` be available?
4. **Schema confirmation:** Do the six ADR-006 object type names exist in the target Ontology, or require renaming?
5. **Export format priority:** JSON bundle only, or also JSONL, CSV, or GeoJSON for map overlays?
6. **Hardening semantics:** Should hardened routes block one attack, require repeated harden, or decay over ticks?
7. **Live sync in CI:** Permitted gated integration test, or manual smoke test only?
8. **Phase 2 naming:** Retain `adsl-phase1` repo name or rename to `adsl` for Phase 2?

---

## Approval Checklist

- [ ] PM approves proposed scope (in/out)
- [ ] PM approves increment sequencing
- [ ] PM confirms first increment to implement
- [ ] Stakeholders acknowledge Foundry dependency timeline
- [ ] Engineering acknowledges no implementation until plan approved

---

## References

- [Phase 1 handover](phase1-handover.md)
- [Phase 1 completion](phase1-completion.md)
- [Phase 1 architecture](architecture/phase1-overview.md)
- [ADR-006: Palantir Integration](decisions/ADR-006-palantir-integration.md)
- [ADR-005: Blue Adaptation Policy](decisions/ADR-005-blue-adaptation-policy.md)
- [Foundation Chain Status Update v2.4](../Foundation_Chain_Status_Update_v2.4.md)
- [Palantir Ontology SDK overview](https://www.palantir.com/docs/foundry/ontology-sdk/overview/)