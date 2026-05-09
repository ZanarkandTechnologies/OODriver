"""OODrive wrappers for custom CARLA map import readiness."""

from __future__ import annotations

from pathlib import Path

from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths, oodrive_command
from driverx.simulators.carla_custom_map import (
    custom_map_run_dir,
    prepare_custom_map_import,
    probe_carla_map,
    validate_custom_map_import,
    write_carla_map_probe,
    write_custom_map_import,
    write_custom_map_validation,
)


def run_studio_prepare_map_import(
    *,
    fbx_path: Path,
    xodr_path: Path,
    map_name: str,
    import_mode: str = "package",
    output_root: Path | None = None,
    run_id: str = "oodrive-custom-map-import",
) -> StudioCommandResult:
    manifest = prepare_custom_map_import(fbx_path=fbx_path, xodr_path=xodr_path, map_name=map_name, import_mode=import_mode)
    run_dir = custom_map_run_dir(output_root, run_id)
    artifacts = artifact_paths(write_custom_map_import(run_dir, manifest))
    return StudioCommandResult(
        command="oodrive prepare-map-import",
        run_id=run_dir.name,
        status=manifest.status,
        artifacts=artifacts,
        next_commands=[oodrive_command(f"validate-map-import --manifest {artifacts['json_path']} --metric-only")],
        summary={"map_name": map_name, "import_mode": import_mode},
        claim_boundaries=manifest.claim_boundaries,
        blockers=manifest.blockers,
    )


def run_studio_validate_map_import(
    *,
    manifest_path: Path,
    output_root: Path | None = None,
    run_id: str = "oodrive-custom-map-validation",
) -> StudioCommandResult:
    validation = validate_custom_map_import(manifest_path)
    run_dir = custom_map_run_dir(output_root or manifest_path.parent, run_id)
    artifacts = artifact_paths(write_custom_map_validation(run_dir, validation))
    return StudioCommandResult(
        command="oodrive validate-map-import",
        run_id=run_dir.name,
        status=validation.status,
        artifacts=artifacts,
        next_commands=[],
        summary={"manifest_path": str(manifest_path)},
        claim_boundaries=validation.claim_boundaries,
        blockers=validation.blockers,
    )


def run_studio_carla_map_probe(
    *,
    map_name: str,
    host: str = "127.0.0.1",
    port: int = 2000,
    timeout_s: float = 20.0,
    output_root: Path | None = None,
    run_id: str = "oodrive-carla-map-probe",
) -> StudioCommandResult:
    probe = probe_carla_map(map_name=map_name, host=host, port=port, timeout_s=timeout_s)
    run_dir = custom_map_run_dir(output_root, run_id)
    artifacts = artifact_paths(write_carla_map_probe(run_dir, probe))
    return StudioCommandResult(
        command="oodrive carla-map-probe",
        run_id=run_dir.name,
        status=probe.status,
        artifacts=artifacts,
        summary={"map_name": map_name, "map_loaded": probe.map_loaded, "available_map_count": len(probe.available_maps)},
        claim_boundaries=probe.claim_boundaries,
        blockers=probe.blockers,
    )


__all__ = ["run_studio_carla_map_probe", "run_studio_prepare_map_import", "run_studio_validate_map_import"]
