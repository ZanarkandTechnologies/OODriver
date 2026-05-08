"""Typed claim contract for paused Alpamayo/CARLA closed-loop evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ClosedLoopMode = Literal["none", "cached_replay", "paused_receding_horizon", "real_time"]


@dataclass(frozen=True)
class ClosedLoopStep:
    step_index: int
    input_frame_id: int
    post_action_frame_id: int
    applied_control_count: int
    model_latency_ms: float | None = None
    prediction_path: str | None = None
    control_trace_path: str | None = None
    checkpoint_path: str | None = None
    inference_result_path: str | None = None
    planned_path: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    actual_path: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    safety_report: dict[str, Any] = field(default_factory=dict)
    sensor_frame_ids: tuple[int, ...] = field(default_factory=tuple)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "input_frame_id": self.input_frame_id,
            "post_action_frame_id": self.post_action_frame_id,
            "applied_control_count": self.applied_control_count,
            "model_latency_ms": self.model_latency_ms,
            "prediction_path": self.prediction_path,
            "control_trace_path": self.control_trace_path,
            "checkpoint_path": self.checkpoint_path,
            "inference_result_path": self.inference_result_path,
            "planned_path": list(self.planned_path),
            "actual_path": list(self.actual_path),
            "safety_report": dict(self.safety_report),
            "sensor_frame_ids": list(self.sensor_frame_ids),
        }


@dataclass(frozen=True)
class ClosedLoopValidation:
    status: str
    mode: ClosedLoopMode
    recurrence_count: int
    applied_control_count: int
    observed_after_action_count: int
    blockers: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return self.status == "passed"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mode": self.mode,
            "recurrence_count": self.recurrence_count,
            "applied_control_count": self.applied_control_count,
            "observed_after_action_count": self.observed_after_action_count,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
        }


def claim_for_mode(mode: str) -> str:
    clean = mode if mode in {"cached_replay", "paused_receding_horizon", "real_time"} else "false"
    return f"closed_loop_vla_control={clean}"


def normalize_closed_loop_trace(payload: dict[str, Any]) -> dict[str, Any]:
    mode = str(payload.get("mode") or payload.get("closed_loop_vla_control") or "none")
    if mode in {"false", "False", "0"}:
        mode = "none"
    if mode not in {"none", "cached_replay", "paused_receding_horizon", "real_time"}:
        mode = "none"
    steps = [_normalize_step(item, index) for index, item in enumerate(_list(payload.get("steps")))]
    claims = _string_list(payload.get("claim_boundaries"))
    if not any(item.startswith("closed_loop_vla_control=") for item in claims):
        claims.append(claim_for_mode(mode))
    if "real_time_vla_control=false" not in claims and mode != "real_time":
        claims.append("real_time_vla_control=false")
    return {
        **payload,
        "mode": mode,
        "steps": steps,
        "claim_boundaries": _dedupe(claims),
    }


def validate_closed_loop_trace(payload: dict[str, Any]) -> ClosedLoopValidation:
    trace = normalize_closed_loop_trace(payload)
    mode = trace["mode"]
    blockers: list[str] = []
    warnings: list[str] = []
    steps = [_mapping(item) for item in _list(trace.get("steps"))]
    applied = sum(max(0, _int(step.get("applied_control_count"))) for step in steps)
    recurrence = 0
    observed_after = 0
    previous_post_frame: int | None = None
    for index, step in enumerate(steps):
        input_frame = _int(step.get("input_frame_id"), -1)
        post_frame = _int(step.get("post_action_frame_id"), -1)
        applied_count = _int(step.get("applied_control_count"))
        if input_frame < 0:
            blockers.append(f"step {index}: missing input_frame_id")
        if applied_count <= 0:
            blockers.append(f"step {index}: no controls applied")
        if post_frame <= input_frame:
            blockers.append(f"step {index}: post_action_frame_id must be after input_frame_id")
        else:
            observed_after += 1
        if previous_post_frame is not None and input_frame < previous_post_frame:
            blockers.append(f"step {index}: input_frame_id predates previous post-action frame")
        if index > 0 and previous_post_frame is not None and input_frame >= previous_post_frame:
            recurrence += 1
        previous_post_frame = post_frame if post_frame >= 0 else previous_post_frame
    claims = set(_string_list(trace.get("claim_boundaries")))
    if mode == "none" and any(item.startswith("closed_loop_vla_control=") and not item.endswith("false") for item in claims):
        blockers.append("trace claims closed-loop control but mode is none")
    if mode == "cached_replay":
        warnings.append("cached_replay applies controls but does not prove fresh model re-observation")
    if mode == "paused_receding_horizon" and recurrence < 1:
        blockers.append("paused_receding_horizon requires at least two observe/infer/act/observe steps")
    if mode == "real_time":
        latency = _float(_mapping(trace.get("latency_ms")).get("max"))
        tick_budget = _float(trace.get("real_time_tick_budget_ms"))
        if latency <= 0 or tick_budget <= 0 or latency > tick_budget:
            blockers.append("real_time claim requires measured max latency within tick budget")
    if mode != "real_time" and "real_time_vla_control=true" in claims:
        blockers.append("real_time_vla_control=true is invalid without real_time mode")
    status = "passed" if not blockers else "blocked"
    return ClosedLoopValidation(
        status=status,
        mode=mode,  # type: ignore[arg-type]
        recurrence_count=recurrence,
        applied_control_count=applied,
        observed_after_action_count=observed_after,
        blockers=tuple(_dedupe(blockers)),
        warnings=tuple(_dedupe(warnings)),
    )


def _normalize_step(value: object, index: int) -> dict[str, Any]:
    step = _mapping(value)
    if "step_index" not in step:
        step["step_index"] = index
    return step


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _string_list(value: object) -> list[str]:
    return [str(item) for item in _list(value) if str(item)]


def _int(value: object, default: int = 0) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


__all__ = [
    "ClosedLoopMode",
    "ClosedLoopStep",
    "ClosedLoopValidation",
    "claim_for_mode",
    "normalize_closed_loop_trace",
    "validate_closed_loop_trace",
]
