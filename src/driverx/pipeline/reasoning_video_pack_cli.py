"""CLI glue for reasoning/video evidence packs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.pipeline.reasoning_video_pack import (
    ReasoningVideoPackInputs,
    build_reasoning_video_pack,
)


def command_build_reasoning_video_pack(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = build_reasoning_video_pack(
        run_dir,
        ReasoningVideoPackInputs(
            ood_video_evidence_path=args.ood_video_evidence,
            alpamayo_scene_path=args.alpamayo_scene,
            alpamayo_comparison_path=args.alpamayo_comparison,
            source_rgb_folder=args.source_rgb_folder,
            fps=args.fps,
        ),
    )
    print(json.dumps(summary, indent=2))
    return 0 if summary.get("status") in {"ready", "partial"} else 2


def register_reasoning_video_pack_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "build-reasoning-video-pack",
        help="Build an HTML/Markdown pack joining CARLA video and Alpamayo reasoning.",
    )
    parser.add_argument("--ood-video-evidence", type=Path, required=True)
    parser.add_argument("--alpamayo-scene", type=Path)
    parser.add_argument("--alpamayo-comparison", type=Path)
    parser.add_argument("--source-rgb-folder", type=Path)
    parser.add_argument("--fps", type=int, default=5)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="reasoning-video-pack")
    parser.set_defaults(func=command_build_reasoning_video_pack)


__all__ = ["command_build_reasoning_video_pack", "register_reasoning_video_pack_parser"]
