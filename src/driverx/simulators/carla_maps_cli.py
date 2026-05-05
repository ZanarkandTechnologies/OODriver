"""CLI glue for CARLA AdditionalMaps install and probe workflows."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.simulators.carla_maps import (
    CarlaMapProbeConfig,
    CarlaMapsInstallConfig,
    install_carla_additional_maps,
    load_carla_map_probe_config,
    load_carla_maps_install_config,
    probe_carla_map_inventory,
    write_carla_maps_report,
)


def command_install_carla_additional_maps(args: argparse.Namespace) -> int:
    config = load_carla_maps_install_config(args.config, dry_run=args.dry_run)
    config = _override_install_config(config, args)
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    result = install_carla_additional_maps(config)
    summary = write_carla_maps_report(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0


def command_probe_carla_maps(args: argparse.Namespace) -> int:
    config = load_carla_map_probe_config(args.config)
    config = _override_probe_config(config, args)
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    result = probe_carla_map_inventory(config)
    summary = write_carla_maps_report(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0 if result.connected else 2


def register_carla_maps_parser(subparsers: Any) -> None:
    install_parser = subparsers.add_parser(
        "install-carla-additional-maps",
        help="Download/stage CARLA AdditionalMaps and write an install report.",
    )
    install_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/carla_maps.local.sample.yaml"),
    )
    install_parser.add_argument("--carla-root", type=Path)
    install_parser.add_argument("--package-url")
    install_parser.add_argument("--package-path", type=Path)
    install_parser.add_argument("--package-cache-dir", type=Path)
    install_parser.add_argument("--platform", choices=["auto", "windows", "ubuntu", "linux"])
    install_parser.add_argument("--map", dest="maps", action="append")
    install_parser.add_argument("--dry-run", action="store_true")
    install_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    install_parser.add_argument("--run-id", default="carla-additional-maps")
    install_parser.set_defaults(func=command_install_carla_additional_maps)

    probe_parser = subparsers.add_parser(
        "probe-carla-maps",
        help="Probe available CARLA maps and optionally load desired maps.",
    )
    probe_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/carla_maps.local.sample.yaml"),
    )
    probe_parser.add_argument("--host")
    probe_parser.add_argument("--port", type=int)
    probe_parser.add_argument("--timeout-s", type=float)
    probe_parser.add_argument("--map", dest="maps", action="append")
    probe_parser.add_argument("--no-load", action="store_true")
    probe_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    probe_parser.add_argument("--run-id", default="carla-map-probe")
    probe_parser.set_defaults(func=command_probe_carla_maps)


def _override_install_config(
    config: CarlaMapsInstallConfig,
    args: argparse.Namespace,
) -> CarlaMapsInstallConfig:
    return replace(
        config,
        carla_root=args.carla_root if args.carla_root is not None else config.carla_root,
        package_url=args.package_url if args.package_url is not None else config.package_url,
        package_path=args.package_path if args.package_path is not None else config.package_path,
        package_cache_dir=(
            args.package_cache_dir
            if args.package_cache_dir is not None
            else config.package_cache_dir
        ),
        platform=args.platform if args.platform is not None else config.platform,
        desired_maps=tuple(args.maps) if args.maps else config.desired_maps,
    )


def _override_probe_config(
    config: CarlaMapProbeConfig,
    args: argparse.Namespace,
) -> CarlaMapProbeConfig:
    return replace(
        config,
        host=args.host if args.host is not None else config.host,
        port=args.port if args.port is not None else config.port,
        timeout_s=args.timeout_s if args.timeout_s is not None else config.timeout_s,
        desired_maps=tuple(args.maps) if args.maps else config.desired_maps,
        attempt_load=not args.no_load,
    )


__all__ = [
    "command_install_carla_additional_maps",
    "command_probe_carla_maps",
    "register_carla_maps_parser",
]
