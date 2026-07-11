# ADSL — Getting Started

**Time to first run:** ~5 minutes  
**Time to understand core value:** ~7 minutes (with [what-is-adsl.md](what-is-adsl.md) and [positioning.md](positioning.md))

---

## Prerequisites

- Python 3.11+
- Git (to clone the repository)
- Optional: [uv](https://docs.astral.sh/uv/) or pip

---

## 1. Install

```bash
git clone <repository-url>
cd adsl-phase1
pip install -e ".[dev]"
```

Verify:

```bash
python -m pytest -q
# Expected: 138 passed
```

---

## 2. Run Your First Simulation

```bash
python scripts/run_simulation.py --quiet-logs
```

This runs the default **Kessari Strait** stress scenario (50 ticks, seed 42). You will see:

- Run status and trace counts
- End-of-run network state (nodes/routes)
- Sample audit traces with reasoning steps
- Ontology payload object counts (offline)

---

## 3. Try a Workshop-Friendly Scenario

```bash
python scripts/run_simulation.py --scenario island-chokepoint-v2 --ticks 100 --seed 42 --quiet-logs
```

Island chokepoint is designed for longer demos — nodes typically remain operational at 100 ticks while routes show contestation.

---

## 4. Export Results for Analysts

```bash
python scripts/export_run.py --scenario island-chokepoint-v2 --ticks 100 --export-dir exports --quiet-logs
```

Output directory contains:

| File | Purpose |
|------|---------|
| `manifest.json` | Bundle index |
| `run_bundle.json` | Complete machine-readable run |
| `audit_traces.jsonl` | One trace per line |
| `simulation_events.jsonl` | One event per line |
| `executive_summary.md` | Human-readable summary |
| `insights.json` | Automated analytics (when generated) |

---

## 5. Generate Analytics Insights

From a fresh run:

```bash
python scripts/analyze_run.py --scenario alpine-valley-v3 --ticks 50 --quiet-logs
```

From an existing export:

```bash
python scripts/analyze_run.py --from-export exports
```

Console entry points (after `pip install -e ".[dev]"`):

```bash
adsl-analyze --scenario alpine-valley-v3 --ticks 50
```

See [analytics-insights.md](analytics-insights.md) for risk scores, focus areas, and what-if comparison.

---

## 6. Compare Two Runs (What-If)

```bash
python scripts/compare_runs.py \
  --scenario alpine-valley-v3 --seed 42 --label baseline \
  --scenario alpine-valley-v3 --seed 99 --label alt-seed \
  --ticks 50 --quiet-logs
```

What-if mode (insight-level comparison):

```bash
python scripts/compare_runs.py --what-if --markdown \
  --scenario alpine-valley-v3 --seed 42 --label baseline \
  --scenario alpine-valley-v3 --seed 99 --label alt-seed \
  --ticks 50 --quiet-logs
```

For pacing overrides, use a `--specs` JSON file (see [analytics-insights.md](analytics-insights.md)). Or use `adsl-compare` for the same interface.

---

## 7. Visualize (Dashboard)

After exporting at least one run:

```bash
python scripts/launch_dashboard.py --export-dir exports
```

Opens `http://127.0.0.1:8765/` — network map with risk overlay, metrics, run switcher, comparison view, and presentation mode. See [visualization.md](visualization.md).

---

## 8. Workshop Collaboration (Optional)

Create a file-based session for team annotations and run linking:

```bash
python scripts/collab_workshop.py session-create "Q3 Workshop" --facilitator "Lead Analyst"
python scripts/collab_workshop.py run-link --session <session_id> --export-dir exports --author "Lead Analyst"
python scripts/collab_workshop.py annotate-add --session <session_id> --run-id <run_id> \
  --author "Lead Analyst" --text "Corridor B shows sustained Red pressure"
```

See [collaboration-workflows.md](collaboration-workflows.md).

---

## 9. Foundry Integration (Optional, Local by Default)

Check integration status (no credentials required):

```bash
python scripts/foundry_status.py
```

Import a scenario dataset locally:

```bash
python scripts/foundry_import.py --scenario island-chokepoint-v2
```

Export results with lineage metadata:

```bash
python scripts/foundry_export.py --from-export exports
```

Live HTTP mode requires `ADSL_FOUNDRY_ENABLED` and credentials — see [foundry-integration.md](foundry-integration.md).

---

## 10. Scale & Performance (Optional)

For stress testing beyond 100 ticks, enable scale mode (up to 500 ticks per ADR-012):

```bash
# Engine-only benchmark (isolates simulation loop from export overhead)
python scripts/benchmark_runs.py --scenario continental-mega-scale-v5 --ticks 200 --scale --engine-only

# Compare against historical baselines
python scripts/benchmark_compare.py --scenario continental-mega-scale-v5 --ticks 200 --scale --engine-only

# Parallel batch export
python scripts/batch_export.py --suite data/performance/benchmark_suite.json --workers 4 --scale
```

See [scale-performance.md](scale-performance.md).

---

## Common CLI Flags

| Flag | Description |
|------|-------------|
| `--scenario` | Scenario ID from registry |
| `--ticks` | Tick count (max 100 default; 500 with `--scale`) |
| `--seed` | Reproducibility seed |
| `--export-dir` | Write ADR-009 bundle after run |
| `--quiet-logs` | Suppress JSON logs (recommended for demos) |
| `--scale` | Enable scale mode (batch/benchmark/profile scripts) |
| `--sync-ontology` | Placeholder sync only — **not live Foundry** |

---

## Scenario Quick Reference

| ID | Best for |
|----|----------|
| `kessari-strait-v1` | Stress testing, fast degradation |
| `island-chokepoint-v2` | Workshops, sustained demos |
| `alpine-valley-v3` | Dual-corridor comparison, Red pacing demos |
| `continental-grid-scale-v4` | Scale stress (grid topology) |
| `continental-mega-scale-v5` | Mega-scale performance benchmarks |

---

## Next Steps

| Goal | Document |
|------|----------|
| What ADSL is | [what-is-adsl.md](what-is-adsl.md) |
| Understand positioning | [positioning.md](positioning.md) |
| Capabilities & limitations | [capabilities-and-limitations.md](capabilities-and-limitations.md) |
| Full capability list | [capabilities-matrix.md](capabilities-matrix.md) |
| Run a workshop | [demo-playbook.md](demo-playbook.md) |
| Architecture depth | [architecture-overview.md](architecture-overview.md) |
| Current status | [status.md](status.md) |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `No module named adsl` | Run `pip install -e ".[dev]"` from project root |
| Unknown scenario | Use IDs from [scenario registry](../data/synthetic/scenario_registry.json) |
| Verbose JSON output | Add `--quiet-logs` |
| Dashboard shows no runs | Export a run to `--export-dir` first |
| Ticks > 100 rejected | Add `--scale` on batch/benchmark/profile scripts, or use `SimulationEngine(scale_mode=True)` |