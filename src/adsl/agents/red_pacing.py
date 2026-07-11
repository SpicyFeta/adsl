# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Red agent strike pacing state (ADR-010)."""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_STRIKE_COOLDOWN_TICKS = 3


@dataclass
class RedPacingState:
    """Tracks per-agent strike cooldown and optional budget across a simulation run."""

    strike_cooldown_ticks: int = DEFAULT_STRIKE_COOLDOWN_TICKS
    strike_budget_remaining: int | None = None
    _initial_strike_budget: int | None = None
    _last_route_attack_tick: int | None = None
    _last_node_attack_tick: int | None = None
    _target_struck_at: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_metadata(cls, metadata: dict) -> RedPacingState:
        cooldown = int(metadata.get("strike_cooldown_ticks", DEFAULT_STRIKE_COOLDOWN_TICKS))
        budget_raw = metadata.get("strike_budget")
        budget = int(budget_raw) if budget_raw is not None else None
        return cls(
            strike_cooldown_ticks=cooldown,
            strike_budget_remaining=budget,
            _initial_strike_budget=budget,
        )

    def reset(self) -> None:
        self._last_route_attack_tick = None
        self._last_node_attack_tick = None
        self._target_struck_at.clear()
        self.strike_budget_remaining = self._initial_strike_budget

    def has_strike_budget(self) -> bool:
        return self.strike_budget_remaining is None or self.strike_budget_remaining > 0

    def route_cooldown_remaining(self, tick: int) -> int:
        if self._last_route_attack_tick is None:
            return 0
        expires_at = self._last_route_attack_tick + self.strike_cooldown_ticks
        if tick <= self._last_route_attack_tick or tick >= expires_at:
            return 0
        return expires_at - tick

    def node_cooldown_remaining(self, tick: int) -> int:
        if self._last_node_attack_tick is None:
            return 0
        expires_at = self._last_node_attack_tick + self.strike_cooldown_ticks
        if tick <= self._last_node_attack_tick or tick >= expires_at:
            return 0
        return expires_at - tick

    def is_route_cooldown_active(self, tick: int) -> bool:
        return self.route_cooldown_remaining(tick) > 0

    def is_node_cooldown_active(self, tick: int) -> bool:
        return self.node_cooldown_remaining(tick) > 0

    def is_target_in_rotation_window(self, target_id: str, tick: int) -> bool:
        struck_at = self._target_struck_at.get(target_id)
        if struck_at is None:
            return False
        return struck_at < tick < struck_at + self.strike_cooldown_ticks

    def record_route_attack(self, tick: int, target_id: str) -> None:
        self._last_route_attack_tick = tick
        self._target_struck_at[target_id] = tick
        if self.strike_budget_remaining is not None:
            self.strike_budget_remaining -= 1

    def record_node_attack(self, tick: int, target_id: str) -> None:
        self._last_node_attack_tick = tick
        self._target_struck_at[target_id] = tick
        if self.strike_budget_remaining is not None:
            self.strike_budget_remaining -= 1