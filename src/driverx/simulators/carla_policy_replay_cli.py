"""CLI glue for cached policy trajectory replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.policies import EgoPose, TrajectoryControlConfig
from driverx.simulators.carla_policy_replay import (
    CarlaPolicyReplayConfig,
    replay_policy_decision,
    write_carla_policy_replay,
)


def command_replay_policy_decision(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    result = replay_policy_decision(
        CarlaPolicyReplayConfig(
            decision_path=args.decision,
            ego_pose=EgoPose(x=args.ego_x, y=args.ego_y, yaw_deg=args.ego_yaw_deg),
            control_config=TrajectoryControlConfig(
                trajectory_frame=args.trajectory_frame,
                max_speed_mps=args.max_speed_mps,
                max_steer=args.max_steer,
                max_brake=args.max_brake,
                max_throttle=args.max_throttle,
                lookahead_points=args.lookahead_points,
                dt_s=args.dt_s,
            ),
            apply_to_actor=False,
        )
    )
    summary = write_carla_policy_replay(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0 if result.error is None else 2


def register_carla_policy_replay_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "replay-policy-decision",
        help="Convert a cached policy decision trajectory into bounded CARLA controls.",
    )
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--ego-x", type=float, default=0.0)
    parser.add_argument("--ego-y", type=float, default=0.0)
    parser.add_argument("--ego-yaw-deg", type=float, default=0.0)
    parser.add_argument("--trajectory-frame", choices=["ego", "world"], default="ego")
    parser.add_argument("--max-speed-mps", type=float, default=6.0)
    parser.add_argument("--max-steer", type=float, default=0.35)
    parser.add_argument("--max-brake", type=float, default=0.5)
    parser.add_argument("--max-throttle", type=float, default=0.45)
    parser.add_argument("--lookahead-points", type=int, default=3)
    parser.add_argument("--dt-s", type=float, default=0.25)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="policy-replay")
    parser.set_defaults(func=command_replay_policy_decision)


__all__ = ["command_replay_policy_decision", "register_carla_policy_replay_parser"]
