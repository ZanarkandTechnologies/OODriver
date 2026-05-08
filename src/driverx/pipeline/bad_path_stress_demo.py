"""Bad-path stress demo generation for OODrive."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir


DEFAULT_CASE_IDS = (
    "static_blocker_stop",
    "road_hole_swerve_recover",
    "rolling_object_yield_swerve",
    "compound_obstacle_detour",
)

CLAIM_BOUNDARIES = [
    "local_scripted_stress_demo=true",
    "carla_visual_evidence=false",
    "closed_loop_vla_control=false",
    "real_time_vla_control=false",
    "sampled_open_loop_reasoning=true",
]

# MEM-0041: local stress demos cannot pass by escaping the drivable corridor.
DRIVABLE_CORRIDOR_HALF_WIDTH_M = 3.25
ADJACENT_LANE_CENTER_M = 2.75


def build_bad_path_stress_demo(
    *,
    output_root: Path,
    run_id: str,
    case_ids: tuple[str, ...] = DEFAULT_CASE_IDS,
    target_duration_s: float = 60.0,
    fps: int = 8,
) -> dict[str, Any]:
    """Build a deterministic stress reel for bad-path autonomy tasks."""

    run_dir = prepare_run_dir(output_root, run_id)
    selected = tuple(case_ids or DEFAULT_CASE_IDS)
    cases = [_simulate_case(case_id) for case_id in selected]
    score = _score(cases)
    manifest: dict[str, Any] = {
        "status": "passed" if score >= 90.0 and all(case["guarded"]["task_pass"] for case in cases) else "blocked",
        "run_id": run_dir.name,
        "case_count": len(cases),
        "bad_path_stress_score": score,
        "target_duration_s": max(9.0, target_duration_s),
        "fps": fps,
        "cases": cases,
        "claim_boundaries": list(CLAIM_BOUNDARIES),
        "blockers": [],
    }
    video = _render_video(
        run_dir=run_dir,
        manifest=manifest,
        target_duration_s=max(9.0, target_duration_s),
        fps=max(1, fps),
    )
    manifest["video_render"] = video
    manifest["video_path"] = video.get("video_path") if video.get("status") == "passed" else None
    if video.get("blockers"):
        manifest["blockers"] = list(video["blockers"])
    return write_bad_path_stress_demo(run_dir, manifest)


def write_bad_path_stress_demo(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Write JSON, Markdown, and HTML stress-demo artifacts."""

    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "bad_path_stress_demo.json"
    report_path = run_dir / "bad_path_stress_demo.md"
    html_path = run_dir / "bad_path_stress_demo.html"
    payload = {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
        "html_path": str(html_path),
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    html_path.write_text(_html(payload), encoding="utf-8")
    return payload


def _simulate_case(case_id: str) -> dict[str, Any]:
    if case_id == "static_blocker_stop":
        return _static_blocker_case()
    if case_id == "road_hole_swerve_recover":
        return _road_hole_case()
    if case_id == "rolling_object_yield_swerve":
        return _rolling_object_case()
    if case_id == "compound_obstacle_detour":
        return _compound_obstacle_detour_case()
    raise ValueError(f"Unknown bad-path stress case: {case_id}")


def _static_blocker_case() -> dict[str, Any]:
    hazard = {"kind": "static_object", "label": "stalled crate stack", "x_m": 18.0, "y_m": 0.0, "radius_m": 1.2}
    times = _times(8.0)
    baseline = [_state(t, 1.0 + 4.0 * t, 0.0, 4.0, 0.0, 0.34, 0.0, "GO") for t in times]
    guarded = []
    for t in times:
        if t < 2.5:
            guarded.append(_state(t, 1.0 + 4.0 * t, 0.0, 4.0, 0.0, 0.28, 0.0, "APPROACH"))
        elif t < 4.0:
            p = (t - 2.5) / 1.5
            x = 11.0 + 3.5 * (1.0 - (1.0 - p) ** 2)
            guarded.append(_state(t, x, 0.0, 4.0 * (1.0 - p), 0.0, 0.0, 0.2 + 0.55 * p, "STOP"))
        else:
            guarded.append(_state(t, 14.5, 0.0, 0.0, 0.0, 0.0, 0.75, "HOLD"))
    return _case_payload(
        case_id="static_blocker_stop",
        title="Object Appears In Lane: Stop Before Contact",
        task="A non-moving object blocks the ego lane. The safe response is brake to a complete stop and hold.",
        hazard=hazard,
        baseline=baseline,
        guarded=guarded,
        success_reason="guarded vehicle stopped with margin before the static blocker",
        task_checks={"stopped_before_blocker": guarded[-1]["x_m"] < hazard["x_m"] - 2.0 and guarded[-1]["speed_mps"] == 0.0},
    )


def _road_hole_case() -> dict[str, Any]:
    hazard = {"kind": "road_hole", "label": "open road hole", "x_m": 20.0, "y_m": 0.0, "radius_m": 1.55}
    times = _times(9.0)
    baseline = [_state(t, 1.0 + 4.0 * t, 0.0, 4.0, 0.0, 0.34, 0.0, "GO") for t in times]
    guarded = []
    previous_y = 0.0
    for t in times:
        x = 1.0 + 3.7 * t
        if x < 12.0:
            y = 0.0
            decision = "APPROACH"
            speed = 3.7
        elif x < 20.0:
            p = (x - 12.0) / 8.0
            y = ADJACENT_LANE_CENTER_M * _smoothstep(p)
            decision = "SWERVE"
            speed = 2.8
        elif x < 30.0:
            p = (x - 20.0) / 10.0
            y = ADJACENT_LANE_CENTER_M * (1.0 - _smoothstep(p))
            decision = "RECOVER"
            speed = 3.1
        else:
            y = 0.0
            decision = "GO"
            speed = 4.0
        steer = _clamp((y - previous_y) * 0.22, -0.42, 0.42)
        previous_y = y
        guarded.append(_state(t, x, y, speed, steer, 0.24 if decision in {"APPROACH", "GO"} else 0.08, 0.14 if decision == "SWERVE" else 0.0, decision))
    return _case_payload(
        case_id="road_hole_swerve_recover",
        title="Hole In Road: Swerve, Clear It, Continue",
        task="A road hole occupies the drivable centerline. The safe response is lateral avoidance and recovery beyond the hazard.",
        hazard=hazard,
        baseline=baseline,
        guarded=guarded,
        success_reason="guarded vehicle left the lane center near the hole, cleared it, and returned to continue forward",
        task_checks={
            "swerved_around_hole": max(abs(item["y_m"]) for item in guarded) >= 2.5,
            "continued_beyond_hole": guarded[-1]["x_m"] >= hazard["x_m"] + 10.0,
            "recovered_lane": abs(guarded[-1]["y_m"]) <= 0.2,
            "stayed_in_drivable_corridor": _stayed_in_drivable_corridor(guarded),
        },
    )


def _rolling_object_case() -> dict[str, Any]:
    hazard = {
        "kind": "moving_object",
        "label": "rolling barrel from accident",
        "radius_m": 1.15,
        "path": [{"t_s": t, "x_m": 18.0, "y_m": 3.4 - 0.86 * t} for t in _times(9.0)],
    }
    times = _times(9.0)
    baseline = [_state(t, 1.0 + 4.0 * t, 0.0, 4.0, 0.0, 0.34, 0.0, "GO") for t in times]
    guarded = []
    previous_y = 0.0
    x = 1.0
    for index, t in enumerate(times):
        if t < 2.4:
            speed = 4.0
            y = 0.0
            decision = "APPROACH"
        elif t < 5.3:
            speed = 1.0
            y = ADJACENT_LANE_CENTER_M * _smoothstep((t - 2.4) / 2.9)
            decision = "YIELD_SWERVE"
        elif t < 6.5:
            speed = 2.5
            y = ADJACENT_LANE_CENTER_M
            decision = "YIELD_SWERVE"
        elif t < 8.2:
            speed = 3.5
            y = ADJACENT_LANE_CENTER_M * (1.0 - _smoothstep((t - 6.5) / 1.7))
            decision = "RECOVER"
        else:
            speed = 4.0
            y = 0.0
            decision = "GO"
        if index > 0:
            x += speed * 0.25
        steer = _clamp((y - previous_y) * 0.2, -0.42, 0.42)
        previous_y = y
        guarded.append(
            _state(
                t,
                x,
                y,
                speed,
                steer,
                0.28 if decision in {"APPROACH", "GO"} else 0.05,
                0.32 if decision == "YIELD_SWERVE" else 0.0,
                decision,
            )
        )
    return _case_payload(
        case_id="rolling_object_yield_swerve",
        title="Accident Debris Rolls Across Path: Slow, Swerve, Resume",
        task="A moving object rolls into the lane on a collision course. The safe response is slow/yield, steer around, then resume only after clearance.",
        hazard=hazard,
        baseline=baseline,
        guarded=guarded,
        success_reason="guarded vehicle slowed, moved laterally away from the rolling object, and resumed after it passed",
        task_checks={
            "slowed_before_conflict": min(item["speed_mps"] for item in guarded if 2.5 <= item["t_s"] <= 5.5) <= 1.8,
            "swerved_from_collision_course": max(abs(item["y_m"]) for item in guarded) >= 2.0,
            "resumed_after_clear": guarded[-1]["speed_mps"] >= 3.5 and guarded[-1]["x_m"] >= 24.0,
            "stayed_in_drivable_corridor": _stayed_in_drivable_corridor(guarded),
        },
    )


def _compound_obstacle_detour_case() -> dict[str, Any]:
    hazard = {
        "kind": "compound_hazard",
        "label": "blocked lane with moving debris and hole",
        "hazards": [
            {
                "kind": "moving_object",
                "label": "rolling panel",
                "radius_m": 1.0,
                "path": [{"t_s": t, "x_m": 12.0, "y_m": -3.0 + 0.85 * t} for t in _times(17.0)],
            },
            {"kind": "static_object", "label": "stalled van", "x_m": 19.0, "y_m": 0.0, "radius_m": 1.45},
            {"kind": "road_hole", "label": "open trench", "x_m": 25.0, "y_m": -2.6, "radius_m": 1.45},
        ],
    }
    times = _times(17.0)
    baseline = [_state(t, 1.0 + 3.6 * t, 0.0, 3.6, 0.0, 0.3, 0.0, "GO") for t in times]
    guarded = []
    x = 1.0
    previous_y = 0.0
    for index, t in enumerate(times):
        if t < 1.6:
            speed = 3.2
            y = 0.0
            decision = "APPROACH"
        elif t < 3.1:
            speed = max(0.0, 3.2 * (1.0 - (t - 1.6) / 1.5))
            y = 0.0
            decision = "STOP_FOR_MOVING_OBJECT"
        elif t < 8.2:
            speed = 0.0
            y = 0.0
            decision = "HOLD_AND_REPLAN"
        elif t < 10.8:
            speed = 1.8
            y = ADJACENT_LANE_CENTER_M * _smoothstep((t - 8.2) / 2.6)
            decision = "DETOUR_LEFT"
        elif t < 14.5:
            speed = 2.2
            y = ADJACENT_LANE_CENTER_M
            decision = "SLOW_THROUGH_DETOUR"
        elif t < 16.0:
            speed = 3.0
            y = ADJACENT_LANE_CENTER_M * (1.0 - _smoothstep((t - 14.5) / 1.5))
            decision = "RECOVER_ROUTE"
        else:
            speed = 3.6
            y = 0.0
            decision = "GO"
        if index > 0:
            x += speed * 0.25
        steer = _clamp((y - previous_y) * 0.18, -0.42, 0.42)
        previous_y = y
        guarded.append(
            _state(
                t,
                x,
                y,
                speed,
                steer,
                0.26 if decision in {"APPROACH", "GO"} else 0.08 if speed > 0.0 else 0.0,
                0.62 if decision == "STOP_FOR_MOVING_OBJECT" else 0.2 if decision == "SLOW_THROUGH_DETOUR" else 0.0,
                decision,
            )
        )
    return _case_payload(
        case_id="compound_obstacle_detour",
        title="Compound Bad Path: Stop, Detour, Slow, Recover",
        task=(
            "A rolling object crosses first, the lane center is blocked, and a trench removes the easy detour. "
            "The safe response is stop, replan around the blocked lane, slow through the alternate route, and recover."
        ),
        hazard=hazard,
        baseline=baseline,
        guarded=guarded,
        success_reason="guarded vehicle stopped for the moving object, chose an alternate route, slowed through it, and recovered forward motion",
        task_checks={
            "stopped_before_replan": min(item["speed_mps"] for item in guarded if 2.5 <= item["t_s"] <= 4.5) == 0.0,
            "found_alternative_route": max(item["y_m"] for item in guarded) >= 2.5,
            "slowed_in_detour": max(item["speed_mps"] for item in guarded if 10.8 <= item["t_s"] < 14.5) <= 2.2,
            "recovered_forward": guarded[-1]["speed_mps"] >= 3.5 and abs(guarded[-1]["y_m"]) <= 0.2,
            "cleared_compound_zone": guarded[-1]["x_m"] >= 27.0,
            "stayed_in_drivable_corridor": _stayed_in_drivable_corridor(guarded),
        },
    )


def _case_payload(
    *,
    case_id: str,
    title: str,
    task: str,
    hazard: dict[str, Any],
    baseline: list[dict[str, Any]],
    guarded: list[dict[str, Any]],
    success_reason: str,
    task_checks: dict[str, bool],
) -> dict[str, Any]:
    baseline_metrics = _track_metrics(baseline, hazard)
    guarded_metrics = _track_metrics(guarded, hazard)
    task_pass = (
        bool(all(task_checks.values()))
        and not bool(guarded_metrics["collision_proxy"])
        and not bool(guarded_metrics["lane_departure_proxy"])
    )
    return {
        "case_id": case_id,
        "title": title,
        "task": task,
        "hazard": hazard,
        "baseline": {
            "label": "bad_baseline",
            "collision_proxy": baseline_metrics["collision_proxy"],
            "lane_departure_proxy": baseline_metrics["lane_departure_proxy"],
            "min_distance_m": baseline_metrics["min_distance_m"],
            "max_abs_y_m": baseline_metrics["max_abs_y_m"],
            "trace": baseline,
        },
        "guarded": {
            "label": "oodrive_guarded_response",
            "collision_proxy": guarded_metrics["collision_proxy"],
            "lane_departure_proxy": guarded_metrics["lane_departure_proxy"],
            "task_pass": task_pass,
            "min_distance_m": guarded_metrics["min_distance_m"],
            "max_abs_y_m": guarded_metrics["max_abs_y_m"],
            "task_checks": task_checks,
            "trace": guarded,
        },
        "key_takeaway": success_reason,
        "sampled_reasoning": _reasoning(case_id),
    }


def _track_metrics(trace: list[dict[str, Any]], hazard: dict[str, Any]) -> dict[str, Any]:
    distances = []
    max_abs_y = max((abs(float(state["y_m"])) for state in trace), default=0.0)
    for state in trace:
        for single_hazard in _iter_hazards(hazard):
            hx, hy = _hazard_position(single_hazard, float(state["t_s"]))
            clearance = math.dist((float(state["x_m"]), float(state["y_m"])), (hx, hy)) - float(single_hazard.get("radius_m", 1.0)) - 0.9
            distances.append(clearance)
    min_distance = min(distances) if distances else math.inf
    return {
        "min_distance_m": round(min_distance, 3),
        "collision_proxy": min_distance <= 0.0,
        "max_abs_y_m": round(max_abs_y, 3),
        "lane_departure_proxy": max_abs_y > DRIVABLE_CORRIDOR_HALF_WIDTH_M,
    }


def _stayed_in_drivable_corridor(trace: list[dict[str, Any]]) -> bool:
    return all(abs(float(item["y_m"])) <= DRIVABLE_CORRIDOR_HALF_WIDTH_M for item in trace)


def _iter_hazards(hazard: dict[str, Any]) -> list[dict[str, Any]]:
    hazards = hazard.get("hazards")
    if isinstance(hazards, list):
        return [item for item in hazards if isinstance(item, dict)]
    return [hazard]


def _hazard_position(hazard: dict[str, Any], t_s: float) -> tuple[float, float]:
    path = hazard.get("path")
    if isinstance(path, list) and path:
        nearest = min((item for item in path if isinstance(item, dict)), key=lambda item: abs(float(item.get("t_s", 0.0)) - t_s))
        return float(nearest.get("x_m", 0.0)), float(nearest.get("y_m", 0.0))
    return float(hazard.get("x_m", 0.0)), float(hazard.get("y_m", 0.0))


def _reasoning(case_id: str) -> str:
    snippets = {
        "static_blocker_stop": "The lane is physically blocked. Do not thread the gap; brake to a full stop and hold until a clear route exists.",
        "road_hole_swerve_recover": "The obstacle is fixed but avoidable. Reduce speed, move laterally around the hole, then recover lane center and continue.",
        "rolling_object_yield_swerve": "The object is moving into the ego path. Slow early, create lateral separation, and resume only after the conflict clears.",
        "compound_obstacle_detour": "Multiple hazards remove the easy path. Stop first, replan to the open side, keep speed low through the detour, and recover only after the route clears.",
    }
    return snippets[case_id]


def _render_video(
    *,
    run_dir: Path,
    manifest: dict[str, Any],
    target_duration_s: float,
    fps: int,
) -> dict[str, Any]:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        return _render_blocked("ffmpeg was not found on PATH")
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        return _render_blocked(f"Pillow unavailable: {exc}")
    frame_dir = run_dir / "bad_path_stress_frames"
    shutil.rmtree(frame_dir, ignore_errors=True)
    frame_dir.mkdir(parents=True, exist_ok=True)
    cases = list(manifest.get("cases", []))
    frames = max(1, int(target_duration_s * fps))
    case_duration = target_duration_s / max(len(cases), 1)
    font = ImageFont.load_default()
    for frame_index in range(frames):
        t_demo = frame_index / fps
        case_index = min(len(cases) - 1, int(t_demo / case_duration)) if cases else 0
        case = cases[case_index]
        local_t = (t_demo - case_index * case_duration) / case_duration * _case_duration(case)
        image = _render_frame(Image, ImageDraw, font, case, local_t, frame_index, manifest)
        image.save(frame_dir / f"frame_{frame_index + 1:06d}.png")
    video_path = run_dir / "bad_path_stress_demo.mp4"
    command = [
        ffmpeg_path,
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frame_dir / "frame_%06d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(fps),
        str(video_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    passed = completed.returncode == 0 and video_path.exists()
    return {
        "status": "passed" if passed else "failed",
        "video_path": str(video_path) if passed else None,
        "frame_dir_path": str(frame_dir),
        "sample_frame_path": str(frame_dir / "frame_000001.png"),
        "fps": fps,
        "frame_count": frames,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "blockers": [] if passed else ["ffmpeg failed to assemble bad-path stress demo"],
    }


def _render_blocked(blocker: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "video_path": None,
        "frame_dir_path": None,
        "sample_frame_path": None,
        "fps": 0,
        "frame_count": 0,
        "command": [],
        "returncode": None,
        "stdout": "",
        "stderr": blocker,
        "blockers": [blocker],
    }


def _render_frame(image_module: Any, draw_module: Any, font: Any, case: dict[str, Any], local_t: float, frame_index: int, manifest: dict[str, Any]) -> Any:
    image = image_module.new("RGB", (1280, 720), (245, 246, 241))
    draw = draw_module.Draw(image, "RGBA")
    draw.rectangle((0, 0, 1280, 92), fill=(14, 18, 22, 235))
    draw.text((28, 20), f"OODrive bad-path stress demo: {case['title']}", fill=(255, 255, 255), font=font)
    draw.text((28, 50), case["task"], fill=(220, 235, 255), font=font)
    draw.text((980, 22), f"frame={frame_index} score={manifest['bad_path_stress_score']}", fill=(255, 230, 180), font=font)
    _draw_panel(draw, font, case, "baseline", local_t, (34, 124, 580, 420), "BAD BASELINE")
    _draw_panel(draw, font, case, "guarded", local_t, (666, 124, 1212, 420), "OODRIVE GUARDED")
    _draw_telemetry(draw, font, case, local_t)
    draw.text((28, 682), " | ".join(CLAIM_BOUNDARIES), fill=(44, 67, 96), font=font)
    return image


def _draw_panel(draw: Any, font: Any, case: dict[str, Any], mode: str, local_t: float, box: tuple[int, int, int, int], label: str) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(226, 232, 224, 255), outline=(74, 93, 81, 255), width=2)
    draw.rectangle((x0, y0 + 74, x1, y0 + 252), fill=(74, 85, 99, 175))
    draw.line((x0 + 18, y0 + 74, x1 - 18, y0 + 74), fill=(226, 232, 240, 255), width=2)
    draw.line((x0 + 18, y0 + 252, x1 - 18, y0 + 252), fill=(226, 232, 240, 255), width=2)
    draw.line((x0 + 18, y0 + 163, x1 - 18, y0 + 163), fill=(248, 250, 252, 255), width=2)
    draw.text((x0 + 14, y0 + 14), label, fill=(20, 32, 44), font=font)
    trace = list(case[mode]["trace"])
    state = _state_at(trace, local_t)
    hazard = case["hazard"]
    _draw_hazard(draw, hazard, local_t, box)
    points = [_map_point(item["x_m"], item["y_m"], box) for item in trace]
    color = (220, 38, 38, 255) if mode == "baseline" else (5, 150, 105, 255)
    if len(points) > 1:
        draw.line(points, fill=color, width=4)
    ex, ey = _map_point(state["x_m"], state["y_m"], box)
    draw.rounded_rectangle((ex - 12, ey - 7, ex + 12, ey + 7), radius=3, fill=color)
    draw.text((x0 + 14, y1 - 48), f"decision={state['decision']} speed={state['speed_mps']}m/s", fill=(20, 32, 44), font=font)
    draw.text(
        (x0 + 14, y1 - 27),
        f"min_distance={case[mode]['min_distance_m']}m collision={case[mode]['collision_proxy']} lane_departure={case[mode]['lane_departure_proxy']}",
        fill=(20, 32, 44),
        font=font,
    )


def _draw_hazard(draw: Any, hazard: dict[str, Any], t_s: float, box: tuple[int, int, int, int]) -> None:
    for single_hazard in _iter_hazards(hazard):
        hx, hy = _hazard_position(single_hazard, t_s)
        x, y = _map_point(hx, hy, box)
        if single_hazard["kind"] == "road_hole":
            draw.ellipse((x - 19, y - 13, x + 19, y + 13), fill=(25, 30, 36, 245), outline=(255, 255, 255, 255), width=2)
        elif single_hazard["kind"] == "moving_object":
            draw.ellipse((x - 15, y - 15, x + 15, y + 15), fill=(249, 115, 22, 245), outline=(124, 45, 18, 255), width=2)
        else:
            draw.rectangle((x - 17, y - 14, x + 17, y + 14), fill=(249, 115, 22, 245), outline=(124, 45, 18, 255), width=2)


def _draw_telemetry(draw: Any, font: Any, case: dict[str, Any], local_t: float) -> None:
    draw.rectangle((34, 468, 1212, 656), fill=(255, 255, 255, 235), outline=(200, 208, 198, 255))
    guarded = _state_at(list(case["guarded"]["trace"]), local_t)
    baseline = _state_at(list(case["baseline"]["trace"]), local_t)
    lines = [
        f"Guarded telemetry: speed={guarded['speed_mps']}m/s throttle={guarded['throttle']} brake={guarded['brake']} steer={guarded['steer']} decision={guarded['decision']}",
        f"Bad baseline: speed={baseline['speed_mps']}m/s throttle={baseline['throttle']} brake={baseline['brake']} decision={baseline['decision']} collision_proxy={case['baseline']['collision_proxy']}",
        f"Safety task: {case['key_takeaway']}",
        f"Sampled reasoning: {case['sampled_reasoning']}",
    ]
    y = 492
    for line in lines:
        for wrapped in textwrap.wrap(line, width=150)[:2]:
            draw.text((54, y), wrapped, fill=(20, 32, 44), font=font)
            y += 22


def _map_point(x_m: float, y_m: float, box: tuple[int, int, int, int]) -> tuple[float, float]:
    x0, y0, x1, y1 = box
    return x0 + 42.0 + x_m * 12.0, (y0 + y1) / 2.0 - y_m * 31.0


def _state_at(trace: list[dict[str, Any]], t_s: float) -> dict[str, Any]:
    return min(trace, key=lambda item: abs(float(item["t_s"]) - t_s))


def _case_duration(case: dict[str, Any]) -> float:
    traces = list(case["guarded"]["trace"])
    return float(traces[-1]["t_s"]) if traces else 1.0


def _score(cases: list[dict[str, Any]]) -> float:
    if not cases:
        return 0.0
    per_case = []
    for case in cases:
        score = 0.0
        if case["baseline"]["collision_proxy"]:
            score += 30.0
        if not case["guarded"]["collision_proxy"]:
            score += 35.0
        if case["guarded"]["task_pass"]:
            score += 35.0
        per_case.append(score)
    return round(sum(per_case) / len(per_case), 4)


def _state(t_s: float, x_m: float, y_m: float, speed_mps: float, steer: float, throttle: float, brake: float, decision: str) -> dict[str, Any]:
    return {
        "t_s": round(t_s, 3),
        "x_m": round(x_m, 3),
        "y_m": round(y_m, 3),
        "speed_mps": round(speed_mps, 3),
        "steer": round(steer, 3),
        "throttle": round(throttle, 3),
        "brake": round(brake, 3),
        "decision": decision,
    }


def _times(duration_s: float, dt_s: float = 0.25) -> list[float]:
    return [round(index * dt_s, 3) for index in range(int(duration_s / dt_s) + 1)]


def _smoothstep(value: float) -> float:
    x = _clamp(value, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OODrive Bad-Path Stress Demo",
        "",
        f"- Status: `{payload['status']}`",
        f"- Score: `{payload['bad_path_stress_score']}`",
        f"- Video: `{payload.get('video_path')}`",
        "",
        "## Cases",
        "",
    ]
    for case in list(payload.get("cases", [])):
        lines.extend(
            [
                f"### {case['title']}",
                "",
                f"- Task: {case['task']}",
                f"- Baseline collision proxy: `{case['baseline']['collision_proxy']}`",
                f"- Guarded collision proxy: `{case['guarded']['collision_proxy']}`",
                f"- Guarded lane departure proxy: `{case['guarded']['lane_departure_proxy']}`",
                f"- Guarded max lateral offset: `{case['guarded']['max_abs_y_m']}m`",
                f"- Guarded task pass: `{case['guarded']['task_pass']}`",
                f"- Takeaway: {case['key_takeaway']}",
                "",
            ]
        )
    if payload.get("blockers"):
        lines.extend(["## Blockers", ""])
        lines.extend(f"- {blocker}" for blocker in list(payload["blockers"]))
    lines.extend(["## Claim Boundaries", ""])
    lines.extend(f"- `{claim}`" for claim in list(payload["claim_boundaries"]))
    return "\n".join(lines) + "\n"


def _html(payload: dict[str, Any]) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{case['title']}</td>"
        f"<td>{case['baseline']['collision_proxy']}</td>"
        f"<td>{case['guarded']['collision_proxy']}</td>"
        f"<td>{case['guarded']['lane_departure_proxy']}</td>"
        f"<td>{case['guarded']['max_abs_y_m']}m</td>"
        f"<td>{case['guarded']['task_pass']}</td>"
        f"<td>{case['key_takeaway']}</td>"
        "</tr>"
        for case in list(payload.get("cases", []))
    )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            "<title>OODrive Bad-Path Stress Demo</title>",
            "<style>body{font-family:Arial,Helvetica,sans-serif;margin:24px;background:#f5f6f2;color:#172033}table{border-collapse:collapse;width:100%}td,th{border:1px solid #c8d0c8;padding:8px;vertical-align:top}code{background:#e7ebdf;padding:2px 4px}</style>",
            "</head>",
            "<body>",
            "<h1>OODrive Bad-Path Stress Demo</h1>",
            f"<p>Status: <code>{payload['status']}</code> Score: <code>{payload['bad_path_stress_score']}</code></p>",
            f"<p>Video: <code>{payload.get('video_path')}</code></p>",
            "<table><thead><tr><th>Case</th><th>Bad baseline collision</th><th>Guarded collision</th><th>Guarded lane departure</th><th>Guarded max lateral offset</th><th>Guarded task pass</th><th>Takeaway</th></tr></thead><tbody>",
            rows,
            "</tbody></table>",
            "<h2>Claim Boundaries</h2>",
            "<ul>",
            *[f"<li><code>{claim}</code></li>" for claim in list(payload["claim_boundaries"])],
            "</ul>",
            "</body></html>",
        ]
    )


__all__ = [
    "CLAIM_BOUNDARIES",
    "DEFAULT_CASE_IDS",
    "build_bad_path_stress_demo",
    "write_bad_path_stress_demo",
]
