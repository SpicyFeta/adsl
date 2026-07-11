# ADSL — Use Cases

**Date:** 2026-07-08

---

## 1. Contested Logistics Workshop

**Audience:** Stakeholders unfamiliar with the codebase  
**Goal:** Demonstrate Red–Blue adaptation with full auditability in under 30 minutes

**How ADSL helps:**
- Run `island-chokepoint-v2` or `alpine-valley-v3` for visible corridor pressure without network collapse
- Export ADR-009 bundles for offline review
- Follow [demo-playbook.md](demo-playbook.md) step-by-step

**Limitation:** No live Foundry presentation unless credentials are delivered and Track B is activated.

---

## 2. Adversary Behavior Analysis

**Audience:** Analysts, red-team reviewers  
**Goal:** Understand *why* Red agents chose specific targets across ticks

**How ADSL helps:**
- Every Red decision has an `ADSL_AuditTrace` with reasoning steps
- ADR-010 pacing produces auditable cooldown and budget holds
- `compare_runs.py` contrasts attack profiles across seeds or pacing configs

**Example:**
```bash
python scripts/compare_runs.py --specs data/analyst/pacing_compare.json --ticks 50 --quiet-logs
```

---

## 3. Supply Network Stress Testing

**Audience:** Engineers, simulation validators  
**Goal:** Saturate a logistics network and observe degradation patterns

**How ADSL helps:**
- `kessari-strait-v1` designed for heavy node destruction
- 78 automated tests with golden traces guard mechanics regressions
- Seeded runs enable before/after comparison when mechanics change

---

## 4. Palantir Ontology Payload Preparation

**Audience:** Platform integrators  
**Goal:** Produce Ontology-ready objects before live Foundry is available

**How ADSL helps:**
- Six mapped object types generated every run (ADR-006)
- Export bundles include full `ontology_payload` snapshot
- SDK skeleton and ADR-007 document activation gates

**Honest boundary:** Payloads are **not validated** against a live schema until Track B delivers credentials and `validate_ontology_payload.py`.

---

## 5. Multi-Run Scenario Comparison

**Audience:** Analysts comparing policy or seed sensitivity  
**Goal:** Batch-run scenarios and compare end-state metrics

**How ADSL helps:**
- `batch_export.py` with `data/analyst/example_batch.json`
- `batch_manifest.json` + `comparison_summary.md`
- Optional dashboard run switcher

---

## 6. Defense Review & Audit

**Audience:** Compliance, review boards  
**Goal:** Defensible record of simulation decisions

**How ADSL helps:**
- Immutable traces — no post-hoc mutation
- Deconfliction suppressions are events, not silent drops
- ADR-governed design with documented policies (ADR-001–010)

---

## When Not to Use ADSL

| Need | Alternative direction |
|------|---------------------|
| Theater-wide force modeling | Dedicated wargaming / OR tools |
| Physics-based engagement | High-fidelity simulation platforms |
| LLM agent orchestration | Frameworks explicitly excluded by ADR-002 |
| Live operational data fusion | Foundry / enterprise data platform (ADSL complements, not replaces) |