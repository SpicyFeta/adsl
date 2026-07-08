# ADR-003: AuditTrace System and Explainability Contract

**Status:** Accepted
**Date:** 2026-07-08  
**Deciders:** ADSL Engineering Team, Project Management  
**Phase:** Phase 1 — Contested Logistics Stress Test MVP

---

## Context

ADSL Phase 1 operates in defense and intelligence contexts where every agent decision must be inspectable, reproducible, and suitable for external audit. Stakeholders—including operators, analysts, and Palantir Ontology consumers—need to answer: *what did the agent know, what did it consider, what did it decide, and why?*

ADR-002 established a custom lightweight agent system with a mandatory `AuditTrace` on every `decide()` call. That contract defines *that* traces are required; this ADR defines *what* a trace contains, *how* it is generated, persisted, and validated.

Explainability and auditability are not logging enhancements—they are first-class system outputs with their own schema, lifecycle, and compliance rules. Unstructured log lines, LLM chain-of-thought blobs, or ad-hoc debug prints cannot satisfy Palantir integration or high-assurance review requirements.

Phase 1 must produce traces that are:

- **Structured** — machine-parseable JSON via Pydantic models.
- **Complete** — capture inputs considered, reasoning steps, and the resulting action.
- **Correlatable** — linkable to simulation runs, agents, ticks, and Ontology objects.
- **Deterministic** — reproducible given the same observation and agent state.
- **Immutable** — append-only once recorded; corrections produce new traces, not edits.

---

## Decision

ADSL Phase 1 will implement a dedicated **AuditTrace system** in `src/adsl/explainability/` (generation utilities) backed by the canonical **`ADSL_AuditTrace` Pydantic model** in `src/adsl/models.py`.

### 1. Canonical model: `ADSL_AuditTrace`

All agent decisions emit an `ADSL_AuditTrace` instance containing at minimum:

| Field group | Purpose |
|-------------|---------|
| **Identity** | `trace_id`, `run_id`, `agent_id`, `agent_side`, `simulation_tick` |
| **Temporal** | `recorded_at` (UTC timestamp) |
| **Decision context** | `decision_category`, `inputs_considered` |
| **Reasoning** | Ordered `reasoning_steps` (each with `step_index`, `description`, `evidence`) |
| **Outcome** | `action_summary`, `action_type`, `target_id` |
| **Integrity** | `schema_version` for forward-compatible evolution |

### 2. Generation system

- Agents build traces via a shared helper (`AuditTraceBuilder` in `src/adsl/explainability/`) or by constructing `ADSL_AuditTrace` directly.
- The base `Agent` class in `src/adsl/agents/base.py` validates trace presence and non-emptiness at the `act()` integration point.
- `structlog` emits trace events in structured JSON alongside model persistence; logs supplement but do not replace the canonical model.

### 3. Persistence and correlation

- Each `ADSL_SimulationRun` correlates to a collection of `ADSL_AuditTrace` records keyed by `run_id`.
- Traces are append-only within a run. Re-decisions in replay/testing produce new `trace_id` values.
- Palantir Ontology mapping (Phase 1) will treat `ADSL_AuditTrace` as a first-class object type in `src/adsl/ontology/` (implementation deferred to integration directive).

### 4. Explainability contract (agent compliance)

Every agent `decide()` must:

1. Return a `DecisionResult` containing a validated `ADSL_AuditTrace`.
2. Include at least one `reasoning_step`.
3. Populate `inputs_considered` with the observation fields material to the decision.
4. Set `action_summary` to a human-readable description of the chosen action.
5. Use stable `decision_category` values from the Phase 1 controlled vocabulary (e.g., `TARGET_SELECTION`, `ROUTE_ADAPTATION`, `RESOURCE_REALLOCATION`, `NO_ACTION`).

The simulation engine (forthcoming) must reject decisions failing validation.

---

## AuditTrace Lifecycle

```
Observation ──► perceive() ──► decide() ──► ADSL_AuditTrace + Action
                                              │
                                              ▼
                                         act() validates trace
                                              │
                                              ▼
                              SimulationEngine.record(trace)
                                              │
                                              ▼
                              structlog structured emission
                                              │
                                              ▼
                              Palantir Ontology sync (Phase 1 integration)
```

---

## Rationale

### 1. Defense-grade auditability

Structured traces with explicit reasoning steps support after-action review, compliance audits, and red-team analysis without reverse-engineering agent internals.

### 2. Palantir Ontology alignment

A canonical Pydantic model maps cleanly to Ontology object types and properties. Unstructured logs require lossy ETL and cannot guarantee field completeness.

### 3. Separation from logging

`structlog` handles operational telemetry (latency, errors, engine events). `ADSL_AuditTrace` captures decision provenance. Conflating the two degrades both.

### 4. Testability

Golden-file tests can assert trace shape and reasoning content. Property tests can verify mandatory fields. Determinism checks compare traces across replays.

### 5. Evolution without breaking audit history

`schema_version` on each trace allows schema upgrades while preserving historical records and migration paths.

---

## Consequences

### Positive

- Every agent decision produces a reviewable, structured artifact.
- Palantir integration has a stable, typed source object.
- Reasoning quality becomes testable and measurable.
- Analysts can filter traces by agent, tick, category, or target.

### Negative / Trade-offs

- Agents carry trace-building overhead on every decision.
- Schema changes require version management and migration consideration.
- Verbose traces increase storage volume (acceptable for Phase 1 MVP scope).
- LLM-generated reasoning (if introduced later) must be constrained to the same schema—free-form chain-of-thought is insufficient alone.

### Neutral

- `structlog` remains in use for operational logging; it is complementary, not replaced.
- Full explainability UI is out of Phase 1 scope; traces are API- and Ontology-ready.

---

## Alternatives Considered

| Alternative | Reason Not Selected (Phase 1) |
|-------------|-------------------------------|
| **Simple logging only** | Unstructured logs lack schema guarantees, complicate Palantir mapping, and fail compliance completeness checks |
| **LLM chain-of-thought only** | Non-deterministic, unstructured, difficult to validate; unsuitable as sole audit artifact in defense contexts |
| **OpenTelemetry spans** | Good for distributed tracing, not semantically rich enough for agent reasoning provenance |
| **Framework-native callbacks (LangChain etc.)** | Prohibited by ADR-002; opaque and not domain-specific |
| **Database-only audit table without Pydantic model** | Loses in-memory validation, test ergonomics, and Ontology SDK type generation benefits |

---

## Compliance Rules for All Agents

1. **No silent decisions** — `DecisionResult.audit_trace` must be present and pass `ADSL_AuditTrace` validation.
2. **Minimum reasoning** — `reasoning_steps` must contain ≥ 1 entry with non-empty `description`.
3. **Input disclosure** — `inputs_considered` must list the observation fields that influenced the decision (redacted per fog-of-war rules, not omitted).
4. **Deterministic traces** — Identical inputs and agent state produce equivalent traces (same steps, same action summary, same action type).
5. **Controlled vocabulary** — `decision_category` and `action_type` must use Phase 1 enum values; free-form categories require ADR amendment.
6. **No post-hoc mutation** — Once `SimulationEngine.record()` accepts a trace, it is immutable.
7. **Base class enforcement** — All agents inherit from `src/adsl/agents/base.py` and pass through `act()` validation before the engine applies actions.
8. **Schema version** — Every trace must set `schema_version` (Phase 1 default: `"1.0"`).

---

## Implementation Notes (Phase 1)

| Component | Location | Status |
|-----------|----------|--------|
| `ADSL_AuditTrace` model | `src/adsl/models.py` | Initial version in this directive |
| `AuditTraceBuilder` helper | `src/adsl/explainability/trace.py` | Initial version in this directive |
| Trace validation | `src/adsl/agents/base.py` | Integrated at `act()` |
| Trace persistence | `src/adsl/simulation/` | Deferred to simulation engine directive |
| Ontology object mapping | `src/adsl/ontology/` | Deferred to Palantir integration directive |

---

## References

- ADR-001: Python 3.11+ as Primary Implementation Language
- ADR-002: Custom Lightweight Multi-Agent System
- ADSL Phase 1 Project Charter — Non-Negotiable Constraints (explainability, auditability)
- [Pydantic v2 documentation](https://docs.pydantic.dev/latest/)
- [structlog documentation](https://www.structlog.org/)
- [Palantir Ontology SDK](https://www.palantir.com/docs/foundry/ontology-sdk/overview/)