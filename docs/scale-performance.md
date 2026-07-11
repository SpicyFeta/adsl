# ADSL Scale & Performance

**Increments 10 & 16** — Profile bottlenecks, optimize the engine for larger networks, parallel batch execution, and committed benchmarks.

---

## Executive Summary

| Scenario | Inc 10 (engine) | Inc 16 (engine) | Improvement |
|----------|-----------------|-----------------|-------------|
| Workshop (`island-chokepoint-v2`, 100 ticks) | ~563 ticks/s | **~965 ticks/s** | ~1.7× |
| Scale (`continental-grid-scale-v4`, 150 ticks) | ~315 ticks/s | **~734 ticks/s** | ~2.3× |
| Mega (`continental-mega-scale-v5`, 200 ticks) | ~127 ticks/s | **~358 ticks/s** | ~2.8× |

Inc 16 introduces **per-side observation caching with dirty invalidation**: agents on the same side reuse snapshots until a state-mutating action applies, then the cache rebuilds. Golden traces and deconfliction semantics are preserved.

Full before/after data: [`data/performance/before_after.json`](../data/performance/before_after.json)

---

## Profiling Bottlenecks

Run a hotspot profile on any scenario:

```bash
python scripts/profile_run.py --scenario continental-mega-scale-v5 --ticks 100 --scale
python scripts/profile_run.py --scenario alpine-valley-v3 --ticks 50 --json
```

### Findings (cProfile, mega-scale-v5, 50 ticks)

| Rank | Function (Inc 10) | Share | Function (Inc 16) | Share |
|------|-------------------|-------|-------------------|-------|
| 1 | `snapshot_nodes` / `model_copy` | ~52% | `build_side_observation_cache` (on miss) | ~18% |
| 2 | `snapshot_routes` / `model_copy` | ~22% | `BlueLogisticsAgent.decide` | ~15% |
| 3 | `BlueLogisticsAgent.decide` | ~10% | `AuditTraceBuilder.build` | ~8% |

**Conclusion:** Observation copying dominated Inc 10 runtime on multi-agent ticks. Inc 16 caches snapshots per side and rebuilds only when an applied action mutates network state — cutting observation CPU by roughly half on mega-scale runs while preserving sequential semantics.

---

## Engine Optimizations

| Optimization | Location | Effect |
|--------------|----------|--------|
| Side observation cache | `simulation/observation_cache.py` | Reuse snapshots across agents until state changes |
| Dirty invalidation | `engine.py` | Rebuild cache after applied attacks, harden, reroute, reallocate |
| Pre-built observation indexes | `observation_cache.py` | `nodes_by_id`, `routes_by_id`, endpoint indexes in context |
| Indexed alternate routes | `blue_logistics.py` | O(k) reroute lookup vs full route scan |
| `NetworkIndex` endpoints | `performance/network_index.py` | O(1) route/node lookups and alternate discovery |
| Guarded structlog | `engine.py` `_emit_logs` | Skips log overhead when `quiet_logs=True` |
| Scale mode | `SCALE_MAX_TICKS = 500` | Extended stress runs without workshop cap |

---

## Scenarios & Current Limits

| Scenario | Nodes | Routes | Agents/tick | Workshop? | Max ticks (default) | Max ticks (scale) |
|----------|-------|--------|-------------|-----------|---------------------|-------------------|
| `kessari-strait-v1` | 10 | 18 | 11 | Stress | 100 | 500 |
| `island-chokepoint-v2` | 12 | 20 | 11 | **Yes** | 100 | 500 |
| `alpine-valley-v3` | 11 | 16 | 11 | **Yes** | 100 | 500 |
| `continental-grid-scale-v4` | 17 | 16 | 20 | Perf test | 100 | 500 |
| `continental-mega-scale-v5` | 37 | 36 | 36 | Perf test | 100 | 500 |

### Soft limits (scale mode, documented not hard-enforced)

| Resource | Recommended max | Notes |
|----------|-----------------|-------|
| Nodes | 64 | `SCALE_MAX_NODES` in config |
| Agents per tick | 48 | `SCALE_MAX_AGENTS` |
| Ticks | 500 | `SCALE_MAX_TICKS` |
| Audit traces per run | ~18,000 | At 500 ticks × 36 agents; export grows linearly |

Beyond these limits, expect linear slowdown and increased memory for event/trace lists. Theater-scale modeling remains out of scope.

---

## Parallel Batch Execution

CPU-bound simulation loops use a **process pool** to bypass the GIL:

```bash
python scripts/batch_export.py \
  --specs data/analyst/example_batch.json \
  --export-dir exports/parallel \
  --workers 4 --quiet-logs --scale
```

`workers=1` (default) preserves sequential behaviour for small batches. Parallelism applies to **multi-run batch export**, not within-tick agent execution (deconfliction requires sequential turns).

---

## Benchmarks & Regression

```bash
# Engine-only (core simulation loop, no export/analytics)
python scripts/benchmark_runs.py --suite data/performance/benchmark_suite.json --scale --engine-only

# Full run (includes ADR-009 bundle + insights)
python scripts/benchmark_runs.py --suite data/performance/benchmark_suite.json --scale

# Compare against historical baselines
python scripts/benchmark_compare.py --scenario continental-mega-scale-v5 --ticks 200 --scale --engine-only

# Update baselines after intentional changes
python scripts/benchmark_runs.py --suite data/performance/benchmark_suite.json --scale --update-baselines

# Memory tracking (adds overhead)
python scripts/benchmark_runs.py --scenario continental-mega-scale-v5 --ticks 200 --scale --memory
```

Baselines: `data/performance/baselines.json` — regression allows **2×** `max_elapsed_seconds`.

### Reference results (seed 42, Inc 16)

| Scenario | Ticks | Engine elapsed | Engine ticks/s | Full-run elapsed | Traces |
|----------|-------|----------------|----------------|------------------|--------|
| island-chokepoint-v2 | 100 | 0.10s | 965 | 0.15s | 1,100 |
| alpine-valley-v3 | 100 | 0.10s | 974 | 0.15s | 1,100 |
| continental-grid-scale-v4 | 150 | 0.20s | 734 | 0.33s | 3,000 |
| continental-mega-scale-v5 | 200 | 0.56s | 358 | 0.86s | 7,200 |

---

## Scaling Recommendations

### Workshop / analyst (≤11 agents)

- Use default mode (100 tick cap)
- `quiet_logs=True` for batch and benchmark runs
- Sequential batch is fine for &lt;5 runs

### Multi-run studies

- `--workers` = CPU cores − 1
- Export to SSD; insight generation adds ~15–25% per full run

### Large-network stress

- Use `continental-mega-scale-v5` or generate custom grids:
  - `scripts/generate_scale_scenario.py`
  - `scripts/generate_mega_scale_scenario.py`
- Enable `--scale` for ticks &gt; 100
- Profile first: `scripts/profile_run.py`
- Use `--engine-only` benchmarks to isolate simulation performance

### Memory

- Peak memory scales with `ticks × agents × (events + traces)`
- Mega scenario 200 ticks (engine-only): ~23–45 MB peak (host-dependent)
- For sweeps &gt;20 runs, prefer parallel export with ample disk

---

## Python API

```python
from adsl.export.runner import RunSpec, execute_run
from adsl.performance.benchmark import benchmark_run, benchmark_engine_run
from adsl.performance.profiler import profile_run

# Large stress run
spec = RunSpec("continental-mega-scale-v5", seed=42, ticks=300)
_, result = execute_run(spec, scale_mode=True, quiet_logs=True)

# Engine-only benchmark (no export overhead)
metrics = benchmark_engine_run(spec, scale_mode=True, track_memory=True)
print(metrics.ticks_per_second, metrics.peak_memory_mb)

# Hotspot profile
report = profile_run(spec, scale_mode=True)
print(report.hotspot_summary)
```

---

## Related

- [ADR-012](decisions/ADR-012-scale-performance.md) — Architecture decision
- [phase3-increment10-completion.md](phase3-increment10-completion.md) — Initial scale delivery
- [phase3-increment16-completion.md](phase3-increment16-completion.md) — Inc 16 optimizations
- [analytics-insights.md](analytics-insights.md) — Post-run analysis