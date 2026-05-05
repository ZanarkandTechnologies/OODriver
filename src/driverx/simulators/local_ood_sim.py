"""Dependency-light top-down simulator for generated OOD policy reactions."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any

from driverx.behaviors.types import BehaviorTrace
from driverx.policies.trajectory_control import ControlTrace
from driverx.policies.types import PolicyDecision
from driverx.scenarios.types import ScenarioRecipe


@dataclass(frozen=True)
class LocalOodPolicyTrack:
    label: str
    decision: PolicyDecision
    control_trace: ControlTrace
    closest_actor_distance_m: float
    risk_level: str

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "policy_id": self.decision.policy_id,
            "adapter_kind": self.decision.adapter_kind,
            "target_behavior": self.decision.intent.target_behavior,
            "speed_profile": self.decision.intent.speed_profile,
            "target_speed_mps": self.decision.action.control.get("target_speed_mps"),
            "yield": self.decision.action.control.get("yield"),
            "memory_guided": self.decision.action.control.get("memory_guided"),
            "retrieved_memory_ids": self.decision.retrieved_memory_ids,
            "latency_ms": self.decision.latency_ms,
            "closest_actor_distance_m": self.closest_actor_distance_m,
            "risk_level": self.risk_level,
            "control_trace": self.control_trace.to_jsonable(),
            "decision": self.decision.to_jsonable(),
        }


@dataclass(frozen=True)
class LocalOodSimResult:
    recipe_id: str
    behavior_id: str
    simulator_kind: str
    actor_metrics: dict[str, float]
    policy_tracks: tuple[LocalOodPolicyTrack, ...]
    min_distance_m: float
    worst_risk_level: str
    svg_path: Path
    html_path: Path
    timeline_path: Path

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "behavior_id": self.behavior_id,
            "simulator_kind": self.simulator_kind,
            "actor_metrics": self.actor_metrics,
            "policy_tracks": [track.to_jsonable() for track in self.policy_tracks],
            "min_distance_m": self.min_distance_m,
            "worst_risk_level": self.worst_risk_level,
            "svg_path": str(self.svg_path),
            "html_path": str(self.html_path),
            "timeline_path": str(self.timeline_path),
            "closed_loop_carla_claim": False,
        }


def run_local_ood_sim(
    *,
    recipe: ScenarioRecipe,
    behavior: BehaviorTrace,
    decisions: list[tuple[str, PolicyDecision]],
    control_traces: list[tuple[str, ControlTrace]],
    output_dir: Path,
) -> LocalOodSimResult:
    """Render and score one local OOD scene without CARLA."""

    output_dir.mkdir(parents=True, exist_ok=True)
    controls_by_label = {label: trace for label, trace in control_traces}
    tracks: list[LocalOodPolicyTrack] = []
    timeline = _timeline(behavior, decisions)
    for label, decision in decisions:
        if decision.action.trajectory is None:
            raise ValueError(f"Policy decision has no trajectory: {label}")
        closest = _closest_distance(
            decision.action.trajectory.points_xy,
            [(sample.x_m, sample.y_m) for sample in behavior.samples],
        )
        tracks.append(
            LocalOodPolicyTrack(
                label=label,
                decision=decision,
                control_trace=controls_by_label[label],
                closest_actor_distance_m=round(closest, 4),
                risk_level=_risk_level(closest),
            )
        )
    min_distance = min((track.closest_actor_distance_m for track in tracks), default=math.inf)
    worst_risk = _worst_risk([track.risk_level for track in tracks])
    timeline_path = output_dir / "local_ood_timeline.json"
    timeline_path.write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    svg_path = output_dir / "local_ood_sim.svg"
    svg_path.write_text(_render_svg(recipe, behavior, tracks), encoding="utf-8")
    html_path = output_dir / "local_ood_sim.html"
    html_path.write_text(_render_html(recipe, behavior, tracks, svg_path), encoding="utf-8")
    return LocalOodSimResult(
        recipe_id=recipe.recipe_id,
        behavior_id=behavior.plan.behavior_id,
        simulator_kind="driverx_local_2d_ood_sim",
        actor_metrics=behavior.metrics,
        policy_tracks=tuple(tracks),
        min_distance_m=round(min_distance, 4),
        worst_risk_level=worst_risk,
        svg_path=svg_path,
        html_path=html_path,
        timeline_path=timeline_path,
    )


def write_local_ood_sim_result(run_dir: Path, result: LocalOodSimResult) -> dict[str, Any]:
    json_path = run_dir / "local_ood_sim.json"
    report_path = run_dir / "local_ood_sim.md"
    payload = result.to_jsonable()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _timeline(
    behavior: BehaviorTrace,
    decisions: list[tuple[str, PolicyDecision]],
) -> dict[str, Any]:
    policy_paths = {
        label: decision.action.trajectory.points_xy if decision.action.trajectory else []
        for label, decision in decisions
    }
    return {
        "dt_s": behavior.plan.dt_s,
        "behavior": behavior.to_jsonable(),
        "policy_paths": {
            label: [{"t_s": round(index * 0.25, 4), "x_m": point[0], "y_m": point[1]} for index, point in enumerate(points)]
            for label, points in policy_paths.items()
        },
    }


def _closest_distance(
    ego_points: list[tuple[float, float]],
    actor_points: list[tuple[float, float]],
) -> float:
    if not ego_points or not actor_points:
        return math.inf
    aligned_count = min(len(ego_points), len(actor_points))
    return min(
        math.dist(ego_points[index], actor_points[index])
        for index in range(aligned_count)
    )


def _risk_level(distance: float) -> str:
    if distance < 1.5:
        return "collision_proxy"
    if distance < 3.0:
        return "near_miss_proxy"
    return "clearance_ok"


def _worst_risk(levels: list[str]) -> str:
    order = {"collision_proxy": 0, "near_miss_proxy": 1, "clearance_ok": 2}
    return min(levels, key=lambda item: order[item]) if levels else "unknown"


def _map(point: tuple[float, float]) -> tuple[float, float]:
    return 90.0 + point[0] * 18.0, 330.0 - point[1] * 34.0


def _polyline(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in (_map(point) for point in points))


def _render_svg(
    recipe: ScenarioRecipe,
    behavior: BehaviorTrace,
    tracks: list[LocalOodPolicyTrack],
) -> str:
    colors = {
        "policy": "#dc2626",
        "policy+memory": "#059669",
        "hybrid": "#7c3aed",
    }
    actor_points = [(sample.x_m, sample.y_m) for sample in behavior.samples]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="640" viewBox="0 0 1040 640">',
        "<style>",
        "text{font-family:Arial,Helvetica,sans-serif;fill:#172033}",
        ".title{font-size:22px;font-weight:700}.small{font-size:13px}.tiny{font-size:11px}",
        "</style>",
        '<rect width="1040" height="640" fill="#f6f7f2"/>',
        f'<text x="30" y="38" class="title">Local OOD simulator: {escape(recipe.recipe_id)}</text>',
        f'<text x="30" y="62" class="small">mutation={escape(recipe.mutation)} | behavior={escape(behavior.plan.behavior_id)} | CARLA claim=false</text>',
        '<rect x="30" y="90" width="690" height="470" rx="5" fill="#e6ebe2" stroke="#4b5d51"/>',
        '<rect x="30" y="250" width="690" height="90" fill="#4b5563" opacity="0.55"/>',
        '<line x1="45" y1="295" x2="705" y2="295" stroke="#f8fafc" stroke-width="2.5" stroke-dasharray="16 12"/>',
        '<line x1="45" y1="250" x2="705" y2="250" stroke="#f8fafc" stroke-width="2" opacity="0.7"/>',
        '<line x1="45" y1="340" x2="705" y2="340" stroke="#f8fafc" stroke-width="2" opacity="0.7"/>',
        '<text x="48" y="110" class="tiny">x forward, y lateral; orange=OOD actor, red=no memory, green=memory-guided</text>',
        f'<polyline points="{_polyline(actor_points)}" fill="none" stroke="#f97316" stroke-width="5"/>',
    ]
    for track in tracks:
        if track.decision.action.trajectory is None:
            continue
        color = colors.get(track.label, "#2563eb")
        parts.append(
            f'<polyline points="{_polyline(track.decision.action.trajectory.points_xy)}" fill="none" stroke="{color}" stroke-width="4"/>'
        )
    for sample in behavior.samples[:: max(1, len(behavior.samples) // 6)]:
        x, y = _map((sample.x_m, sample.y_m))
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#fb923c" stroke="#7c2d12"/>')
    parts.extend(
        [
            '<rect x="750" y="90" width="255" height="470" rx="5" fill="#ffffff" stroke="#c8d0c8"/>',
            '<text x="770" y="122" class="title">Policy reaction</text>',
        ]
    )
    y = 155
    for track in tracks:
        parts.extend(
            [
                f'<text x="770" y="{y}" class="small">{escape(track.label)}: {escape(track.risk_level)}</text>',
                f'<text x="790" y="{y + 22}" class="tiny">closest={track.closest_actor_distance_m}m speed={escape(str(track.decision.action.control.get("target_speed_mps")))}</text>',
                f'<text x="790" y="{y + 41}" class="tiny">yield={escape(str(track.decision.action.control.get("yield")))} memory={escape(str(track.decision.action.control.get("memory_guided")))}</text>',
            ]
        )
        y += 80
    parts.extend(
        [
            f'<text x="770" y="500" class="small">Expected failure</text>',
            f'<text x="770" y="522" class="tiny">{escape(recipe.expected_failure_mode[:48])}</text>',
            "</svg>",
        ]
    )
    return "\n".join(parts)


def _render_html(
    recipe: ScenarioRecipe,
    behavior: BehaviorTrace,
    tracks: list[LocalOodPolicyTrack],
    svg_path: Path,
) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{escape(track.label)}</td>"
        f"<td>{escape(track.risk_level)}</td>"
        f"<td>{track.closest_actor_distance_m}</td>"
        f"<td>{escape(str(track.decision.action.control.get('target_speed_mps')))}</td>"
        f"<td>{escape(', '.join(track.decision.retrieved_memory_ids))}</td>"
        "</tr>"
        for track in tracks
    )
    timeline_rows = "\n".join(
        [
            f"<tr><td>OOD actor</td><td>{escape(behavior.plan.behavior_id)}</td><td>{len(behavior.samples)}</td><td>{escape(behavior.plan.expected_pressure)}</td></tr>",
            "<tr><td>Ego reference</td><td>fixture history</td><td>5</td><td>stationary local frame used for trajectory comparison</td></tr>",
            *(
                f"<tr><td>{escape(track.label)}</td><td>{escape(track.decision.adapter_kind)}</td><td>{len(track.control_trace.commands)}</td><td>{escape(track.risk_level)}</td></tr>"
                for track in tracks
            ),
        ]
    )
    svg = svg_path.read_text(encoding="utf-8")
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            f"<title>DriverX Local OOD Demo - {escape(recipe.recipe_id)}</title>",
            "<style>body{font-family:Arial,Helvetica,sans-serif;margin:24px;background:#f6f7f2;color:#172033}table{border-collapse:collapse}td,th{border:1px solid #cbd5c0;padding:8px 10px;text-align:left}svg{max-width:100%;height:auto}</style>",
            "</head>",
            "<body>",
            f"<h1>Local OOD Demo: {escape(recipe.recipe_id)}</h1>",
            "<p>This is a lightweight 2D simulator artifact. It is not a closed-loop CARLA or real-time VLA control claim.</p>",
            svg,
            "<h2>Policy Reaction Table</h2>",
            "<table><thead><tr><th>Mode</th><th>Risk</th><th>Closest actor distance (m)</th><th>Target speed</th><th>Memory ids</th></tr></thead><tbody>",
            rows,
            "</tbody></table>",
            "<h2>Timeline Tracks</h2>",
            "<table><thead><tr><th>Track</th><th>Source</th><th>Samples</th><th>Note</th></tr></thead><tbody>",
            timeline_rows,
            "</tbody></table>",
            f"<h2>Behavior Pressure</h2><p>{escape(behavior.plan.expected_pressure)}</p>",
            "</body></html>",
        ]
    )


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Local OOD Simulator",
        "",
        f"- recipe_id: `{payload['recipe_id']}`",
        f"- behavior_id: `{payload['behavior_id']}`",
        f"- simulator_kind: `{payload['simulator_kind']}`",
        f"- closed_loop_carla_claim: `{payload['closed_loop_carla_claim']}`",
        f"- worst_risk_level: `{payload['worst_risk_level']}`",
        f"- min_distance_m: `{payload['min_distance_m']}`",
        f"- svg_path: `{payload['svg_path']}`",
        f"- html_path: `{payload['html_path']}`",
        "",
        "## Policy Tracks",
        "",
    ]
    for track in list(payload["policy_tracks"]):
        lines.extend(
            [
                f"### {track['label']}",
                "",
                f"- policy_id: `{track['policy_id']}`",
                f"- adapter_kind: `{track['adapter_kind']}`",
                f"- risk_level: `{track['risk_level']}`",
                f"- closest_actor_distance_m: `{track['closest_actor_distance_m']}`",
                f"- target_behavior: `{track['target_behavior']}`",
                f"- target_speed_mps: `{track['target_speed_mps']}`",
                f"- retrieved_memory_ids: `{', '.join(track['retrieved_memory_ids'])}`",
                "",
            ]
        )
    return "\n".join(lines)


__all__ = [
    "LocalOodPolicyTrack",
    "LocalOodSimResult",
    "run_local_ood_sim",
    "write_local_ood_sim_result",
]
