"""CLI glue for live Alpamayo inference shape reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.policies.alpamayo_probe import DEFAULT_ALPAMAYO_MODEL_ID
from driverx.policies.alpamayo_shape_probe import write_alpamayo_shape_probe_report


def command_probe_alpamayo_shapes(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_alpamayo_shape_probe_report(
        run_dir,
        artifact_root=args.artifact_root,
        model_id=args.model_id,
    )
    print(json.dumps(summary, indent=2))
    return 0


def register_alpamayo_shape_probe_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "probe-alpamayo-shapes",
        help="Summarize live Alpamayo inference shape artifacts.",
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        help="Directory containing pulled remote shape probe artifacts. Defaults to the new run dir.",
    )
    parser.add_argument("--model-id", default=DEFAULT_ALPAMAYO_MODEL_ID)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="alpamayo-shape-probe")
    parser.set_defaults(func=command_probe_alpamayo_shapes)


__all__ = [
    "command_probe_alpamayo_shapes",
    "register_alpamayo_shape_probe_parser",
]
