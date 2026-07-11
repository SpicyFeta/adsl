# ADSL Phase 1 — Handover

**Date:** 2026-07-08  
**Status:** Phase 1 complete  
**Next milestone:** v2.4 strategic review

---

## What Was Delivered

ADSL Phase 1 is a contested-logistics simulation MVP with full auditability and Palantir Ontology integration scaffolding.

| Area | Deliverable |
|------|-------------|
| Simulation | Tick-based engine (max 100 ticks), Red-before-Blue orchestration |
| Agents | Red interdiction (`red_interdiction.py`), Blue adaptation (`blue_logistics.py`) |
| Data | Kessari Strait synthetic scenario — 10 nodes, 18 routes, 4 Red / 7 Blue agents |
| Explainability | Immutable `ADSL_AuditTrace` per agent decision (ADR-003) |
| Ontology | Mapping layer + placeholder sync in `src/adsl/ontology/integration.py` (ADR-006) |
| CLI | `scripts/run_simulation.py` |
| Tests | 23 tests including end-to-end (`test_end_to_end.py`), ~91% coverage |
| Documentation | ADR-001–006 (accepted), architecture overview, completion summary |

Key source paths: `src/adsl/`, `data/synthetic/logistics_scenario_v1.json`, `scripts/`, `docs/decisions/`.

---

## How to Run the Simulation

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup and run

```bash
cd adsl-phase1
uv sync --extra dev

# Default run (50 ticks, seed 42)
python scripts/run_simulation.py

# Full stress test (100 ticks)
python scripts/run_simulation.py --ticks 100

# Run all tests
uv run pytest
```

### CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--dataset` | `data/synthetic/logistics_scenario_v1.json` | Scenario JSON |
| `--ticks` | `50` | Tick count (max 100) |
| `--seed` | `42` | Random seed |
| `--sync-ontology` | off | Enable placeholder Ontology sync |

Ontology sync is **off by default**. To enable placeholder writes, pass `--sync-ontology` or set `ADSL_ONTOLOGY_SYNC_ENABLED=true`.

### Expected output

The CLI prints:

1. Simulation run metadata (ID, status, tick count, trace/event counts)
2. End-of-run network state (node and route status breakdown)
3. Key events (recent agent decisions and actions)
4. Audit trace summary (counts by side, action, category; sample traces)
5. Palantir Ontology payload counts

A 100-tick run produces **1,100 audit traces** and **~2,400 simulation events**. Structured JSON logs are also emitted via `structlog`.

### Docker (optional)

```bash
docker compose build
docker compose run --rm adsl pytest
```

---

## Known Limitations

| Limitation | Detail |
|------------|--------|
| Offline Ontology sync | Placeholder read/write only; no live Foundry SDK connection |
| Single scenario | Kessari Strait synthetic JSON only; no Ontology-driven loading |
| No UI | CLI and logs; no workshop dashboard |
| Batch sync | Traces and events batched at run end, not streamed per tick |
| Simplified dynamics | No physics, doctrine, or theater-scale modeling |
| Credentials unset | `FOUNDRY_URL`, `FOUNDRY_TOKEN`, `ONTOLOGY_RID` not configured |
| SDK not installed | Palantir Ontology SDK deferred until schema/credentials confirmed |

These are intentional Phase 1 boundaries documented in ADR-006.

---

## Readiness for v2.4 Strategic Review

Phase 1 is **complete and ready** for the v2.4 strategic review.

### Demonstrated capabilities

- Red agents intelligently interdict a logistics network under contested conditions.
- Blue agents adapt (reroute, harden, reallocate) with auditable reasoning.
- Simulation outputs map to six Palantir Ontology object types.
- End-to-end path verified: dataset → simulation → traces → Ontology payloads.

### Review topics for stakeholders

1. **Foundry integration** — Ontology RID, credentials, SDK package, schema validation.
2. **Demo format** — CLI vs. workshop UI vs. exported payloads.
3. **Scenario roadmap** — Beyond Kessari Strait.
4. **Phase 2 scope** — Doctrine, scale, deployment constraints.
5. **Success metrics** — Acceptance criteria for live integration.

### Related documents

- [Phase 1 completion summary](phase1-completion.md)
- [Architecture overview](architecture/phase1-overview.md)
- [ADR index](decisions/)
- [README](../README.md)