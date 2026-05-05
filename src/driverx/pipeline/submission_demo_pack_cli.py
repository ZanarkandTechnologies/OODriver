"""CLI glue for submission demo pack generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.pipeline.submission_demo_pack import build_submission_demo_pack


def command_build_submission_demo_pack(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = build_submission_demo_pack(
        run_dir,
        local_demo_path=args.local_demo,
        generated_suite_path=args.generated_suite,
        policy_matrix_path=args.policy_matrix,
        alpamayo_probe_path=args.alpamayo_probe,
        route_evidence_path=args.route_evidence,
        alpamayo_comparison_path=args.alpamayo_comparison,
        cached_replay_path=args.cached_replay,
        blockers_path=args.blockers,
        progress_path=args.progress,
    )
    print(json.dumps(summary, indent=2))
    return 0


def register_submission_demo_pack_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "build-demo-pack",
        help="Build a judge-facing demo outline, artifact map, declarations, and write-up draft.",
    )
    parser.add_argument("--generated-suite", type=Path)
    parser.add_argument("--local-demo", type=Path)
    parser.add_argument("--policy-matrix", type=Path)
    parser.add_argument("--alpamayo-probe", type=Path)
    parser.add_argument("--route-evidence", type=Path)
    parser.add_argument("--alpamayo-comparison", type=Path)
    parser.add_argument("--cached-replay", type=Path)
    parser.add_argument("--blockers", type=Path, default=Path("blockers.md"))
    parser.add_argument("--progress", type=Path, default=Path("docs/progress.md"))
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="submission-demo-pack")
    parser.set_defaults(func=command_build_submission_demo_pack)


__all__ = [
    "command_build_submission_demo_pack",
    "register_submission_demo_pack_parser",
]
