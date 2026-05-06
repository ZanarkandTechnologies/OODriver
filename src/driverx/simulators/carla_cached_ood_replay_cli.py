"""CLI for cached Alpamayo trajectory replay in DriverX OOD scenes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.simulators.carla_cached_ood_replay import (
    load_cached_ood_replay_config,
    run_cached_ood_replay,
    write_cached_ood_replay,
)


def command_run_cached_ood_replay(args: argparse.Namespace) -> int:
    config = load_cached_ood_replay_config(args.config, decision_path=args.decision)
    if args.live:
        config = type(config)(**{**config.__dict__, "live": True})
    if args.tick_count is not None:
        config = type(config)(**{**config.__dict__, "tick_count": args.tick_count})
    if args.behavior_id:
        config = type(config)(**{**config.__dict__, "behavior_id": args.behavior_id})
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    result = run_cached_ood_replay(config, run_dir)
    summary = write_cached_ood_replay(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0 if result.status in {"passed", "partial"} else 2


def register_carla_cached_ood_replay_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "run-cached-ood-replay",
        help="Replay a cached Alpamayo policy decision as bounded CARLA/DriverX controls.",
    )
    parser.add_argument("--config", type=Path, default=Path("configs/carla_cached_ood_replay.local.sample.yaml"))
    parser.add_argument("--decision", type=Path)
    parser.add_argument("--behavior-id")
    parser.add_argument("--tick-count", type=int)
    parser.add_argument("--live", action="store_true", help="Attempt live CARLA replay instead of synthetic proof.")
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="cached-ood-replay")
    parser.set_defaults(func=command_run_cached_ood_replay)


__all__ = ["command_run_cached_ood_replay", "register_carla_cached_ood_replay_parser"]
