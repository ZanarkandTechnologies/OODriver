"""CLI for Alpamayo OOD batch comparison planning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.pipeline.alpamayo_ood_batch import (
    AlpamayoOodBatchConfig,
    AlpamayoRemoteConfig,
    run_alpamayo_ood_batch,
)


def command_run_alpamayo_ood_batch(args: argparse.Namespace) -> int:
    config = AlpamayoOodBatchConfig(
        output_root=args.output_root,
        run_id=args.run_id,
        campaign_summary_path=args.campaign,
        package_paths=tuple(args.package or ()),
        baseline_decision_paths=tuple(args.baseline_decision or ()),
        memory_decision_paths=tuple(args.memory_decision or ()),
        comparison_paths=tuple(args.comparison or ()),
        limit=args.limit,
        execute_remote=args.execute_remote,
        remote=AlpamayoRemoteConfig(
            remote=args.remote,
            ssh_opts=args.ssh_opts,
            python_bin=args.python_bin,
            attn_implementation=args.attn_implementation,
            num_traj_samples=args.num_traj_samples,
        ),
    )
    summary = run_alpamayo_ood_batch(config)
    print(json.dumps(summary, indent=2))
    return 0 if summary.get("status") in {"passed", "planned", "blocked"} else 2


def register_alpamayo_ood_batch_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "run-alpamayo-ood-batch",
        help="Plan or execute Alpamayo inference over generated OOD cases.",
    )
    parser.add_argument("--campaign", type=Path)
    parser.add_argument("--package", type=Path, action="append")
    parser.add_argument("--baseline-decision", type=Path, action="append")
    parser.add_argument("--memory-decision", type=Path, action="append")
    parser.add_argument("--comparison", type=Path, action="append")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--execute-remote", action="store_true")
    parser.add_argument("--remote", default="root@195.26.233.80")
    parser.add_argument("--ssh-opts", default="-p 55050 -i ~/.ssh/id_ed25519_runpod")
    parser.add_argument("--python-bin", default="/workspace/alpamayo1.5/a1_5_venv/bin/python")
    parser.add_argument("--attn-implementation", default="eager")
    parser.add_argument("--num-traj-samples", type=int, default=1)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="alpamayo-ood-batch")
    parser.set_defaults(func=command_run_alpamayo_ood_batch)


__all__ = ["command_run_alpamayo_ood_batch", "register_alpamayo_ood_batch_parser"]
