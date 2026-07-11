# ADR-012: Scale & Performance Optimizations

**Status:** Accepted  
**Date:** 2026-07-08  
**Increment:** Phase 3 Increment 10

---

## Context

Analyst workflows increasingly run multi-scenario batches, extended tick counts for stress testing, and automated insight generation. The Phase 1 engine copied the full network state for every agent turn and used linear scans for state mutations — acceptable for workshop scenarios (≤100 ticks, ~11 agents) but limiting for batch throughput.

Increment 10 requires bounded scale improvements without opening theater-scale simulation scope.

---

## Decision

1. **Network index** — Maintain `NetworkIndex` with O(1) node/route lookups in engine apply paths.

2. **Shallow observation snapshots** — Use Pydantic `model_copy(deep=False)` for per-agent observations. Agents are read-only (ADR-002); scalar fields snapshot at copy time; per-turn ordering semantics preserved (golden traces verified).

3. **Scale mode tick cap** — Retain `DEFAULT_MAX_TICKS = 100` for workshop runs; allow `SCALE_MAX_TICKS = 500` when `SimulationEngine(scale_mode=True)` or `execute_run(scale_mode=True)`.

4. **Parallel batch execution** — `batch_export_runs(workers=N)` delegates to `ProcessPoolExecutor` for CPU-bound runs (GIL bypass).

5. **Benchmark harness** — `adsl.performance.benchmark` with committed baselines in `data/performance/baselines.json` and regression factor 2.0×.

6. **Scale stress scenarios** — `continental-grid-scale-v4` (17 nodes, 20 agents) and `continental-mega-scale-v5` (37 nodes, 36 agents) for performance validation.
7. **Profiler harness** — `adsl.performance.profiler` and `scripts/profile_run.py` for cProfile hotspot reports.

---

## Consequences

### Positive

- O(1) action application lookups via `NetworkIndex`.
- Leaner observation copies via Pydantic `model_copy`.
- Parallel batch export improves multi-run workshop prep time on multi-core hosts.
- Regression baselines catch accidental performance degradation.

### Negative / Limits

- Scale mode does **not** change simulation semantics — only tick cap and performance paths.
- Process pool adds Windows spawn overhead for very small batches (workers=1 remains default).
- `continental-grid-scale-v4` is a synthetic stress fixture, not a stakeholder workshop scenario.

---

## Alternatives Considered

| Alternative | Rejected because |
|-------------|------------------|
| Remove observation isolation | Violates agent/state separation contract |
| ThreadPoolExecutor for batch | GIL limits CPU-bound simulation speedup |
| Unlimited tick counts | Unbounded runtime without stakeholder ADR |
| C extension / Rust engine | Out of Phase 3 scope per ADR-001 |

---

## Compliance

- ADR-003 audit trace contract unchanged.
- ADR-004 orchestration order unchanged.
- Golden trace determinism preserved (verified in `test_performance.py`).