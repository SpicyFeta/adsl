# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Scale and performance utilities for ADSL simulation workloads."""

from adsl.performance.config import DEFAULT_MAX_TICKS, SCALE_MAX_TICKS
from adsl.performance.network_index import NetworkIndex

__all__ = [
    "DEFAULT_MAX_TICKS",
    "SCALE_MAX_TICKS",
    "NetworkIndex",
]


def __getattr__(name: str):
    """Lazy exports to avoid circular imports with export.runner."""
    if name in {
        "BENCHMARK_SCHEMA_VERSION",
        "BenchmarkResult",
        "benchmark_run",
        "benchmark_suite",
        "load_baselines",
        "save_baselines",
        "check_regression",
    }:
        from adsl.performance import benchmark as _benchmark

        return getattr(_benchmark, name)
    if name == "parallel_batch_export_runs":
        from adsl.performance import parallel as _parallel

        return _parallel.parallel_batch_export_runs
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")