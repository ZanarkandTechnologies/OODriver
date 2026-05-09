"""Route-video smoke planning for Fail2Drive without launching CARLA."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from driverx.simulators.carla import CarlaRunConfig


@dataclass(frozen=True)
class Fail2DriveVideoSmokeConfig:
    host: str
    port: int
    fail2drive_root: Path
    carla_root: Path | None
    route_path: Path
    agent_path: Path
    output_dir: Path
    track: str = "MAP"
    timeout_s: float = 300.0
    live_visu: bool = True
    method_name: str = "DriverXRouteSmoke"
    agent_config: Path | None = None
    traffic_manager_port: int | None = None

    @classmethod
    def from_carla_config(
        cls,
        config: CarlaRunConfig,
        *,
        output_dir: Path | None = None,
        timeout_s: float = 300.0,
        live_visu: bool = True,
        method_name: str = "DriverXRouteSmoke",
        agent_config: Path | None = None,
        traffic_manager_port: int | None = None,
    ) -> "Fail2DriveVideoSmokeConfig":
        return cls(
            host=config.host,
            port=config.port,
            fail2drive_root=config.fail2drive_root,
            carla_root=config.carla_root,
            route_path=config.route_path,
            agent_path=config.agent_path,
            output_dir=output_dir if output_dir is not None else config.output_dir,
            track=config.track,
            timeout_s=timeout_s,
            live_visu=live_visu,
            method_name=method_name,
            agent_config=agent_config,
            traffic_manager_port=traffic_manager_port,
        )


@dataclass(frozen=True)
class Fail2DriveVideoSmokePlan:
    route_path: Path
    agent_path: Path
    evaluator_path: Path
    video_tool_path: Path
    cwd: Path
    run_command: list[str]
    video_command: list[str]
    env: dict[str, str]
    expected_outputs: dict[str, Path]
    live_blockers: list[str]
    dry_run: bool = True

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "route_path": str(self.route_path),
            "agent_path": str(self.agent_path),
            "evaluator_path": str(self.evaluator_path),
            "video_tool_path": str(self.video_tool_path),
            "cwd": str(self.cwd),
            "run_command": self.run_command,
            "video_command": self.video_command,
            "env": self.env,
            "expected_outputs": {
                key: str(value)
                for key, value in self.expected_outputs.items()
            },
            "live_blockers": self.live_blockers,
            "dry_run": self.dry_run,
        }


def plan_fail2drive_video_smoke(
    config: Fail2DriveVideoSmokeConfig,
) -> Fail2DriveVideoSmokePlan:
    root = config.fail2drive_root.expanduser().resolve()
    route_path = _resolve_under(root, config.route_path).resolve()
    agent_path = _resolve_under(root, config.agent_path).resolve()
    agent_config = (
        _resolve_under(root, config.agent_config).resolve()
        if config.agent_config is not None
        else None
    )
    output_dir = config.output_dir.expanduser().resolve()
    save_path = output_dir / "visualizations"
    rgb_folder = save_path / _route_stem(route_path) / "rgb"
    result_path = output_dir / f"{_route_stem(route_path)}_res.json"
    debug_path = output_dir / f"{_route_stem(route_path)}_debug.txt"
    video_path = output_dir / f"{_route_stem(route_path)}.mp4"
    evaluator = root / "leaderboard" / "leaderboard" / "leaderboard_evaluator_local.py"
    video_tool = root / "tools" / "generate_video.py"
    run_command = [
        "python",
        str(evaluator),
        "--routes",
        str(route_path),
        "--repetitions",
        "1",
        "--track",
        config.track,
        "--checkpoint",
        str(result_path),
        "--debug-checkpoint",
        str(debug_path),
        "--timeout",
        str(int(config.timeout_s)),
        "--agent",
        str(agent_path),
        "--host",
        config.host,
        "--port",
        str(config.port),
    ]
    if config.traffic_manager_port is not None:
        run_command.extend(["--traffic-manager-port", str(config.traffic_manager_port)])
    if agent_config is not None:
        run_command.extend(["--agent-config", str(agent_config)])
    video_command = [
        "python",
        str(video_tool),
        "-f",
        str(rgb_folder),
        "-o",
        str(video_path),
    ]
    env = {
        "CARLA_HOST": config.host,
        "CARLA_PORT": str(config.port),
        "FAIL2DRIVE_ROOT": str(root),
        "DRIVERX_METHOD_NAME": config.method_name,
        "REPETITION": "0",
        "SAVE_PATH": str(save_path),
        "SCENARIO_RUNNER_ROOT": str(root / "scenario_runner"),
        "TOWN": _route_town(route_path),
        "VIZ_PATH": str(rgb_folder),
        "PYTHONPATH": _fail2drive_pythonpath(root, config.carla_root),
    }
    if config.live_visu:
        env["LIVE_VISU"] = "1"
    blockers = _live_blockers(
        root=root,
        evaluator=evaluator,
        route_path=route_path,
        agent_path=agent_path,
        agent_config=agent_config,
        video_tool=video_tool,
        rgb_folder=rgb_folder,
    )
    return Fail2DriveVideoSmokePlan(
        route_path=route_path,
        agent_path=agent_path,
        evaluator_path=evaluator,
        video_tool_path=video_tool,
        cwd=root,
        run_command=run_command,
        video_command=video_command,
        env=env,
        expected_outputs={
            "result": result_path,
            "debug": debug_path,
            "save_path": save_path,
            "rgb_folder": rgb_folder,
            "video": video_path,
        },
        live_blockers=blockers,
    )


def write_fail2drive_video_smoke_plan(
    run_dir: Path,
    plan: Fail2DriveVideoSmokePlan,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = plan.to_jsonable()
    json_path = run_dir / "fail2drive_video_smoke_plan.json"
    report_path = run_dir / "fail2drive_video_smoke_plan.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown_report(plan), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def _resolve_under(root: Path, path: Path | None) -> Path:
    if path is None:
        raise ValueError("Path is required.")
    expanded = path.expanduser()
    return expanded if expanded.is_absolute() else root / expanded


def _route_stem(route_path: Path) -> str:
    return route_path.stem or "route"


def _route_town(route_path: Path) -> str:
    try:
        root = ET.parse(route_path).getroot()
    except (OSError, ET.ParseError):
        return ""
    route = root.find("route")
    if route is None:
        return ""
    return str(route.attrib.get("town", ""))


def _fail2drive_pythonpath(root: Path, carla_root: Path | None) -> str:
    paths = [
        root,
        root / "leaderboard",
        root / "scenario_runner",
        root / "team_code",
    ]
    if carla_root is not None:
        resolved_carla_root = carla_root.expanduser().resolve()
        paths.extend(
            [
                resolved_carla_root / "PythonAPI" / "carla",
                resolved_carla_root / "carla",
            ]
        )
    existing = os.environ.get("PYTHONPATH")
    if existing:
        paths.extend(Path(item) for item in existing.split(os.pathsep) if item)
    return os.pathsep.join(str(path) for path in paths)


def _live_blockers(
    *,
    root: Path,
    evaluator: Path,
    route_path: Path,
    agent_path: Path,
    agent_config: Path | None,
    video_tool: Path,
    rgb_folder: Path,
) -> list[str]:
    blockers: list[str] = []
    if not root.exists():
        blockers.append(f"Fail2Drive checkout not found: {root}")
    elif not root.is_dir():
        blockers.append(f"Fail2Drive root must be a directory: {root}")
    blockers.extend(_missing_file_blocker(evaluator, "Fail2Drive evaluator"))
    blockers.extend(_missing_file_blocker(route_path, "Fail2Drive route"))
    blockers.extend(_missing_file_blocker(agent_path, "Fail2Drive agent"))
    if agent_config is not None:
        blockers.extend(_missing_path_blocker(agent_config, "Fail2Drive agent config"))
    blockers.extend(_missing_file_blocker(video_tool, "Fail2Drive video tool"))
    if not rgb_folder.exists():
        blockers.append(
            "RGB folder does not exist yet; run the route command with SAVE_PATH "
            f"before generating video: {rgb_folder}"
        )
    return blockers


def _missing_file_blocker(path: Path, label: str) -> list[str]:
    if not path.exists():
        return [f"{label} not found: {path}"]
    if not path.is_file():
        return [f"{label} must be a file: {path}"]
    return []


def _missing_path_blocker(path: Path, label: str) -> list[str]:
    if not path.exists():
        return [f"{label} not found: {path}"]
    return []


def _markdown_report(plan: Fail2DriveVideoSmokePlan) -> str:
    outputs = plan.expected_outputs
    lines = [
        "# Fail2Drive Video Smoke Plan",
        "",
        f"- dry_run: `{plan.dry_run}`",
        f"- route_path: `{plan.route_path}`",
        f"- agent_path: `{plan.agent_path}`",
        f"- cwd: `{plan.cwd}`",
        f"- blockers: `{len(plan.live_blockers)}`",
        "",
        "## Route Command",
        "",
        "```bash",
        _format_env(plan.env),
        " ".join(plan.run_command),
        "```",
        "",
        "## Video Command",
        "",
        "```bash",
        " ".join(plan.video_command),
        "```",
        "",
        "## Expected Outputs",
        "",
        f"- result: `{outputs['result']}`",
        f"- debug: `{outputs['debug']}`",
        f"- save_path: `{outputs['save_path']}`",
        f"- rgb_folder: `{outputs['rgb_folder']}`",
        f"- video: `{outputs['video']}`",
        "",
        "## Live Blockers",
        "",
    ]
    if plan.live_blockers:
        lines.extend(f"- {blocker}" for blocker in plan.live_blockers)
    else:
        lines.append("- None. CARLA/live runtime is ready to try the command.")
    lines.append("")
    return "\n".join(lines)


def _format_env(env: dict[str, str]) -> str:
    return " ".join(f"{key}={value!r}" for key, value in sorted(env.items()))


__all__ = [
    "Fail2DriveVideoSmokeConfig",
    "Fail2DriveVideoSmokePlan",
    "plan_fail2drive_video_smoke",
    "write_fail2drive_video_smoke_plan",
]
