# ADSL — Aether Defense Simulation Layer

**Phase 1: Contested Logistics Stress Test MVP**

ADSL is a specialized, high-assurance multi-agent simulation system focused on contested logistics and intelligent wargaming. It augments platforms like Palantir by providing deep adversarial simulation capabilities with strong explainability and auditability.

Phase 1 delivers a working MVP that demonstrates Red agents intelligently attacking logistics networks and Blue agents adapting under pressure, with full reasoning traces and Palantir Ontology integration.

---

## Phase 1 Goals and Scope

### Goals

- Demonstrate Red agents that intelligently target logistics networks under contested conditions.
- Demonstrate Blue agents that adapt logistics operations under adversarial pressure.
- Produce structured, auditable reasoning traces for every major agent decision.
- Integrate with Palantir's Ontology via the official Palantir Ontology SDK.

### In Scope (Phase 1)

- Custom lightweight multi-agent simulation (no LangChain, CrewAI, AutoGen, or similar frameworks).
- Contested logistics network stress testing with synthetic datasets.
- Explainability via `structlog` and a custom AuditTrace system.
- Palantir Ontology integration layer.
- Docker-based reproducible development and deployment environments.
- High code quality, test coverage, and Architecture Decision Records (ADRs).

### Out of Scope (Phase 1)

- Advanced doctrine modeling.
- High-fidelity physics simulation.
- Large-scale (theater-wide) simulations.
- Complex human-machine teaming features.

---

## Technology Stack

| Component | Choice |
|-----------|--------|
| Language | Python 3.11+ |
| Data modeling | Pydantic v2 |
| Agent framework | Custom (lightweight) |
| Palantir integration | Official Palantir Ontology SDK |
| Testing | pytest + pytest-cov |
| Logging / audit | structlog + custom AuditTrace |
| Environment | Docker + uv |

---

## Project Structure

```
adsl-phase1/
├── src/
│   ├── adsl/
│   │   ├── agents/           # Red and Blue agent logic
│   │   ├── simulation/       # Core simulation engine
│   │   ├── ontology/         # Palantir integration layer
│   │   ├── explainability/   # Audit trace generation
│   │   └── utils/
│   └── tests/
├── data/
│   └── synthetic/            # Synthetic test datasets
├── docs/
│   ├── architecture/
│   ├── integration/
│   └── decisions/            # Architecture Decision Records (ADRs)
├── scripts/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Development Environment Setup

### Prerequisites

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) (recommended package manager)
- Docker and Docker Compose (optional, for containerized workflows)

### Local Setup (uv)

```bash
# Clone the repository
git clone <repository-url>
cd adsl-phase1

# Install dependencies (including dev tools)
uv sync --extra dev

# Run tests
uv run pytest

# Run tests with coverage report
uv run pytest --cov=adsl --cov-report=term-missing
```

### Docker Setup

```bash
# Build the development image
docker compose build

# Run tests inside the container
docker compose run --rm adsl pytest
```

---

## Current Status

| Area | Status |
|------|--------|
| Project scaffolding | Complete |
| Core dependencies | Configured (pydantic, structlog, pytest, pytest-cov) |
| Agent logic | Not started |
| Simulation engine | Not started |
| Explainability / AuditTrace | Not started |
| Palantir Ontology integration | Not started |
| Synthetic datasets | Not started |
| ADRs | ADR-001 (Python language) recorded |

**Phase 1 progress:** Initialization complete. Awaiting next directive.

---

## Documentation

- Architecture Decision Records: [`docs/decisions/`](docs/decisions/)
- Architecture docs: [`docs/architecture/`](docs/architecture/)
- Integration guides: [`docs/integration/`](docs/integration/)

---

## License

TBD — to be confirmed by project stakeholders.