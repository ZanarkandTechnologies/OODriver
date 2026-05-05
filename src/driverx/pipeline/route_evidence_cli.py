"""CLI glue for route evidence bundling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.pipeline.route_evidence import RouteEvidenceInputs, build_route_evidence


def command_build_route_evidence(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = build_route_evidence(
        run_dir,
        RouteEvidenceInputs(
            plan_path=args.plan,
            route_run_path=args.route_run,
            result_path=args.result,
            entity_tracks_path=args.entity_tracks,
            video_path=args.video,
            screenshot_paths=tuple(args.screenshot or []),
            log_paths=tuple(args.log or []),
            video_duration_s=args.video_duration_s,
        ),
    )
    print(json.dumps(summary, indent=2))
    return 0


def register_route_evidence_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "build-route-evidence",
        help="Bundle route result, video, tracks, screenshots, and logs into review evidence.",
    )
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--route-run", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--entity-tracks", type=Path)
    parser.add_argument("--video", type=Path)
    parser.add_argument("--video-duration-s", type=float)
    parser.add_argument("--screenshot", type=Path, action="append")
    parser.add_argument("--log", type=Path, action="append")
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="route-evidence")
    parser.set_defaults(func=command_build_route_evidence)


__all__ = ["command_build_route_evidence", "register_route_evidence_parser"]
