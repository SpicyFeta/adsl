# ADSL Visualization Dashboard

**Increments 6 + 14** — Optional web dashboard for exploring ADR-009 exports with analytics overlay.

The dashboard reads exported run bundles and analytics insights only. It does not modify simulation data.

---

## Quick Start

```bash
# Export runs
python scripts/export_run.py --scenario alpine-valley-v3 --ticks 100 --seed 42 --export-dir exports

# Batch export for comparison
python scripts/batch_export.py --specs data/analyst/pacing_compare.json --export-dir exports --quiet-logs

# Launch dashboard
python scripts/launch_dashboard.py --export-dir exports
```

Opens `http://127.0.0.1:8765/` (use `--no-browser` to skip auto-open).

---

## Features

### Network map

| Visual encoding | Meaning |
|-----------------|---------|
| Node fill color | OPERATIONAL (green), DEGRADED (yellow), DESTROYED (red) |
| Route color | OPEN (green), CONTESTED (orange, dashed), CLOSED (red) |
| Risk ring | Orange ≥45, red ≥70 heuristic risk score |
| Bottleneck ring | Blue ring on structural chokepoints |
| Focus marker | Purple diamond on recommended focus areas |
| Risk badge | Numeric score on high-risk nodes/routes |
| Route width | Scales with risk score and Red attack count |
| Comparison highlight | Purple dashed outline for entities worsened vs baseline |

### Side panels

- **Network metrics** — destroyed nodes, action counts, status bar charts
- **Top risks** — click any item to highlight on the map
- **Automated insights** — key insights, critical highlights, corridor risk, focus areas
- **Team annotations** — collaboration comments from `annotations.json`

### Filters

| Filter | Effect |
|--------|--------|
| Contested routes only | Hide OPEN and CLOSED routes |
| Hide OPEN routes | Show CONTESTED + CLOSED only |
| High-risk only (≥45) | Filter to elevated-risk entities |
| Highlight focus areas | Emphasize recommended focus entities |
| Show bottlenecks | Blue rings on chokepoints |
| Emphasize Red activity | Size/width scales with attack count |
| Show risk score badges | Numeric labels on map |

### Run comparison

1. Export multiple runs to one directory (batch export recommended).
2. Enable **Compare Runs** in the sidebar.
3. Select a **baseline** run; the current **Run** dropdown is the comparison target.
4. Entities that worsened (status or risk ≥10 points) are highlighted in purple.
5. Summary panel shows metric deltas (destroyed nodes, closed routes).

### Presentation mode

Click **Present** in the top bar for larger typography and map — suitable for workshop projection.

---

## Architecture

```
scripts/launch_dashboard.py
    └── src/adsl/viz/server.py
            ├── /api/runs
            ├── /api/viz/{run_id}      ← bundle + analytics overlay (schema 1.1)
            ├── /api/insights/{run_id}
            ├── /api/annotations/{run_id}
            └── /api/compare?baseline=&compare=
    └── src/adsl/viz/transform.py      ADR-009 + insights → viz payload
    └── src/adsl/viz/compare.py        Two-run diff payload
viz/dashboard/                         Static HTML/CSS/JS (no build step)
```

**Data sources:** `run_bundle.json` + generated or cached `insights.json`. Analytics scores are computed at viz-payload build time if insights are not cached separately.

---

## API Endpoints

| Endpoint | Returns |
|----------|---------|
| `GET /api/runs` | Discoverable runs in export directory |
| `GET /api/viz/{run_id}` | Viz payload with `risk_score`, `analytics_overlay` |
| `GET /api/insights/{run_id}` | Full insights report |
| `GET /api/annotations/{run_id}` | Team annotations |
| `GET /api/compare?baseline=X&compare=Y` | Metric and entity diffs between runs |

### Viz payload schema (1.1) highlights

```json
{
  "schema_version": "1.1",
  "nodes": [{ "id": "...", "risk_score": 58.2, "risk_severity": "high", "is_focus_area": true }],
  "routes": [{ "id": "...", "risk_score": 72.0, "risk_severity": "critical", "corridor": "north_ridge" }],
  "analytics_overlay": {
    "recommended_focus_areas": [...],
    "top_node_risks": [...],
    "top_route_risks": [...]
  }
}
```

---

## Workshop workflow

1. Facilitator batch-exports baseline + variant runs.
2. Launch dashboard on the export directory.
3. Walk through **Focus Areas** — click each to highlight on the map.
4. Toggle **High-risk only** to isolate problem corridors.
5. Enable **Compare Runs** to show what changed between pacing variants.
6. Switch to **Present** mode for stakeholder briefing.

---

## Limitations

| Limitation | Notes |
|------------|-------|
| 2D SVG map only | No geospatial tiles or 3D |
| Lat/long layout | Nodes positioned by scenario coordinates, not real map projection |
| Post-run only | No live tick animation |
| No authentication | Local server; use `--host` carefully on shared networks |
| Comparison is visual | Full what-if analysis via `adsl-compare` CLI for detailed deltas |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No runs found | Export at least one run to `--export-dir` |
| Empty risk scores | Re-export run (insights generated on export) or ensure `insights.json` exists |
| Comparison unavailable | Need ≥2 runs in export directory |
| Port in use | `python scripts/launch_dashboard.py --port 8766` |

---

## Related

- [analytics-insights.md](analytics-insights.md) — how risk scores are computed
- [demo-playbook.md](demo-playbook.md) — workshop execution
- [collaboration-workflows.md](collaboration-workflows.md) — team annotations on exports