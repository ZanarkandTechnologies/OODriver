"""OODrive wrappers for CARLA custom asset packaging and probing."""

from __future__ import annotations

from pathlib import Path

from driverx.assets.carla_packaging import (
    build_asset_package_plan,
    build_asset_cook_plan,
    custom_asset_run_dir,
    probe_asset_blueprint,
    spawn_custom_asset,
    spawn_runtime_mesh_path,
    write_asset_package_plan,
    write_asset_cook_plan,
    write_blueprint_probe,
    write_custom_asset_spawn_proof,
    write_runtime_mesh_spawn_proof,
)
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths, oodrive_command


def run_studio_package_asset(
    *,
    asset_manifest_path: Path,
    carla_root: Path | None = None,
    import_package_name: str | None = None,
    output_root: Path | None = None,
    run_id: str = "oodrive-asset-package",
) -> StudioCommandResult:
    plan = build_asset_package_plan(
        asset_manifest_path,
        carla_root=carla_root,
        import_package_name=import_package_name,
    )
    run_dir = custom_asset_run_dir(output_root, run_id)
    artifacts = artifact_paths(write_asset_package_plan(run_dir, plan))
    carla_prop_id = f"static.prop.{plan.prop_name.lower()}"
    return StudioCommandResult(
        command="oodrive package-asset",
        run_id=run_dir.name,
        status=plan.status,
        artifacts=artifacts,
        next_commands=[oodrive_command(f"probe-asset-blueprint --blueprint-id {carla_prop_id}")],
        summary={
            "asset_id": plan.asset_id,
            "expected_blueprint_id": plan.expected_blueprint_id,
            "expected_carla_prop_id": carla_prop_id,
            "import_package_name": plan.import_package_name,
            "carla_root_capabilities": plan.carla_root_capabilities,
        },
        claim_boundaries=plan.claim_boundaries,
        blockers=[*plan.blockers, *[f"warning: {item}" for item in plan.warnings]],
    )


def run_studio_cook_asset_package(
    *,
    package_plan_path: Path,
    carla_source_root: Path | None = None,
    carla_package_root: Path | None = None,
    cooked_package_path: Path | None = None,
    output_dir: Path | None = None,
    mode: str = "auto",
    execute: bool = False,
    output_root: Path | None = None,
    run_id: str = "oodrive-asset-cook",
) -> StudioCommandResult:
    plan = build_asset_cook_plan(
        package_plan_path,
        carla_source_root=carla_source_root,
        carla_package_root=carla_package_root,
        cooked_package_path=cooked_package_path,
        output_dir=output_dir,
        mode=mode,
        execute=execute,
    )
    run_dir = custom_asset_run_dir(output_root, run_id)
    artifacts = artifact_paths(write_asset_cook_plan(run_dir, plan))
    return StudioCommandResult(
        command="oodrive cook-asset-package",
        run_id=run_dir.name,
        status=plan.status,
        artifacts=artifacts,
        next_commands=[
            oodrive_command(f"probe-asset-blueprint --blueprint-id static.prop.{plan.import_package_name.removeprefix('OODrive_').lower()}")
        ]
        if plan.status == "passed"
        else [],
        summary={
            "import_package_name": plan.import_package_name,
            "mode": plan.mode,
            "executed": plan.executed,
            "programmatic_asset_cook_available": "programmatic_asset_cook_available=true" in plan.claim_boundaries,
            "cooked_package_import_available": "cooked_package_import_available=true" in plan.claim_boundaries,
        },
        claim_boundaries=plan.claim_boundaries,
        blockers=[*plan.blockers, *[f"warning: {item}" for item in plan.warnings]],
    )


def run_studio_probe_asset_blueprint(
    *,
    blueprint_id: str,
    host: str = "127.0.0.1",
    port: int = 2000,
    timeout_s: float = 20.0,
    output_root: Path | None = None,
    run_id: str = "oodrive-blueprint-probe",
) -> StudioCommandResult:
    result = probe_asset_blueprint(blueprint_id, host=host, port=port, timeout_s=timeout_s)
    run_dir = custom_asset_run_dir(output_root, run_id)
    artifacts = artifact_paths(write_blueprint_probe(run_dir, result))
    return StudioCommandResult(
        command="oodrive probe-asset-blueprint",
        run_id=run_dir.name,
        status=result.status,
        artifacts=artifacts,
        next_commands=[oodrive_command(f"spawn-custom-asset --blueprint-id {blueprint_id}")],
        summary={"blueprint_id": blueprint_id, "blueprint_registered": result.blueprint_registered},
        claim_boundaries=result.claim_boundaries,
        blockers=result.blockers,
    )


def run_studio_spawn_custom_asset(
    *,
    blueprint_id: str,
    host: str = "127.0.0.1",
    port: int = 2000,
    timeout_s: float = 20.0,
    spawn_index: int = 0,
    output_root: Path | None = None,
    run_id: str = "oodrive-custom-asset-spawn",
) -> StudioCommandResult:
    run_dir = custom_asset_run_dir(output_root, run_id)
    proof = spawn_custom_asset(
        blueprint_id,
        host=host,
        port=port,
        timeout_s=timeout_s,
        run_dir=run_dir,
        spawn_index=spawn_index,
    )
    artifacts = artifact_paths(write_custom_asset_spawn_proof(run_dir, proof))
    return StudioCommandResult(
        command="oodrive spawn-custom-asset",
        run_id=run_dir.name,
        status=proof.status,
        artifacts=artifacts,
        summary={"blueprint_id": blueprint_id, "spawned_actor_id": proof.spawned_actor_id},
        claim_boundaries=proof.claim_boundaries,
        blockers=proof.blockers,
    )


def run_studio_spawn_runtime_mesh(
    *,
    mesh_path: str,
    host: str = "127.0.0.1",
    port: int = 2000,
    timeout_s: float = 20.0,
    scale: float = 1.0,
    spawn_index: int = 0,
    x: float | None = None,
    y: float | None = None,
    z: float | None = None,
    yaw: float = 0.0,
    output_root: Path | None = None,
    run_id: str = "oodrive-runtime-mesh-spawn",
) -> StudioCommandResult:
    run_dir = custom_asset_run_dir(output_root, run_id)
    proof = spawn_runtime_mesh_path(
        mesh_path,
        host=host,
        port=port,
        timeout_s=timeout_s,
        scale=scale,
        run_dir=run_dir,
        spawn_index=spawn_index,
        x=x,
        y=y,
        z=z,
        yaw=yaw,
    )
    artifacts = artifact_paths(write_runtime_mesh_spawn_proof(run_dir, proof))
    return StudioCommandResult(
        command="oodrive spawn-runtime-mesh",
        run_id=run_dir.name,
        status=proof.status,
        artifacts=artifacts,
        summary={
            "mesh_path": mesh_path,
            "runtime_mesh_blueprint_id": proof.runtime_mesh_blueprint_id,
            "spawned_actor_id": proof.spawned_actor_id,
            "scale": proof.scale,
        },
        claim_boundaries=proof.claim_boundaries,
        blockers=proof.blockers,
    )


__all__ = [
    "run_studio_package_asset",
    "run_studio_cook_asset_package",
    "run_studio_probe_asset_blueprint",
    "run_studio_spawn_custom_asset",
    "run_studio_spawn_runtime_mesh",
]
