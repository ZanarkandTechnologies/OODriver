"""OODrive product wrappers for agent-authored OpenSCENARIO 2.0 files."""

from __future__ import annotations

from pathlib import Path

from driverx.scenarios.openscenario2 import (
    prepare_osc2_run_dir,
    run_openscenario2,
    validate_openscenario2,
    write_openscenario2_run,
    write_openscenario2_validation,
)
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths, oodrive_command


def run_studio_validate_osc2(
    *,
    osc2_path: Path,
    sidecar_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str = "oodrive-osc2-validation",
) -> StudioCommandResult:
    validation = validate_openscenario2(osc2_path, sidecar_path=sidecar_path)
    run_dir = prepare_osc2_run_dir(output_root, run_id)
    artifacts = artifact_paths(write_openscenario2_validation(run_dir, validation))
    return StudioCommandResult(
        command="oodrive validate-osc2",
        run_id=run_dir.name,
        status=validation.status,
        artifacts=artifacts,
        next_commands=[oodrive_command(f"run-osc2 --osc2 {osc2_path}")],
        summary={
            "coverage_ratio": validation.coverage_ratio,
            "supported_feature_count": len(validation.supported_features),
            "unsupported_feature_count": len(validation.unsupported_features),
        },
        claim_boundaries=validation.claim_boundaries,
        blockers=validation.blockers,
    )


def run_studio_run_osc2(
    *,
    osc2_path: Path,
    scenario_runner_root: Path | None = None,
    output_root: Path | None = None,
    run_id: str = "oodrive-osc2-run",
    timeout_s: float = 120.0,
) -> StudioCommandResult:
    run_dir = prepare_osc2_run_dir(output_root, run_id)
    result = run_openscenario2(
        osc2_path,
        scenario_runner_root=scenario_runner_root,
        output_dir=run_dir,
        timeout_s=timeout_s,
    )
    artifacts = artifact_paths(write_openscenario2_run(run_dir, result))
    return StudioCommandResult(
        command="oodrive run-osc2",
        run_id=run_dir.name,
        status=result.status,
        artifacts=artifacts,
        next_commands=[],
        summary={
            "scenario_runner_root": str(scenario_runner_root) if scenario_runner_root else None,
            "returncode": result.returncode,
            "command": " ".join(result.command),
        },
        claim_boundaries=result.claim_boundaries,
        blockers=result.blockers,
    )


__all__ = ["run_studio_run_osc2", "run_studio_validate_osc2"]
