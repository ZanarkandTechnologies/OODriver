"""Custom CARLA asset OODrive CLI registration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_asset_runtime import (
    run_studio_cook_asset_package,
    run_studio_package_asset,
    run_studio_probe_asset_blueprint,
    run_studio_spawn_custom_asset,
    run_studio_spawn_runtime_mesh,
)


def register_asset_commands(nested: argparse._SubParsersAction) -> None:
    package = nested.add_parser("package-asset", help="Build a CARLA packaging plan for a generated/ingested asset manifest.")
    package.add_argument("--asset-manifest", type=Path, required=True)
    package.add_argument("--carla-root", type=Path)
    package.add_argument("--import-package-name")
    package.add_argument("--output-root", type=Path)
    package.add_argument("--run-id", default="oodrive-asset-package")
    package.set_defaults(func=_command_package_asset)

    cook = nested.add_parser("cook-asset-package", help="Preflight or run CARLA custom asset cooking/import commands.")
    cook.add_argument("--package-plan", type=Path, required=True)
    cook.add_argument("--carla-source-root", type=Path)
    cook.add_argument("--carla-package-root", type=Path)
    cook.add_argument("--cooked-package", type=Path)
    cook.add_argument("--cook-output-dir", type=Path)
    cook.add_argument("--mode", choices=["auto", "source", "docker", "import_cooked"], default="auto")
    cook.add_argument("--execute", action="store_true")
    cook.add_argument("--output-root", type=Path)
    cook.add_argument("--run-id", default="oodrive-asset-cook")
    cook.set_defaults(func=_command_cook_asset_package)

    probe = nested.add_parser("probe-asset-blueprint", help="Probe a live CARLA blueprint library for a custom asset id.")
    probe.add_argument("--blueprint-id", required=True)
    probe.add_argument("--host", default="127.0.0.1")
    probe.add_argument("--port", type=int, default=2000)
    probe.add_argument("--timeout-s", type=float, default=20.0)
    probe.add_argument("--output-root", type=Path)
    probe.add_argument("--run-id", default="oodrive-blueprint-probe")
    probe.set_defaults(func=_command_probe_asset_blueprint)

    spawn = nested.add_parser("spawn-custom-asset", help="Spawn a registered custom CARLA blueprint and capture proof.")
    spawn.add_argument("--blueprint-id", required=True)
    spawn.add_argument("--host", default="127.0.0.1")
    spawn.add_argument("--port", type=int, default=2000)
    spawn.add_argument("--timeout-s", type=float, default=20.0)
    spawn.add_argument("--spawn-index", type=int, default=0)
    spawn.add_argument("--output-root", type=Path)
    spawn.add_argument("--run-id", default="oodrive-custom-asset-spawn")
    spawn.set_defaults(func=_command_spawn_custom_asset)

    runtime_mesh = nested.add_parser(
        "spawn-runtime-mesh",
        help="Spawn CARLA static.prop.mesh with a mesh_path attribute and capture proof.",
    )
    runtime_mesh.add_argument("--mesh-path", required=True)
    runtime_mesh.add_argument("--host", default="127.0.0.1")
    runtime_mesh.add_argument("--port", type=int, default=2000)
    runtime_mesh.add_argument("--timeout-s", type=float, default=20.0)
    runtime_mesh.add_argument("--scale", type=float, default=1.0)
    runtime_mesh.add_argument("--spawn-index", type=int, default=0)
    runtime_mesh.add_argument("--x", type=float)
    runtime_mesh.add_argument("--y", type=float)
    runtime_mesh.add_argument("--z", type=float)
    runtime_mesh.add_argument("--yaw", type=float, default=0.0)
    runtime_mesh.add_argument("--output-root", type=Path)
    runtime_mesh.add_argument("--run-id", default="oodrive-runtime-mesh-spawn")
    runtime_mesh.set_defaults(func=_command_spawn_runtime_mesh)


def _print(result: StudioCommandResult) -> int:
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_package_asset(args: argparse.Namespace) -> int:
    return _print(
        run_studio_package_asset(
            asset_manifest_path=args.asset_manifest,
            carla_root=args.carla_root,
            import_package_name=args.import_package_name,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_cook_asset_package(args: argparse.Namespace) -> int:
    return _print(
        run_studio_cook_asset_package(
            package_plan_path=args.package_plan,
            carla_source_root=args.carla_source_root,
            carla_package_root=args.carla_package_root,
            cooked_package_path=args.cooked_package,
            output_dir=args.cook_output_dir,
            mode=args.mode,
            execute=args.execute,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_probe_asset_blueprint(args: argparse.Namespace) -> int:
    return _print(
        run_studio_probe_asset_blueprint(
            blueprint_id=args.blueprint_id,
            host=args.host,
            port=args.port,
            timeout_s=args.timeout_s,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_spawn_custom_asset(args: argparse.Namespace) -> int:
    return _print(
        run_studio_spawn_custom_asset(
            blueprint_id=args.blueprint_id,
            host=args.host,
            port=args.port,
            timeout_s=args.timeout_s,
            spawn_index=args.spawn_index,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_spawn_runtime_mesh(args: argparse.Namespace) -> int:
    return _print(
        run_studio_spawn_runtime_mesh(
            mesh_path=args.mesh_path,
            host=args.host,
            port=args.port,
            timeout_s=args.timeout_s,
            scale=args.scale,
            spawn_index=args.spawn_index,
            x=args.x,
            y=args.y,
            z=args.z,
            yaw=args.yaw,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


__all__ = ["register_asset_commands"]
