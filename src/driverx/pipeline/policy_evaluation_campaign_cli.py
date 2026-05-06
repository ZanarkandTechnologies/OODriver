"""CLI for policy evaluation campaigns over scenario catalogs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.pipeline.policy_evaluation_campaign import (
    PolicyEvaluationCampaignConfig,
    run_policy_evaluation_campaign,
)


def register_policy_evaluation_campaign_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "run-policy-evaluation-campaign",
        help="Run a policy evidence matrix over cataloged generated OOD scenarios.",
    )
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--policy-mode", action="append")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="policy-evaluation-campaign")
    parser.set_defaults(func=_command_run_policy_evaluation_campaign)


def _command_run_policy_evaluation_campaign(args: argparse.Namespace) -> int:
    summary = run_policy_evaluation_campaign(
        PolicyEvaluationCampaignConfig(
            catalog_path=args.catalog,
            selection_path=args.selection,
            policy_modes=tuple(args.policy_mode) if args.policy_mode else (
                "deterministic-baseline",
                "memory-guided",
                "alpamayo-open-loop",
            ),
            limit=args.limit,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_policy_evaluation_campaign_parser"]
