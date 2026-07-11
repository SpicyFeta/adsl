# Capabilities & Limitations

**Last updated:** 2026-07-08 (after Phase 3 Increments 6–16)

An honest summary of what ADSL delivers today and what remains out of scope or in development.

**Reading time:** ~4 minutes

---

## What Works Well Today

### Simulation core

| Capability | Notes |
|------------|-------|
| Tick-based engine | Default ≤100 ticks; scale mode up to 500 (ADR-012) |
| Red-before-Blue orchestration | Deterministic, auditable turn order (ADR-004) |
| Five scenarios | Stress, workshop, dual-corridor, and two scale fixtures |
| Red interdiction + Blue adaptation | Route/node attacks; reroute, harden, reallocate |
| Hardening v2 | First attack absorption on hardened routes (ADR-008) |
| Same-tick deconfliction | Conflicts produce `ACTION_SUPPRESSED` events (ADR-008) |
| Red pacing | Cooldown, budget, target rotation (ADR-010) |
| Reproducibility | Seeded runs; golden trace regression suite |
| Large-network performance | Side observation cache with dirty invalidation (Inc 16); ~2.8× mega-scale speedup |

### Explainability

| Capability | Notes |
|------------|-------|
| Immutable audit traces | Every agent decision — ADR-003 contract |
| Reasoning steps | Policy citations in each trace |
| Structured logging | `structlog` JSON events (suppressible via `--quiet-logs`) |
| Suppression transparency | Deconflicted actions are recorded, not dropped |

### Analyst & workshop tooling

| Capability | Notes |
|------------|-------|
| ADR-009 export bundles | JSON, JSONL, executive summary, insights, annotations |
| Automated analytics | Bottlenecks, node/route/corridor risk, Red patterns, focus areas |
| What-if comparison | `compare_runs.py --what-if` / `adsl-compare` |
| Batch export | Sequential or parallel (`--workers N`) |
| Visualization dashboard | Risk overlay, run comparison, presentation mode (Inc 14) |
| Team collaboration | File-based sessions, scenario sharing, annotations (ADR-013) |
| Demo playbook | ~30-minute workshop guide |
| Performance tooling | Benchmarks (`--engine-only`), profiling, `benchmark_compare.py` (Inc 10/16) |

### Platform integration (optional)

| Capability | Notes |
|------------|-------|
| Ontology mapping | Six object types — offline payloads (ADR-006) |
| Foundry datasets | Import scenarios, export results with lineage (ADR-011) |
| Local mode default | No credentials required; CI-safe filesystem adapter |
| Live HTTP mode | When `ADSL_FOUNDRY_ENABLED` + credentials are configured |

### Quality

| Metric | Value |
|--------|-------|
| Automated tests | **138 passing** |
| Code coverage | **~89%** overall |
| ADRs | ADR-001–014 (governed design decisions) |
| Engine isolation | Zero Palantir SDK imports in `simulation/` |

---

## Known Limitations

### Platform & integration

| Limitation | Current state |
|------------|---------------|
| Live Foundry sync | **Not active by default** — requires credentials + env gate |
| No objects written to live Ontology | Unless operator enables gated HTTP sync |
| Foundry Workshop app | Deferred — stakeholder decision |
| Schema validation against live Ontology | Script deferred to Track B |
| Per-tick Foundry streaming | Not planned — batch-at-run-end only |

### Simulation scope

| Limitation | Rationale |
|------------|-----------|
| Doctrine modeling | Out of scope without scoped ADR + SME input |
| Physics / kinetic fidelity | Phase 1/2 boundary |
| Theater-scale networks | Bounded logistics scope by design |
| Operational / classified data | Synthetic scenarios only in this repo |
| LLM-driven open-ended agents | Prohibited by ADR-002 |
| Within-tick parallel agents | Deconfliction requires sequential turns |

### Tooling & workflow

| Limitation | Notes |
|------------|-------|
| CLI-first primary workflow | Dashboard and exports are optional layers |
| File-based collaboration | No real-time multi-user editing |
| Rule-based analytics only | No ML; heuristics may miss domain-specific doctrine |
| 2D SVG dashboard | No geospatial tiles or 3D visualization |
| No authentication on dashboard | Local server; use `--host` carefully on shared networks |
| Batch/offline focus | Not optimized for real-time streaming simulation |

### Performance boundaries

| Limitation | Notes |
|------------|-------|
| Soft scale caps | 64 nodes, 48 agents, 500 ticks documented — not hard-enforced |
| Memory growth | Events and traces grow linearly with ticks × agents |
| Export overhead | Full runs include bundle build + insights (~15–25% beyond engine time) |
| Host-dependent benchmarks | Reference numbers in `before_after.json`; verify on your hardware |

### Process & governance

| Item | Status |
|------|--------|
| Independent facilitator sign-off | Playbook engineering-validated; non-author review pending |
| Ontology schema manifest from platform team | Not yet delivered |
| Live credentials (`FOUNDRY_URL`, `FOUNDRY_TOKEN`, `ONTOLOGY_RID`) | IT/platform configuration pending |

---

## In Development / Blocked

| Item | Blocker |
|------|---------|
| Production live Foundry deployment | Credentials, schema manifest, PM acceptance of ADR-007 HTTP path |
| Foundry Workshop native experience | Stakeholder demo-format decision |
| Doctrine-level agent policies | Requires scoped ADR and subject-matter expertise |

---

## Explicitly Out of Scope

These will not be delivered without a new Architecture Decision Record and program approval:

- Theater-wide force modeling
- Real-time collaborative scenario editing
- LangChain / CrewAI / AutoGen agent orchestration
- Classified deployment hardening (operations concern)
- Distributed/cluster simulation or GPU acceleration
- Unlimited tick counts without performance ADR

---

## How to Verify Claims

```bash
pip install -e ".[dev]"
python -m pytest -q                    # 138 passed
python scripts/foundry_status.py       # integration gate status
python scripts/analyze_run.py --scenario alpine-valley-v3 --ticks 50
python scripts/benchmark_runs.py --scenario continental-mega-scale-v5 --ticks 200 --scale --engine-only
```

Full matrix: [capabilities-matrix.md](capabilities-matrix.md)  
Project status: [status.md](status.md)  
Performance details: [scale-performance.md](scale-performance.md)