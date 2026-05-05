"""CLI glue for route video assembly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.simulators.route_video_assembly import (
    plan_route_video_assembly,
    run_route_video_assembly,
    write_route_video_assembly,
)


def command_assemble_route_video(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    plan = plan_route_video_assembly(
        args.rgb_folder,
        output_video=args.output_video,
        fps=args.fps,
        ffmpeg_path=args.ffmpeg_path,
    )
    result = run_route_video_assembly(plan) if args.run else plan
    summary = write_route_video_assembly(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0


def register_route_video_assembly_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "assemble-route-video",
        help="Plan or run ffmpeg video assembly from a Fail2Drive RGB frame folder.",
    )
    parser.add_argument("--rgb-folder", type=Path, required=True)
    parser.add_argument("--output-video", type=Path)
    parser.add_argument("--fps", type=int, default=20)
    parser.add_argument("--ffmpeg-path")
    parser.add_argument("--run", action="store_true", help="Execute ffmpeg when no live blockers exist.")
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="route-video-assembly")
    parser.set_defaults(func=command_assemble_route_video)


__all__ = ["command_assemble_route_video", "register_route_video_assembly_parser"]
