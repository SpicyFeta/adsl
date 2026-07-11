# ADSL Current State Summary

**Date:** 2026-07-08  
**Audience:** Stakeholders, program management, platform partners  
**Status:** Phase 1–2 complete · Phase 3 Increments 1–17 complete

---

## What ADSL Is

ADSL (Aether Defense Simulation Layer) is an audit-first contested-logistics simulation system. Red and Blue agents make decisions over a supply network; **every decision produces an immutable audit trace** suitable for defense review, workshops, analytics, and optional Palantir Foundry dataset integration.

ADSL complements enterprise platforms — it generates structured adversarial simulation outputs with full explainability and honest offline-first delivery today.

---

## Delivery Timeline

| Phase / Increment | Status | Headline outcome |
|-------------------|--------|------------------|
| **Phase 1** | Complete | MVP — agents, traces, Ontology mapping |
| **Phase 2** | Complete | Workshop platform — exports, hardening, deconfliction |
| **Phase 3 Inc 1** | Complete | Red pacing (ADR-010) + playbook validation |
| **Phase 3 Inc 2** | Complete | Third scenario (`alpine-valley-v3`) |
| **Phase 3 Inc 4** | Complete | Multi-run comparison + batch export |
| **Phase 3 Inc 6** | Complete | Visualization dashboard |
| **Phase 3 Inc 9** | Complete | Analytics module + insights in exports |
| **Phase 3 Inc 10** | Complete | Scale mode, parallel batch, mega-scale scenarios |
| **Phase 3 Inc 11** | Complete | File-based collaboration (ADR-013) |
| **Phase 3 Inc 12** | Complete | Foundry dataset import/export (ADR-011) |
| **Phase 3 Inc 13** | Complete | Risk scoring, focus areas, CLI aliases |
| **Phase 3 Inc 14** | Complete | Dashboard viz improvements |
| **Phase 3 Inc 15–17** | Complete | Documentation & positioning (current) |
| **Phase 3 Inc 16** | Complete | Engine performance — ~2.8× mega-scale speedup |
| **Live Palantir** | **Optional / gated** | Local mode default; HTTP when credentials configured |

---

## Key Capabilities Today

- **5 scenarios** — stress, workshop, dual-corridor, and two scale fixtures
- **Full auditability** — 100% agent decisions traced; deconfliction suppressions auditable
- **Workshop exports** — ADR-009 bundles + executive summary + insights
- **Explainable analytics** — risk scores, bottlenecks, Red patterns, what-if comparison
- **Visualization** — dashboard with risk overlay, comparison API, presentation mode
- **Collaboration** — file-based sessions, scenario sharing, annotations
- **Foundry path** — optional dataset import/export with lineage (local mode default)
- **Performance** — observation cache (Inc 16), scale mode (500 ticks), parallel batch, benchmarks
- **Quality** — 138 tests, ~89% coverage

---

## What Is Still Pending

- **Live Foundry credentials** and schema manifest for production HTTP sync (Track B)
- **Foundry Workshop app** — stakeholder demo-format decision
- **Independent facilitator** sign-off for demo playbook
- **Doctrine / theater-scale / physics** — out of scope unless explicitly opened

---

## Documentation (Increment 17)

| Document | Purpose |
|----------|---------|
| [README.md](../README.md) | Project entry point |
| [what-is-adsl.md](what-is-adsl.md) | Core value and overview |
| [getting-started.md](getting-started.md) | 5-minute setup with examples |
| [capabilities-and-limitations.md](capabilities-and-limitations.md) | Honest current state |
| [positioning.md](positioning.md) | Competitive differentiation |
| [capabilities-matrix.md](capabilities-matrix.md) | Feature matrix |
| [architecture-overview.md](architecture-overview.md) | Architecture + diagrams |
| [scale-performance.md](scale-performance.md) | Benchmarks and scaling |
| [status.md](status.md) | Project status |

**Recommended reading path (~7 min):** what-is-adsl → getting-started → capabilities-and-limitations or positioning

---

## Metrics at a Glance

| Metric | Value |
|--------|-------|
| Automated tests | 138 passing |
| Code coverage | ~89% |
| Scenarios | 5 |
| ADRs | ADR-001–014 |
| Live Foundry sync | **Not active by default** |
| Mega-scale benchmark (200 ticks, engine) | ~358 ticks/s (seed 42, reference host) |