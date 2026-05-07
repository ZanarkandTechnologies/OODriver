"""CLI for CARLA track-derived risk timelines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.perception.risk_timeline import (
    RiskTimelineConfig,
    build_risk_timeline,
    load_entity_tracks,
    write_risk_timeline,
)


def register_risk_timeline_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "build-risk-timeline",
        help="Build a simulator-ground-truth risk timeline from CARLA entity tracks.",
    )
    parser.add_argument("--tracks", type=Path, required=True)
    parser.add_argument("--scenario-id")
    parser.add_argument("--behavior-id")
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="risk-timeline-v1")
    parser.set_defaults(func=_command_build_risk_timeline)


def _command_build_risk_timeline(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    tracks = load_entity_tracks(args.tracks)
    timeline = build_risk_timeline(
        tracks,
        RiskTimelineConfig(scenario_id=args.scenario_id, behavior_id=args.behavior_id),
    )
    summary = write_risk_timeline(run_dir, timeline)
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_risk_timeline_parser"]
