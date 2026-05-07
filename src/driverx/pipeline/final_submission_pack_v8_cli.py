"""CLI for the V8 paper-style final submission pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.pipeline.final_submission_pack_v8 import (
    FinalSubmissionPackV8Inputs,
    run_final_submission_pack_v8,
)


def register_final_submission_pack_v8_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "build-final-submission-pack-v8",
        help="Build the V8 paper-style final submission packet.",
    )
    parser.add_argument("--workbench-bundle", type=Path, required=True)
    parser.add_argument("--agentic-loop", type=Path, required=True)
    parser.add_argument("--risk-timeline", type=Path, required=True)
    parser.add_argument("--reasoning-overlay", type=Path, required=True)
    parser.add_argument("--timewarp", type=Path, required=True)
    parser.add_argument("--alpamayo-batch", type=Path, required=True)
    parser.add_argument("--final-demo-video", type=Path)
    parser.add_argument("--blockers", type=Path, default=Path("blockers.md"))
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="final-submission-pack-v8")
    parser.set_defaults(func=_command_build_final_submission_pack_v8)


def _command_build_final_submission_pack_v8(args: argparse.Namespace) -> int:
    summary = run_final_submission_pack_v8(
        FinalSubmissionPackV8Inputs(
            workbench_bundle_path=args.workbench_bundle,
            agentic_loop_path=args.agentic_loop,
            risk_timeline_path=args.risk_timeline,
            reasoning_overlay_path=args.reasoning_overlay,
            timewarp_path=args.timewarp,
            alpamayo_batch_path=args.alpamayo_batch,
            final_demo_video_path=args.final_demo_video,
            blockers_path=args.blockers,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_final_submission_pack_v8_parser"]
