"""OODrive wrappers for CARLA custom asset packaging and probing."""

from __future__ import annotations

from pathlib import Path

from driverx.assets.carla_packaging import (
    build_asset_package_plan,
    custom_asset_run_dir,
    probe_asset_blueprint,
    spawn_custom_asset,
    write_asset_package_plan,
    write_blueprint_probe,
    write_custom_asset_spawn_proof,
)
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths, oodrive_command


def run_studio_package_asset(
    *,
    asset_manifest_path: Path,
    output_root: Path | None = None,
    run_id: str = "oodrive-asset-package",
) -> StudioCommandResult:
    plan = build_asset_package_plan(asset_manifest_path)
    run_dir = custom_asset_run_dir(output_root, run_id)
    artifacts = artifact_paths(write_asset_package_plan(run_dir, plan))
    return StudioCommandResult(
        command="oodrive package-asset",
        run_id=run_dir.name,
        status=plan.status,
        artifacts=artifacts,
        next_commands=[oodrive_command(f"probe-asset-blueprint --blueprint-id {plan.expected_blueprint_id}")],
        summary={"asset_id": plan.asset_id, "expected_blueprint_id": plan.expected_blueprint_id},
        claim_boundaries=plan.claim_boundaries,
        blockers=plan.blockers,
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
    output_root: Path | None = None,
    run_id: str = "oodrive-custom-asset-spawn",
) -> StudioCommandResult:
    proof = spawn_custom_asset(blueprint_id, host=host, port=port, timeout_s=timeout_s)
    run_dir = custom_asset_run_dir(output_root, run_id)
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


__all__ = ["run_studio_package_asset", "run_studio_probe_asset_blueprint", "run_studio_spawn_custom_asset"]
