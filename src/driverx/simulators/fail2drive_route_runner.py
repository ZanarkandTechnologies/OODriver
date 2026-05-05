"""Execute a planned Fail2Drive route command with structured evidence."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Fail2DriveRouteRunConfig:
    plan_path: Path
    run_dir: Path
    timeout_s: float | None = 120.0
    dry_run: bool = False


@dataclass(frozen=True)
class ExpectedOutputStatus:
    label: str
    path: Path
    exists: bool
    size_bytes: int | None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "path": str(self.path),
            "exists": self.exists,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class Fail2DriveRouteRunResult:
    plan_path: Path
    run_dir: Path
    command: list[str]
    cwd: Path
    env: dict[str, str]
    dry_run: bool
    timeout_s: float | None
    started_at_monotonic_s: float | None
    finished_at_monotonic_s: float | None
    exit_code: int | None
    stdout_path: Path
    stderr_path: Path
    expected_outputs: list[ExpectedOutputStatus]
    route_blockers: list[str]
    error: str | None = None

    @property
    def status(self) -> str:
        if self.dry_run:
            return "planned" if not self.route_blockers else "blocked"
        if self.route_blockers:
            return "blocked"
        if self.error is not None:
            return "failed"
        return "passed" if self.exit_code == 0 else "failed"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "plan_path": str(self.plan_path),
            "run_dir": str(self.run_dir),
            "command": self.command,
            "cwd": str(self.cwd),
            "env": self.env,
            "dry_run": self.dry_run,
            "timeout_s": self.timeout_s,
            "started_at_monotonic_s": self.started_at_monotonic_s,
            "finished_at_monotonic_s": self.finished_at_monotonic_s,
            "duration_s": (
                round(self.finished_at_monotonic_s - self.started_at_monotonic_s, 6)
                if self.started_at_monotonic_s is not None and self.finished_at_monotonic_s is not None
                else None
            ),
            "exit_code": self.exit_code,
            "stdout_path": str(self.stdout_path),
            "stderr_path": str(self.stderr_path),
            "expected_outputs": [output.to_jsonable() for output in self.expected_outputs],
            "route_blockers": self.route_blockers,
            "error": self.error,
        }


def run_fail2drive_route(config: Fail2DriveRouteRunConfig) -> Fail2DriveRouteRunResult:
    """Run a planned Fail2Drive route command and capture durable evidence."""

    plan_path = config.plan_path.expanduser().resolve()
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    command = _resolve_command_executable([str(item) for item in list(payload.get("run_command", []))])
    cwd = Path(str(payload.get("cwd", "."))).expanduser().resolve()
    env = {str(key): str(value) for key, value in dict(payload.get("env", {})).items()}
    run_dir = config.run_dir.expanduser().resolve()
    log_dir = run_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = log_dir / "fail2drive_route.stdout.log"
    stderr_path = log_dir / "fail2drive_route.stderr.log"
    outputs = _expected_outputs(payload)
    route_blockers = _route_blockers(payload, command, cwd)
    if config.dry_run or route_blockers:
        return Fail2DriveRouteRunResult(
            plan_path=plan_path,
            run_dir=run_dir,
            command=command,
            cwd=cwd,
            env=env,
            dry_run=config.dry_run,
            timeout_s=config.timeout_s,
            started_at_monotonic_s=None,
            finished_at_monotonic_s=None,
            exit_code=None,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            expected_outputs=outputs,
            route_blockers=route_blockers,
        )
    started_at = time.monotonic()
    merged_env = os.environ.copy()
    merged_env.update(env)
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            env=merged_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=config.timeout_s,
            check=False,
        )
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        finished_at = time.monotonic()
        outputs = _expected_outputs(payload)
        inferred = _infer_runtime_blockers(completed.returncode, completed.stdout, completed.stderr)
        return Fail2DriveRouteRunResult(
            plan_path=plan_path,
            run_dir=run_dir,
            command=command,
            cwd=cwd,
            env=env,
            dry_run=False,
            timeout_s=config.timeout_s,
            started_at_monotonic_s=started_at,
            finished_at_monotonic_s=finished_at,
            exit_code=completed.returncode,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            expected_outputs=outputs,
            route_blockers=inferred,
        )
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(exc.stdout or "", encoding="utf-8")
        stderr_path.write_text(exc.stderr or "", encoding="utf-8")
        return Fail2DriveRouteRunResult(
            plan_path=plan_path,
            run_dir=run_dir,
            command=command,
            cwd=cwd,
            env=env,
            dry_run=False,
            timeout_s=config.timeout_s,
            started_at_monotonic_s=started_at,
            finished_at_monotonic_s=time.monotonic(),
            exit_code=None,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            expected_outputs=_expected_outputs(payload),
            route_blockers=["Fail2Drive route command timed out."],
            error=f"Timed out after {config.timeout_s} seconds.",
        )
    except OSError as exc:
        return Fail2DriveRouteRunResult(
            plan_path=plan_path,
            run_dir=run_dir,
            command=command,
            cwd=cwd,
            env=env,
            dry_run=False,
            timeout_s=config.timeout_s,
            started_at_monotonic_s=started_at,
            finished_at_monotonic_s=time.monotonic(),
            exit_code=None,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            expected_outputs=_expected_outputs(payload),
            route_blockers=[f"Failed to start Fail2Drive route command: {exc}"],
            error=str(exc),
        )


def write_fail2drive_route_run(
    run_dir: Path,
    result: Fail2DriveRouteRunResult,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = result.to_jsonable()
    json_path = run_dir / "fail2drive_route_run.json"
    report_path = run_dir / "fail2drive_route_run.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _expected_outputs(payload: dict[str, Any]) -> list[ExpectedOutputStatus]:
    outputs: list[ExpectedOutputStatus] = []
    for label, raw_path in dict(payload.get("expected_outputs", {})).items():
        path = Path(str(raw_path)).expanduser()
        exists = path.exists()
        outputs.append(
            ExpectedOutputStatus(
                label=str(label),
                path=path,
                exists=exists,
                size_bytes=path.stat().st_size if exists and path.is_file() else None,
            )
        )
    return outputs


def _route_blockers(payload: dict[str, Any], command: list[str], cwd: Path) -> list[str]:
    blockers: list[str] = []
    if not command:
        blockers.append("Plan contains no run_command.")
    if not cwd.exists():
        blockers.append(f"Fail2Drive cwd not found: {cwd}")
    elif not cwd.is_dir():
        blockers.append(f"Fail2Drive cwd must be a directory: {cwd}")
    for label in ("evaluator_path", "route_path", "agent_path"):
        raw = payload.get(label)
        if raw is None:
            blockers.append(f"Plan missing {label}.")
            continue
        path = Path(str(raw)).expanduser()
        if not path.exists():
            blockers.append(f"{label} not found: {path}")
        elif not path.is_file():
            blockers.append(f"{label} must be a file: {path}")
    return blockers


def _resolve_command_executable(command: list[str]) -> list[str]:
    if not command:
        return command
    if command[0] != "python":
        return command
    if shutil.which("python") is not None:
        return command
    replacement = shutil.which("python3") or sys.executable
    return [replacement, *command[1:]]


def _infer_runtime_blockers(returncode: int, stdout: str, stderr: str) -> list[str]:
    if returncode == 0:
        return []
    text = f"{stdout}\n{stderr}".lower()
    if "no module named" in text or "modulenotfounderror" in text:
        missing_module = _missing_module_name(stdout, stderr)
        suffix = f": {missing_module}" if missing_module else "; inspect stderr log for module name"
        return [f"Fail2Drive Python dependency is missing{suffix}."]
    if "connection refused" in text or "failed to connect" in text or "timeout" in text:
        return ["Fail2Drive could not connect to CARLA or timed out."]
    if "no such file" in text:
        return ["Fail2Drive route command referenced a missing file."]
    return [f"Fail2Drive route command exited non-zero: {returncode}."]


def _missing_module_name(stdout: str, stderr: str) -> str | None:
    match = re.search(r"No module named ['\"]([^'\"]+)['\"]", f"{stdout}\n{stderr}")
    return match.group(1) if match else None


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Fail2Drive Route Run",
        "",
        f"- status: `{payload.get('status')}`",
        f"- exit_code: `{payload.get('exit_code')}`",
        f"- duration_s: `{payload.get('duration_s')}`",
        f"- stdout: `{payload.get('stdout_path')}`",
        f"- stderr: `{payload.get('stderr_path')}`",
        "",
        "## Command",
        "",
        "```bash",
        _format_env(dict(payload.get("env", {}))),
        " ".join(str(item) for item in list(payload.get("command", []))),
        "```",
        "",
        "## Expected Outputs",
        "",
        "| label | exists | size_bytes | path |",
        "|---|---:|---:|---|",
    ]
    for output in list(payload.get("expected_outputs", [])):
        if isinstance(output, dict):
            lines.append(
                f"| `{output.get('label')}` | `{output.get('exists')}` | `{output.get('size_bytes')}` | `{output.get('path')}` |"
            )
    lines.extend(["", "## Blockers", ""])
    blockers = list(payload.get("route_blockers", []))
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("- none")
    return "\n".join(lines)


def _format_env(env: dict[str, str]) -> str:
    return " ".join(f"{key}={value!r}" for key, value in sorted(env.items()))


__all__ = [
    "ExpectedOutputStatus",
    "Fail2DriveRouteRunConfig",
    "Fail2DriveRouteRunResult",
    "run_fail2drive_route",
    "write_fail2drive_route_run",
]
