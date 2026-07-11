# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Pattern analysis of Red agent behavior from audit traces."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from adsl.analytics.evidence import make_evidence


def _red_traces(audit_traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [trace for trace in audit_traces if trace.get("agent_side") == "RED"]


def _attack_windows(traces: list[dict[str, Any]]) -> list[int]:
    return sorted(
        {
            trace["simulation_tick"]
            for trace in traces
            if trace.get("action_type") in {"ATTACK_ROUTE", "ATTACK_NODE"}
        }
    )


def _timing_phase(tick: int, total_ticks: int) -> str:
    if total_ticks <= 0:
        return "unknown"
    fraction = tick / total_ticks
    if fraction < 0.34:
        return "early"
    if fraction < 0.67:
        return "mid"
    return "late"


def _disruption_zone_pattern(
    red_traces: list[dict[str, Any]],
    total_ticks: int,
    routes: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Identify the corridor/zone with the most Red attacks in each timing phase."""
    route_corridor = {
        route["route_id"]: (route.get("metadata") or {}).get("corridor", "unassigned")
        for route in routes
    }
    phase_targets: dict[str, Counter[str]] = {
        "early": Counter(),
        "mid": Counter(),
        "late": Counter(),
    }
    phase_trace_ids: dict[str, list[str]] = {"early": [], "mid": [], "late": []}

    for trace in red_traces:
        if trace.get("action_type") != "ATTACK_ROUTE":
            continue
        target = trace.get("target_id")
        if not target:
            continue
        phase = _timing_phase(trace["simulation_tick"], total_ticks)
        corridor = route_corridor.get(target, "unassigned")
        phase_targets[phase][corridor] += 1
        phase_trace_ids[phase].append(trace["trace_id"])

    dominant_phase = max(phase_targets, key=lambda p: sum(phase_targets[p].values()))
    if not phase_targets[dominant_phase]:
        return None

    top_corridor, attack_count = phase_targets[dominant_phase].most_common(1)[0]
    total_attacks = sum(phase_targets[dominant_phase].values())
    share = attack_count / total_attacks if total_attacks else 0.0
    if share < 0.3:
        return None

    reasoning = [
        f"Dominant attack phase: {dominant_phase} ({total_attacks} strikes in phase).",
        f"Corridor '{top_corridor}' received {attack_count} attacks ({share:.0%} of phase total).",
        "Derived from Red ATTACK_ROUTE traces grouped by simulation_tick phase.",
    ]
    return {
        "insight_type": "red_pattern",
        "pattern_id": "disruption_zone_timing",
        "severity": "high" if share >= 0.5 else "medium",
        "summary": (
            f"Peak Red disruption in {dominant_phase} phase — "
            f"corridor '{top_corridor}' absorbed {share:.0%} of phase attacks "
            f"({attack_count} strikes)."
        ),
        "reasoning_steps": reasoning,
        "metrics": {
            "dominant_phase": dominant_phase,
            "corridor": top_corridor,
            "phase_attack_count": attack_count,
            "phase_share": round(share, 3),
            "attacks_by_phase": {phase: dict(counter) for phase, counter in phase_targets.items()},
        },
        "evidence": make_evidence(
            source="audit_traces.timing",
            entity_ids=[top_corridor],
            trace_ids=phase_trace_ids[dominant_phase][:10],
            ticks=[
                trace["simulation_tick"]
                for trace in red_traces
                if trace.get("action_type") == "ATTACK_ROUTE"
                and _timing_phase(trace["simulation_tick"], total_ticks) == dominant_phase
            ][:15],
            counts={"phase_attack_count": attack_count},
            reasoning_steps=reasoning,
        ),
    }


def analyze_red_patterns(bundle: dict[str, Any]) -> dict[str, Any]:
    """Detect Red targeting, pacing, and agent specialization patterns."""
    red_traces = _red_traces(bundle["audit_traces"])
    if not red_traces:
        return {
            "patterns": [],
            "summary": "No Red agent activity recorded.",
            "metrics": {"red_trace_count": 0},
        }

    by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_action: Counter[str] = Counter()
    route_targets: Counter[str] = Counter()
    node_targets: Counter[str] = Counter()
    attack_trace_ids: list[str] = []

    for trace in red_traces:
        by_agent[trace["agent_id"]].append(trace)
        action = trace.get("action_type", "")
        by_action[action] += 1
        target = trace.get("target_id")
        if action == "ATTACK_ROUTE" and target:
            route_targets[target] += 1
            attack_trace_ids.append(trace["trace_id"])
        elif action == "ATTACK_NODE" and target:
            node_targets[target] += 1
            attack_trace_ids.append(trace["trace_id"])

    ticks = [trace["simulation_tick"] for trace in red_traces]
    attack_ticks = _attack_windows(red_traces)
    total_ticks = bundle["execution"]["ticks_executed"]
    attack_rate = len(attack_ticks) / total_ticks if total_ticks else 0.0

    patterns: list[dict[str, Any]] = []
    routes = bundle["network_state"]["routes"]

    timing_pattern = _disruption_zone_pattern(red_traces, total_ticks, routes)
    if timing_pattern:
        patterns.append(timing_pattern)

    top_route = route_targets.most_common(1)
    if top_route:
        target_id, count = top_route[0]
        share = count / max(by_action.get("ATTACK_ROUTE", 1), 1)
        if share >= 0.35:
            focus_reasoning = [
                f"Route {target_id} received {count} of {by_action.get('ATTACK_ROUTE', 0)} route attacks.",
                f"Share {share:.0%} exceeds 35% focus threshold.",
                "Indicates deliberate interdiction priority rather than broad rotation.",
            ]
            patterns.append(
                {
                    "insight_type": "red_pattern",
                    "pattern_id": "route_focus",
                    "severity": "high" if share >= 0.5 else "medium",
                    "summary": (
                        f"Red concentrated {share:.0%} of route attacks on {target_id} "
                        f"({count} strikes)."
                    ),
                    "reasoning_steps": focus_reasoning,
                    "metrics": {
                        "target_id": target_id,
                        "attack_count": count,
                        "share_of_route_attacks": round(share, 3),
                    },
                    "evidence": make_evidence(
                        source="audit_traces",
                        entity_ids=[target_id],
                        trace_ids=[
                            t["trace_id"]
                            for t in red_traces
                            if t.get("action_type") == "ATTACK_ROUTE"
                            and t.get("target_id") == target_id
                        ][:10],
                        counts={"attack_count": count},
                        reasoning_steps=focus_reasoning,
                    ),
                }
            )

    if len(route_targets) >= 3:
        top_three = sum(count for _, count in route_targets.most_common(3))
        total_route_attacks = by_action.get("ATTACK_ROUTE", 0)
        rotation_share = top_three / total_route_attacks if total_route_attacks else 0.0
        if rotation_share < 0.75:
            patterns.append(
                {
                    "insight_type": "red_pattern",
                    "pattern_id": "target_rotation",
                    "severity": "medium",
                    "summary": (
                        f"Red rotated across {len(route_targets)} routes; "
                        f"top-3 absorbed only {rotation_share:.0%} of strikes."
                    ),
                    "metrics": {
                        "distinct_route_targets": len(route_targets),
                        "top_three_share": round(rotation_share, 3),
                    },
                    "evidence": make_evidence(
                        source="audit_traces",
                        entity_ids=[target for target, _ in route_targets.most_common(5)],
                        counts={"distinct_route_targets": len(route_targets)},
                    ),
                }
            )

    no_action = by_action.get("NO_ACTION", 0)
    no_action_rate = no_action / len(red_traces)
    if no_action_rate >= 0.5:
        patterns.append(
            {
                "insight_type": "red_pattern",
                "pattern_id": "conservative_pacing",
                "severity": "medium",
                "summary": (
                    f"Red held fire on {no_action_rate:.0%} of decision ticks "
                    f"({no_action} NO_ACTION traces)."
                ),
                "metrics": {
                    "no_action_count": no_action,
                    "no_action_rate": round(no_action_rate, 3),
                },
                "evidence": make_evidence(
                    source="audit_traces",
                    trace_ids=[
                        t["trace_id"]
                        for t in red_traces
                        if t.get("action_type") == "NO_ACTION"
                    ][:10],
                    counts={"no_action_count": no_action},
                ),
            }
        )
    elif attack_rate >= 0.35:
        patterns.append(
            {
                "insight_type": "red_pattern",
                "pattern_id": "sustained_pressure",
                "severity": "high",
                "summary": (
                    f"Red attacked on {attack_rate:.0%} of simulation ticks "
                    f"({len(attack_ticks)} active attack ticks)."
                ),
                "metrics": {
                    "attack_tick_count": len(attack_ticks),
                    "attack_tick_rate": round(attack_rate, 3),
                },
                "evidence": make_evidence(
                    source="audit_traces",
                    ticks=attack_ticks[:20],
                    trace_ids=attack_trace_ids[:10],
                    counts={"attack_tick_count": len(attack_ticks)},
                ),
            }
        )

    agent_specialists: list[tuple[str, str, int]] = []
    for agent_id, traces in by_agent.items():
        actions = Counter(t.get("action_type", "") for t in traces)
        dominant_action, dominant_count = actions.most_common(1)[0]
        if dominant_count / len(traces) >= 0.8 and dominant_action != "NO_ACTION":
            agent_specialists.append((agent_id, dominant_action, dominant_count))

    for agent_id, action, count in agent_specialists[:3]:
        patterns.append(
            {
                "insight_type": "red_pattern",
                "pattern_id": "agent_specialization",
                "severity": "low",
                "summary": f"{agent_id} specialized in {action} ({count} traces).",
                "metrics": {
                    "agent_id": agent_id,
                    "dominant_action": action,
                    "action_count": count,
                },
                "evidence": make_evidence(
                    source="audit_traces",
                    entity_ids=[agent_id],
                    trace_ids=[
                        t["trace_id"]
                        for t in by_agent[agent_id]
                        if t.get("action_type") == action
                    ][:8],
                    counts={"action_count": count},
                ),
            }
        )

    return {
        "patterns": patterns,
        "summary": (
            f"{len(red_traces)} Red traces across {len(by_agent)} agents; "
            f"{by_action.get('ATTACK_ROUTE', 0)} route attacks, "
            f"{no_action} holds."
        ),
        "metrics": {
            "red_trace_count": len(red_traces),
            "red_agent_count": len(by_agent),
            "actions_by_type": dict(by_action),
            "top_route_targets": dict(route_targets.most_common(5)),
            "top_node_targets": dict(node_targets.most_common(5)),
            "attack_tick_rate": round(attack_rate, 3),
            "tick_range": [min(ticks), max(ticks)] if ticks else [],
        },
    }