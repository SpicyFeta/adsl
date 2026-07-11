# ADSL Phase 1 — Architecture Overview

**Status:** MVP complete (pending stakeholder review)  
**Date:** 2026-07-08  
**Scenario:** Kessari Strait contested logistics stress test

---

## Purpose

ADSL Phase 1 demonstrates a lightweight multi-agent simulation where Red forces interdict a logistics network and Blue forces adapt under pressure. Every agent decision produces an immutable audit trace, and simulation outputs map to Palantir Ontology object types for external consumption.

---

## High-Level Architecture

```
data/synthetic/logistics_scenario_v1.json
            │
            ▼
    SimulationEngine (tick loop, max 100)
            │
    ┌───────┴───────┐
    ▼               ▼
 Red Agents     Blue Agents
 (interdiction) (adaptation)
    │               │
    └───────┬───────┘
            ▼
   AuditTrace + SimulationEvent
            │
            ▼
   Ontology Integration Layer
   (mappers + placeholder sync)
            │
            ▼
   Palantir Foundry Ontology (future SDK)
```

---

## Core Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| Data models | `src/adsl/models.py` | Pydantic v2 schemas for nodes, routes, agents, traces, runs |
| Agent base | `src/adsl/agents/base.py` | `perceive → decide → act` contract |
| Red agent | `src/adsl/agents/red_interdiction.py` | Target selection and attack actions (ADR-004) |
| Blue agent | `src/adsl/agents/blue_logistics.py` | Reroute, harden, reallocate, no-action (ADR-005) |
| Orchestration | `src/adsl/simulation/orchestration.py` | Red-before-Blue ordering, visibility rules |
| Simulation engine | `src/adsl/simulation/engine.py` | Tick loop, action application, event/trace recording |
| Audit trace | `src/adsl/explainability/trace.py` | Immutable reasoning artifact builder (ADR-003) |
| Ontology layer | `src/adsl/ontology/integration.py` | ADSL → Ontology mapping and sync placeholders (ADR-006) |
| CLI runner | `scripts/run_simulation.py` | Load dataset, run simulation, print summary |

---

## Simulation Flow (Per Tick)

1. **Tick start** — increment counter, emit structured log event.
2. **Red phase** — each Red force element perceives visible network state, decides an action, acts (attack node/route or no-action).
3. **Blue phase** — each Blue force element perceives post-Red state, decides adaptation (reroute, harden, reallocate, or no-action), acts.
4. **State update** — engine applies attacks and adaptations to node/route status.
5. **Recording** — audit traces and simulation events appended for every agent decision.
6. **Tick complete** — loop continues until `max_ticks` reached or termination condition met.

Default CLI run uses **50 ticks** with seed **42** against the Kessari Strait synthetic dataset (10 nodes, 18 routes, 4 Red / 7 Blue agents → 550 audit traces per run).

---

## Integration Points

### Palantir Ontology (ADR-006)

| ADSL model | Ontology object type | Sync timing |
|------------|---------------------|-------------|
| `ADSL_LogisticsNode` | `ADSL_LogisticsNode` | Bootstrap + run complete |
| `ADSL_LogisticsRoute` | `ADSL_LogisticsRoute` | Bootstrap + run complete |
| `ADSL_ForceElement` | `ADSL_ForceElement` | Bootstrap |
| `ADSL_AuditTrace` | `ADSL_AuditTrace` | Run complete (append-only) |
| `ADSL_SimulationRun` | `ADSL_SimulationRun` | Run complete |
| `SimulationEvent` | `ADSL_SimulationEvent` | Run complete (append-only) |

Live sync is gated by `ADSL_ONTOLOGY_SYNC_ENABLED`. Phase 1 uses placeholder read/write functions; the official Palantir Ontology SDK will replace placeholders when credentials are available.

### Structured Logging

`structlog` emits JSON events for simulation lifecycle, agent decisions, and audit trace recording. CLI summary output is human-readable; logs are machine-parseable.

### Synthetic Data

`data/synthetic/logistics_scenario_v1.json` is the canonical Phase 1 scenario. Simulations are self-contained from this file; Ontology read is not used in Phase 1.

---

## Key Design Decisions

| ADR | Decision |
|-----|----------|
| ADR-001 | Python 3.11+ |
| ADR-002 | Custom lightweight agent system (no LangChain/CrewAI) |
| ADR-003 | Immutable AuditTrace explainability contract |
| ADR-004 | Red-before-Blue tick orchestration |
| ADR-005 | Blue adaptation policy (P1–P6 priorities) |
| ADR-006 | Write-oriented Ontology integration with offline placeholders |

---

## Phase 1 Boundaries

**Included:** Synthetic scenario, Red/Blue agents, tick engine, audit traces, Ontology mapping, CLI runner, unit and end-to-end tests.

**Excluded:** Live Foundry SDK wiring, doctrine modeling, physics simulation, theater-scale scenarios, workshop UI, Ontology-driven scenario loading.

---

## References

- [ADR index](../decisions/)
- [ADR-006: Palantir Integration](../decisions/ADR-006-palantir-integration.md)
- [Palantir Ontology SDK overview](https://www.palantir.com/docs/foundry/ontology-sdk/overview/)