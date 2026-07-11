# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""CPU profiling helpers for ADSL simulation runs."""

from __future__ import annotations

import cProfile
import io
import pstats
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adsl.export.runner import RunSpec, execute_run


@dataclass(frozen=True)
class ProfileReport:
    """Summary of a profiled simulation run."""

    scenario_id: str
    ticks: int
    elapsed_seconds: float
    peak_memory_mb: float
    top_functions: list[dict[str, Any]]
    hotspot_summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "ticks": self.ticks,
            "elapsed_seconds": self.elapsed_seconds,
            "peak_memory_mb": self.peak_memory_mb,
            "hotspot_summary": self.hotspot_summary,
            "top_functions": self.top_functions,
        }


def _summarize_hotspots(stats: pstats.Stats, limit: int = 8) -> tuple[list[dict[str, Any]], str]:
    stats.strip_dirs()
    stats.sort_stats("cumulative")

    top_functions: list[dict[str, Any]] = []
    for index, (key, value) in enumerate(stats.stats.items()):
        if index >= limit:
            break
        filename, line, func = key
        cc, nc, tt, ct, callers = value
        top_functions.append(
            {
                "ncalls": nc,
                "tottime": round(tt, 4),
                "cumtime": round(ct, 4),
                "function": f"{filename}:{line}({func})",
            }
        )

    hotspot_parts = [
        f"{entry['function']} ({entry['cumtime']}s cumulative)"
        for entry in top_functions[:5]
    ]
    summary = (
        "Primary hotspots: " + "; ".join(hotspot_parts)
        if hotspot_parts
        else "No hotspots captured."
    )
    return top_functions, summary


def profile_run(
    spec: RunSpec,
    *,
    synthetic_dir: Path | None = None,
    quiet_logs: bool = True,
    scale_mode: bool = False,
    top_n: int = 12,
) -> ProfileReport:
    """Execute a run under cProfile + tracemalloc and return a summary report."""
    import time

    tracemalloc.start()
    profiler = cProfile.Profile()
    start = time.perf_counter()
    profiler.enable()
    _, result = execute_run(
        spec,
        synthetic_dir=synthetic_dir,
        quiet_logs=quiet_logs,
        scale_mode=scale_mode,
    )
    profiler.disable()
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    top_functions, hotspot_summary = _summarize_hotspots(stats, limit=top_n)

    return ProfileReport(
        scenario_id=result.bundle["run"]["scenario_id"],
        ticks=result.bundle["execution"]["ticks_executed"],
        elapsed_seconds=round(elapsed, 4),
        peak_memory_mb=round(peak / (1024 * 1024), 2),
        top_functions=top_functions,
        hotspot_summary=hotspot_summary,
    )