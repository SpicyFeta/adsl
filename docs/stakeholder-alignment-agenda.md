# ADSL Stakeholder Alignment Meeting — Proposed Agenda

**Date proposed:** 2026-07-08  
**Duration:** 60 minutes  
**Purpose:** Align stakeholders on ADSL delivery status, Foundry integration timeline, and Phase 3 priorities after Increment 1 completion.

---

## Suggested Attendees

| Role | Representative | Why needed |
|------|----------------|------------|
| Program Manager | ADSL PM | Decision authority on increment ordering and scope |
| Engineering lead | ADSL engineering | Delivery status, technical constraints, demo |
| Platform / Palantir partner | Foundry / Ontology owner | Credentials, schema manifest, SDK guidance |
| IT / Operations | Credential and network owner | `FOUNDRY_URL`, token provisioning, egress |
| Workshop / analyst stakeholder | End-user representative | Demo format, export sufficiency, analyst workflows |
| Optional: Foundation Chain liaison | Governance alignment | Separate track; no ADSL scope bleed |

---

## Desired Outcomes

By end of meeting, stakeholders should have:

1. **A committed or formally deferred timeline** for Foundry credentials and schema manifest delivery
2. **Confirmed Phase 3 increment priority** for the next 1–2 quarters (Track A vs. Track B)
3. **A chosen demo format** for external audiences (or a decision deadline)
4. **Ratified success metrics** for the first live Ontology sync run
5. **Assignment** of an independent demo playbook facilitator (or acceptance of engineering proxy with follow-up date)

---

## Agenda

| Time | Topic | Lead | Notes |
|------|-------|------|-------|
| 0:00–0:05 | **Welcome and objectives** | PM | Confirm desired outcomes above |
| 0:05–0:15 | **Current state briefing** | Engineering | Walk through `current-state-summary.md`: Phases 1–2 + Inc 1 delivered; live Foundry **not active** |
| 0:15–0:25 | **Live demo (offline)** | Engineering | 10-min CLI + export bundle walkthrough using `island-chokepoint-v2`; optional Red pacing trace highlight (ADR-010) |
| 0:25–0:35 | **Foundry credentials timeline** | Platform + IT | `FOUNDRY_URL`, `FOUNDRY_TOKEN`, `ONTOLOGY_RID`, schema manifest, network egress |
| 0:35–0:45 | **Phase 3 priorities** | PM + stakeholders | Inc 2 (scenario) vs. Inc 3 (live SDK when unblocked) vs. Inc 4 (analyst tools) vs. Inc 5 (UI) |
| 0:45–0:52 | **Demo validation status** | PM | Engineering proxy PASS; independent facilitator assignment |
| 0:52–0:58 | **Live sync success metrics** | Platform + Engineering | Ratify or amend v2.5 proposed metrics (see below) |
| 0:58–1:00 | **Actions and next meeting** | PM | Named owners and dates for open decisions |

---

## Discussion Topics (Detail)

### 1. Foundry credentials timeline

**Current status:** Not configured. ADR-007 architecture is drafted (Proposed); SDK skeleton exists; no live writes have occurred.

**Questions for stakeholders:**

- When will `FOUNDRY_URL`, `FOUNDRY_TOKEN`, and `ONTOLOGY_RID` be available?
- Who owns delivery of the Ontology schema manifest (`docs/integration/ontology-schema-manifest.json`)?
- Which Palantir Python SDK package and version should ADSL pin?
- Is network egress to Foundry confirmed from development environments?

**Decision needed:** Committed delivery date, named owner, or formal deferral to a specific quarter/increment.

---

### 2. Phase 3 priorities

**Increment 1 (complete):** Red agent variety + playbook validation — delivered without Foundry dependency.

**Recommended default ordering (engineering view):**

| Priority | Increment | Rationale |
|----------|-----------|-----------|
| Next (Track A) | Inc 2 — Additional scenario | Credential-independent; extends workshop library |
| When unblocked | Inc 3 — Live SDK activation | Highest platform leverage; blocked on credentials |
| After need confirmed | Inc 4 — Analyst workflows | Multi-run comparison, batch export |
| After format decision | Inc 5 — Demo surface | UI or Foundry Workshop app |
| Optional | Inc 6 — Advanced mechanics | Only if workshop feedback demands it |

**Questions for stakeholders:**

- Should Track B (live SDK) preempt Inc 2 when credentials arrive?
- Is doctrine modeling, theater-scale, or physics simulation in scope for the next 6–9 months? (Currently out of scope.)
- Is multi-run comparison needed, or are current export bundles sufficient?

**Decision needed:** Confirmed increment order and any reprioritization.

---

### 3. Demo validation

**Current status:**

- Demo playbook Parts 1–4 validated in ~5 minutes (engineering proxy run) — **PASS**
- 58 automated tests passing; both scenarios complete at 100 ticks
- Independent non-author facilitator run **not yet completed**

**Questions for stakeholders:**

- Who will serve as independent facilitator for full playbook sign-off?
- Is CLI + export bundle acceptable for external workshops, or is a UI/Foundry-native surface required?

**Decision needed:** Facilitator assignment and demo format direction.

---

### 4. Success metrics for first live sync

**Proposed metrics (v2.5 — ratification pending):**

1. `validate_ontology_payload.py` passes against the delivered schema manifest
2. Gated `pytest -m live_foundry` passes in a Foundry-connected environment
3. ≥ 1 `ADSL_AuditTrace` and ≥ 1 `ADSL_SimulationRun` visible in Foundry Ontology after a completed run
4. Rollback verified: simulation runs successfully with `ADSL_ONTOLOGY_SYNC_ENABLED=false`

**Questions for stakeholders:**

- Are these four criteria sufficient for declaring "live integration complete"?
- Should `source_system` remain `ADSL_PHASE2` or change to `ADSL_PHASE3`?
- Is batch-at-run-end sync acceptable, or is per-tick streaming required?

**Decision needed:** Ratify, amend, or replace success metrics before Increment 3 lock-in.

---

## Pre-Read Materials

| Document | Audience note |
|----------|---------------|
| [current-state-summary.md](current-state-summary.md) | Primary briefing — non-technical where possible |
| [phase3-scoping.md](phase3-scoping.md) | Roadmap and increment status |
| [phase3-increment1-completion.md](phase3-increment1-completion.md) | Inc 1 outcomes |
| [demo-playbook.md](demo-playbook.md) | Workshop execution guide |
| [Foundation_Chain_Status_Update_v2.5.md](../Foundation_Chain_Status_Update_v2.5.md) | Strategic context |

---

## Action Item Template

| # | Action | Owner | Due date |
|---|--------|-------|----------|
| A1 | Deliver Foundry credentials (`FOUNDRY_URL`, `FOUNDRY_TOKEN`, `ONTOLOGY_RID`) | Platform / IT | TBD |
| A2 | Deliver Ontology schema manifest | Platform team | TBD |
| A3 | Confirm Phase 3 increment priority order | PM + stakeholders | This meeting |
| A4 | Choose demo format (CLI/export vs. UI vs. Foundry Workshop) | Stakeholders | TBD |
| A5 | Ratify live sync success metrics | PM + Platform | This meeting |
| A6 | Assign independent playbook facilitator | PM | TBD |
| A7 | Authorize Increment 2 (additional scenario) or reprioritize | PM | After alignment |

---

*Proposed agenda for stakeholder alignment. No implementation authorized by this document.*