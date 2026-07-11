# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Benchmark harness and baseline management for ADSL runs."""

from __future__ import annotations

import json
import time
import tracemalloc
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from adsl.performance.config import BASELINE_REGRESSION_FACTOR

if False:  # TYPE_CHECKING
    from adsl.export.runner import RunSpec

BENCHMARK_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class BenchmarkResult:
    """Timing result for a single benchmarked simulation run."""

    scenario_id: str
    ticks: int
    seed: int
    elapsed_seconds: float
    ticks_per_second: float
    audit_trace_count: int
    event_count: int
    node_count: int
    route_count: int
    agent_count: int
    peak_memory_mb: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def benchmark_engine_run(
    spec: "RunSpec",
    *,
    synthetic_dir: Path | None = None,
    quiet_logs: bool = True,
    scale_mode: bool = False,
    track_memory: bool = False,
) -> BenchmarkResult:
    """
    Benchmark simulation engine only (excludes export bundle and analytics).

    Use this to measure core loop performance without export-layer overhead.
    """
    from adsl.export.runner import DEFAULT_SYNTHETIC_DIR, apply_red_pacing_overrides
    from adsl.simulation.engine import SimulationEngine
    from adsl.simulation.loader import load_scenario_package
    from adsl.simulation.registry import resolve_scenario_path

    base_dir = synthetic_dir or DEFAULT_SYNTHETIC_DIR
    dataset_path = resolve_scenario_path(spec.scenario_id, synthetic_dir=base_dir)
    package = load_scenario_package(dataset_path)
    package = apply_red_pacing_overrides(package, spec.red_pacing_overrides)

    if track_memory:
        tracemalloc.start()
    start = time.perf_counter()
    engine = SimulationEngine(
        max_ticks=spec.ticks,
        seed=spec.seed,
        quiet_logs=quiet_logs,
        scale_mode=scale_mode,
    )
    run = engine.run_scenario(package)
    elapsed = time.perf_counter() - start
    peak = 0
    if track_memory:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    ticks = run.current_tick + 1 if run is not None else spec.ticks
    tps = ticks / elapsed if elapsed > 0 else 0.0
    agent_count = len(package.red_force_elements) + len(package.blue_force_elements)

    return BenchmarkResult(
        scenario_id=package.scenario.scenario_id,
        ticks=ticks,
        seed=spec.seed,
        elapsed_seconds=round(elapsed, 4),
        ticks_per_second=round(tps, 2),
        audit_trace_count=len(engine.audit_traces),
        event_count=len(engine.events),
        node_count=len(package.scenario.nodes),
        route_count=len(package.scenario.routes),
        agent_count=agent_count,
        peak_memory_mb=round(peak / (1024 * 1024), 2),
    )


def benchmark_run(
    spec: "RunSpec",
    *,
    synthetic_dir: Path | None = None,
    quiet_logs: bool = True,
    scale_mode: bool = False,
    track_memory: bool = False,
    engine_only: bool = False,
) -> BenchmarkResult:
    """Execute one run and return timing metrics."""
    if engine_only:
        return benchmark_engine_run(
            spec,
            synthetic_dir=synthetic_dir,
            quiet_logs=quiet_logs,
            scale_mode=scale_mode,
            track_memory=track_memory,
        )

    from adsl.export.runner import execute_run

    if track_memory:
        tracemalloc.start()
    start = time.perf_counter()
    _, result = execute_run(
        spec,
        synthetic_dir=synthetic_dir,
        quiet_logs=quiet_logs,
        scale_mode=scale_mode,
    )
    elapsed = time.perf_counter() - start
    peak = 0
    if track_memory:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    bundle = result.bundle
    ticks = bundle["execution"]["ticks_executed"]
    tps = ticks / elapsed if elapsed > 0 else 0.0

    nodes = bundle["network_state"]["nodes"]
    routes = bundle["network_state"]["routes"]
    agent_count = len(bundle["audit_traces"]) // max(ticks, 1)

    return BenchmarkResult(
        scenario_id=bundle["run"]["scenario_id"],
        ticks=ticks,
        seed=bundle["execution"]["seed"],
        elapsed_seconds=round(elapsed, 4),
        ticks_per_second=round(tps, 2),
        audit_trace_count=len(bundle["audit_traces"]),
        event_count=len(bundle["simulation_events"]),
        node_count=len(nodes),
        route_count=len(routes),
        agent_count=agent_count,
        peak_memory_mb=round(peak / (1024 * 1024), 2),
    )


def benchmark_suite(
    specs: list["RunSpec"],
    *,
    synthetic_dir: Path | None = None,
    quiet_logs: bool = True,
    scale_mode: bool = False,
    track_memory: bool = False,
    engine_only: bool = False,
) -> list[BenchmarkResult]:
    """Benchmark multiple run specifications sequentially."""
    return [
        benchmark_run(
            spec,
            synthetic_dir=synthetic_dir,
            quiet_logs=quiet_logs,
            scale_mode=scale_mode,
            track_memory=track_memory,
            engine_only=engine_only,
        )
        for spec in specs
    ]


def load_baselines(path: Path) -> dict[str, Any]:
    """Load performance baseline thresholds from JSON."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != BENCHMARK_SCHEMA_VERSION:
        raise ValueError(f"Unsupported baseline schema: {data.get('schema_version')}")
    return data


def save_baselines(path: Path, baselines: dict[str, Any]) -> None:
    """Write performance baselines to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(baselines, indent=2), encoding="utf-8")


def check_regression(
    result: BenchmarkResult,
    baselines: dict[str, Any],
    *,
    factor: float = BASELINE_REGRESSION_FACTOR,
) -> list[str]:
    """
    Return human-readable regression violations against stored baselines.

    Baselines key format: ``{scenario_id}@{ticks}/seed={seed}`` with
    ``max_elapsed_seconds`` threshold.
    """
    key = f"{result.scenario_id}@{result.ticks}/seed={result.seed}"
    entry = baselines.get("benchmarks", {}).get(key)
    if entry is None:
        return []

    max_elapsed = float(entry["max_elapsed_seconds"])
    if result.elapsed_seconds > max_elapsed * factor:
        return [
            f"{key}: {result.elapsed_seconds:.3f}s exceeds baseline "
            f"{max_elapsed:.3f}s × {factor}"
        ]
    return []