"""CLI registration for OOD video evidence assembly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.pipeline.ood_video_evidence import (
    OodVideoEvidenceInputs,
    build_ood_video_evidence,
)


def register_ood_video_evidence_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "assemble-ood-video",
        help="Render OOD evidence overlays and assemble a video from RGB frames.",
    )
    parser.add_argument("--rgb-folder", type=Path, required=True)
    parser.add_argument("--tracks", type=Path)
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--behavior-id", required=True)
    parser.add_argument("--ood-tags", default="")
    parser.add_argument("--source-kind", default="scripted_carla")
    parser.add_argument("--claim-label", default="scripted_carla_ood_demo")
    parser.add_argument("--output-video", type=Path)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--min-frames", type=int, default=1)
    parser.add_argument("--ffmpeg-path")
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="ood-video-evidence")
    parser.set_defaults(func=_command_assemble_ood_video)


def _command_assemble_ood_video(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    tags = [tag.strip() for tag in str(args.ood_tags).split(",") if tag.strip()]
    summary = build_ood_video_evidence(
        run_dir,
        OodVideoEvidenceInputs(
            rgb_folder=args.rgb_folder,
            tracks_path=args.tracks,
            scenario_id=args.scenario_id,
            behavior_id=args.behavior_id,
            ood_tags=tags,
            source_kind=args.source_kind,
            claim_label=args.claim_label,
            output_video=args.output_video,
            fps=args.fps,
            min_frames=args.min_frames,
            ffmpeg_path=args.ffmpeg_path,
        ),
    )
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_ood_video_evidence_parser"]
