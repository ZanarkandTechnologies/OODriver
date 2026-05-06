"""Road-local coordinate helpers for CARLA scenario generation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RoadFrameSelector:
    """Selects the CARLA route anchor used as the local scenario origin."""

    spawn_index: int = 0
    forward_offset_m: float = 0.0
    lateral_offset_m: float = 0.0
    yaw_delta_deg: float = 0.0
    lane_width_m: float = 3.5
    max_lateral_offset_m: float = 6.0

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "spawn_index": self.spawn_index,
            "forward_offset_m": self.forward_offset_m,
            "lateral_offset_m": self.lateral_offset_m,
            "yaw_delta_deg": self.yaw_delta_deg,
            "lane_width_m": self.lane_width_m,
            "max_lateral_offset_m": self.max_lateral_offset_m,
        }


@dataclass(frozen=True)
class RoadFrame:
    """A lane-relative local frame.

    Local `x` points forward along the road. Local `y` is lateral, positive to
    the right of the selected anchor heading in the DriverX convention.
    """

    origin_x: float
    origin_y: float
    origin_z: float
    yaw_deg: float
    lane_width_m: float = 3.5
    road_id: int | None = None
    lane_id: int | None = None
    spawn_index: int = 0
    selector: RoadFrameSelector = field(default_factory=RoadFrameSelector)
    source: str = "spawn_point"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "origin": {"x": self.origin_x, "y": self.origin_y, "z": self.origin_z},
            "yaw_deg": self.yaw_deg,
            "lane_width_m": self.lane_width_m,
            "road_id": self.road_id,
            "lane_id": self.lane_id,
            "spawn_index": self.spawn_index,
            "selector": self.selector.to_jsonable(),
            "source": self.source,
        }


@dataclass(frozen=True)
class RoadAlignmentReport:
    actor_ref: str
    num_samples: int
    offroad_samples: int
    max_abs_lateral_m: float | None
    starts_on_road: bool
    passes: bool
    max_lateral_offset_m: float
    road_frame: RoadFrame

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "actor_ref": self.actor_ref,
            "num_samples": self.num_samples,
            "offroad_samples": self.offroad_samples,
            "max_abs_lateral_m": self.max_abs_lateral_m,
            "starts_on_road": self.starts_on_road,
            "passes": self.passes,
            "max_lateral_offset_m": self.max_lateral_offset_m,
            "road_frame": self.road_frame.to_jsonable(),
        }


def transform_payload(
    x: float,
    y: float,
    z: float = 0.2,
    yaw: float = 0.0,
) -> dict[str, dict[str, float]]:
    return {
        "location": {"x": float(x), "y": float(y), "z": float(z)},
        "rotation": {"pitch": 0.0, "yaw": float(yaw), "roll": 0.0},
    }


def resolve_road_frame(world_map: Any, selector: RoadFrameSelector | None = None) -> RoadFrame:
    """Resolve a road-local frame from a CARLA-like map object."""

    selector = selector or RoadFrameSelector()
    spawn_points = list(world_map.get_spawn_points())
    if not spawn_points:
        raise RuntimeError("CARLA map has no spawn points.")
    spawn_index = max(0, min(selector.spawn_index, len(spawn_points) - 1))
    spawn_transform = spawn_points[spawn_index]
    anchor = _project_to_road(world_map, spawn_transform) or spawn_transform
    location = getattr(anchor, "location", getattr(spawn_transform, "location", None))
    rotation = getattr(anchor, "rotation", getattr(spawn_transform, "rotation", None))
    if location is None or rotation is None:
        raise RuntimeError("CARLA spawn point did not expose location and rotation.")
    lane_width = _float_attr(anchor, "lane_width", selector.lane_width_m)
    yaw = _float_attr(rotation, "yaw", 0.0) + selector.yaw_delta_deg
    origin_payload = local_pose_to_payload(
        RoadFrame(
            origin_x=_float_attr(location, "x", 0.0),
            origin_y=_float_attr(location, "y", 0.0),
            origin_z=_float_attr(location, "z", 0.0),
            yaw_deg=yaw,
            lane_width_m=lane_width,
            road_id=_optional_int_attr(anchor, "road_id"),
            lane_id=_optional_int_attr(anchor, "lane_id"),
            spawn_index=spawn_index,
            selector=selector,
            source="waypoint" if anchor is not spawn_transform else "spawn_point",
        ),
        selector.forward_offset_m,
        selector.lateral_offset_m,
        0.0,
        0.0,
    )
    origin = origin_payload["location"]
    return RoadFrame(
        origin_x=origin["x"],
        origin_y=origin["y"],
        origin_z=_float_attr(location, "z", 0.0),
        yaw_deg=yaw,
        lane_width_m=lane_width,
        road_id=_optional_int_attr(anchor, "road_id"),
        lane_id=_optional_int_attr(anchor, "lane_id"),
        spawn_index=spawn_index,
        selector=selector,
        source="waypoint" if anchor is not spawn_transform else "spawn_point",
    )


def local_pose_to_payload(
    frame: RoadFrame,
    x_m: float,
    y_m: float,
    z_m: float = 0.2,
    yaw_delta_deg: float = 0.0,
) -> dict[str, dict[str, float]]:
    """Convert a road-local pose into a CARLA transform payload."""

    yaw_rad = math.radians(frame.yaw_deg)
    cos_yaw = math.cos(yaw_rad)
    sin_yaw = math.sin(yaw_rad)
    world_x = frame.origin_x + float(x_m) * cos_yaw - float(y_m) * sin_yaw
    world_y = frame.origin_y + float(x_m) * sin_yaw + float(y_m) * cos_yaw
    world_z = frame.origin_z + float(z_m)
    return transform_payload(
        round(world_x, 6),
        round(world_y, 6),
        round(world_z, 6),
        round(frame.yaw_deg + float(yaw_delta_deg), 6),
    )


def payload_to_local_xy(
    frame: RoadFrame,
    transform: dict[str, dict[str, float]],
) -> tuple[float, float]:
    location = transform.get("location", {})
    dx = float(location.get("x", 0.0)) - frame.origin_x
    dy = float(location.get("y", 0.0)) - frame.origin_y
    yaw_rad = math.radians(frame.yaw_deg)
    cos_yaw = math.cos(yaw_rad)
    sin_yaw = math.sin(yaw_rad)
    local_x = dx * cos_yaw + dy * sin_yaw
    local_y = -dx * sin_yaw + dy * cos_yaw
    return (local_x, local_y)


def transform_payload_to_road_frame(
    frame: RoadFrame,
    transform: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    location = transform.get("location", {})
    rotation = transform.get("rotation", {})
    return local_pose_to_payload(
        frame,
        float(location.get("x", 0.0)),
        float(location.get("y", 0.0)),
        float(location.get("z", 0.2)),
        float(rotation.get("yaw", 0.0)),
    )


def validate_road_aligned_track(
    frame: RoadFrame,
    transforms: list[dict[str, dict[str, float]]],
    *,
    actor_ref: str,
    max_lateral_offset_m: float | None = None,
) -> RoadAlignmentReport:
    allowed = (
        float(max_lateral_offset_m)
        if max_lateral_offset_m is not None
        else frame.selector.max_lateral_offset_m
    )
    local_y_values = [abs(payload_to_local_xy(frame, transform)[1]) for transform in transforms]
    offroad = sum(1 for value in local_y_values if value > allowed)
    starts_on_road = bool(local_y_values) and local_y_values[0] <= allowed
    return RoadAlignmentReport(
        actor_ref=actor_ref,
        num_samples=len(transforms),
        offroad_samples=offroad,
        max_abs_lateral_m=max(local_y_values) if local_y_values else None,
        starts_on_road=starts_on_road,
        passes=bool(local_y_values) and starts_on_road and offroad == 0,
        max_lateral_offset_m=allowed,
        road_frame=frame,
    )


def _project_to_road(world_map: Any, transform: Any) -> Any | None:
    if not hasattr(world_map, "get_waypoint"):
        return None
    try:
        waypoint = world_map.get_waypoint(
            transform.location,
            project_to_road=True,
        )
    except TypeError:
        try:
            waypoint = world_map.get_waypoint(transform.location)
        except Exception:
            return None
    except Exception:
        return None
    if waypoint is None:
        return None
    waypoint_transform = getattr(waypoint, "transform", None)
    if waypoint_transform is None:
        return None
    return waypoint_transform


def _float_attr(value: Any, attr: str, default: float) -> float:
    try:
        return float(getattr(value, attr))
    except (TypeError, ValueError, AttributeError):
        return float(default)


def _optional_int_attr(value: Any, attr: str) -> int | None:
    try:
        raw = getattr(value, attr)
    except AttributeError:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


__all__ = [
    "RoadAlignmentReport",
    "RoadFrame",
    "RoadFrameSelector",
    "local_pose_to_payload",
    "payload_to_local_xy",
    "resolve_road_frame",
    "transform_payload",
    "transform_payload_to_road_frame",
    "validate_road_aligned_track",
]
