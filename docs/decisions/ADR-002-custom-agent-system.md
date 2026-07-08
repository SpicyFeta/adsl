# ADR-002: Custom Lightweight Multi-Agent System

**Status:** Accepted  
**Date:** 2026-07-08  
**Deciders:** ADSL Engineering Team, Project Management  
**Phase:** Phase 1 — Contested Logistics Stress Test MVP

---

## Context

ADSL Phase 1 requires Red and Blue agents that make intelligible, auditable decisions within a contested logistics simulation. Every major agent action must produce a structured reasoning trace suitable for defense and intelligence review.

Commercial multi-agent frameworks (LangChain, CrewAI, AutoGen, and similar) offer rapid prototyping but introduce concerns that conflict with Phase 1 non-negotiables:

- **Opaque decision pipelines** — framework abstractions often bury reasoning steps inside chains, graphs, or orchestration layers that are difficult to audit line-by-line.
- **Heavy dependency trees** — large transitive dependency surfaces increase supply-chain risk and complicate security review in high-assurance environments.
- **Framework-imposed patterns** — tool-calling, memory, and orchestration models may not align with contested logistics simulation semantics or Palantir Ontology integration requirements.
- **Explainability as an afterthought** — audit traces must be first-class artifacts, not log side-effects of framework callbacks.

Phase 1 scope is deliberately narrow: a bounded logistics network, Red agents that attack it intelligently, Blue agents that adapt under pressure, and full traceability. This workload does not require general-purpose LLM orchestration infrastructure.

We need a purpose-built agent architecture with explicit contracts, minimal dependencies, and trace emission wired into every decision path from day one.

---

## Decision

ADSL Phase 1 will implement a **custom lightweight multi-agent system** in `src/adsl/agents/`.

The following frameworks are **explicitly prohibited** in Phase 1:

- LangChain (and LangGraph)
- CrewAI
- AutoGen (Microsoft)
- Any similar general-purpose agent orchestration framework

Agents will conform to a minimal interface contract (defined below). The simulation engine in `src/adsl/simulation/` will orchestrate agent turns; agents will not self-orchestrate via external frameworks.

---

## Minimal Agent Interface Contract (Phase 1)

All Red and Blue agents must implement the following contract. This is the stable boundary between agent logic, the simulation engine, and the explainability layer.

### Core types (conceptual)

| Type | Responsibility |
|------|----------------|
| `AgentIdentity` | Stable identifier, side (`RED` / `BLUE`), and role label |
| `Observation` | Read-only view of simulation state visible to the agent at decision time |
| `Action` | Validated, typed intent the agent wishes to execute |
| `DecisionResult` | The chosen `Action` plus a mandatory `AuditTrace` |
| `AuditTrace` | Structured reasoning record (see ADR-003, forthcoming) |

### Interface

```python
class Agent(Protocol):
    """Minimal contract for all Phase 1 agents."""

    @property
    def identity(self) -> AgentIdentity:
        """Return stable agent identity."""

    def perceive(self, observation: Observation) -> None:
        """Ingest observation; update internal state if needed. Must not mutate simulation."""

    def decide(self, observation: Observation) -> DecisionResult:
        """
        Produce a decision and mandatory audit trace.
        Must be deterministic given the same observation and internal state.
        Must not perform side effects outside returned Action.
        """

    def reset(self) -> None:
        """Return agent to initial state for a new simulation run."""
```

### Behavioral requirements

1. **Trace mandatory** — `decide()` must always return a `DecisionResult` containing a non-empty `AuditTrace`. Silent decisions are prohibited.
2. **Determinism** — Given identical `Observation` input and agent internal state, `decide()` must produce the same `Action` and equivalent trace. Non-deterministic behavior requires explicit ADR approval and documented seeding.
3. **No hidden side effects** — Agents may not mutate simulation state directly. All state changes flow through validated `Action` objects applied by the simulation engine.
4. **Observation boundary** — Agents receive only what their side and role are permitted to observe (fog-of-war / information asymmetry enforced by the simulation layer, not by agent convention).
5. **Pydantic validation** — `Observation`, `Action`, `DecisionResult`, and `AuditTrace` are Pydantic v2 models with explicit schemas.

### Red / Blue specialization

| Agent side | Phase 1 responsibility |
|------------|--------------------------|
| **Red** | Select logistics targets (nodes, routes, depots) and attack modalities under contested conditions |
| **Blue** | Adapt logistics operations (reroute, reallocate, harden) in response to Red actions and network degradation |

Both sides share the same `Agent` interface. Side-specific logic lives in `RedAgent` and `BlueAgent` implementations; the simulation engine treats them uniformly.

### Orchestration model

```
SimulationEngine
    │
    ├── tick() ──► build Observations per agent
    │
    ├── for each agent (ordered by simulation policy):
    │       agent.perceive(observation)
    │       result = agent.decide(observation)
    │       engine.validate(result.action)
    │       engine.apply(result.action)
    │       engine.record(result.audit_trace)
    │
    └── advance simulation clock
```

The simulation engine owns turn order, state mutation, and trace persistence. Agents are stateless decision units except for explicitly managed internal memory cleared on `reset()`.

---

## Rationale

### 1. Explainability and auditability are first-class

A custom system lets us require `AuditTrace` emission at the interface level. Framework callbacks and implicit chain-of-thought storage do not give us the same guarantees for defense review.

### 2. Scope-appropriate complexity

Phase 1 agents operate on a structured logistics domain with typed actions—not open-ended tool-use against arbitrary APIs. A thin `perceive → decide` loop is sufficient and easier to test exhaustively.

### 3. Security and supply-chain posture

Avoiding heavy agent frameworks reduces dependency surface area, simplifies vulnerability scanning, and keeps the codebase reviewable by stakeholders without framework expertise.

### 4. Clean Palantir integration boundary

A custom agent layer produces domain-specific `Action` and `AuditTrace` objects that map directly to Ontology object types. Framework-specific message formats would require an extra translation layer.

### 5. Testability

Deterministic `decide()` contracts enable unit tests with fixed observations, property-based tests on action validity, and golden-file comparisons on audit traces—without mocking framework internals.

---

## Consequences

### Positive

- Full control over decision loops, trace schema, and simulation coupling.
- Smaller dependency tree; faster security and compliance review.
- Uniform Red/Blue interface simplifies simulation engine design.
- Every agent decision is explicitly testable in isolation.

### Negative / Trade-offs

- We build orchestration, validation, and agent lifecycle ourselves—no framework shortcuts.
- No out-of-the-box LLM tool-calling or memory abstractions; if LLM-backed reasoning is introduced later, it must be wrapped behind our interface.
- Less community documentation to reference; we must maintain our own agent development guide.

### Neutral

- Future phases may introduce optional LLM reasoning behind the same `Agent` interface without changing the simulation contract.
- This ADR does not prohibit using an LLM API directly (e.g., via `httpx`)—only heavy orchestration frameworks.

---

## Alternatives Considered

| Alternative | Reason Not Selected (Phase 1) |
|-------------|-------------------------------|
| **LangChain / LangGraph** | Large dependency tree; graph abstractions obscure audit trails; oriented toward LLM tool-use, not domain simulation |
| **CrewAI** | Role-based crew model does not map cleanly to turn-based logistics simulation; limited trace control |
| **AutoGen** | Multi-agent conversation model mismatches contested logistics semantics; complex runtime |
| **Custom + thin LLM wrapper** | Viable for a later ADR if LLM reasoning is required; Phase 1 agents use rule/utility-based logic first |

---

## Compliance

- No LangChain, CrewAI, AutoGen, or equivalent dependencies in `pyproject.toml`.
- All agent implementations in `src/adsl/agents/` must satisfy the `Agent` interface contract.
- Simulation engine must reject `DecisionResult` objects with missing or empty `AuditTrace`.
- Unit tests must cover `decide()` determinism and trace presence for every agent implementation.

---

## References

- ADR-001: Python 3.11+ as Primary Implementation Language
- ADSL Phase 1 Project Charter — Non-Negotiable Constraints (explainability, no heavy frameworks)
- `src/adsl/agents/` — agent implementations (forthcoming)
- `src/adsl/explainability/` — AuditTrace system (forthcoming; ADR-003)