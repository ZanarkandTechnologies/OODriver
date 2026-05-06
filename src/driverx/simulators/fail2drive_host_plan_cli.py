"""CLI for stock Fail2Drive graphics-host handoff planning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.simulators.fail2drive_host_plan import (
    Fail2DriveHostPlanConfig,
    build_fail2drive_host_plan,
    write_fail2drive_host_plan,
)


def command_plan_full_fail2drive_score_host(args: argparse.Namespace) -> int:
    diagnostics = _load_json(args.diagnostics) if args.diagnostics else None
    plan = build_fail2drive_host_plan(
        Fail2DriveHostPlanConfig(
            target_route=args.target_route,
            remote=args.remote,
            ssh_opts=args.ssh_opts,
            output_root_remote=args.remote_output_root,
            carla_version=args.carla_version,
        ),
        diagnostics_payload=diagnostics,
    )
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_fail2drive_host_plan(run_dir, plan)
    print(json.dumps(summary, indent=2))
    return 0


def register_fail2drive_host_plan_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "plan-full-fail2drive-score-host",
        help="Build the host checklist and command pack for one stock Fail2Drive score run.",
    )
    parser.add_argument("--target-route", default="Generalization_PedestriansOnRoad_1088")
    parser.add_argument("--remote")
    parser.add_argument("--ssh-opts")
    parser.add_argument("--remote-output-root", default="/workspace/0xdriver-artifacts/fail2drive-score")
    parser.add_argument("--carla-version", default="0.9.16")
    parser.add_argument("--diagnostics", type=Path)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="fail2drive-host-plan")
    parser.set_defaults(func=command_plan_full_fail2drive_score_host)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


__all__ = [
    "command_plan_full_fail2drive_score_host",
    "register_fail2drive_host_plan_parser",
]
