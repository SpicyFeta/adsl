# Foundry Local Datasets (Offline Mode)

When `ADSL_FOUNDRY_ENABLED` is not set, ADSL reads and writes dataset records under this directory using the local filesystem adapter.

## Layout

```
datasets/
  scenarios/records.jsonl    # adsl_scenario_package records (import source)
  results/records.jsonl      # simulation export records (write target)
```

## Example Records

Each line in `records.jsonl` is a self-contained JSON object:

| `record_type` | Direction | Purpose |
|---------------|-----------|---------|
| `adsl_scenario_package` | Import | Full `ADSL_ScenarioPackage` + lineage |
| `adsl_simulation_run` | Export | Run metadata and summary statistics |
| `adsl_network_snapshot` | Export | End-state nodes and routes |
| `adsl_audit_trace` | Export | One immutable trace per record |
| `adsl_annotations` | Export | Team annotations (when present) |
| `adsl_insights` | Export | Automated insights report |
| `adsl_lineage` | Both | Provenance summary |

See [docs/foundry-integration.md](../../docs/foundry-integration.md) for live Foundry setup.