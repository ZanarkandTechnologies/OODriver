"""CLI glue for Alpamayo trajectory conversion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.policies.alpamayo_trajectory import write_alpamayo_trajectory_conversion


def command_convert_alpamayo_trajectory(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_alpamayo_trajectory_conversion(
        run_dir,
        prediction_json=args.prediction_json,
        batch_index=args.batch_index,
        set_index=args.set_index,
        sample_index=args.sample_index,
    )
    print(json.dumps(summary, indent=2))
    return 0


def register_alpamayo_trajectory_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "convert-alpamayo-trajectory",
        help="Convert saved Alpamayo pred_xyz JSON into a DriverX 20-point trajectory.",
    )
    parser.add_argument("--prediction-json", type=Path, required=True)
    parser.add_argument("--batch-index", type=int, default=0)
    parser.add_argument("--set-index", type=int, default=0)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="alpamayo-trajectory")
    parser.set_defaults(func=command_convert_alpamayo_trajectory)


__all__ = [
    "command_convert_alpamayo_trajectory",
    "register_alpamayo_trajectory_parser",
]
