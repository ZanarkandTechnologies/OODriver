"""Convert Alpamayo native trajectory predictions into DriverX chunks."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Sequence

from driverx.core.types import TrajectoryCandidate

ALPAMAYO_NATIVE_HZ = 10.0
ALPAMAYO_NATIVE_STEPS = 64
DRIVERX_TRAJECTORY_HZ = 4.0
DRIVERX_TRAJECTORY_STEPS = 20
DRIVERX_TRAJECTORY_HORIZON_S = 5.0

Number = int | float
Point3 = tuple[float, float, float]


def select_alpamayo_xyz_sample(
    pred_xyz: Any,
    *,
    batch_index: int = 0,
    set_index: int = 0,
    sample_index: int = 0,
) -> list[Point3]:
    """Select one `T x 3` sample from common Alpamayo output nestings."""

    data = _unwrap_tensorish(pred_xyz)
    trajectory = _select_with_flexible_rank(
        data,
        batch_index=batch_index,
        set_index=set_index,
        sample_index=sample_index,
    )
    points = [_coerce_point3(item) for item in list(trajectory)]
    if len(points) < _minimum_native_steps():
        raise ValueError(
            f"Alpamayo trajectory has {len(points)} points; need at least {_minimum_native_steps()} for a 5s 4Hz chunk."
        )
    return points


def select_alpamayo_rot_sample(
    pred_rot: Any,
    *,
    batch_index: int = 0,
    set_index: int = 0,
    sample_index: int = 0,
) -> list[float]:
    """Select one native Alpamayo rotation sample and return ego-frame yaw radians."""

    data = _unwrap_tensorish(pred_rot)
    rotations = _select_rotation_with_flexible_rank(
        data,
        batch_index=batch_index,
        set_index=set_index,
        sample_index=sample_index,
    )
    yaw_rad = [_rotation_to_yaw(item) for item in list(rotations)]
    if len(yaw_rad) < _minimum_native_steps():
        raise ValueError(
            f"Alpamayo rotation trajectory has {len(yaw_rad)} points; need at least {_minimum_native_steps()} for a 5s 4Hz chunk."
        )
    return yaw_rad


def resample_alpamayo_xy(
    points_xyz: Sequence[Sequence[Number]],
    *,
    source_hz: float = ALPAMAYO_NATIVE_HZ,
    target_hz: float = DRIVERX_TRAJECTORY_HZ,
    target_steps: int = DRIVERX_TRAJECTORY_STEPS,
) -> list[tuple[float, float]]:
    """Linearly resample native future xyz waypoints into DriverX xy points."""

    if source_hz <= 0 or target_hz <= 0:
        raise ValueError("source_hz and target_hz must be positive.")
    points = [_coerce_point3(item) for item in points_xyz]
    minimum_steps = int(target_steps * source_hz / target_hz)
    if len(points) < minimum_steps:
        raise ValueError(
            f"Alpamayo trajectory has {len(points)} points; need at least {minimum_steps} for a {target_steps / target_hz:.1f}s {target_hz:g}Hz chunk."
        )
    last_source_t = len(points) / source_hz
    last_target_t = target_steps / target_hz
    if last_source_t + 1e-9 < last_target_t:
        raise ValueError(
            f"Native trajectory horizon {last_source_t:.2f}s is shorter than target horizon {last_target_t:.2f}s."
        )

    resampled: list[tuple[float, float]] = []
    for step in range(target_steps):
        target_t = (step + 1) / target_hz
        source_position = target_t * source_hz - 1.0
        left_index = max(0, int(source_position))
        right_index = min(left_index + 1, len(points) - 1)
        ratio = source_position - left_index
        left = points[left_index]
        right = points[right_index]
        x = left[0] + (right[0] - left[0]) * ratio
        y = left[1] + (right[1] - left[1]) * ratio
        resampled.append((round(x, 4), round(y, 4)))
    return resampled


def resample_alpamayo_yaw(
    yaw_rad: Sequence[Number],
    *,
    source_hz: float = ALPAMAYO_NATIVE_HZ,
    target_hz: float = DRIVERX_TRAJECTORY_HZ,
    target_steps: int = DRIVERX_TRAJECTORY_STEPS,
) -> list[float]:
    """Linearly resample native yaw predictions into DriverX control ticks."""

    if source_hz <= 0 or target_hz <= 0:
        raise ValueError("source_hz and target_hz must be positive.")
    yaw = [float(value) for value in yaw_rad]
    minimum_steps = int(target_steps * source_hz / target_hz)
    if len(yaw) < minimum_steps:
        raise ValueError(
            f"Alpamayo rotation trajectory has {len(yaw)} points; need at least {minimum_steps} for a {target_steps / target_hz:.1f}s {target_hz:g}Hz chunk."
        )
    resampled: list[float] = []
    unwrapped = _unwrap_angles(yaw)
    for step in range(target_steps):
        target_t = (step + 1) / target_hz
        source_position = target_t * source_hz - 1.0
        left_index = max(0, int(source_position))
        right_index = min(left_index + 1, len(unwrapped) - 1)
        ratio = source_position - left_index
        value = unwrapped[left_index] + (unwrapped[right_index] - unwrapped[left_index]) * ratio
        resampled.append(round(_wrap_angle(value), 6))
    return resampled


def alpamayo_prediction_to_trajectory(
    pred_xyz: Any,
    *,
    pred_rot: Any | None = None,
    batch_index: int = 0,
    set_index: int = 0,
    sample_index: int = 0,
    source: str = "alpamayo",
    score: float = 0.0,
    reasoning: str | None = None,
) -> TrajectoryCandidate:
    """Convert native Alpamayo predictions to a DriverX trajectory candidate."""

    native = select_alpamayo_xyz_sample(
        pred_xyz,
        batch_index=batch_index,
        set_index=set_index,
        sample_index=sample_index,
    )
    xy = resample_alpamayo_xy(native)
    yaw_rad: list[float] | None = None
    if pred_rot is not None:
        yaw_rad = resample_alpamayo_yaw(
            select_alpamayo_rot_sample(
                pred_rot,
                batch_index=batch_index,
                set_index=set_index,
                sample_index=sample_index,
            )
        )
    return TrajectoryCandidate(
        points_xy=xy,
        source=source,
        score=score,
        metadata={
            "native_steps": len(native),
            "native_hz": ALPAMAYO_NATIVE_HZ,
            "target_steps": DRIVERX_TRAJECTORY_STEPS,
            "target_hz": DRIVERX_TRAJECTORY_HZ,
            "batch_index": batch_index,
            "set_index": set_index,
            "sample_index": sample_index,
            "reasoning": reasoning,
            **({"target_yaw_rad": yaw_rad} if yaw_rad is not None else {}),
        },
    )


def load_prediction_json(path: Path) -> Any:
    """Load a saved Alpamayo prediction payload or raw nested `pred_xyz` list."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        pred_xyz = None
        for key in ("pred_xyz", "native_pred_xyz", "trajectory"):
            if key in payload:
                pred_xyz = payload[key]
                break
        if pred_xyz is not None:
            pred_rot = payload.get("pred_rot") or payload.get("native_pred_rot")
            if pred_rot is not None:
                return {"pred_xyz": pred_xyz, "pred_rot": pred_rot}
            return pred_xyz
    return payload


def write_alpamayo_trajectory_conversion(
    run_dir: Path,
    *,
    prediction_json: Path,
    batch_index: int = 0,
    set_index: int = 0,
    sample_index: int = 0,
) -> dict[str, Any]:
    """Convert a saved prediction JSON and write JSON/Markdown artifacts."""

    run_dir.mkdir(parents=True, exist_ok=True)
    prediction = load_prediction_json(prediction_json)
    pred_xyz = prediction
    pred_rot = None
    if isinstance(prediction, dict) and "pred_xyz" in prediction:
        pred_xyz = prediction["pred_xyz"]
        pred_rot = prediction.get("pred_rot")
    trajectory = alpamayo_prediction_to_trajectory(
        pred_xyz,
        pred_rot=pred_rot,
        batch_index=batch_index,
        set_index=set_index,
        sample_index=sample_index,
    )
    payload = {
        "prediction_json": str(prediction_json),
        "trajectory": {
            "points_xy": trajectory.points_xy,
            "source": trajectory.source,
            "score": trajectory.score,
            "metadata": trajectory.metadata,
        },
    }
    json_path = run_dir / "alpamayo_trajectory.json"
    report_path = run_dir / "alpamayo_trajectory.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def _minimum_native_steps() -> int:
    return int(DRIVERX_TRAJECTORY_HORIZON_S * ALPAMAYO_NATIVE_HZ)


def _unwrap_tensorish(value: Any) -> Any:
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def _select_with_flexible_rank(
    data: Any,
    *,
    batch_index: int,
    set_index: int,
    sample_index: int,
) -> Any:
    rank = _nested_rank(data)
    if rank == 5:
        return data[batch_index][set_index][sample_index]
    if rank == 4:
        return data[set_index][sample_index]
    if rank == 3:
        return data[sample_index]
    if rank == 2:
        return data
    raise ValueError(
        "Expected Alpamayo pred_xyz shaped as [B][sets][samples][T][3], [sets][samples][T][3], [samples][T][3], or [T][3]."
    )


def _select_rotation_with_flexible_rank(
    data: Any,
    *,
    batch_index: int,
    set_index: int,
    sample_index: int,
) -> Any:
    rank = _nested_rank(data)
    if rank == 6:
        return data[batch_index][set_index][sample_index]
    if rank == 5:
        return data[set_index][sample_index]
    if rank == 4:
        return data[sample_index]
    if rank in {1, 3}:
        return data
    raise ValueError(
        "Expected Alpamayo pred_rot shaped as [B][sets][samples][T][3][3], [sets][samples][T][3][3], [samples][T][3][3], [T][3][3], or [T]."
    )


def _nested_rank(value: Any) -> int:
    rank = 0
    current = value
    while isinstance(current, list) and current:
        rank += 1
        current = current[0]
    return rank


def _coerce_point3(value: Sequence[Number]) -> Point3:
    if len(value) < 3:
        raise ValueError("Alpamayo xyz point must contain at least three numeric values.")
    return (float(value[0]), float(value[1]), float(value[2]))


def _rotation_to_yaw(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, Sequence) or len(value) < 2:
        raise ValueError("Alpamayo rotation must be a 3x3 matrix or yaw scalar.")
    first = value[0]
    if isinstance(first, (int, float)):
        return float(first)
    row0 = list(value[0])
    row1 = list(value[1])
    if len(row0) < 1 or len(row1) < 1:
        raise ValueError("Alpamayo rotation matrix rows must contain values.")
    return float(math.atan2(float(row1[0]), float(row0[0])))


def _unwrap_angles(values: Sequence[float]) -> list[float]:
    if not values:
        return []
    result = [float(values[0])]
    for value in values[1:]:
        current = float(value)
        previous = result[-1]
        while current - previous > math.pi:
            current -= 2.0 * math.pi
        while current - previous < -math.pi:
            current += 2.0 * math.pi
        result.append(current)
    return result


def _wrap_angle(value: float) -> float:
    return (float(value) + math.pi) % (2.0 * math.pi) - math.pi


def _markdown(payload: dict[str, Any]) -> str:
    trajectory = payload["trajectory"]
    points = list(trajectory["points_xy"])
    first = points[0] if points else None
    last = points[-1] if points else None
    metadata = trajectory["metadata"]
    return "\n".join(
        [
            "# Alpamayo Trajectory Conversion",
            "",
            f"- prediction_json: `{payload['prediction_json']}`",
            f"- source: `{trajectory['source']}`",
            f"- points: `{len(points)}`",
            f"- native_steps: `{metadata['native_steps']}`",
            f"- native_hz: `{metadata['native_hz']}`",
            f"- target_hz: `{metadata['target_hz']}`",
            f"- first_xy: `{first}`",
            f"- last_xy: `{last}`",
            "",
        ]
    )


__all__ = [
    "ALPAMAYO_NATIVE_HZ",
    "ALPAMAYO_NATIVE_STEPS",
    "DRIVERX_TRAJECTORY_HZ",
    "DRIVERX_TRAJECTORY_STEPS",
    "alpamayo_prediction_to_trajectory",
    "load_prediction_json",
    "resample_alpamayo_xy",
    "resample_alpamayo_yaw",
    "select_alpamayo_rot_sample",
    "select_alpamayo_xyz_sample",
    "write_alpamayo_trajectory_conversion",
]
