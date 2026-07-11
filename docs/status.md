# ADSL — Project Status

**Last updated:** 2026-07-08  
**Release posture:** Phase 3 complete through Increment 16 — workshop, analytics, collaboration, Foundry tooling, and engine performance optimizations delivered; live platform integration optional and gated

---

## At a Glance

| Metric | Value |
|--------|-------|
| Automated tests | **138 passing** |
| Code coverage | **~89%** |
| Scenarios | **5** in registry |
| ADRs | ADR-001–014 (ADR-007 HTTP path accepted; live activation gated) |
| Live Foundry sync | **Not active by default** — local mode |

---

## Delivery Status

| Phase / Increment | Status | Summary |
|-------------------|--------|---------|
| Phase 1 | ✅ Complete | MVP — simulation, agents, audit traces, Ontology mapping |
| Phase 2 | ✅ Complete | Multi-scenario, exports, hardening v2, deconfliction, SDK prep |
| Phase 3 Inc 1 | ✅ Complete | Red agent variety (ADR-010), playbook validation |
| Phase 3 Inc 2 | ✅ Complete | Third scenario (`alpine-valley-v3`) |
| Phase 3 Inc 4 | ✅ Complete | Multi-run comparison, batch export |
| Phase 3 Inc 6 | ✅ Complete | Optional visualization dashboard |
| Phase 3 Inc 7 | ✅ Complete | Documentation & positioning (initial) |
| Phase 3 Inc 9 | ✅ Complete | Analytics module, `analyze_run.py`, insights in exports |
| Phase 3 Inc 10 | ✅ Complete | Scale mode (500 ticks), parallel batch, benchmarks, mega-scale scenarios |
| Phase 3 Inc 11 | ✅ Complete | File-based collaboration (ADR-013), `collab_workshop.py` |
| Phase 3 Inc 12 | ✅ Complete | Foundry dataset import/export (ADR-011), local mode default |
| Phase 3 Inc 13 | ✅ Complete | Node risk, focus areas, `adsl-analyze` / `adsl-compare` CLI |
| Phase 3 Inc 14 | ✅ Complete | Dashboard risk overlay, run comparison API, presentation mode |
| Phase 3 Inc 15 | ✅ Complete | Documentation & positioning refresh |
| Phase 3 Inc 16 | ✅ Complete | Observation cache, engine benchmarks, ~2.8× mega-scale speedup |
| Phase 3 Inc 17 | ✅ Complete | Documentation & positioning overhaul |
| Track B — Live Foundry | ⏸ Optional | Credentials + env gate; local adapter is default |
| Foundry Workshop app | ⏸ Deferred | Stakeholder demo-format decision |

---

## Capability Status

| Capability | Status | Notes |
|------------|--------|-------|
| Tick simulation (≤100 default) | ✅ Production | Red-before-Blue orchestration |
| Scale mode (≤500 ticks) | ✅ Production | Opt-in via ADR-012 |
| Large-network performance | ✅ Production | Side observation cache (Inc 16) |
| Red / Blue agents | ✅ Production | Custom agents; ADR-004/005/010 |
| Audit traces (100%) | ✅ Production | ADR-003 immutable contract |
| Hardening v2 | ✅ Production | ADR-008 |
| Deconfliction | ✅ Production | `ACTION_SUPPRESSED` events |
| Workshop exports | ✅ Production | ADR-009 bundles + insights |
| Explainable analytics | ✅ Production | Risk, bottlenecks, focus areas (ADR-014) |
| Analyst workflows | ✅ Production | Compare, what-if, batch export |
| Visualization dashboard | ✅ Optional | Risk overlay, comparison, presentation mode |
| File-based collaboration | ✅ Optional | Sessions, annotations (ADR-013) |
| Foundry datasets | ✅ Optional | Local mode default (ADR-011) |
| Performance benchmarks | ✅ Production | `--engine-only`, `benchmark_compare.py` |
| Ontology payloads (offline) | ✅ Production | Six object types |
| Live Foundry HTTP | ⏸ Gated | Requires credentials and env configuration |
| Doctrine / physics / theater-scale | ❌ Out of scope | Unless PM opens via ADR |
| Per-tick Foundry streaming | ❌ Not planned | Batch-at-run-end today |
| Within-tick parallel agents | ❌ Not planned | Deconfliction constraint |

---

## Known Limitations (Current)

1. **Live Foundry not active by default** — local filesystem adapter; no objects written to live Ontology unless gated HTTP is enabled
2. **Synthetic scenarios only** — five bundled datasets; no live operational data ingestion
3. **Bounded mechanics** — single harden absorption layer; no multi-level doctrine modeling
4. **CLI-first workflow** — dashboard, analytics, and collaboration are optional layers
5. **File-based collaboration** — no real-time multi-user scenario editing
6. **Batch/offline focus** — not optimized for real-time streaming simulation
7. **Independent playbook sign-off** — engineering validation complete; non-author facilitator pending

---

## External Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| `FOUNDRY_URL`, `FOUNDRY_TOKEN`, `ONTOLOGY_RID` | IT / Platform | Not configured (local mode works without) |
| Ontology schema manifest | Platform team | Not delivered |
| Demo format decision | Stakeholders | Unresolved |

---

## Health Indicators

| Indicator | Assessment |
|-----------|------------|
| Test regression | ✅ Stable — 138 tests, golden traces |
| Coverage | ✅ ~89% maintained |
| Module boundaries | ✅ Engine has zero Palantir SDK imports |
| Documentation | ✅ README, what-is-adsl, capabilities, architecture, positioning (Inc 17) |
| Performance baselines | ✅ `baselines.json`, `before_after.json` committed |
| Honesty boundaries | ✅ No live integration claims in default docs |

---

## Related Documents

- [What is ADSL?](what-is-adsl.md)
- [Capabilities & limitations](capabilities-and-limitations.md)
- [Capabilities matrix](capabilities-matrix.md)
- [Architecture overview](architecture-overview.md)
- [Positioning](positioning.md)
- [Scale & performance](scale-performance.md)
- [Current state summary](current-state-summary.md)
- [Phase 3 scoping](phase3-scoping.md)