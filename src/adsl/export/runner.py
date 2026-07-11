# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Simulation run execution helpers for analyst workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from adsl.export.bundle import build_run_bundle
from adsl.models import ADSL_ScenarioPackage, ADSL_SimulationRun
from adsl.simulation.engine import SimulationEngine
from adsl.simulation.loader import load_scenario_package
from adsl.simulation.registry import resolve_scenario_path

DEFAULT_SYNTHETIC_DIR = Path(__file__).resolve().parents[3] / "data" / "synthetic"


@dataclass(frozen=True)
class RunSpec:
    """Specification for a single simulation run in a comparison or batch."""

    scenario_id: str
    seed: int = 42
    ticks: int = 50
    label: str | None = None
    red_pacing_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)

    def display_label(self) -> str:
        return self.label or f"{self.scenario_id}/seed={self.seed}"


@dataclass
class RunResult:
    """Outcome of executing a RunSpec."""

    spec: RunSpec
    bundle: dict[str, Any]
    dataset_path: Path


def apply_red_pacing_overrides(
    package: ADSL_ScenarioPackage,
    overrides: dict[str, dict[str, Any]],
) -> ADSL_ScenarioPackage:
    """Return a copy of the package with Red force element metadata patched."""
    if not overrides:
        return package

    patched_red: list = []
    for element in package.red_force_elements:
        element_overrides = overrides.get(element.element_id)
        if element_overrides:
            merged_metadata = {**element.metadata, **element_overrides}
            patched_red.append(element.model_copy(update={"metadata": merged_metadata}))
        else:
            patched_red.append(element)

    return package.model_copy(update={"red_force_elements": patched_red})


def execute_run(
    spec: RunSpec,
    *,
    synthetic_dir: Path | None = None,
    quiet_logs: bool = True,
    scale_mode: bool = False,
) -> tuple[SimulationEngine, RunResult]:
    """Execute one simulation from a RunSpec and build an ADR-009 run bundle."""
    base_dir = synthetic_dir or DEFAULT_SYNTHETIC_DIR
    dataset_path = resolve_scenario_path(spec.scenario_id, synthetic_dir=base_dir)
    package = load_scenario_package(dataset_path)
    package = apply_red_pacing_overrides(package, spec.red_pacing_overrides)

    engine = SimulationEngine(
        max_ticks=spec.ticks,
        seed=spec.seed,
        quiet_logs=quiet_logs,
        scale_mode=scale_mode,
    )
    run = engine.run_scenario(package)
    if run is None:
        raise RuntimeError(f"Simulation did not produce a run for {spec.display_label()}")

    bundle = build_run_bundle(
        run=run,
        scenario=package.scenario,
        nodes=engine.nodes,
        routes=engine.routes,
        audit_traces=engine.audit_traces,
        events=engine.events,
        scenario_package=package,
        dataset_path=dataset_path,
        ticks_executed=run.current_tick + 1,
    )
    if spec.label:
        bundle["execution"]["label"] = spec.label
    if spec.red_pacing_overrides:
        bundle["execution"]["red_pacing_overrides"] = spec.red_pacing_overrides

    result = RunResult(spec=spec, bundle=bundle, dataset_path=dataset_path)
    return engine, result


def load_run_bundle_from_export(export_run_dir: Path) -> dict[str, Any]:
    """Load a run_bundle.json from an ADR-009 export directory."""
    bundle_path = export_run_dir / "run_bundle.json"
    if not bundle_path.exists():
        raise FileNotFoundError(f"run_bundle.json not found in {export_run_dir}")

    import json

    return json.loads(bundle_path.read_text(encoding="utf-8"))