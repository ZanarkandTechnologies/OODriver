"""Custom CARLA asset OODrive CLI registration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_asset_runtime import (
    run_studio_package_asset,
    run_studio_probe_asset_blueprint,
    run_studio_spawn_custom_asset,
)


def register_asset_commands(nested: argparse._SubParsersAction) -> None:
    package = nested.add_parser("package-asset", help="Build a CARLA packaging plan for a generated/ingested asset manifest.")
    package.add_argument("--asset-manifest", type=Path, required=True)
    package.add_argument("--output-root", type=Path)
    package.add_argument("--run-id", default="oodrive-asset-package")
    package.set_defaults(func=_command_package_asset)

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
    spawn.add_argument("--output-root", type=Path)
    spawn.add_argument("--run-id", default="oodrive-custom-asset-spawn")
    spawn.set_defaults(func=_command_spawn_custom_asset)


def _print(result: StudioCommandResult) -> int:
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_package_asset(args: argparse.Namespace) -> int:
    return _print(run_studio_package_asset(asset_manifest_path=args.asset_manifest, output_root=args.output_root, run_id=args.run_id))


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
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


__all__ = ["register_asset_commands"]
