"""CLI for final SoTA submission pack V7."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.pipeline.final_submission_pack import run_final_submission_pack


def register_final_submission_pack_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "build-final-submission-pack",
        help="Build the final V7 judge-facing submission dossier, script, write-up, and artifact map.",
    )
    parser.add_argument("--eval-matrix", type=Path)
    parser.add_argument("--scenario-studio", type=Path)
    parser.add_argument("--alpamayo-rag-batch", type=Path)
    parser.add_argument("--fail2drive-extension", type=Path)
    parser.add_argument("--hero-video-evidence", type=Path)
    parser.add_argument("--scenario-browser", type=Path)
    parser.add_argument("--blockers", type=Path, default=Path("blockers.md"))
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="final-submission-pack-v7")
    parser.set_defaults(func=_command_build_final_submission_pack)


def _command_build_final_submission_pack(args: argparse.Namespace) -> int:
    summary = run_final_submission_pack(
        output_root=args.output_root,
        run_id=args.run_id,
        eval_matrix_path=args.eval_matrix,
        scenario_studio_path=args.scenario_studio,
        alpamayo_rag_batch_path=args.alpamayo_rag_batch,
        fail2drive_extension_path=args.fail2drive_extension,
        hero_video_evidence_path=args.hero_video_evidence,
        scenario_browser_path=args.scenario_browser,
        blockers_path=args.blockers,
    )
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_final_submission_pack_parser"]
