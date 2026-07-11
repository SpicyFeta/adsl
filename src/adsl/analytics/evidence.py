# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Evidence references that trace insights back to raw simulation data."""

from __future__ import annotations

from typing import Any


def make_evidence(
    *,
    source: str,
    trace_ids: list[str] | None = None,
    ticks: list[int] | None = None,
    entity_ids: list[str] | None = None,
    counts: dict[str, int | float] | None = None,
    details: dict[str, Any] | None = None,
    reasoning_steps: list[str] | None = None,
) -> dict[str, Any]:
    """Build a traceable evidence block for an insight."""
    evidence: dict[str, Any] = {"source": source}
    if trace_ids:
        evidence["trace_ids"] = trace_ids[:20]
        evidence["trace_count"] = len(trace_ids)
    if ticks is not None:
        evidence["ticks"] = sorted(set(ticks))[:20]
    if entity_ids:
        evidence["entity_ids"] = entity_ids
    if counts:
        evidence["counts"] = counts
    if details:
        evidence["details"] = details
    if reasoning_steps:
        evidence["reasoning_steps"] = reasoning_steps
    return evidence