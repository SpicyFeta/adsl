# ADSL Analytics & Insights

**Increments 9 + 13** — Automated analysis that turns ADR-009 run bundles into actionable, explainable insights.

---

## Overview

The `adsl.analytics` module reads **only** from ADR-009 `run_bundle.json` data (network state, audit traces, summary statistics). It does not mutate simulation state. Every finding includes an `evidence` block traceable to raw data: trace IDs, entity IDs, tick ranges, and counts.

| Capability | Module | Output |
|------------|--------|--------|
| Bottleneck detection | `bottlenecks.py` | Structural chokepoints by degree and metadata |
| Vulnerability ranking | `bottlenecks.py` | Nodes scored by status, Red pressure, adjacency |
| Node risk scoring | `risk.py` | Key nodes 0–100 with Red interdiction exposure |
| Route risk scoring | `risk.py` | Per-route 0–100 risk with attack trace refs |
| Corridor risk scoring | `risk.py` | Aggregated risk by `metadata.corridor` |
| Red behavior patterns | `red_patterns.py` | Target focus, rotation, pacing, timing/disruption zones |
| Recommended focus areas | `report.py` | Prioritized analyst attention areas with evidence |
| What-if comparison | `what_if.py` | Metric + insight deltas across runs |
| Full report | `report.py` | Structured JSON insight report |

---

## Interpreting Risk Scores

All scores are **0–100 heuristic rankings**, not probabilities. Higher = more analyst attention warranted.

| Score range | Severity | Typical meaning |
|-------------|----------|-----------------|
| 70–100 | Critical | Destroyed/degraded asset, heavy Red pressure, or corridor largely closed |
| 45–69 | High | Contested chokepoint, sustained attacks, or structural bottleneck |
| 20–44 | Medium | Elevated exposure but network still functional |
| 0–19 | Low | Filtered out of ranked lists |

**Node risk** combines: chokepoint metadata, strategic value, node degree, Red node attacks, adjacent route status.

**Route risk** combines: route status, chokepoint flag, metadata risk level, Red attack count, endpoint node vulnerability.

**Corridor risk** aggregates route scores with closure fraction weighting.

---

## CLI Usage

Installed aliases (after `pip install -e ".[dev]"`):

```bash
adsl-analyze --scenario alpine-valley-v3 --ticks 50
adsl-compare --specs data/analyst/pacing_compare.json --what-if
```

### Single-run insights

```bash
# Live run
python scripts/analyze_run.py --scenario alpine-valley-v3 --seed 42 --ticks 50

# From existing export
python scripts/analyze_run.py --from-export exports/<run_id>

# Full Markdown report
python scripts/analyze_run.py --scenario alpine-valley-v3 --markdown

# Structured JSON
python scripts/analyze_run.py --from-export exports/<run_id> --json --write reports/insights.json
```

### What-if comparison

```bash
python scripts/compare_runs.py --specs data/analyst/pacing_compare.json --what-if
python scripts/compare_runs.py --specs data/analyst/pacing_compare.json --what-if --markdown
```

---

## Export Bundle Integration

ADR-009 exports now include:

| File | Description |
|------|-------------|
| `insights.json` | Machine-readable insight report |
| `insights_report.md` | Human-readable Markdown report |

Generated automatically by `export_run_bundle()` alongside `executive_summary.md`.

---

## Dashboard

The visualization dashboard exposes insights via:

- **API:** `GET /api/insights/{run_id}`
- **UI:** Automated Insights panel (key insights, critical highlights, corridor risk, focus areas, node risk)

Launch with:

```bash
python scripts/launch_dashboard.py --export-dir exports
```

---

## Example Insights

From `alpine-valley-v3` seed 42 (50 ticks), typical outputs include:

**Key insights (executive summary bullets):**

1. `5 routes closed at end of run — review alternate paths.`
2. `Corridor 'north_ridge' composite risk 58/100 — 3 closed, 0 contested, 22 Red attacks.`
3. `Red concentrated 42% of route attacks on R-NR-PASS-01 (17 strikes).`

**Critical highlight (with evidence):**

```json
{
  "insight_type": "corridor_risk",
  "severity": "high",
  "entity_id": "north_ridge",
  "summary": "Corridor 'north_ridge' composite risk 58/100 — 3 closed, 0 contested, 22 Red attacks.",
  "evidence": {
    "source": "network_state.routes.metadata.corridor",
    "entity_ids": ["R-NR-01", "R-NR-02", "..."],
    "trace_ids": ["b4788832-c166-41f9-8fca-703e0102752f", "..."],
    "counts": {"composite_risk_score": 58.2, "closed_routes": 3}
  }
}
```

**Red pattern:**

- `route_focus` — Red concentrated strikes on a single corridor pass
- `conservative_pacing` — High NO_ACTION rate when cooldowns are long
- `sustained_pressure` — Attacks on ≥35% of ticks when pacing is aggressive

**What-if (fast vs slow Red pacing):**

- Metric deltas: more `ATTACK_ROUTE`, fewer `NO_ACTION` in fast pacing
- Insight deltas: corridor risk shifts, new critical highlights on chokepoint routes
- Recommendations: investigate increased pressure on specific corridors

---

## Traceability Contract

Every insight object includes:

| Field | Purpose |
|-------|---------|
| `evidence.source` | Which bundle section(s) informed the finding |
| `evidence.trace_ids` | Audit trace IDs (up to 20) for Red/Blue decisions |
| `evidence.entity_ids` | Node, route, corridor, or agent IDs |
| `evidence.ticks` | Simulation ticks where pattern observed |
| `evidence.counts` | Numeric values used in scoring |

Analysts can follow `trace_ids` into `audit_traces.jsonl` or `run_bundle.json` → `audit_traces` for full reasoning steps.

---

## Python API

```python
from adsl.analytics import generate_insights_report, compare_what_if
from adsl.export.runner import load_run_bundle_from_export

bundle = load_run_bundle_from_export("exports/<run_id>")
report = generate_insights_report(bundle)

print(report["key_insights"])
for highlight in report["findings"]["critical_highlights"]:
    print(highlight["summary"], highlight["evidence"]["trace_ids"][:3])
```

---

## Limitations (v1)

| Limitation | Notes |
|------------|-------|
| Rule-based only | No ML; heuristics may miss domain-specific doctrine |
| Post-run analysis | No real-time per-tick analytics during simulation |
| Metadata-dependent | Corridor/chokepoint scoring requires scenario metadata |
| Static thresholds | Severity cutoffs (45/70) are not scenario-adaptive |
| What-if scope | Compares insight deltas, not full trace-by-trace diff |
| Dashboard simplicity | Text panels only — no dedicated insight charts |

---

## Related Documentation

- [Visualization](visualization.md) — Map and metrics dashboard
- [Demo Playbook](demo-playbook.md) — Workshop flow
- [Architecture Overview](architecture-overview.md) — Module boundaries
- [ADR-014](decisions/ADR-014-analytics-insights.md) — Analytics architecture decision