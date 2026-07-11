# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Same-tick action deconfliction (ADR-008)."""

from __future__ import annotations

from dataclasses import dataclass, field

from adsl.models import Action, ActionType, AgentSide

SUPPRESSION_REASON = "same_tick_target_conflict"


def action_target_key(action: Action) -> str | None:
    """Return the deconfliction registry key for an action, if any."""
    if action.action_type == ActionType.NO_ACTION:
        return None
    if action.action_type in {
        ActionType.ATTACK_ROUTE,
        ActionType.HARDEN,
        ActionType.REROUTE,
    }:
        if action.target_id:
            return f"route:{action.target_id}"
        return None
    if action.action_type in {ActionType.ATTACK_NODE, ActionType.REALLOCATE}:
        if action.target_id:
            return f"node:{action.target_id}"
        return None
    return None


@dataclass
class TickTargetRegistry:
    """Tracks claimed targets within a single simulation tick."""

    _claims: dict[str, str] = field(default_factory=dict)

    def clear(self) -> None:
        self._claims.clear()

    def try_claim(self, target_key: str, agent_id: str) -> bool:
        """Claim a target for an agent. Returns False if already claimed."""
        if target_key in self._claims:
            return False
        self._claims[target_key] = agent_id
        return True

    def claimed_by(self, target_key: str) -> str | None:
        return self._claims.get(target_key)

    def should_suppress(
        self,
        action: Action,
        agent_id: str,
    ) -> tuple[bool, str | None, str | None]:
        """
        Determine whether an action should be suppressed.

        Returns (suppress, target_key, claimed_by_agent_id).
        """
        target_key = action_target_key(action)
        if target_key is None:
            return False, None, None
        if self.try_claim(target_key, agent_id):
            return False, target_key, None
        return True, target_key, self.claimed_by(target_key)