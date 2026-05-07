"""CLI for reasoning/RAG overlay video generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.pipeline.reasoning_overlay_video import ReasoningOverlayInputs, build_reasoning_overlay_video


def register_reasoning_overlay_video_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "build-reasoning-overlay-video",
        help="Overlay risk, RAG memory, and sampled VLA reasoning panels onto a CARLA MP4.",
    )
    parser.add_argument("--input-video", type=Path, required=True)
    parser.add_argument("--output-video", type=Path, required=True)
    parser.add_argument("--workbench-bundle", type=Path, required=True)
    parser.add_argument("--risk-timeline", type=Path, required=True)
    parser.add_argument("--alpamayo-batch", type=Path, required=True)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--speed-factor", type=float, default=3.0)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="reasoning-overlay-video")
    parser.set_defaults(func=_command_build_reasoning_overlay_video)


def _command_build_reasoning_overlay_video(args: argparse.Namespace) -> int:
    summary = build_reasoning_overlay_video(
        ReasoningOverlayInputs(
            input_video=args.input_video,
            output_video=args.output_video,
            workbench_bundle_path=args.workbench_bundle,
            risk_timeline_path=args.risk_timeline,
            alpamayo_batch_path=args.alpamayo_batch,
            output_root=args.output_root,
            run_id=args.run_id,
            fps=args.fps,
            speed_factor=args.speed_factor,
        )
    )
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "passed" else 1


__all__ = ["register_reasoning_overlay_video_parser"]
