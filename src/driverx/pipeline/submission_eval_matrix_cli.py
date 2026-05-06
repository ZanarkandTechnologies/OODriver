"""CLI for final submission evaluation matrix generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.pipeline.submission_eval_matrix import (
    SubmissionEvalMatrixConfig,
    run_submission_eval_matrix,
)


def register_submission_eval_matrix_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "build-submission-eval-matrix",
        help="Select final judge-facing scenarios and evidence gaps for the SoTA sprint.",
    )
    parser.add_argument("--catalog", type=Path, action="append", required=True)
    parser.add_argument("--evidence", type=Path, action="append", default=[])
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="submission-eval-matrix")
    parser.set_defaults(func=_command_build_submission_eval_matrix)


def _command_build_submission_eval_matrix(args: argparse.Namespace) -> int:
    summary = run_submission_eval_matrix(
        SubmissionEvalMatrixConfig(
            catalog_paths=tuple(args.catalog),
            evidence_paths=tuple(args.evidence or ()),
            output_root=args.output_root,
            run_id=args.run_id,
            limit=args.limit,
        )
    )
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_submission_eval_matrix_parser"]
