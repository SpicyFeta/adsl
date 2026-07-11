# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Route hardening v2 mechanics (ADR-008)."""

from __future__ import annotations

from adsl.models import ADSL_LogisticsRoute, RouteStatus

HARDEN_LEVEL_INITIAL = 1


def apply_harden(route: ADSL_LogisticsRoute) -> bool:
    """Apply HARDEN action: CONTESTED → OPEN with harden_level set."""
    if route.status != RouteStatus.CONTESTED:
        return False
    route.status = RouteStatus.OPEN
    route.metadata["hardened"] = True
    route.metadata["harden_level"] = HARDEN_LEVEL_INITIAL
    return True


def apply_attack_route(route: ADSL_LogisticsRoute) -> tuple[bool, bool]:
    """
    Apply ATTACK_ROUTE to a route.

    Returns (applied, absorbed). When absorbed=True, route status is unchanged.
    """
    harden_level = int(route.metadata.get("harden_level", 0))
    if harden_level > 0:
        route.metadata["harden_level"] = harden_level - 1
        route.metadata["harden_absorbed"] = int(route.metadata.get("harden_absorbed", 0)) + 1
        return True, True

    if route.status == RouteStatus.OPEN:
        route.status = RouteStatus.CONTESTED
        return True, False
    if route.status == RouteStatus.CONTESTED:
        route.status = RouteStatus.CLOSED
        return True, False
    return False, False