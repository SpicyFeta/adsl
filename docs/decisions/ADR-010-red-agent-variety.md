# ADR-010: Red Agent Variety Mechanics

**Status:** Accepted  
**Date:** 2026-07-08  
**Deciders:** ADSL Engineering Team, Project Management  
**Phase:** Phase 3 — Increment 1 (Red Agent Variety + Playbook Validation)

---

## Context

ADR-004 defined Red-before-Blue orchestration and role-based Red targeting (`STRIKE`, `FIRE_SUPPORT`, `RECONNAISSANCE`). Phase 1 and Phase 2 Red agents use deterministic utility scoring with `readiness` weighting and in-run `_engaged_targets` deprioritization, but long runs (50–100 ticks) still exhibit repetitive strike patterns — particularly on `kessari-strait-v1` where network saturation produces clustered `ATTACK_ROUTE` and `ATTACK_NODE` decisions.

Phase 2 Increment 3 deferred **P2-F07 Red variety** (cooldowns, strike budgets, pacing) to keep ADR-008 hardening and deconfliction scope bounded. Phase 3 Increment 1 addresses this gap with **agent-side pacing mechanics** that do not alter engine orchestration, ADR-008 deconfliction, or Blue adaptation policy.

This ADR defines high-level Red variety rules consumed by `RedInterdictionAgent`. **No implementation is authorized until this ADR is Accepted and PM issues an implementation directive.**

---

## Decision

### 1. Strike cooldown

After a Red agent's `ATTACK_ROUTE` or `ATTACK_NODE` action is **selected** in `decide()` (regardless of later engine suppression per ADR-008), that agent enters a cooldown window.

| Parameter | Source | Default |
|-----------|--------|---------|
| `strike_cooldown_ticks` | `ADSL_ForceElement.metadata` | `3` |

**During cooldown:**

1. Agent must not return `ATTACK_ROUTE` or `ATTACK_NODE` (respectively) from `decide()`.
2. Agent returns `NO_ACTION` with `DecisionCategory.NO_ACTION` and reasoning citing **ADR-010**.
3. Audit trace evidence includes `cooldown_remaining` (integer ticks).

Cooldown is **per agent**, not per target. Route and node cooldowns are tracked independently (an agent may still attack a node while on route cooldown if role permits — subject to role logic).

Cooldown state resets on simulation run boundary (`Agent.reset()`).

### 2. Strike budget (optional)

Force elements may specify a per-run attack budget:

| Parameter | Source | Default |
|-----------|--------|---------|
| `strike_budget` | `ADSL_ForceElement.metadata` | omitted = unlimited |

**When budget is set:**

1. Each `ATTACK_ROUTE` or `ATTACK_NODE` selected in `decide()` decrements budget by 1 when the decision is made.
2. When budget reaches 0, agent returns `NO_ACTION` with ADR-010 reasoning and evidence `strike_budget_remaining: 0`.
3. Budget does not decrement on `NO_ACTION` or on actions suppressed by ADR-008 (budget decrements only when agent **chooses** an attack action).

### 3. Target rotation preference

Existing `_engaged_targets` deprioritization (utility multiplier zero for engaged targets) is **retained and extended**:

- Targets struck within the current cooldown window are treated as engaged for utility scoring.
- Reasoning steps should note rotation preference when a lower-utility alternate is chosen due to engagement/cooldown.

No new action types or multi-hop targeting in Increment 1.

### 4. Role behavior (unchanged scope)

| Role | Increment 1 behavior |
|------|----------------------|
| `STRIKE` | Route attacks subject to cooldown/budget; node attacks not used |
| `FIRE_SUPPORT` | Node attacks subject to cooldown/budget |
| `RECONNAISSANCE` | Unchanged — surveillance `NO_ACTION` only |

Scenario v2 (route-focused Red) remains valid; cooldown applies to `ATTACK_ROUTE` only for STRIKE elements.

### 5. Interaction with ADR-008 deconfliction

Red variety gates operate in **`decide()`** before the engine applies deconfliction:

1. Agent selects action per ADR-010 pacing rules.
2. Engine may still suppress duplicate-target actions same tick per ADR-008.
3. Suppression does not refund strike budget (budget consumed on agent decision, not engine apply — see §2 note: PM may amend at implementation if reconciliation is needed; default: decrement on decision).

If implementation reveals budget/deconfliction double-counting friction, an ADR-010 amendment may clarify; Inc 1 locked plan defaults to **decrement on decision**.

### 6. Audit trace requirements

When cooldown or budget causes `NO_ACTION`:

- Reasoning step must cite **ADR-010**.
- Evidence must include at least one of: `cooldown_remaining`, `strike_budget_remaining`, `pacing_hold_reason`.
- `action_summary` must indicate hold due to pacing (e.g., "Hold — strike cooldown active").

When attack proceeds despite pacing metadata:

- Trace may note cooldown clear and budget remaining for audit completeness.

### 7. Determinism and testing

- Cooldown and budget state must be derivable from `(tick, agent_id, prior agent decisions)` for golden trace reproducibility.
- No randomness introduced.
- Golden trace tests required for cooldown hold and budget exhaustion scenarios.

---

## Rationale

### 1. Closes P2-F07 deferral without engine churn

Agent-side gating preserves ADR-004 orchestration and ADR-008 deconfliction modules unchanged.

### 2. Improves workshop demonstration quality

Long runs show intentional pacing and hold decisions rather than repetitive strike spam at network saturation.

### 3. Full auditability

Holds are explicit `NO_ACTION` traces with ADR-010 evidence — not silent skips.

### 4. Bounded scope

Default cooldown of 3 ticks, optional budget, no doctrine or modality rotation. Prevents Increment 1 complexity creep.

### 5. Configurable per force element

Scenario designers tune pacing via metadata without code changes.

---

## Consequences

### Positive

- More varied Red decision timelines over 100 ticks.
- Reproducible golden traces for pacing behavior.
- Clear policy reference for workshop explanation.

### Negative / Trade-offs

- More Red `NO_ACTION` traces may increase trace volume.
- Cooldown may reduce interdiction intensity on short runs (< 10 ticks) — acceptable for workshop-focused 50–100 tick demos.
- Budget/deconfliction interaction may require clarification amendment at implementation.

### Neutral

- Blue agents unaffected in Increment 1.
- Export bundle schema unchanged (ADR-009).

---

## Out of Scope (Increment 1)

- Engine-level cooldown registry
- Per-target cooldown (as opposed to per-agent action-type cooldown)
- Modality rotation (interdiction vs raids labels only in traces today)
- Doctrine-based rules of engagement
- Blue counter-pacing or adaptive Red learning

---

## Compliance Rules

1. Red variety logic must live in `src/adsl/agents/red_interdiction.py` (or extracted `red_pacing.py` helper imported only by Red agent).
2. Engine must not import pacing logic.
3. Cooldown/budget must not bypass ADR-003 trace requirements.
4. Golden trace tests required before Increment 1 exit.
5. No implementation until ADR-010 Accepted and PM implementation directive issued.

---

## Implementation Status

| Item | Status |
|------|--------|
| ADR-010 | Accepted |
| Locked increment plan | `docs/phase3-increment1-plan.md` |
| `red_pacing.py` + `red_interdiction.py` updates | Delivered |
| Tests | `test_red_pacing.py`, `test_red_variety.py`, golden traces |
| Playbook validation | `docs/phase3-increment1-playbook-validation.md` |

---

## References

- ADR-004: Simulation Orchestration Policy
- ADR-008: Hardening v2 and Action Deconfliction Policy
- `docs/phase3-increment1-plan.md` — locked success criteria
- `docs/phase3-scoping.md` — P3-F05
- Phase 2 deferred P2-F07 in `docs/phase2-planning.md`