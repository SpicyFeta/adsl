# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Performance and scale configuration constants."""

from __future__ import annotations

DEFAULT_MAX_TICKS = 100
SCALE_MAX_TICKS = 500

# Documented soft limits for scale-mode stress scenarios (not hard-enforced).
SCALE_MAX_NODES = 64
SCALE_MAX_AGENTS = 48

# Regression guard: benchmark may not exceed baseline * this factor.
BASELINE_REGRESSION_FACTOR = 2.0