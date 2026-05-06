"""DriverX-owned route video assembly from Fail2Drive RGB frames."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RouteVideoAssemblyPlan:
    rgb_folder: Path
    output_video: Path
    fps: int
    frame_count: int
    frame_pattern: str | None
    ffmpeg_path: str | None
    command: list[str]
    live_blockers: list[str]
    dry_run: bool = True

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "rgb_folder": str(self.rgb_folder),
            "output_video": str(self.output_video),
            "fps": self.fps,
            "frame_count": self.frame_count,
            "frame_pattern": self.frame_pattern,
            "ffmpeg_path": self.ffmpeg_path,
            "command": self.command,
            "live_blockers": self.live_blockers,
            "dry_run": self.dry_run,
        }


@dataclass(frozen=True)
class RouteVideoAssemblyRun:
    plan: RouteVideoAssemblyPlan
    returncode: int | None
    stdout: str
    stderr: str
    executed: bool

    @property
    def status(self) -> str:
        if not self.executed:
            return "blocked" if self.plan.live_blockers else "planned"
        return "passed" if self.returncode == 0 else "failed"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "plan": self.plan.to_jsonable(),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "executed": self.executed,
        }


@dataclass(frozen=True)
class FrameWatchResult:
    rgb_folder: Path
    min_frames: int
    timeout_s: float
    poll_interval_s: float
    waited_s: float
    frame_count: int
    ready: bool
    first_frame: Path | None
    last_frame: Path | None
    live_blockers: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "rgb_folder": str(self.rgb_folder),
            "min_frames": self.min_frames,
            "timeout_s": self.timeout_s,
            "poll_interval_s": self.poll_interval_s,
            "waited_s": self.waited_s,
            "frame_count": self.frame_count,
            "ready": self.ready,
            "first_frame": str(self.first_frame) if self.first_frame else None,
            "last_frame": str(self.last_frame) if self.last_frame else None,
            "live_blockers": self.live_blockers,
        }


def wait_for_rgb_frames(
    rgb_folder: Path,
    *,
    min_frames: int,
    timeout_s: float,
    poll_interval_s: float = 1.0,
) -> FrameWatchResult:
    """Wait until a Fail2Drive RGB folder contains enough frames for video evidence."""

    folder = rgb_folder.expanduser().resolve()
    needed = max(1, min_frames)
    started_at = time.monotonic()
    deadline = started_at + max(0.0, timeout_s)
    frames: list[Path] = []
    while True:
        frames = _frame_paths(folder)
        if len(frames) >= needed:
            return _frame_watch_result(
                folder,
                needed,
                timeout_s,
                poll_interval_s,
                started_at,
                frames,
                ready=True,
            )
        if time.monotonic() >= deadline:
            return _frame_watch_result(
                folder,
                needed,
                timeout_s,
                poll_interval_s,
                started_at,
                frames,
                ready=False,
            )
        time.sleep(max(0.0, poll_interval_s))


def assemble_route_video_from_watch(
    watch: FrameWatchResult,
    output_video: Path,
    *,
    fps: int = 20,
    ffmpeg_path: str | None = None,
) -> RouteVideoAssemblyRun:
    """Assemble MP4 evidence from a completed frame watch result."""

    if not watch.ready:
        plan = RouteVideoAssemblyPlan(
            rgb_folder=watch.rgb_folder,
            output_video=output_video.expanduser().resolve(),
            fps=fps,
            frame_count=watch.frame_count,
            frame_pattern=None,
            ffmpeg_path=ffmpeg_path or shutil.which("ffmpeg"),
            command=[],
            live_blockers=[
                *watch.live_blockers,
                f"Frame watch did not reach {watch.min_frames} frame(s).",
            ],
        )
        return RouteVideoAssemblyRun(
            plan=plan,
            returncode=None,
            stdout="",
            stderr="\n".join(plan.live_blockers),
            executed=False,
        )
    plan = plan_route_video_assembly(
        watch.rgb_folder,
        output_video=output_video,
        fps=fps,
        ffmpeg_path=ffmpeg_path,
    )
    return run_route_video_assembly(plan)


def plan_route_video_assembly(
    rgb_folder: Path,
    *,
    output_video: Path | None = None,
    fps: int = 20,
    ffmpeg_path: str | None = None,
) -> RouteVideoAssemblyPlan:
    folder = rgb_folder.expanduser().resolve()
    video = (
        output_video.expanduser().resolve()
        if output_video is not None
        else folder.parent.parent / f"{folder.parent.name}.mp4"
    )
    selected_ffmpeg = ffmpeg_path or shutil.which("ffmpeg")
    frames = _frame_paths(folder)
    pattern = _frame_pattern(frames)
    blockers = _blockers(folder, frames, selected_ffmpeg)
    command = (
        [
            selected_ffmpeg or "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-pattern_type",
            "glob",
            "-i",
            pattern or str(folder / "*.png"),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "26",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(video),
        ]
        if pattern is not None
        else []
    )
    return RouteVideoAssemblyPlan(
        rgb_folder=folder,
        output_video=video,
        fps=fps,
        frame_count=len(frames),
        frame_pattern=pattern,
        ffmpeg_path=selected_ffmpeg,
        command=command,
        live_blockers=blockers,
    )


def run_route_video_assembly(plan: RouteVideoAssemblyPlan) -> RouteVideoAssemblyRun:
    if plan.live_blockers:
        return RouteVideoAssemblyRun(
            plan=plan,
            returncode=None,
            stdout="",
            stderr="\n".join(plan.live_blockers),
            executed=False,
        )
    plan.output_video.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        plan.command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return RouteVideoAssemblyRun(
        plan=plan,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        executed=True,
    )


def write_route_video_assembly(
    run_dir: Path,
    result: RouteVideoAssemblyPlan | RouteVideoAssemblyRun,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = (
        {"status": "blocked" if result.live_blockers else "planned", "plan": result.to_jsonable()}
        if isinstance(result, RouteVideoAssemblyPlan)
        else result.to_jsonable()
    )
    json_path = run_dir / "route_video_assembly.json"
    report_path = run_dir / "route_video_assembly.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _frame_paths(folder: Path) -> list[Path]:
    if not folder.exists() or not folder.is_dir():
        return []
    suffixes = {".png", ".jpg", ".jpeg"}
    return sorted(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in suffixes)


def _frame_pattern(frames: list[Path]) -> str | None:
    if not frames:
        return None
    suffix = frames[0].suffix.lower()
    return str(frames[0].parent / f"*{suffix}")


def _blockers(folder: Path, frames: list[Path], ffmpeg_path: str | None) -> list[str]:
    blockers: list[str] = []
    if not folder.exists():
        blockers.append(f"RGB folder not found: {folder}")
    elif not folder.is_dir():
        blockers.append(f"RGB folder must be a directory: {folder}")
    elif not frames:
        blockers.append(f"No RGB frames found in {folder}; expected .png, .jpg, or .jpeg files.")
    if ffmpeg_path is None:
        blockers.append("ffmpeg not found on PATH; install ffmpeg or pass --ffmpeg-path.")
    return blockers


def _frame_watch_result(
    folder: Path,
    min_frames: int,
    timeout_s: float,
    poll_interval_s: float,
    started_at: float,
    frames: list[Path],
    *,
    ready: bool,
) -> FrameWatchResult:
    blockers: list[str] = []
    if not ready:
        if not folder.exists():
            blockers.append(f"RGB folder not found before timeout: {folder}")
        else:
            blockers.append(
                f"Only {len(frames)} RGB frame(s) found before timeout; expected {min_frames}."
            )
    return FrameWatchResult(
        rgb_folder=folder,
        min_frames=min_frames,
        timeout_s=timeout_s,
        poll_interval_s=poll_interval_s,
        waited_s=round(time.monotonic() - started_at, 6),
        frame_count=len(frames),
        ready=ready,
        first_frame=frames[0] if frames else None,
        last_frame=frames[-1] if frames else None,
        live_blockers=blockers,
    )


def _markdown(payload: dict[str, Any]) -> str:
    plan = dict(payload.get("plan", {}))
    lines = [
        "# Route Video Assembly",
        "",
        f"- status: `{payload.get('status')}`",
        f"- rgb_folder: `{plan.get('rgb_folder')}`",
        f"- output_video: `{plan.get('output_video')}`",
        f"- frame_count: `{plan.get('frame_count')}`",
        f"- ffmpeg_path: `{plan.get('ffmpeg_path')}`",
        "",
        "## Command",
        "",
        "```bash",
        " ".join(str(item) for item in list(plan.get("command", []))),
        "```",
        "",
        "## Blockers",
        "",
    ]
    blockers = list(plan.get("live_blockers", []))
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("- none")
    return "\n".join(lines)


__all__ = [
    "FrameWatchResult",
    "RouteVideoAssemblyPlan",
    "RouteVideoAssemblyRun",
    "assemble_route_video_from_watch",
    "plan_route_video_assembly",
    "run_route_video_assembly",
    "wait_for_rgb_frames",
    "write_route_video_assembly",
]
