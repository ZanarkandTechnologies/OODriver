"""CLI glue for submission dossier generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.pipeline.submission_dossier import build_submission_dossier


def command_build_submission_dossier(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = build_submission_dossier(
        run_dir,
        ood_suite_manifest_path=args.ood_suite_manifest,
        gpu_host_suitability_path=args.gpu_host_suitability,
        demo_pack_path=args.demo_pack,
        reasoning_pack_path=args.reasoning_pack,
        campaign_summary_path=args.campaign_summary,
        alpamayo_batch_path=args.alpamayo_batch,
        cached_replay_path=args.cached_replay,
        progress_path=args.progress,
        blockers_path=args.blockers,
    )
    print(json.dumps(summary, indent=2))
    return 0


def register_submission_dossier_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "build-submission-dossier",
        help="Build a Markdown/JSON dossier from current OOD and GPU evidence.",
    )
    parser.add_argument("--ood-suite-manifest", type=Path)
    parser.add_argument("--gpu-host-suitability", type=Path)
    parser.add_argument("--demo-pack", type=Path)
    parser.add_argument("--reasoning-pack", type=Path)
    parser.add_argument("--campaign-summary", type=Path)
    parser.add_argument("--alpamayo-batch", type=Path)
    parser.add_argument("--cached-replay", type=Path)
    parser.add_argument("--progress", type=Path, default=Path("docs/archive/legacy-docs/progress.md"))
    parser.add_argument("--blockers", type=Path, default=Path("blockers.md"))
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="submission-dossier")
    parser.set_defaults(func=command_build_submission_dossier)


__all__ = ["command_build_submission_dossier", "register_submission_dossier_parser"]
