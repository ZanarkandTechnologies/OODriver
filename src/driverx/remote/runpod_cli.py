"""CLI glue for RunPod SSH resolution."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.remote.runpod import (
    DEFAULT_RUNPOD_REST_API,
    extract_runpod_pods,
    fetch_runpod_pods,
    load_env_values,
    select_runpod_ssh_target,
    write_runpod_ssh_resolution,
)


def register_runpod_remote_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "resolve-runpod-ssh",
        help="Resolve the current RunPod direct TCP SSH target from pod metadata.",
    )
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--pods-json", type=Path)
    parser.add_argument("--api-url", default=DEFAULT_RUNPOD_REST_API)
    parser.add_argument("--pod-id")
    parser.add_argument("--pod-name")
    parser.add_argument("--user", default="root")
    parser.add_argument("--ssh-key", type=Path, default=Path("~/.ssh/id_ed25519_runpod"))
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="runpod-ssh")
    parser.set_defaults(func=_command_resolve_runpod_ssh)


def _command_resolve_runpod_ssh(args: argparse.Namespace) -> int:
    if args.pods_json is not None:
        payload = json.loads(args.pods_json.read_text(encoding="utf-8"))
    else:
        values = load_env_values(args.env_file)
        api_key = values.get("RUNPOD_API_KEY") or os.environ.get("RUNPOD_API_KEY")
        if not api_key:
            print("driverx error: RUNPOD_API_KEY is not set.", file=sys.stderr)
            return 2
        payload = fetch_runpod_pods(api_key, api_url=args.api_url)
    pods = extract_runpod_pods(payload)
    target = select_runpod_ssh_target(
        pods,
        pod_id=args.pod_id,
        pod_name=args.pod_name,
        user=args.user,
        key_file=args.ssh_key,
    )
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_runpod_ssh_resolution(run_dir, target, pods)
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_runpod_remote_parser"]
