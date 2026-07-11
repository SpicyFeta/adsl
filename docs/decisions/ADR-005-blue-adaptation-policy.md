# ADR-005: Blue Adaptation Policy (REROUTE, REALLOCATE, HARDEN)

**Status:** Accepted
**Date:** 2026-07-08  
**Deciders:** ADSL Engineering Team, Project Management  
**Phase:** Phase 1 — Contested Logistics Stress Test MVP

---

## Context

ADR-004 established that Blue agents act after Red agents each tick and observe Red-induced network damage. Red interdiction (`RedInterdictionAgent`) degrades routes (`OPEN → CONTESTED → CLOSED`) and nodes (`OPERATIONAL → DEGRADED → DESTROYED`). Blue force elements in the Kessari Strait scenario have distinct roles—logistics managers, route security, depot operators, distribution controllers, and medical logistics cells—that imply different adaptation responses.

Phase 1 requires explicit, auditable rules governing **when Blue chooses to reroute, reallocate, harden, or accept risk** (`NO_ACTION`). Without a formal policy, Blue agent implementations may be inconsistent, untestable, or produce AuditTraces that do not explain the operational rationale.

This ADR defines the Blue Adaptation Policy consumed by `BlueLogisticsAgent` in `src/adsl/agents/blue_logistics.py`.

---

## Decision

ADSL Phase 1 adopts the following **Blue Adaptation Policy** for all Blue force elements.

### 1. Adaptation actions (Phase 1)

| Action | Purpose | Primary roles |
|--------|---------|---------------|
| **HARDEN** | Stabilize a contested corridor against further interdiction | `ROUTE_SECURITY` |
| **REROUTE** | Shift flow from a disrupted route to an alternate open path | `LOGISTICS_MANAGER`, `ROUTE_COORDINATOR`, `MEDICAL_LOGISTICS` |
| **REALLOCATE** | Shift materiel/load from a stressed node to one with spare capacity | `DEPOT_OPERATOR`, `DISTRIBUTION_CONTROLLER` |
| **NO_ACTION** | Accept current risk when network is stable on patrol scope | All roles (default) |

### 2. Threat assessment inputs

Blue agents assess adaptation need using only `Observation` fields (ADR-004 fog-of-war):

- Status of **patrol routes** (`patrol_route_ids` from force element context)
- Status of **home node** (`home_node_id`)
- **Readiness** of the force element
- Visible node **load/capacity** ratios
- Alternate routes sharing source or target endpoints with disrupted patrol routes

### 3. Decision priority (deterministic)

For each Blue agent turn, evaluate in order; execute the **first matching** rule:

| Priority | Condition | Action | Decision category |
|----------|-----------|--------|-------------------|
| **P1** | Patrol route `CLOSED` AND alternate `OPEN` route shares source or target with closed route | `REROUTE` | `ROUTE_ADAPTATION` |
| **P2** | Patrol route `CONTESTED` AND role is `ROUTE_SECURITY` | `HARDEN` | `HARDENING` |
| **P3** | Patrol route `CONTESTED` AND role is `LOGISTICS_MANAGER`, `ROUTE_COORDINATOR`, or `MEDICAL_LOGISTICS` AND alternate `OPEN` route exists | `REROUTE` | `ROUTE_ADAPTATION` |
| **P4** | Home node `DEGRADED` OR load ratio ≥ 0.85 on home/patrol endpoint node AND another node has spare capacity ≥ 15% | `REALLOCATE` | `RESOURCE_REALLOCATION` |
| **P5** | Role is `DEPOT_OPERATOR` or `DISTRIBUTION_CONTROLLER` AND FOB endpoint node load ratio ≥ 0.80 | `REALLOCATE` | `RESOURCE_REALLOCATION` |
| **P6** | No qualifying threat on patrol scope | `NO_ACTION` | `NO_ACTION` |

Tie-breaking: when multiple candidates qualify, select lexicographically smallest route/node ID (deterministic).

### 4. Role-to-action mapping (summary)

| Blue role | Primary action | Fallback |
|-----------|----------------|----------|
| `ROUTE_SECURITY` | `HARDEN` on contested patrol routes | `NO_ACTION` |
| `LOGISTICS_MANAGER` | `REROUTE` around closed/contested patrol routes | `REALLOCATE` if home depot stressed |
| `ROUTE_COORDINATOR` | `REROUTE` | `NO_ACTION` |
| `DEPOT_OPERATOR` | `REALLOCATE` toward FOB-serving nodes | `REROUTE` (P1/P3 if logistics overlap) |
| `DISTRIBUTION_CONTROLLER` | `REALLOCATE` across hub network | `REROUTE` |
| `MEDICAL_LOGISTICS` | `REROUTE` for medical patrol routes | `NO_ACTION` |

### 5. Accept risk (`NO_ACTION`) conditions

Blue accepts risk (no adaptation) when:

- All patrol routes are `OPEN`
- Home node is `OPERATIONAL` with load ratio < 0.85
- No alternate route is required
- Readiness is sufficient but threat does not meet any threshold above

`NO_ACTION` must still produce a full AuditTrace per ADR-003.

### 6. Engine application semantics (Phase 1)

| Action | Engine effect |
|--------|---------------|
| `HARDEN` | `CONTESTED → OPEN`; set `metadata.hardened = true` on route |
| `REROUTE` | Record `metadata.reroute_from` / `metadata.reroute_to` on involved routes; no status downgrade |
| `REALLOCATE` | Transfer up to 15% of source node `capacity` as load from source to target node |
| `NO_ACTION` | No state change |

Hardened routes: subsequent `ATTACK_ROUTE` in the same run still applies (Phase 1 does not grant immunity); `hardened` flag is audit metadata only. Full hardening effects are a future-phase concern.

### 7. AuditTrace requirements

Every Blue decision must record in `inputs_considered`:

- `patrol_route_ids` and their statuses
- `home_node_id` and home node status/load
- `role` and `readiness`
- Evaluated policy priority (P1–P6) that fired, or why none fired

Reasoning steps must cite the policy rule (e.g., "P1: closed patrol route R-010 with alternate R-017 open").

---

## Rationale

### 1. Role-aligned adaptation

Different Blue elements have different missions. Security hardens corridors; logistics reroutes; depot/distribution cells reallocate materiel. A single monolithic Blue policy would produce unrealistic behavior.

### 2. Priority ordering prevents ambiguity

Explicit P1–P6 ordering ensures deterministic decisions and testable golden traces. The first matching threat drives the response.

### 3. Proportional response (Phase 1)

Reroute before reallocate for route disruption; harden before reroute for security elements facing contested corridors. Accept risk when the network is stable to avoid overreaction.

### 4. Auditability

Policy rule IDs in traces allow reviewers to verify Blue acted per doctrine without reading agent source code.

### 5. Scope control

No multi-hop pathfinding, ML optimization, or convoy physics. Alternates are single-hop routes sharing endpoints—sufficient for MVP.

---

## Consequences

### Positive

- Blue responses are explainable, role-specific, and testable.
- Red damage from the same tick is addressable by Blue in the same tick (ADR-004).
- Clear handoff to Palantir Ontology mapping for adaptation events.
- Engineers can extend policy with new priorities without rewriting the agent interface.

### Negative / Trade-offs

- Single-hop reroute only; may miss optimal multi-hop paths.
- `hardened` metadata does not mechanically block Red attacks in Phase 1.
- Load reallocation uses a fixed 15% transfer increment—coarse but predictable.
- Alphabetical tie-breaking is arbitrary for equally scored alternates.

### Neutral

- Blue does not coordinate explicitly across agents; sequential application (ADR-004) provides implicit coordination.
- Policy does not model fuel cost or time delays for adaptation actions.

---

## Alternatives Considered

| Alternative | Reason Not Selected (Phase 1) |
|-------------|-------------------------------|
| **Always reroute on any CONTESTED route** | Over-aggressive; ignores security hardening role and accept-risk cases |
| **ML/optimization-based adaptation** | Out of Phase 1 scope; non-deterministic; weak audit story |
| **Blue always HARDEN first regardless of role** | Misaligns non-security element missions |
| **Global central planner for all Blue agents** | Violates lightweight per-agent model (ADR-002); adds complexity |
| **No accept-risk (always act)** | Unrealistic; produces noise in traces and state |

---

## Compliance Rules

1. All Blue agents inherit `BlueLogisticsAgent` (or satisfy the same policy contract).
2. Decisions must follow P1–P6 priority order exactly.
3. Only `REROUTE`, `REALLOCATE`, `HARDEN`, and `NO_ACTION` may be emitted in Phase 1.
4. Every decision produces a validated `ADSL_AuditTrace` (ADR-003).
5. Agents must not mutate simulation state; engine applies actions (ADR-004).
6. Adaptation targets must be drawn from `Observation` visible nodes/routes only.
7. Determinism: identical observation and internal state yield identical action and trace.

---

## Implementation Map

| Component | Location |
|-----------|----------|
| Blue Adaptation Policy (this ADR) | `docs/decisions/ADR-005-blue-adaptation-policy.md` |
| `BlueLogisticsAgent` | `src/adsl/agents/blue_logistics.py` |
| Blue action application | `SimulationEngine._apply_action()` in `src/adsl/simulation/engine.py` |

---

## References

- ADR-002: Custom Lightweight Multi-Agent System
- ADR-003: AuditTrace System and Explainability Contract
- ADR-004: Simulation Orchestration Policy
- `src/adsl/agents/red_interdiction.py` — Red damage model
- `data/synthetic/logistics_scenario_v1.json` — Kessari Strait Blue force elements