# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Unit tests for Red strike pacing state (ADR-010)."""

from adsl.agents.red_pacing import DEFAULT_STRIKE_COOLDOWN_TICKS, RedPacingState


def test_default_cooldown_is_three() -> None:
    state = RedPacingState.from_metadata({})
    assert state.strike_cooldown_ticks == DEFAULT_STRIKE_COOLDOWN_TICKS


def test_route_cooldown_blocks_ticks_after_attack() -> None:
    state = RedPacingState.from_metadata({"strike_cooldown_ticks": 3})
    state.record_route_attack(5, "R-001")

    assert state.is_route_cooldown_active(5) is False
    assert state.is_route_cooldown_active(6) is True
    assert state.is_route_cooldown_active(7) is True
    assert state.is_route_cooldown_active(8) is False
    assert state.route_cooldown_remaining(6) == 2
    assert state.route_cooldown_remaining(7) == 1


def test_node_cooldown_independent_of_route() -> None:
    state = RedPacingState.from_metadata({})
    state.record_route_attack(1, "R-001")

    assert state.is_route_cooldown_active(2) is True
    assert state.is_node_cooldown_active(2) is False


def test_strike_budget_decrements_on_attack() -> None:
    state = RedPacingState.from_metadata({"strike_budget": 2})
    assert state.has_strike_budget() is True

    state.record_route_attack(0, "R-001")
    assert state.strike_budget_remaining == 1
    assert state.has_strike_budget() is True

    state.record_node_attack(10, "N-001")
    assert state.strike_budget_remaining == 0
    assert state.has_strike_budget() is False


def test_reset_restores_budget_and_clears_cooldown() -> None:
    state = RedPacingState.from_metadata({"strike_budget": 1})
    state.record_route_attack(3, "R-001")
    state.reset()

    assert state.strike_budget_remaining == 1
    assert state.is_route_cooldown_active(4) is False
    assert state.is_target_in_rotation_window("R-001", 4) is False


def test_target_rotation_window_matches_cooldown() -> None:
    state = RedPacingState.from_metadata({"strike_cooldown_ticks": 3})
    state.record_route_attack(10, "R-CONTEST")

    assert state.is_target_in_rotation_window("R-CONTEST", 11) is True
    assert state.is_target_in_rotation_window("R-CONTEST", 12) is True
    assert state.is_target_in_rotation_window("R-CONTEST", 13) is False