# What Is ADSL?

**Aether Defense Simulation Layer (ADSL)** is an audit-first simulation system for contested logistics. It models how adversary (Red) and defender (Blue) agents make decisions over a supply network — and records **every decision** as an immutable audit trace with reasoning steps.

ADSL is built for defense analysts, workshop facilitators, and platform integrators who need **defensible, reproducible simulation outputs** — not a general-purpose wargame or agent framework.

---

## The Problem ADSL Solves

Contested logistics analysis often lacks:

- **Traceable decisions** — hard to explain why an agent chose a particular action
- **Reproducible runs** — results vary without seeded, deterministic mechanics
- **Workshop-ready artifacts** — stakeholders need exportable bundles, not terminal-only output
- **Platform-ready structure** — enterprise systems need mapped objects, not ad-hoc spreadsheets
- **Scalable offline analysis** — larger networks and longer runs must remain practical

ADSL addresses these by making audit traces first-class, keeping simulation bounded and testable, producing ADR-009 export bundles, and optimizing the engine for multi-agent scale (Phase 3 Increments 10 and 16).

---

## Core Value

| Value | What you get |
|-------|--------------|
| **Auditability** | 100% of agent decisions produce `ADSL_AuditTrace` with reasoning steps (ADR-003) |
| **Determinism** | Seeded runs, golden trace regression, auditable deconfliction (ADR-008) |
| **Workshop usability** | Export bundles, demo playbook, dashboard, file-based collaboration |
| **Analyst depth** | Automated risk scoring, bottlenecks, Red patterns, what-if comparison (ADR-014) |
| **Scale & performance** | Mega-scale scenarios (37 nodes, 36 agents); observation cache with dirty invalidation (Inc 16) |
| **Platform path** | Six Ontology object types; optional Foundry dataset import/export (ADR-011) |
| **Honest scope** | Clear boundaries — no overclaiming live integration or theater-scale modeling |

---

## What ADSL Is Not

- A general-purpose AI agent framework (no LangChain/CrewAI/AutoGen — ADR-002)
- A physics or kinetic simulation engine
- A theater-scale force-on-force wargame
- A live Palantir Foundry replacement (integration is optional and gated)
- A real-time collaborative scenario editor
- A distributed or GPU-accelerated simulation cluster

---

## Typical Workflow

```
Scenario → Simulation → Audit Traces → Export Bundle → Analytics / Dashboard / Workshop
```

1. **Run** a scenario (`run_simulation.py` or `export_run.py`)
2. **Export** an ADR-009 bundle (JSON, traces, executive summary, insights)
3. **Analyze** with automated insights (`analyze_run.py`) or compare runs (`compare_runs.py --what-if`)
4. **Present** via dashboard (`launch_dashboard.py`) or workshop collaboration (`collab_workshop.py`)
5. **Integrate** optionally with Foundry datasets when credentials are configured
6. **Benchmark** large scenarios with `benchmark_runs.py --engine-only` when tuning performance

---

## Who ADSL Is For

| Audience | Primary use |
|----------|-------------|
| **Analysts** | Risk assessment, corridor comparison, what-if pacing studies |
| **Workshop facilitators** | 30-minute demos with exportable artifacts and visual dashboard |
| **Engineers / integrators** | Ontology payloads, Foundry dataset paths, testable mechanics |
| **Decision-makers** | Honest capability assessment via status and limitations docs |

---

## Read Next (~7 minutes)

| Document | Time | Purpose |
|----------|------|---------|
| [getting-started.md](getting-started.md) | 5 min | Install and first run |
| [positioning.md](positioning.md) | 3 min | How ADSL compares to alternatives |
| [capabilities-and-limitations.md](capabilities-and-limitations.md) | 3 min | What works and what does not |