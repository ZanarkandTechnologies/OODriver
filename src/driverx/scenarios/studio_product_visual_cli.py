"""Visual-fidelity gate CLI registration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_visual_runtime import run_studio_score_visual_fidelity


def register_visual_commands(nested: argparse._SubParsersAction) -> None:
    score = nested.add_parser("score-visual-fidelity", help="Score whether CARLA media visibly matches an agent-authored scenario.")
    score.add_argument("--media-manifest", type=Path, required=True)
    score.add_argument("--output-root", type=Path)
    score.add_argument("--run-id", default="oodrive-visual-fidelity-score")
    score.add_argument("--threshold", type=float, default=90.0)
    score.add_argument("--metric-only", action="store_true")
    score.set_defaults(func=_command_score_visual_fidelity)


def _print(result: StudioCommandResult) -> int:
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_score_visual_fidelity(args: argparse.Namespace) -> int:
    return _print(
        run_studio_score_visual_fidelity(
            media_manifest_path=args.media_manifest,
            output_root=args.output_root,
            run_id=args.run_id,
            threshold=args.threshold,
            metric_only=args.metric_only,
        )
    )


__all__ = ["register_visual_commands"]
