# ADSL Workshop Demo Playbook

**Audience:** Facilitator or participant unfamiliar with the codebase  
**Duration:** ~25 minutes (under 30-minute target)  
**Prerequisites:** Python 3.11+, project cloned to local machine

---

## Before You Begin (2 minutes)

Confirm you are in the project root and dependencies are installed:

```bash
cd adsl-phase1
pip install -e ".[dev]"
```

Verify the test suite passes (optional but recommended):

```bash
python -m pytest -q
```

Expected: `138 passed`.

---

## Part 1 — Baseline Stress Test (5 minutes)

Run the original Kessari Strait scenario at full 100-tick stress:

```bash
python scripts/run_simulation.py --scenario kessari-strait-v1 --ticks 100 --seed 42 --quiet-logs
```

### What to highlight

1. **Simulation Run** — status `COMPLETED`, 1,100 audit traces (11 agents × 100 ticks)
2. **Network State** — heavy node destruction (stress-test scenario by design)
3. **Audit Trace Summary** — action mix: reroutes, hardens, attacks, reallocations
4. **Sample traces** — each decision has reasoning steps citing ADR policies
5. **Ontology Payload** — six object types mapped offline (sync disabled)

**Talking point:** Phase 1 delivered the core Red/Blue contested-logistics loop with full auditability. This scenario saturates quickly — useful for stress testing, less ideal for extended demos.

---

## Part 2 — Workshop Scenario (5 minutes)

Run the Phase 2 island chokepoint scenario designed for slower degradation:

```bash
python scripts/run_simulation.py --scenario island-chokepoint-v2 --ticks 100 --seed 42 --quiet-logs
```

### What to highlight

1. **All nodes remain OPERATIONAL** at 100 ticks (0% destruction)
2. **Route contestation** — mix of OPEN and CLOSED routes shows corridor pressure without network collapse
3. **Red focus** — route interdiction only (no fire-support node strikes in v2)
4. **Blue adaptation** — reroutes dominate; agents cite ADR-005 P1 closed-route policy

**Talking point:** Scenario v2 was engineered for workshop demos where stakeholders need visible adaptation over time, not immediate network collapse.

### Optional — Dual-Corridor Alpine Scenario (Phase 3 Inc 2)

Run the third scenario to compare parallel ridge corridors:

```bash
python scripts/run_simulation.py --scenario alpine-valley-v3 --ticks 100 --seed 42 --quiet-logs
```

**What to highlight:**

1. **Parallel north-ridge and south-ridge corridors** — distinct topology from coastal (v1) and island (v2) scenarios
2. **Route contestation across both passes** — OPEN, CONTESTED, and CLOSED routes visible at 100 ticks
3. **Red pacing rotation** — ADR-010 cooldowns rotate strikes between north and south patrol corridors

**Talking point:** Scenario v3 demonstrates corridor failover and Red variety mechanics on an inland dual-corridor network.

---

## Part 3 — Export Workshop Bundle (5 minutes)

Produce an ADR-009 export bundle in one command:

```bash
python scripts/export_run.py --scenario island-chokepoint-v2 --ticks 100 --seed 42 --export-dir exports --quiet-logs
```

The script prints the export path, e.g.:

```
Export written: exports/<run_id>/
```

### Bundle contents

| File | Purpose |
|------|---------|
| `manifest.json` | Bundle index, schema version, metadata |
| `run_bundle.json` | Complete machine-readable run data |
| `audit_traces.jsonl` | One audit trace per line |
| `simulation_events.jsonl` | One simulation event per line |
| `executive_summary.md` | Human-readable workshop summary |

**Talking point:** Stakeholders can ingest these artifacts without re-running the simulation or parsing raw CLI output. When Foundry credentials arrive, the same payload structure maps to Ontology objects (ADR-006/009).

---

## Part 4 — Inspect Artifacts (5 minutes)

Open the exported directory and review:

```bash
# Windows
dir exports\<run_id>
type exports\<run_id>\executive_summary.md

# macOS / Linux
ls exports/<run_id>/
cat exports/<run_id>/executive_summary.md
```

### Inspection checklist

- [ ] `manifest.json` shows `export_schema_version: "1.0"` and `source_system: "ADSL_PHASE2"`
- [ ] `executive_summary.md` readable without code knowledge
- [ ] `audit_traces.jsonl` contains reasoning steps per agent decision
- [ ] `simulation_events.jsonl` includes `ACTION_RECORDED` and tick lifecycle events

**Talking point:** Export bundles are the offline workshop path. Live Foundry sync uses the same mapper payloads when ADR-007 is activated.

---

## Part 5 — Phase 2/3 Mechanics Demo (5 minutes)

Demonstrate hardening v2, deconfliction, and Red pacing without reading source code:

### Hardening v2 (ADR-008)

Re-run Kessari with logs enabled to show a harden event:

```bash
python scripts/run_simulation.py --scenario kessari-strait-v1 --ticks 30 --seed 42
```

In the audit trace summary, look for `HARDEN` actions. Blue traces cite **ADR-008** and `harden_level=1`. The first subsequent `ATTACK_ROUTE` on that route is **absorbed** (route status unchanged; `harden_level` decrements).

### Deconfliction (ADR-008)

Explain: when two agents target the same route or node in one tick, the first agent (Red before Blue, lexicographic by agent ID) wins. The second action is **suppressed** with an `ACTION_SUPPRESSED` event — still auditable, but not applied.

**Talking point:** Deterministic conflict resolution produces reproducible golden traces for defense review.

### Red agent variety (ADR-010)

In the audit trace summary, look for Red `NO_ACTION` traces citing **ADR-010** with "strike cooldown active" or "strike budget exhausted". Red agents pace strikes across ticks and rotate among patrol routes.

**Talking point:** Phase 3 Increment 1 adds auditable pacing without changing engine orchestration or Blue policies.

---

## Part 6 — Analyst Workflows (optional, 5 minutes)

Compare runs across seeds, scenarios, or Red pacing configurations:

```bash
python scripts/compare_runs.py --scenario alpine-valley-v3 --seed 42 --label baseline --scenario alpine-valley-v3 --seed 99 --label alt-seed --ticks 50 --quiet-logs
```

Batch-export a workshop comparison set:

```bash
python scripts/batch_export.py --specs data/analyst/example_batch.json --export-dir exports/workshop-batch --quiet-logs
```

**Outputs:** `batch_manifest.json`, `comparison_summary.md`, and per-run ADR-009 bundles under the export directory.

**Red pacing comparison** — use `data/analyst/pacing_compare.json` to compare default vs fast vs slow cooldown on the same seed.

**Talking point:** Analysts can compare degradation and agent action profiles without re-parsing raw CLI output.

---

## Part 7 — Visualization Dashboard (optional, 3 minutes)

After exporting a run, launch the web dashboard:

```bash
python scripts/launch_dashboard.py --export-dir exports
```

Walk through the network map, filters (contested routes, bottlenecks), and run switcher when multiple exports exist.

**Talking point:** Visualization is optional and read-only — simulation and audit data remain in ADR-009 exports.

See [`docs/visualization.md`](visualization.md) for full usage.

---

## Part 8 — Palantir Integration Status (3 minutes)

State clearly for the audience:

| Capability | Status |
|------------|--------|
| Ontology object mapping (6 types) | **Ready** — offline payloads generated every run |
| Export bundles for workshop | **Ready** — ADR-009 |
| Placeholder sync (`--sync-ontology`) | **Ready** — synthetic RIDs, no network |
| Live Foundry SDK | **Not active** — awaiting credentials per ADR-007 |

To show placeholder sync (optional):

```bash
python scripts/run_simulation.py --scenario island-chokepoint-v2 --ticks 50 --sync-ontology --quiet-logs
```

Output shows `Placeholder RIDs` count — not live Foundry writes.

**Talking point:** Do not claim live Palantir integration until `FOUNDRY_URL`, `FOUNDRY_TOKEN`, and `ONTOLOGY_RID` are configured and ADR-007 is activated.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Dataset not found` | Run from project root; check `data/synthetic/` exists |
| `No module named adsl` | Run `pip install -e ".[dev]"` from project root |
| `max_ticks` error | Use `--ticks` ≤ 100 |
| Unknown scenario | Use `kessari-strait-v1`, `island-chokepoint-v2`, or `alpine-valley-v3` |
| Verbose JSON logs | Add `--quiet-logs` |

---

## Demo Close — Key Messages

1. ADSL simulates contested logistics with **full audit traces** for every agent decision.
2. Phase 2 adds **workshop exports**, **multi-scenario support**, and **material hardening/deconfliction**.
3. Palantir Ontology mapping is **ready offline**; live sync is **prepared but gated**.
4. Phase 3 analyst workflows support multi-run comparison and batch export offline.
5. Live Foundry sync and demo surface remain stakeholder-gated.

---

## Reference

- Handover: [`docs/phase2-handover.md`](phase2-handover.md)
- ADR index: [`docs/decisions/README.md`](decisions/README.md)
- Environment template: [`.env.example`](../.env.example)