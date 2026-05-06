"""CLI glue for planned Fail2Drive route execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.simulators.fail2drive_route_runner import (
    Fail2DriveRouteRunConfig,
    run_fail2drive_route,
    write_fail2drive_route_run,
)


def command_run_fail2drive_route(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    result = run_fail2drive_route(
        Fail2DriveRouteRunConfig(
            plan_path=args.plan,
            run_dir=run_dir,
            timeout_s=args.timeout_s,
            dry_run=args.dry_run,
            min_video_frames=args.min_video_frames,
            video_fps=args.video_fps,
            video_timeout_s=args.video_timeout_s,
            stop_after_video=args.stop_after_video,
            ffmpeg_path=args.ffmpeg_path,
        )
    )
    summary = write_fail2drive_route_run(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0


def register_fail2drive_route_runner_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "run-fail2drive-route",
        help="Execute a planned Fail2Drive route command with logs and timeout evidence.",
    )
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--timeout-s", type=float, default=120.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--min-video-frames", type=int)
    parser.add_argument("--video-fps", type=int, default=20)
    parser.add_argument("--video-timeout-s", type=float)
    parser.add_argument("--stop-after-video", action="store_true")
    parser.add_argument("--ffmpeg-path")
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="fail2drive-route-run")
    parser.set_defaults(func=command_run_fail2drive_route)


__all__ = ["command_run_fail2drive_route", "register_fail2drive_route_runner_parser"]
