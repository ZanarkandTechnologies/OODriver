"""CLI glue for Alpamayo OOD comparison reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.pipeline.alpamayo_ood_evaluation import (
    AlpamayoOodEvaluationInputs,
    build_alpamayo_ood_evaluation,
)


def command_build_alpamayo_ood_comparison(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = build_alpamayo_ood_evaluation(
        run_dir,
        AlpamayoOodEvaluationInputs(
            baseline_decision_path=args.baseline_decision,
            memory_decision_path=args.memory_decision,
            source_package_path=args.source_package,
            route_evidence_path=args.route_evidence,
            memory_entries_path=args.memory,
        ),
    )
    print(json.dumps(summary, indent=2))
    return 0


def register_alpamayo_ood_evaluation_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "build-alpamayo-ood-comparison",
        help="Compare open-loop Alpamayo behavior with and without DriverX memory context.",
    )
    parser.add_argument("--baseline-decision", type=Path, required=True)
    parser.add_argument("--memory-decision", type=Path)
    parser.add_argument("--source-package", type=Path)
    parser.add_argument("--route-evidence", type=Path)
    parser.add_argument("--memory", type=Path)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="alpamayo-ood-comparison")
    parser.set_defaults(func=command_build_alpamayo_ood_comparison)


__all__ = [
    "command_build_alpamayo_ood_comparison",
    "register_alpamayo_ood_evaluation_parser",
]
