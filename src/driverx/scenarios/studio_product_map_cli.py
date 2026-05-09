"""Custom CARLA map OODrive CLI registration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_map_runtime import (
    run_studio_carla_map_probe,
    run_studio_prepare_map_import,
    run_studio_validate_map_import,
)


def register_map_commands(nested: argparse._SubParsersAction) -> None:
    prepare = nested.add_parser("prepare-map-import", help="Prepare a CARLA custom map import manifest from FBX and XODR files.")
    prepare.add_argument("--fbx", type=Path, required=True)
    prepare.add_argument("--xodr", type=Path, required=True)
    prepare.add_argument("--map-name", required=True)
    prepare.add_argument("--import-mode", choices=["package", "source_build", "manual_unreal"], default="package")
    prepare.add_argument("--output-root", type=Path)
    prepare.add_argument("--run-id", default="oodrive-custom-map-import")
    prepare.set_defaults(func=_command_prepare_map_import)

    validate = nested.add_parser("validate-map-import", help="Validate a CARLA custom map import manifest.")
    validate.add_argument("--manifest", type=Path, required=True)
    validate.add_argument("--output-root", type=Path)
    validate.add_argument("--run-id", default="oodrive-custom-map-validation")
    validate.add_argument("--metric-only", action="store_true")
    validate.set_defaults(func=_command_validate_map_import)

    probe = nested.add_parser("carla-map-probe", help="Probe whether a CARLA map is installed and loadable.")
    probe.add_argument("--map", dest="map_name", required=True)
    probe.add_argument("--host", default="127.0.0.1")
    probe.add_argument("--port", type=int, default=2000)
    probe.add_argument("--timeout-s", type=float, default=20.0)
    probe.add_argument("--output-root", type=Path)
    probe.add_argument("--run-id", default="oodrive-carla-map-probe")
    probe.set_defaults(func=_command_carla_map_probe)


def _print(result: StudioCommandResult) -> int:
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_prepare_map_import(args: argparse.Namespace) -> int:
    return _print(
        run_studio_prepare_map_import(
            fbx_path=args.fbx,
            xodr_path=args.xodr,
            map_name=args.map_name,
            import_mode=args.import_mode,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_validate_map_import(args: argparse.Namespace) -> int:
    result = run_studio_validate_map_import(manifest_path=args.manifest, output_root=args.output_root, run_id=args.run_id)
    if args.metric_only:
        print(f"METRIC custom_map_import_valid={1.0 if result.status == 'passed' else 0.0:.4f}")
        return 0
    return _print(result)


def _command_carla_map_probe(args: argparse.Namespace) -> int:
    return _print(
        run_studio_carla_map_probe(
            map_name=args.map_name,
            host=args.host,
            port=args.port,
            timeout_s=args.timeout_s,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


__all__ = ["register_map_commands"]
