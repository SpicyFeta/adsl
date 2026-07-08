# ADR-001: Python 3.11+ as Primary Implementation Language

**Status:** Accepted  
**Date:** 2026-07-08  
**Deciders:** ADSL Engineering Team, Project Management  
**Phase:** Phase 1 — Contested Logistics Stress Test MVP

---

## Context

ADSL Phase 1 requires a language and runtime that supports rapid MVP delivery while meeting defense and intelligence use-case standards for maintainability, auditability, and integration with external systems—particularly Palantir's Ontology.

The Phase 1 workload is dominated by:

- Structured data modeling for logistics networks, agent state, and simulation events.
- Custom multi-agent decision logic (Red and Blue) without heavy third-party agent frameworks.
- Integration with the Palantir Ontology SDK.
- Structured logging and custom audit-trace generation for explainability.
- Automated testing with high coverage expectations from project inception.

We need a language with mature ecosystem support for these concerns, strong typing discipline, and broad adoption within the defense technology community.

---

## Decision

**Python 3.11 or later** is the primary implementation language for ADSL Phase 1.

All production code, tests, and tooling in this phase will target Python 3.11+ as the minimum supported version.

---

## Rationale

### 1. Ecosystem alignment with confirmed stack

Python is the native language for every confirmed Phase 1 dependency:

- **Pydantic v2** — industry-standard runtime validation and schema definition.
- **structlog** — structured, machine-parseable logging for audit trails.
- **pytest / pytest-cov** — mature testing and coverage tooling.
- **Palantir Ontology SDK** — official SDK with first-class Python support.

Choosing Python avoids cross-language FFI overhead and reduces integration risk for the Palantir layer.

### 2. Custom agent logic without framework lock-in

Phase 1 explicitly prohibits heavy agent frameworks (LangChain, CrewAI, AutoGen). Python's simplicity and expressiveness make it well-suited for building a purpose-built, lightweight multi-agent system where we control every decision loop, state transition, and trace emission.

### 3. Explainability and auditability

Defense and intelligence customers require decisions to be inspectable and reproducible. Python's readability—combined with Pydantic models for explicit schemas and structlog for structured output—supports the "reasoning trace as a first-class artifact" requirement without ceremony.

### 4. Python 3.11+ specifically

Version 3.11 delivers meaningful performance improvements (CPython optimizations, faster startup) and quality-of-life features (improved error messages, `tomllib`, `ExceptionGroup`) that benefit long-running simulations and test suites. Setting 3.11 as the floor keeps us on a supported, modern baseline without chasing bleeding-edge releases.

### 5. Team velocity and hiring

Python is widely understood across defense tech, data engineering, and simulation teams. This reduces onboarding friction and supports the incremental, directive-driven development model for Phase 1.

### 6. Container reproducibility

Python 3.11+ is well-supported in official Docker base images, enabling the Docker-based reproducibility requirement with minimal configuration.

---

## Consequences

### Positive

- Single-language codebase for agents, simulation, ontology integration, and explainability.
- Direct use of Palantir Ontology SDK without language bridges.
- Fast iteration on MVP features with strong test and type-validation tooling.
- Broad talent pool and extensive library ecosystem for future phases.

### Negative / Trade-offs

- Python's GIL limits true CPU parallelism for compute-heavy simulation loops; Phase 1 scope (lightweight contested logistics, not large-scale physics) mitigates this.
- Runtime performance is lower than compiled languages; acceptable for Phase 1 MVP demonstration scope.
- Dependency management discipline is required to avoid supply-chain and version-conflict issues; mitigated by `uv` lockfiles and pinned Docker images.

### Neutral

- Future phases may introduce performance-critical components in other languages behind clean interfaces; this ADR does not preclude that, but Phase 1 remains Python-only.

---

## Alternatives Considered

| Alternative | Reason Not Selected (Phase 1) |
|-------------|-------------------------------|
| **Rust** | Higher development cost for MVP; Palantir SDK integration less straightforward; team velocity risk. |
| **Go** | Weaker ecosystem for scientific/simulation modeling and Pydantic-equivalent validation. |
| **Java / Kotlin** | Heavier boilerplate; slower MVP iteration; less common in agentic simulation prototyping. |
| **TypeScript (Node)** | Palantir SDK and defense simulation ecosystems are predominantly Python-oriented for this class of work. |

---

## Compliance

- All `pyproject.toml` metadata enforces `requires-python = ">=3.11"`.
- Dockerfile base image uses `python:3.11-slim` (or later 3.11.x patch).
- CI and local development must validate against Python 3.11+.

---

## References

- [Python 3.11 release notes](https://docs.python.org/3/whatsnew/3.11.html)
- [Pydantic v2 documentation](https://docs.pydantic.dev/latest/)
- [Palantir Ontology SDK](https://www.palantir.com/docs/foundry/ontology-sdk/overview/)
- ADSL Phase 1 Project Charter (internal)