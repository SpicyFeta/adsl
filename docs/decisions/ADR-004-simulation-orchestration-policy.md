# ADR-004: Simulation Orchestration Policy (Tick Order, Fog-of-War, Red-Before-Blue)

**Status:** Accepted
**Date:** 2026-07-08  
**Deciders:** ADSL Engineering Team, Project Management  
**Phase:** Phase 1 — Contested Logistics Stress Test MVP

---

## Context

ADSL Phase 1 requires a deterministic, auditable simulation loop where Red and Blue agents make decisions under explicit information boundaries. ADR-002 defined the agent interface and high-level orchestration model; ADR-003 defined AuditTrace requirements. Neither ADR specifies the concrete rules governing:

- Tick structure and lifecycle events
- Turn order within and across ticks
- Fog-of-war (information asymmetry) for observations
- When state mutations become visible to subsequent agents
- Agent ordering for reproducibility

Without a formal orchestration policy, engine implementations may diverge, replay tests may fail, and audit traces may not reflect the information an agent actually possessed at decision time. Defense reviewers must be able to answer: *in what order did agents act, what did each side know, and when did the world state change?*

---

## Decision

ADSL Phase 1 adopts the following **Simulation Orchestration Policy**, implemented in `src/adsl/simulation/orchestration.py` and enforced by `SimulationEngine` in `src/adsl/simulation/engine.py`.

### 1. Tick structure

| Phase | Event | Description |
|-------|-------|-------------|
| **Run start** | `RUN_STARTED` | Initialize run metadata, agents, and network state from scenario |
| **Per tick `t`** (0 ≤ t < max_ticks) | `TICK_START` | Begin tick; set `current_tick = t` |
| | Red phase | Each Red agent acts in deterministic order (see §2) |
| | Blue phase | Each Blue agent acts in deterministic order (see §2) |
| | `TICK_END` | Close tick |
| **Run end** | `RUN_COMPLETED` | Finalize run status and timestamps |

- **max_ticks** defaults to 100 and must not exceed 100 in Phase 1.
- Ticks are discrete and synchronous; no parallel agent execution within a tick.

### 2. Turn order: Red before Blue

Within every tick:

1. **All Red agents act first**, in ascending `element_id` order (stable alphabetical sort).
2. **All Blue agents act second**, in ascending `element_id` order.

Rationale: Red initiates contested pressure; Blue responds to the post-Red world state within the same tick. This matches Phase 1 demonstration goals and the synthetic scenario metadata (`turn_order: ["RED", "BLUE"]`).

### 3. Sequential state application within a phase

When an agent completes `decide()` and passes `act()` validation:

1. The simulation engine **immediately applies** the action to internal network state (before the next agent in the same phase acts).
2. Subsequent agents in the **same phase** observe the updated state.
3. Blue agents always observe Red-induced changes from the **current tick** before making decisions.

Agents must not mutate simulation state directly (ADR-002). Only the engine applies actions.

### 4. Fog-of-war rules (Phase 1)

Observations are built by the engine; agents receive only `Observation` objects.

| Viewer | Nodes visible | Routes visible | Additional context |
|--------|---------------|----------------|-------------------|
| **Red** | All nodes (including `DESTROYED`) | All routes (including `CLOSED`) | Force element config: `patrol_route_ids`, `readiness`, `priority_target`, `capability` |
| **Blue** | All nodes where `status != DESTROYED` | All routes (full network awareness of Blue-owned logistics) | Force element config: `home_node_id`, `patrol_route_ids`, `readiness` |

Phase 1 simplifications (explicitly in scope):

- Red has battlespace awareness suitable for interdiction planning.
- Blue retains logistics network situational awareness but cannot see destroyed nodes (removed from picture).
- Red actions in the current tick are reflected in Blue observations via sequential application (§3).
- No GPS jitter, delayed reporting, or probabilistic detection in Phase 1.

Out of scope: partial route visibility, classified overlays, SIGINT-derived uncertainty models.

### 5. Per-agent turn micro-cycle

For each agent on each tick, the engine executes:

```
build_observation(agent, tick)
    → agent.perceive(observation)
    → decision = agent.decide(observation)
    → action = agent.act(decision)          # AuditTrace validated (ADR-003)
    → engine.record(decision.audit_trace)
    → engine.apply(action)                  # state mutation
    → structlog emission
```

### 6. Determinism requirements

Given identical `scenario`, `seed`, and `max_ticks`:

- Agent turn order is identical across runs.
- Observations at decision time are identical.
- Agent decisions must be deterministic (ADR-002, ADR-003).
- Action application is deterministic (no random damage rolls in Phase 1).

The `seed` field on `ADSL_SimulationRun` is recorded for future stochastic extensions; Phase 1 Red/Blue logic is rule-based and does not consume the seed.

### 7. Action application semantics (Phase 1)

| Action type | Effect |
|-------------|--------|
| `ATTACK_ROUTE` | `OPEN → CONTESTED`; `CONTESTED → CLOSED` |
| `ATTACK_NODE` | `OPERATIONAL → DEGRADED`; `DEGRADED → DESTROYED` |
| `NO_ACTION` | No state change |
| Blue actions (`REROUTE`, `REALLOCATE`, `HARDEN`) | Deferred to Blue agent directive |

Invalid targets (already `CLOSED` routes, `DESTROYED` nodes) are not applied; the action is logged as recorded but skipped for mutation.

---

## Rationale

### 1. Auditability

Fixed tick and turn ordering makes event logs and AuditTrace sequences replayable and reviewable. Analysts can reconstruct the exact sequence of Red pressure and Blue response.

### 2. Red-before-Blue models contested logistics

Interdiction precedes adaptation within a decision cycle. Blue decisions in tick `t` reflect Red actions taken earlier in the same tick.

### 3. Sequential application prevents stale observations

If all Red actions were applied in batch after the Red phase, agents would make decisions on outdated state. Sequential application within the phase is more faithful to simultaneous conflict at discrete time steps.

### 4. Explicit fog-of-war avoids agent-side cheating

Information boundaries are enforced by the engine, not agent convention (ADR-002 compliance rule #4).

### 5. Phase 1 appropriate complexity

Full intelligence simulation is out of scope. These rules are sufficient for MVP demonstration with the Kessari Strait synthetic dataset.

---

## Consequences

### Positive

- Deterministic, replayable simulation runs.
- Clear contract for engine and agent developers.
- Audit traces align with actual observation content.
- Blue agents (when implemented) have meaningful Red-induced state to react to.

### Negative / Trade-offs

- Red-before-Blue may bias outcomes if Red accumulates multiple strikes before any Blue response in tick 0; acceptable for Phase 1 stress-test narrative.
- Blue full-route visibility is optimistic; may overstate Blue SA.
- Alphabetical agent ordering is arbitrary (not priority-based); priority-based ordering requires a future ADR amendment.
- Synchronous ticks do not model continuous time or concurrent convoy movement.

### Neutral

- Palantir Ontology sync is unaffected; events and traces remain the integration artifacts.
- `seed` is reserved but unused by rule-based agents in Phase 1.

---

## Alternatives Considered

| Alternative | Reason Not Selected (Phase 1) |
|-------------|-------------------------------|
| **Simultaneous reveal (batch apply after phase)** | Agents would decide on stale state within the same phase; weakens audit fidelity |
| **Blue before Red** | Contradicts contested interdiction narrative and scenario metadata |
| **Random agent order within side** | Breaks determinism and replay testing |
| **Full fog-of-war with detection probabilities** | Out of Phase 1 scope; adds stochastic complexity |
| **Parallel agent execution** | Complicates trace ordering and state consistency; unnecessary for ≤11 agents per side |

---

## Compliance Rules for the Engine

1. **Red-before-Blue** — Every tick must complete all Red agent turns before any Blue agent turn.
2. **Stable ordering** — Agents sorted by `element_id` ascending within each side.
3. **Engine-owned observations** — Agents must not build their own world view; use `build_observation()` only.
4. **Immediate application** — Actions applied before the next agent in the same phase acts.
5. **Fog-of-war enforcement** — `visible_nodes` and `visible_routes` must follow §4; no supplemental hidden channels on `Observation`.
6. **Force element context** — `Observation.context` must include patrol routes, readiness, and role-relevant metadata from `ADSL_ForceElement`.
7. **Trace before apply** — AuditTrace recorded before action application (trace reflects pre-action decision intent).
8. **max_ticks ≤ 100** — Enforced at engine construction.
9. **Event emission** — Every tick boundary and agent decision emits `SimulationEvent` and structlog entries.

---

## Implementation Map

| Policy area | Location |
|-------------|----------|
| Turn order, fog-of-war helpers | `src/adsl/simulation/orchestration.py` |
| Tick loop, apply semantics | `src/adsl/simulation/engine.py` |
| Red agent (interdiction logic) | `src/adsl/agents/red_interdiction.py` |
| Blue agent | Placeholder until Blue directive |

---

## References

- ADR-002: Custom Lightweight Multi-Agent System
- ADR-003: AuditTrace System and Explainability Contract
- `data/synthetic/logistics_scenario_v1.meta.json` — `turn_order` default
- ADSL Phase 1 Project Charter — contested logistics stress test scope