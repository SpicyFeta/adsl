# ADR-008: Hardening v2 and Action Deconfliction Policy

**Status:** Accepted  
**Date:** 2026-07-08  
**Deciders:** ADSL Engineering Team, Project Management  
**Phase:** Phase 2 — Increment 3 (Simulation Mechanics v2)

---

## Context

ADR-005 defined Blue `HARDEN` semantics for Phase 1: contested routes become `OPEN` with `metadata.hardened = true`, but subsequent Red `ATTACK_ROUTE` actions still applied normal degradation — hardening was audit metadata only.

Phase 2 Increment 3 requires **material hardening effects** and **same-tick action deconfliction** so that:

- Blue corridor hardening meaningfully resists interdiction.
- Competing agent actions against the same target in one tick are resolved deterministically with full auditability.

This ADR defines engine-level mechanics consumed by `SimulationEngine`, with agent trace updates citing ADR-008 rules.

---

## Decision

### 1. Hardening v2

#### Application (`HARDEN` action)

| Precondition | Effect |
|--------------|--------|
| Target route status is `CONTESTED` | Route status → `OPEN` |
| | `metadata.hardened = true` |
| | `metadata.harden_level = 1` (Phase 2 Inc 3 maximum) |

Re-hardening a route with `harden_level >= 1` while `CONTESTED` is not expected in Inc 3 (route becomes `OPEN` after harden). Blue P2 fires on `CONTESTED` routes only.

#### Attack absorption (`ATTACK_ROUTE` against hardened route)

When `metadata.harden_level > 0`:

1. Decrement `harden_level` by 1.
2. Increment `metadata.harden_absorbed` counter.
3. **Do not change route status.**
4. Action is `applied=True` with `absorbed=True` in event payload.

When `harden_level == 0`, normal ADR-004/Phase 1 degradation applies:

| Current status | After attack |
|----------------|--------------|
| `OPEN` | `CONTESTED` |
| `CONTESTED` | `CLOSED` |
| `CLOSED` | No change |

`ATTACK_NODE` is unaffected by hardening v2.

#### Blue agent trace (P2)

Reasoning steps must cite **ADR-008** and note that `harden_level=1` absorbs one subsequent route attack.

#### Red agent trace

When attacking a route with `harden_level > 0`, reasoning must note potential absorption per ADR-008.

---

### 2. Action deconfliction (same tick)

#### Target claim keys

| Action | Claim key |
|--------|-----------|
| `ATTACK_ROUTE` | `route:{target_id}` |
| `HARDEN` | `route:{target_id}` |
| `REROUTE` | `route:{target_id}` (alternate route) |
| `ATTACK_NODE` | `node:{target_id}` |
| `REALLOCATE` | `node:{target_id}` (destination node) |
| `NO_ACTION` | None (no claim) |

#### Resolution order

Agents execute in existing ADR-004 order:

1. Red force elements (sorted by `element_id`)
2. Blue force elements (sorted by `element_id`)

Within a tick, the **first agent to claim a target key** may apply its action. Subsequent agents targeting the same key have their action **suppressed**.

#### Suppression behaviour

When an action is suppressed:

1. Agent decision and audit trace are still recorded (agent chose the action).
2. `SimulationEventType.ACTION_SUPPRESSED` is emitted with payload:
   - `suppressed_agent_id`
   - `action_type`
   - `target_id`
   - `target_key`
   - `claimed_by_agent_id`
   - `reason`: `"same_tick_target_conflict"`
3. `ACTION_RECORDED` follows with `applied=False` and `suppressed=True`.

Deconfliction does not mutate network state for suppressed actions.

#### Module boundary

Target registry logic lives in `src/adsl/simulation/deconfliction.py`. Hardening logic lives in `src/adsl/simulation/hardening.py`.

---

## Rationale

### 1. Closes ADR-005 hardening gap

Hardening now affects outcomes, not just metadata.

### 2. Deterministic conflict resolution

Lexicographic agent ordering within side + Red-before-Blue produces reproducible golden traces.

### 3. Full auditability

Suppressed actions remain visible in traces and events.

### 4. Bounded scope

Single absorption layer (`harden_level=1`); no multi-tick decay or stacking in Inc 3.

---

## Consequences

### Positive

- More realistic Blue defensive value.
- Auditable conflict resolution for dense agent scenarios.
- Pure helper modules enable unit tests without full simulation.

### Negative / Trade-offs

- Slightly more complex engine apply path.
- Suppression may increase `NO_ACTION` effective rate when agents collide.

### Neutral

- Red variety / cooldowns (P2-F07) deferred unless PM reprioritizes.

---

## Compliance Rules

1. Hardening logic must live in `src/adsl/simulation/hardening.py`.
2. Deconfliction logic must live in `src/adsl/simulation/deconfliction.py`.
3. Agent audit traces for harden/attack must reference ADR-008 where applicable.
4. Golden trace and regression tests required for v1 and v2 scenarios.

---

## References

- ADR-004: Simulation Orchestration Policy
- ADR-005: Blue Adaptation Policy
- `docs/phase2-planning.md` — Increment 3 scope