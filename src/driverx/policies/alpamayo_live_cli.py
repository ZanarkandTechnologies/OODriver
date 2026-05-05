"""CLI glue for open-loop Alpamayo live policy artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.policies.alpamayo_live import run_alpamayo_live_package
from driverx.policies.alpamayo_probe import DEFAULT_ALPAMAYO_MODEL_ID


def command_run_alpamayo_live(args: argparse.Namespace) -> int:
    summary = run_alpamayo_live_package(
        package_path=args.package,
        prediction_json=args.prediction_json,
        output_root=args.output_root,
        run_id=args.run_id,
        model_id=args.model_id,
        sample_index=args.sample_index,
    )
    print(json.dumps(summary, indent=2))
    return 0


def register_alpamayo_live_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "run-alpamayo-live",
        help="Convert a live Alpamayo prediction payload into an open-loop DriverX policy decision.",
    )
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--prediction-json", type=Path, required=True)
    parser.add_argument("--model-id", default=DEFAULT_ALPAMAYO_MODEL_ID)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="alpamayo-live-policy")
    parser.set_defaults(func=command_run_alpamayo_live)


__all__ = [
    "command_run_alpamayo_live",
    "register_alpamayo_live_parser",
]
