"""CLI glue for direct CARLA world controls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.simulators.carla_control import (
    CarlaControlConfig,
    control_carla_world,
    write_carla_control_report,
)


def command_control_carla(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    result = control_carla_world(
        CarlaControlConfig(
            host=args.host,
            port=args.port,
            timeout_s=args.timeout_s,
            town=args.town,
            map_name=args.map_name,
            load_map=args.load_map,
            weather_preset_name=args.weather_preset,
            capture=args.capture,
            spawn_index=args.spawn_index,
            camera_width=args.camera_width,
            camera_height=args.camera_height,
            camera_fov=args.camera_fov,
            tick_count=args.tick_count,
        ),
        run_dir,
    )
    summary = write_carla_control_report(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0 if result.connected else 2


def register_carla_control_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "control-carla",
        help="Agent-friendly CARLA map/weather/screenshot control command.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--timeout-s", type=float, default=30.0)
    parser.add_argument("--town", help="Friendly town selector such as Town03 or Town10HD.")
    parser.add_argument("--map-name", help="Exact CARLA map name such as Town03_Opt.")
    parser.add_argument("--load-map", action="store_true")
    parser.add_argument("--weather-preset", choices=["clear_day", "wet_overcast", "night_rain_fog", "low_sun_glare", "flooded_surface"])
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--spawn-index", type=int, default=0)
    parser.add_argument("--camera-width", type=int, default=1280)
    parser.add_argument("--camera-height", type=int, default=720)
    parser.add_argument("--camera-fov", type=float, default=90.0)
    parser.add_argument("--tick-count", type=int, default=3)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="carla-control")
    parser.set_defaults(func=command_control_carla)


__all__ = ["command_control_carla", "register_carla_control_parser"]
