"""CLI for scripted OOD campaign execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.pipeline.scripted_ood_campaign import (
    load_scripted_ood_campaign_config,
    run_scripted_ood_campaign,
)


def command_run_scripted_ood_campaign(args: argparse.Namespace) -> int:
    config = load_scripted_ood_campaign_config(args.config)
    updates: dict[str, Any] = {}
    if args.limit is not None:
        updates["count"] = args.limit
    if args.live:
        updates["live"] = True
    if args.assemble_video:
        updates["assemble_video"] = True
    if args.run_id:
        updates["run_id"] = args.run_id
    if args.output_root is not None:
        updates["output_root"] = args.output_root
    if updates:
        config = type(config)(**{**config.__dict__, **updates})
    summary = run_scripted_ood_campaign(config)
    print(json.dumps(summary, indent=2))
    return 0 if summary.get("status") in {"passed", "partial"} else 2


def register_scripted_ood_campaign_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "run-scripted-ood-campaign",
        help="Run or fake-plan a small campaign of generated scripted CARLA OOD cases.",
    )
    parser.add_argument("--config", type=Path, default=Path("configs/scripted_ood_campaign.local.sample.yaml"))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--assemble-video", action="store_true")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--run-id", default=None)
    parser.set_defaults(func=command_run_scripted_ood_campaign)


__all__ = ["command_run_scripted_ood_campaign", "register_scripted_ood_campaign_parser"]
