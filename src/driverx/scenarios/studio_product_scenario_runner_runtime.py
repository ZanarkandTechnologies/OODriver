"""OODrive wrappers for CARLA ScenarioRunner integration."""

from __future__ import annotations

from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.scenarios.scenario_runner_bridge import (
    build_scenario_runner_package,
    run_scenario_runner_package,
    write_scenario_runner_package_report,
)
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths, oodrive_command


def run_studio_scenario_runner_package(
    *,
    scenario_graph_path: Path | None = None,
    osc2_path: Path | None = None,
    sidecar_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str = "oodrive-scenario-runner-package",
) -> StudioCommandResult:
    package = build_scenario_runner_package(
        scenario_graph_path=scenario_graph_path,
        osc2_path=osc2_path,
        sidecar_path=sidecar_path,
        output_root=output_root,
        run_id=run_id,
    )
    artifacts = artifact_paths(write_scenario_runner_package_report(package))
    return StudioCommandResult(
        command="oodrive scenario-runner-package",
        run_id=Path(package.package_dir).parent.name,
        status=package.status,
        artifacts=artifacts,
        next_commands=[oodrive_command(f"scenario-runner-run --package {package.package_manifest_path}")],
        summary={
            "entrypoint": package.entrypoint,
            "native_field_count": len(package.coverage.get("native_fields", [])),
            "sidecar_field_count": len(package.coverage.get("sidecar_fields", [])),
        },
        claim_boundaries=package.claim_boundaries,
        blockers=package.blockers,
    )


def run_studio_scenario_runner_run(
    *,
    package_path: Path,
    scenario_runner_root: Path | None = None,
    output_root: Path | None = None,
    run_id: str = "oodrive-scenario-runner-run",
    timeout_s: float = 120.0,
) -> StudioCommandResult:
    run_dir = prepare_run_dir(output_root or package_path.parent, run_id)
    result = run_scenario_runner_package(
        package_path,
        scenario_runner_root=scenario_runner_root,
        output_root=run_dir.parent,
        run_id=run_dir.name,
        timeout_s=timeout_s,
    )
    artifacts = {
        "run_result_path": str(run_dir / "scenario_runner_run.json"),
        "run_result_report_path": str(run_dir / "scenario_runner_run.md"),
    }
    if result.stdout_path:
        artifacts["stdout_path"] = result.stdout_path
    if result.stderr_path:
        artifacts["stderr_path"] = result.stderr_path
    return StudioCommandResult(
        command="oodrive scenario-runner-run",
        run_id=run_dir.name,
        status=result.status,
        artifacts=artifacts,
        summary={
            "scenario_runner_root": str(scenario_runner_root) if scenario_runner_root else None,
            "returncode": result.returncode,
            "command": " ".join(result.command),
        },
        claim_boundaries=result.claim_boundaries,
        blockers=result.blockers,
    )


__all__ = ["run_studio_scenario_runner_package", "run_studio_scenario_runner_run"]
