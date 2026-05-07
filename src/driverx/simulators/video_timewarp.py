"""Offline video time-warping for CARLA demo evidence."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VideoTimewarpResult:
    status: str
    input_path: str
    output_path: str
    speed_factor: float
    fps: int
    input_duration_s: float | None
    output_duration_s: float | None
    command: list[str]
    returncode: int | None
    stdout: str
    stderr: str
    blockers: list[str]
    claim_boundaries: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "speed_factor": self.speed_factor,
            "fps": self.fps,
            "input_duration_s": self.input_duration_s,
            "output_duration_s": self.output_duration_s,
            "command": self.command,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "blockers": self.blockers,
            "claim_boundaries": self.claim_boundaries,
        }


def timewarp_video(
    input_path: Path,
    output_path: Path,
    *,
    speed_factor: float,
    fps: int,
    ffmpeg_path: str | None = None,
    ffprobe_path: str | None = None,
    run: bool = True,
) -> VideoTimewarpResult:
    selected_ffmpeg = ffmpeg_path or shutil.which("ffmpeg")
    selected_ffprobe = ffprobe_path or shutil.which("ffprobe")
    blockers = _blockers(input_path, speed_factor, fps, selected_ffmpeg, selected_ffprobe)
    command = _command(selected_ffmpeg or "ffmpeg", input_path, output_path, speed_factor, fps)
    input_duration = _probe_duration(input_path, selected_ffprobe) if selected_ffprobe and input_path.exists() else None
    if blockers or not run:
        status = "blocked" if blockers else "planned"
        return VideoTimewarpResult(
            status=status,
            input_path=str(input_path),
            output_path=str(output_path),
            speed_factor=speed_factor,
            fps=fps,
            input_duration_s=input_duration,
            output_duration_s=None,
            command=command,
            returncode=None,
            stdout="",
            stderr="\n".join(blockers),
            blockers=blockers,
            claim_boundaries=_claim_boundaries(),
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    output_duration = _probe_duration(output_path, selected_ffprobe) if selected_ffprobe and output_path.exists() else None
    return VideoTimewarpResult(
        status="passed" if proc.returncode == 0 and output_path.exists() else "failed",
        input_path=str(input_path),
        output_path=str(output_path),
        speed_factor=speed_factor,
        fps=fps,
        input_duration_s=input_duration,
        output_duration_s=output_duration,
        command=command,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        blockers=[],
        claim_boundaries=_claim_boundaries(),
    )


def write_video_timewarp(run_dir: Path, result: VideoTimewarpResult) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = result.to_jsonable()
    json_path = run_dir / "video_timewarp.json"
    report_path = run_dir / "video_timewarp.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_report_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _blockers(
    input_path: Path,
    speed_factor: float,
    fps: int,
    ffmpeg_path: str | None,
    ffprobe_path: str | None,
) -> list[str]:
    blockers: list[str] = []
    if not input_path.exists():
        blockers.append(f"Input video does not exist: {input_path}")
    if speed_factor <= 0:
        blockers.append("speed_factor must be > 0")
    if fps <= 0:
        blockers.append("fps must be > 0")
    if not ffmpeg_path:
        blockers.append("ffmpeg was not found on PATH")
    if not ffprobe_path:
        blockers.append("ffprobe was not found on PATH")
    return blockers


def _command(ffmpeg_path: str, input_path: Path, output_path: Path, speed_factor: float, fps: int) -> list[str]:
    return [
        ffmpeg_path,
        "-y",
        "-i",
        str(input_path),
        "-filter:v",
        f"setpts=PTS/{speed_factor},fps={fps}",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        str(output_path),
    ]


def _probe_duration(path: Path, ffprobe_path: str | None) -> float | None:
    if ffprobe_path is None or not path.exists():
        return None
    proc = subprocess.run(
        [
            ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    try:
        return round(float(proc.stdout.strip()), 4)
    except ValueError:
        return None


def _claim_boundaries() -> list[str]:
    return [
        "time_warped_offline_demo=true",
        "real_time_vla_control=false",
        "source_video_retimed_for_presentation=true",
    ]


def _report_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Video Timewarp",
            "",
            f"- Status: `{payload['status']}`",
            f"- Input: `{payload['input_path']}`",
            f"- Output: `{payload['output_path']}`",
            f"- Speed: `{payload['speed_factor']}x`",
            f"- Input duration: `{payload['input_duration_s']}`",
            f"- Output duration: `{payload['output_duration_s']}`",
            "",
            "## Claim Boundaries",
            "",
            *[f"- `{item}`" for item in payload["claim_boundaries"]],
        ]
    ) + "\n"
