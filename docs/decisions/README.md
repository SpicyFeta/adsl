# Architecture Decision Records (ADR Index)

ADSL uses Architecture Decision Records to document significant technical and policy choices. All ADRs live in this directory.

**Last updated:** 2026-07-08 (Phase 3 Increment 15)

---

## Index

| ADR | Title | Status | Phase | File |
|-----|-------|--------|-------|------|
| ADR-001 | Python Language Selection | Accepted | 1 | [ADR-001-python-language.md](ADR-001-python-language.md) |
| ADR-002 | Custom Agent System | Accepted | 1 | [ADR-002-custom-agent-system.md](ADR-002-custom-agent-system.md) |
| ADR-003 | AuditTrace System | Accepted | 1 | [ADR-003-audittrace-system.md](ADR-003-audittrace-system.md) |
| ADR-004 | Simulation Orchestration Policy | Accepted | 1 | [ADR-004-simulation-orchestration-policy.md](ADR-004-simulation-orchestration-policy.md) |
| ADR-005 | Blue Adaptation Policy | Accepted | 1 | [ADR-005-blue-adaptation-policy.md](ADR-005-blue-adaptation-policy.md) |
| ADR-006 | Palantir Integration Architecture and Sync Policy | Accepted | 1 | [ADR-006-palantir-integration.md](ADR-006-palantir-integration.md) |
| ADR-007 | Live Palantir Ontology SDK Integration | **Accepted** (HTTP path) | 2/3 | [ADR-007-live-palantir-sdk-integration.md](ADR-007-live-palantir-sdk-integration.md) |
| ADR-008 | Hardening v2 and Action Deconfliction Policy | Accepted | 2 | [ADR-008-hardening-deconfliction.md](ADR-008-hardening-deconfliction.md) |
| ADR-009 | Run Export Bundle and Executive Summary Contract | Accepted | 2 | [ADR-009-export-contract.md](ADR-009-export-contract.md) |
| ADR-010 | Red Agent Variety Mechanics | Accepted | 3 (Inc 1) | [ADR-010-red-agent-variety.md](ADR-010-red-agent-variety.md) |
| ADR-011 | Foundry Dataset Integration | Accepted | 3 (Inc 12) | [ADR-011-foundry-dataset-integration.md](ADR-011-foundry-dataset-integration.md) |
| ADR-012 | Scale & Performance Optimizations | Accepted | 3 (Inc 10) | [ADR-012-scale-performance.md](ADR-012-scale-performance.md) |
| ADR-013 | File-Based Collaboration for Workshops | Accepted | 3 (Inc 11) | [ADR-013-collaboration.md](ADR-013-collaboration.md) |
| ADR-014 | Explainable Analytics & Insights | Accepted | 3 (Inc 13) | [ADR-014-analytics-insights.md](ADR-014-analytics-insights.md) |

---

## Phase Summary

### Phase 1 (ADR-001–006)

Foundation: Python stack, custom agents, audit traces, simulation orchestration, Blue adaptation policy, Palantir Ontology mapping with placeholder sync.

### Phase 2 (ADR-007–009)

- **ADR-007** — Ontology client architecture; live HTTP path via ADR-011 (no official SDK package)
- **ADR-008** — Hardening v2 (`harden_level` absorption) and same-tick deconfliction (`ACTION_SUPPRESSED`)
- **ADR-009** — Workshop export bundle schema, file layout, executive summary contract

### Phase 3 (ADR-010+)

- **ADR-010** — Red agent strike cooldown, optional budget, target rotation (Accepted; Inc 1 delivered)
- **ADR-012** — Network index, scale mode (500 ticks), parallel batch, benchmarks (Accepted; Inc 10 delivered)
- **ADR-011** — Foundry dataset import/export, lineage, local + HTTP adapters (Accepted; Inc 12 delivered)
- **ADR-013** — File-based workshop sessions, scenario sharing, annotations, version history (Accepted; Inc 11 delivered)
- **ADR-014** — Explainable analytics, risk scoring, what-if comparison, focus areas (Accepted; Inc 13 delivered)

---

## Status Definitions

| Status | Meaning |
|--------|---------|
| Accepted | Decision is active and implemented |
| Proposed | Draft decision; not yet activated (ADR-007 awaits credentials and PM approval) |
| Superseded | Replaced by a later ADR (none currently) |
| Deprecated | No longer recommended (none currently) |

---

## Compliance Rules (Cross-ADR)

1. Simulation engine must not import Palantir SDK directly (ADR-006, ADR-007).
2. Every agent decision must produce an immutable `ADSL_AuditTrace` (ADR-003).
3. Red executes before Blue within each tick (ADR-004).
4. Hardening logic lives in `simulation/hardening.py`; deconfliction in `simulation/deconfliction.py` (ADR-008).
5. Live Ontology sync gated by `ADSL_ONTOLOGY_SYNC_ENABLED` plus credentials (ADR-006, ADR-007).
6. Export bundles use `EXPORT_SCHEMA_VERSION = "1.0"` and `source_system: "ADSL_PHASE2"` (ADR-009).

---

## Related Documentation

- [Phase 1 handover](../phase1-handover.md)
- [Phase 2 handover](../phase2-handover.md)
- [Phase 2 planning](../phase2-planning.md)
- [Architecture overview](../architecture/phase1-overview.md)
- [Demo playbook](../demo-playbook.md)
- [Phase 3 scoping](../phase3-scoping.md)
- [Phase 3 Increment 1 plan](../phase3-increment1-plan.md)