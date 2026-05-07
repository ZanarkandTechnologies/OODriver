"""CLI for deterministic agentic OOD scenario generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.scenarios.agentic_loop import (
    DEFAULT_SEED_THEMES,
    AgenticOodLoopConfig,
    run_agentic_ood_generation_loop,
)


def register_agentic_ood_loop_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "run-ood-generation-loop",
        help="Generate, novelty-score, curate, and queue OOD scenario candidates.",
    )
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--severity", type=int, default=4)
    parser.add_argument("--count-per-brief", type=int, default=1)
    parser.add_argument("--theme", action="append")
    parser.add_argument("--seeds-path", type=Path, default=Path("tests/fixtures/fail2drive_like/seeds.json"))
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--min-accept-score", type=float, default=0.55)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="agentic-ood-generation-loop")
    parser.set_defaults(func=_command_run_ood_generation_loop)


def _command_run_ood_generation_loop(args: argparse.Namespace) -> int:
    config = AgenticOodLoopConfig(
        count=max(1, args.count),
        random_seed=args.seed,
        severity=max(1, min(5, args.severity)),
        count_per_brief=max(1, args.count_per_brief),
        seed_themes=tuple(args.theme) if args.theme else DEFAULT_SEED_THEMES,
        seeds_path=args.seeds_path,
        catalog_path=args.catalog,
        output_root=args.output_root,
        run_id=args.run_id,
        min_accept_score=args.min_accept_score,
    )
    summary = run_agentic_ood_generation_loop(config)
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_agentic_ood_loop_parser"]
