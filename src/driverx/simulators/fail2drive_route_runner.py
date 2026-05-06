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

from driverx.simulators.route_video_assembly import (
    assemble_route_video_from_watch,
    wait_for_rgb_frames,
)


@dataclass(frozen=True)
class Fail2DriveRouteRunConfig:
    plan_path: Path
    run_dir: Path
    timeout_s: float | None = 120.0
    dry_run: bool = False
    min_video_frames: int | None = None
    video_fps: int = 20
    video_timeout_s: float | None = None
    stop_after_video: bool = False
    ffmpeg_path: str | None = None


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
    frame_watch: dict[str, Any] | None = None
    video_assembly: dict[str, Any] | None = None

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
            "frame_watch": self.frame_watch,
            "video_assembly": self.video_assembly,
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
    if config.min_video_frames is not None:
        return _run_fail2drive_route_streaming(config, payload, command, cwd, env, run_dir, stdout_path, stderr_path)
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
        inferred = _post_run_blockers(
            completed.returncode,
            completed.stdout,
            completed.stderr,
            outputs,
        )
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
        timeout_stdout = _timeout_text(exc.stdout)
        timeout_stderr = _timeout_text(exc.stderr)
        stdout_path.write_text(timeout_stdout, encoding="utf-8")
        stderr_path.write_text(timeout_stderr, encoding="utf-8")
        outputs = _expected_outputs(payload)
        timeout_blockers = ["Fail2Drive route command timed out."]
        timeout_blockers.extend(_specific_runtime_blockers(timeout_stdout, timeout_stderr))
        timeout_blockers.extend(_checkpoint_blockers(outputs))
        timeout_blockers.extend(_missing_rgb_blockers(outputs))
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
            expected_outputs=outputs,
            route_blockers=timeout_blockers,
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


def _run_fail2drive_route_streaming(
    config: Fail2DriveRouteRunConfig,
    payload: dict[str, Any],
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    run_dir: Path,
    stdout_path: Path,
    stderr_path: Path,
) -> Fail2DriveRouteRunResult:
    started_at = time.monotonic()
    merged_env = os.environ.copy()
    merged_env.update(env)
    outputs = _expected_outputs(payload)
    rgb_folder = _expected_output_path(payload, "rgb_folder")
    video_output = _expected_output_path(payload, "video") or (run_dir / "route_partial.mp4")
    min_frames = max(1, int(config.min_video_frames or 1))
    video_timeout_s = float(config.video_timeout_s if config.video_timeout_s is not None else (config.timeout_s or 120.0))
    route_blockers: list[str] = []
    frame_watch: dict[str, Any] | None = None
    video_assembly: dict[str, Any] | None = None
    error: str | None = None
    exit_code: int | None = None

    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open("w", encoding="utf-8") as stderr_file:
            process = subprocess.Popen(
                command,
                cwd=str(cwd),
                env=merged_env,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
            )
            watch_deadline = started_at + video_timeout_s
            route_deadline = started_at + config.timeout_s if config.timeout_s is not None else None
            captured_video = False
            while True:
                exit_code = process.poll()
                if exit_code is not None:
                    break
                now = time.monotonic()
                if not captured_video and rgb_folder is not None:
                    watch = wait_for_rgb_frames(
                        rgb_folder,
                        min_frames=min_frames,
                        timeout_s=0.0,
                        poll_interval_s=0.0,
                    )
                    if watch.ready:
                        assembly = assemble_route_video_from_watch(
                            watch,
                            video_output,
                            fps=config.video_fps,
                            ffmpeg_path=config.ffmpeg_path,
                        )
                        frame_watch = watch.to_jsonable()
                        video_assembly = assembly.to_jsonable()
                        captured_video = bool(assembly.executed and assembly.returncode == 0)
                        if not captured_video:
                            route_blockers.extend(assembly.plan.live_blockers)
                        if config.stop_after_video:
                            route_blockers.append(
                                "Fail2Drive route stopped after early video capture; route score is intentionally partial."
                            )
                            process.terminate()
                            try:
                                exit_code = process.wait(timeout=10.0)
                            except subprocess.TimeoutExpired:
                                process.kill()
                                exit_code = process.wait(timeout=10.0)
                            break
                if not captured_video and rgb_folder is not None and now >= watch_deadline:
                    watch = wait_for_rgb_frames(
                        rgb_folder,
                        min_frames=min_frames,
                        timeout_s=0.0,
                        poll_interval_s=0.0,
                    )
                    frame_watch = watch.to_jsonable()
                    route_blockers.extend(watch.live_blockers)
                    if config.stop_after_video:
                        process.terminate()
                        try:
                            exit_code = process.wait(timeout=10.0)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            exit_code = process.wait(timeout=10.0)
                        break
                if route_deadline is not None and now >= route_deadline:
                    route_blockers.append("Fail2Drive route command timed out.")
                    process.kill()
                    exit_code = process.wait(timeout=10.0)
                    error = f"Timed out after {config.timeout_s} seconds."
                    break
                time.sleep(1.0)
    except OSError as exc:
        route_blockers.append(f"Failed to start Fail2Drive route command: {exc}")
        error = str(exc)

    finished_at = time.monotonic()
    outputs = _expected_outputs(payload)
    stdout = _read_log(stdout_path)
    stderr = _read_log(stderr_path)
    if exit_code is not None and not config.stop_after_video:
        route_blockers.extend(_post_run_blockers(exit_code, stdout, stderr, outputs))
    elif config.stop_after_video:
        route_blockers.extend(_checkpoint_blockers(outputs))
    if frame_watch is None and rgb_folder is not None:
        watch = wait_for_rgb_frames(
            rgb_folder,
            min_frames=min_frames,
            timeout_s=0.0,
            poll_interval_s=0.0,
        )
        frame_watch = watch.to_jsonable()
        if watch.ready and video_assembly is None:
            assembly = assemble_route_video_from_watch(
                watch,
                video_output,
                fps=config.video_fps,
                ffmpeg_path=config.ffmpeg_path,
            )
            video_assembly = assembly.to_jsonable()
            if not (assembly.executed and assembly.returncode == 0):
                route_blockers.extend(assembly.plan.live_blockers)
    return Fail2DriveRouteRunResult(
        plan_path=config.plan_path.expanduser().resolve(),
        run_dir=run_dir,
        command=command,
        cwd=cwd,
        env=env,
        dry_run=False,
        timeout_s=config.timeout_s,
        started_at_monotonic_s=started_at,
        finished_at_monotonic_s=finished_at,
        exit_code=exit_code,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        expected_outputs=outputs,
        route_blockers=_dedupe(route_blockers),
        error=error,
        frame_watch=frame_watch,
        video_assembly=video_assembly,
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


def _expected_output_path(payload: dict[str, Any], label: str) -> Path | None:
    raw_path = dict(payload.get("expected_outputs", {})).get(label)
    return Path(str(raw_path)).expanduser() if raw_path else None


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
    specific = _specific_runtime_blockers(stdout, stderr)
    if specific:
        return specific
    if "no module named" in text or "modulenotfounderror" in text:
        missing_module = _missing_module_name(stdout, stderr)
        suffix = f": {missing_module}" if missing_module else "; inspect stderr log for module name"
        return [f"Fail2Drive Python dependency is missing{suffix}."]
    if "connection refused" in text or "failed to connect" in text or "connection timed out" in text:
        return ["Fail2Drive could not connect to CARLA or timed out."]
    if "no such file" in text:
        return ["Fail2Drive route command referenced a missing file."]
    return [f"Fail2Drive route command exited non-zero: {returncode}."]


def _specific_runtime_blockers(stdout: str, stderr: str) -> list[str]:
    text = f"{stdout}\n{stderr}".lower()
    blockers: list[str] = []
    if "no module named" in text or "modulenotfounderror" in text:
        missing_module = _missing_module_name(stdout, stderr)
        suffix = f": {missing_module}" if missing_module else "; inspect stderr log for module name"
        blockers.append(f"Fail2Drive Python dependency is missing{suffix}.")
    if "connection refused" in text or "failed to connect" in text or "connection timed out" in text:
        blockers.append("Fail2Drive could not connect to CARLA or timed out.")
    if "map '" in text and "not found" in text:
        blockers.append("Fail2Drive route requires a CARLA map that is not installed.")
    return blockers


def _post_run_blockers(
    returncode: int,
    stdout: str,
    stderr: str,
    outputs: list[ExpectedOutputStatus],
) -> list[str]:
    blockers = _infer_runtime_blockers(returncode, stdout, stderr)
    blockers.extend(_checkpoint_blockers(outputs))
    blockers.extend(_missing_rgb_blockers(outputs))
    return blockers


def _checkpoint_blockers(outputs: list[ExpectedOutputStatus]) -> list[str]:
    result_output = next((output for output in outputs if output.label == "result" and output.exists), None)
    if result_output is None:
        return []
    try:
        payload = json.loads(result_output.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Fail2Drive result checkpoint could not be parsed: {exc}"]
    checkpoint = dict(payload.get("_checkpoint", {}))
    global_record = dict(checkpoint.get("global_record", {}))
    status = str(global_record.get("status", ""))
    blockers: list[str] = []
    if status.lower() == "failed":
        blockers.append("Fail2Drive result checkpoint reports global status Failed.")
    for record in list(checkpoint.get("records", [])):
        if not isinstance(record, dict):
            continue
        record_status = str(record.get("status", ""))
        if "failed" in record_status.lower():
            route_id = str(record.get("route_id", "unknown-route"))
            blockers.append(f"Fail2Drive route record failed: {route_id}: {record_status}")
    return blockers


def _missing_rgb_blockers(outputs: list[ExpectedOutputStatus]) -> list[str]:
    rgb_output = next((output for output in outputs if output.label == "rgb_folder"), None)
    if rgb_output is None:
        return []
    if not rgb_output.exists:
        return [f"RGB frames were not produced by Fail2Drive route run: {rgb_output.path}"]
    if not _frame_paths(rgb_output.path):
        return [f"No RGB frames found in Fail2Drive route output: {rgb_output.path}"]
    return []


def _missing_module_name(stdout: str, stderr: str) -> str | None:
    match = re.search(r"No module named ['\"]([^'\"]+)['\"]", f"{stdout}\n{stderr}")
    return match.group(1) if match else None


def _timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _frame_paths(folder: Path) -> list[Path]:
    if not folder.exists() or not folder.is_dir():
        return []
    suffixes = {".jpg", ".jpeg", ".png"}
    return sorted(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in suffixes)


def _read_log(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item not in seen:
            output.append(item)
            seen.add(item)
    return output


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
    frame_watch = dict(payload.get("frame_watch") or {})
    video_assembly = dict(payload.get("video_assembly") or {})
    if frame_watch or video_assembly:
        lines.extend(
            [
                "",
                "## Early Video",
                "",
                f"- frame_watch_ready: `{frame_watch.get('ready')}`",
                f"- frame_count: `{frame_watch.get('frame_count')}`",
                f"- video_status: `{video_assembly.get('status')}`",
                f"- output_video: `{dict(video_assembly.get('plan') or {}).get('output_video')}`",
            ]
        )
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
