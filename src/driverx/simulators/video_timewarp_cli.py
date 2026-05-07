"""CLI for offline CARLA video retiming."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.simulators.video_timewarp import timewarp_video, write_video_timewarp


def register_video_timewarp_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "timewarp-video",
        help="Retiming utility for offline CARLA demo videos.",
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--speed-factor", type=float, default=3.0)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--ffmpeg-path")
    parser.add_argument("--ffprobe-path")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="video-timewarp")
    parser.set_defaults(func=_command_timewarp_video)


def _command_timewarp_video(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    result = timewarp_video(
        args.input,
        args.output,
        speed_factor=args.speed_factor,
        fps=args.fps,
        ffmpeg_path=args.ffmpeg_path,
        ffprobe_path=args.ffprobe_path,
        run=not args.dry_run,
    )
    summary = write_video_timewarp(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] in {"passed", "planned"} else 1


__all__ = ["register_video_timewarp_parser"]
