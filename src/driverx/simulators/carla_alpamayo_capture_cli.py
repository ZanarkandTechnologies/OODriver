"""CLI glue for live CARLA Alpamayo input capture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.simulators.carla import load_carla_run_config
from driverx.simulators.carla_alpamayo_capture import (
    CarlaActorAttachConfig,
    CarlaAlpamayoCaptureConfig,
    run_carla_alpamayo_capture,
    write_carla_alpamayo_capture,
)


def command_capture_alpamayo_carla_input(args: argparse.Namespace) -> int:
    config = load_carla_run_config(args.config)
    capture_config = CarlaAlpamayoCaptureConfig(
        host=args.host if args.host is not None else config.host,
        port=args.port if args.port is not None else config.port,
        timeout_s=args.timeout_s if args.timeout_s is not None else config.timeout_s,
        tick_count=args.tick_count,
        camera_width=args.camera_width,
        camera_height=args.camera_height,
        route_id=args.route_id,
        route_name=args.route_name,
        route_evidence_path=args.route_evidence,
    )
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    attach = None
    if args.attach_role_name is not None or args.actor_id is not None:
        attach = CarlaActorAttachConfig(
            role_name=args.attach_role_name,
            actor_id=args.actor_id,
            blueprint_filter=args.blueprint_filter,
            fallback_spawn=not args.no_fallback_spawn,
        )
    result = run_carla_alpamayo_capture(capture_config, run_dir, attach=attach)
    summary = write_carla_alpamayo_capture(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0


def register_carla_alpamayo_capture_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "capture-alpamayo-carla-input",
        help="Capture CARLA RGB windows and ego history for an Alpamayo input package.",
    )
    parser.add_argument("--config", type=Path, default=Path("configs/carla_local.sample.yaml"))
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--timeout-s", type=float)
    parser.add_argument("--tick-count", type=int, default=4)
    parser.add_argument("--camera-width", type=int, default=320)
    parser.add_argument("--camera-height", type=int, default=180)
    parser.add_argument("--attach-role-name")
    parser.add_argument("--actor-id", type=int)
    parser.add_argument("--blueprint-filter", default="vehicle.*")
    parser.add_argument("--no-fallback-spawn", action="store_true")
    parser.add_argument("--route-id")
    parser.add_argument("--route-name")
    parser.add_argument("--route-evidence", type=Path)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="alpamayo-carla-input")
    parser.set_defaults(func=command_capture_alpamayo_carla_input)


__all__ = [
    "command_capture_alpamayo_carla_input",
    "register_carla_alpamayo_capture_parser",
]
