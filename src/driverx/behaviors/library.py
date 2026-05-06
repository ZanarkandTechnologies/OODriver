"""Deterministic regional/OOD behavior traces."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Callable

from driverx.behaviors.types import BehaviorPlan, BehaviorSample, BehaviorTrace


def default_behavior_plans() -> list[BehaviorPlan]:
    return [
        BehaviorPlan(
            behavior_id="no_signal_cut_in",
            actor_kind="vehicle",
            parameters={"start_y": 3.5, "end_y": 0.0, "speed_mps": 8.0},
            tags=["cut_in", "no_signal", "lateral_aggression"],
            expected_pressure="Actor cuts across lane without indicator or sufficient gap.",
        ),
        BehaviorPlan(
            behavior_id="sudden_brake",
            actor_kind="vehicle",
            parameters={"speed_mps": 11.0, "brake_time_s": 2.0, "final_speed_mps": 0.8},
            tags=["sudden_brake", "rear_end_risk"],
            expected_pressure="Lead actor brakes hard after a steady approach.",
        ),
        BehaviorPlan(
            behavior_id="motorcycle_filtering",
            actor_kind="motorcycle",
            parameters={"speed_mps": 13.0, "lane_center_y": 1.75, "weave_m": 1.0},
            tags=["motorcycle", "filtering", "lateral_uncertainty"],
            expected_pressure="Fast two-wheeler filters between lanes with lateral weave.",
        ),
        BehaviorPlan(
            behavior_id="wrong_way_shoulder_creep",
            actor_kind="vehicle",
            parameters={"start_x": 18.0, "speed_mps": -2.5, "shoulder_y": -5.2},
            tags=["wrong_way", "shoulder", "creep"],
            expected_pressure="Actor creeps against route direction along the shoulder.",
        ),
        BehaviorPlan(
            behavior_id="informal_right_of_way_push",
            actor_kind="vehicle",
            parameters={"speed_mps": 3.0, "push_start_s": 1.5, "conflict_y": 0.0},
            tags=["right_of_way", "creep", "assertive_gap"],
            expected_pressure="Actor slowly pushes into a conflict zone instead of yielding.",
        ),
        BehaviorPlan(
            behavior_id="stunt_motorcycle_proxy",
            actor_kind="motorcycle",
            parameters={"speed_mps": 15.0, "weave_m": 1.2, "low_profile": True},
            tags=["motorcycle", "stunt_proxy", "fast_low_profile"],
            expected_pressure="Low-profile fast two-wheeler surrogate creates perception and prediction stress.",
        ),
        BehaviorPlan(
            behavior_id="double_parked_door_swerve",
            actor_kind="vehicle",
            parameters={"speed_mps": 4.0, "start_y": 3.2, "intrusion_y": 0.35, "swerve_start_s": 1.25},
            tags=["double_parked", "door_open", "sudden_swerve", "urban_clutter"],
            expected_pressure="Double-parked actor abruptly intrudes into lane as if avoiding an opening door.",
        ),
        BehaviorPlan(
            behavior_id="unsignaled_u_turn",
            actor_kind="vehicle",
            parameters={"turn_center_x": 8.0, "turn_center_y": -2.0, "radius_m": 2.3, "approach_speed_mps": 5.0},
            tags=["u_turn", "no_signal", "opposing_conflict", "heading_reversal"],
            expected_pressure="Actor begins an unsignaled U-turn across ego's path with rapid heading reversal.",
        ),
    ]


def _sample_times(plan: BehaviorPlan) -> list[float]:
    steps = int(plan.duration_s / plan.dt_s)
    return [round(index * plan.dt_s, 6) for index in range(steps + 1)]


def _linear(start: float, end: float, alpha: float) -> float:
    return start + (end - start) * max(0.0, min(1.0, alpha))


def _no_signal_cut_in(plan: BehaviorPlan) -> list[BehaviorSample]:
    start_y = float(plan.parameters["start_y"])
    end_y = float(plan.parameters["end_y"])
    speed = float(plan.parameters["speed_mps"])
    return [
        BehaviorSample(
            t_s=t,
            x_m=speed * t,
            y_m=_linear(start_y, end_y, t / max(plan.duration_s * 0.7, plan.dt_s)),
            speed_mps=speed,
            heading_deg=-8.0 if t < plan.duration_s * 0.7 else 0.0,
        )
        for t in _sample_times(plan)
    ]


def _sudden_brake(plan: BehaviorPlan) -> list[BehaviorSample]:
    speed = float(plan.parameters["speed_mps"])
    final_speed = float(plan.parameters["final_speed_mps"])
    brake_time = float(plan.parameters["brake_time_s"])
    samples: list[BehaviorSample] = []
    x = 0.0
    last_t = 0.0
    for t in _sample_times(plan):
        dt = t - last_t
        current_speed = speed if t < brake_time else _linear(speed, final_speed, (t - brake_time) / 0.75)
        x += current_speed * dt
        samples.append(BehaviorSample(t, x, 0.0, current_speed, 0.0))
        last_t = t
    return samples


def _motorcycle_filtering(plan: BehaviorPlan) -> list[BehaviorSample]:
    speed = float(plan.parameters["speed_mps"])
    lane_center = float(plan.parameters["lane_center_y"])
    weave = float(plan.parameters["weave_m"])
    return [
        BehaviorSample(
            t_s=t,
            x_m=speed * t,
            y_m=lane_center + weave * math.sin(t * math.pi * 1.5),
            speed_mps=speed,
            heading_deg=6.0 * math.sin(t * math.pi * 1.5),
        )
        for t in _sample_times(plan)
    ]


def _wrong_way_shoulder_creep(plan: BehaviorPlan) -> list[BehaviorSample]:
    start_x = float(plan.parameters["start_x"])
    speed = float(plan.parameters["speed_mps"])
    shoulder_y = float(plan.parameters["shoulder_y"])
    return [
        BehaviorSample(t, start_x + speed * t, shoulder_y, abs(speed), 180.0)
        for t in _sample_times(plan)
    ]


def _informal_right_of_way_push(plan: BehaviorPlan) -> list[BehaviorSample]:
    speed = float(plan.parameters["speed_mps"])
    push_start = float(plan.parameters["push_start_s"])
    conflict_y = float(plan.parameters["conflict_y"])
    samples: list[BehaviorSample] = []
    for t in _sample_times(plan):
        active_t = max(0.0, t - push_start)
        samples.append(
            BehaviorSample(
                t_s=t,
                x_m=-4.0 + speed * active_t,
                y_m=_linear(-3.5, conflict_y, active_t / 2.5),
                speed_mps=speed if t >= push_start else 0.5,
                heading_deg=20.0 if t >= push_start else 0.0,
            )
        )
    return samples


def _stunt_motorcycle_proxy(plan: BehaviorPlan) -> list[BehaviorSample]:
    speed = float(plan.parameters["speed_mps"])
    weave = float(plan.parameters["weave_m"])
    return [
        BehaviorSample(
            t_s=t,
            x_m=speed * t,
            y_m=weave * math.sin(t * math.pi * 2.2),
            speed_mps=speed,
            heading_deg=10.0 * math.sin(t * math.pi * 2.2),
        )
        for t in _sample_times(plan)
    ]


def _double_parked_door_swerve(plan: BehaviorPlan) -> list[BehaviorSample]:
    speed = float(plan.parameters["speed_mps"])
    start_y = float(plan.parameters["start_y"])
    intrusion_y = float(plan.parameters["intrusion_y"])
    swerve_start = float(plan.parameters["swerve_start_s"])
    samples: list[BehaviorSample] = []
    for t in _sample_times(plan):
        active_t = max(0.0, t - swerve_start)
        y = _linear(start_y, intrusion_y, active_t / 0.9)
        if active_t > 2.0:
            y = _linear(intrusion_y, start_y, (active_t - 2.0) / 1.4)
        samples.append(
            BehaviorSample(
                t_s=t,
                x_m=speed * t + 2.0,
                y_m=y,
                speed_mps=speed,
                heading_deg=-24.0 if swerve_start <= t <= swerve_start + 1.0 else 0.0,
            )
        )
    return samples


def _unsignaled_u_turn(plan: BehaviorPlan) -> list[BehaviorSample]:
    center_x = float(plan.parameters["turn_center_x"])
    center_y = float(plan.parameters["turn_center_y"])
    radius = float(plan.parameters["radius_m"])
    approach_speed = float(plan.parameters["approach_speed_mps"])
    samples: list[BehaviorSample] = []
    for t in _sample_times(plan):
        if t < 1.0:
            samples.append(
                BehaviorSample(
                    t_s=t,
                    x_m=center_x - approach_speed * (1.0 - t),
                    y_m=center_y - radius,
                    speed_mps=approach_speed,
                    heading_deg=0.0,
                )
            )
            continue
        alpha = min(1.0, (t - 1.0) / 2.0)
        theta = -math.pi / 2.0 + alpha * math.pi
        samples.append(
            BehaviorSample(
                t_s=t,
                x_m=center_x + radius * math.cos(theta),
                y_m=center_y + radius * math.sin(theta),
                speed_mps=approach_speed * 0.75,
                heading_deg=round(alpha * 180.0, 4),
            )
        )
    return samples


SIMULATORS: dict[str, Callable[[BehaviorPlan], list[BehaviorSample]]] = {
    "no_signal_cut_in": _no_signal_cut_in,
    "sudden_brake": _sudden_brake,
    "motorcycle_filtering": _motorcycle_filtering,
    "wrong_way_shoulder_creep": _wrong_way_shoulder_creep,
    "informal_right_of_way_push": _informal_right_of_way_push,
    "stunt_motorcycle_proxy": _stunt_motorcycle_proxy,
    "double_parked_door_swerve": _double_parked_door_swerve,
    "unsignaled_u_turn": _unsignaled_u_turn,
}


def _metrics(samples: list[BehaviorSample]) -> dict[str, float]:
    if len(samples) < 2:
        return {}
    lateral_displacement = max(sample.y_m for sample in samples) - min(sample.y_m for sample in samples)
    longitudinal_displacement = samples[-1].x_m - samples[0].x_m
    max_lateral_speed = 0.0
    max_deceleration = 0.0
    max_heading_abs = max(abs(sample.heading_deg) for sample in samples)
    for left, right in zip(samples, samples[1:]):
        dt = max(right.t_s - left.t_s, 1e-6)
        max_lateral_speed = max(max_lateral_speed, abs(right.y_m - left.y_m) / dt)
        decel = (left.speed_mps - right.speed_mps) / dt
        max_deceleration = max(max_deceleration, decel)
    return {
        "lateral_displacement_m": round(lateral_displacement, 4),
        "longitudinal_displacement_m": round(longitudinal_displacement, 4),
        "max_lateral_speed_mps": round(max_lateral_speed, 4),
        "max_deceleration_mps2": round(max_deceleration, 4),
        "max_heading_abs_deg": round(max_heading_abs, 4),
        "wrong_way_distance_m": round(abs(min(0.0, longitudinal_displacement)), 4),
    }


def simulate_behavior(plan: BehaviorPlan) -> BehaviorTrace:
    simulator = SIMULATORS.get(plan.behavior_id)
    if simulator is None:
        raise ValueError(f"Unsupported behavior_id: {plan.behavior_id}")
    samples = simulator(plan)
    return BehaviorTrace(plan=plan, samples=samples, metrics=_metrics(samples))


def summarize_behavior_suite(traces: list[BehaviorTrace]) -> dict[str, object]:
    metric_records = [
        {
            "trace_id": _trace_id(trace, index),
            "behavior_id": trace.plan.behavior_id,
            "metrics": trace.metrics,
        }
        for index, trace in enumerate(traces)
    ]
    return {
        "num_behaviors": len(traces),
        "behavior_ids": [trace.plan.behavior_id for trace in traces],
        "metrics": {
            record["trace_id"]: record["metrics"]
            for record in metric_records
        },
        "metric_records": metric_records,
    }


def _behavior_markdown(traces: list[BehaviorTrace]) -> str:
    lines = ["# Behavior Suite", ""]
    for trace in traces:
        lines.extend(
            [
                f"## {trace.plan.behavior_id}",
                "",
                f"- actor_kind: `{trace.plan.actor_kind}`",
                f"- tags: `{', '.join(trace.plan.tags)}`",
                f"- expected_pressure: {trace.plan.expected_pressure}",
                f"- samples: `{len(trace.samples)}`",
            ]
        )
        for key, value in trace.metrics.items():
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")
    return "\n".join(lines)


def write_behavior_suite(run_dir: Path, traces: list[BehaviorTrace]) -> dict[str, object]:
    run_dir.mkdir(parents=True, exist_ok=True)
    traces_path = run_dir / "behavior_traces.json"
    summary_path = run_dir / "behavior_summary.json"
    report_path = run_dir / "behavior_report.md"
    traces_path.write_text(
        json.dumps([trace.to_jsonable() for trace in traces], indent=2),
        encoding="utf-8",
    )
    summary = summarize_behavior_suite(traces)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path.write_text(_behavior_markdown(traces), encoding="utf-8")
    return {
        **summary,
        "traces_path": str(traces_path),
        "summary_path": str(summary_path),
        "report_path": str(report_path),
    }


def _trace_id(trace: BehaviorTrace, index: int) -> str:
    variant_tags = [tag for tag in trace.plan.tags if tag.startswith("variant_")]
    suffix = variant_tags[-1] if variant_tags else f"trace_{index:03d}"
    return f"{trace.plan.behavior_id}:{suffix}"
