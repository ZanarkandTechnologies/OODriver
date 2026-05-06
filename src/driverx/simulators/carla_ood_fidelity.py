"""High-fidelity helper seams for DriverX CARLA OOD demos."""

from __future__ import annotations

from typing import Any, Callable, Protocol

from driverx.simulators.carla_road_frame import RoadFrame


ROAD_ACTOR_SPAWN_Z_M = 0.6


class CarlaOodFidelityConfig(Protocol):
    road_lane_width_m: float
    fidelity_mode: str
    background_vehicle_count: int
    background_pedestrian_count: int
    camera_preset: str
    ood_motion_smoothing: str
    ood_max_step_m: float


TransformPayload = dict[str, dict[str, float]]
RoadTransformFn = Callable[[CarlaOodFidelityConfig, RoadFrame, float, float, float, float], TransformPayload]
CarlaTransformFn = Callable[[object, TransformPayload], object]
BlueprintFinderFn = Callable[[object], object]
PatternBlueprintFinderFn = Callable[[object, str], object]
SpawnActorFn = Callable[[object, object, object], object | None]
ActorSideEffectFn = Callable[[object], None]


def camera_transform(carla: object, preset: str) -> object:
    if preset == "chase":
        return carla.Transform(
            carla.Location(x=-7.5, z=3.2),
            carla.Rotation(pitch=-12.0),
        )
    if preset == "wide_context":
        return carla.Transform(
            carla.Location(x=-3.5, y=-4.5, z=4.1),
            carla.Rotation(pitch=-18.0, yaw=18.0),
        )
    return carla.Transform(
        carla.Location(x=1.6, z=2.3),
        carla.Rotation(pitch=-8.0),
    )


def smoothed_ood_pose(
    x_m: float,
    y_m: float,
    heading_deg: float,
    previous: tuple[float, float, float] | None,
    config: CarlaOodFidelityConfig,
) -> tuple[float, float, float]:
    if previous is None or config.ood_motion_smoothing == "linear":
        return x_m, y_m, heading_deg
    prev_x, prev_y, prev_heading = previous
    dx = x_m - prev_x
    dy = y_m - prev_y
    distance = (dx * dx + dy * dy) ** 0.5
    if distance <= config.ood_max_step_m:
        return x_m, y_m, heading_deg
    scale = config.ood_max_step_m / max(distance, 1e-6)
    return prev_x + dx * scale, prev_y + dy * scale, prev_heading + (heading_deg - prev_heading) * scale


def spawn_background_actors(
    world: object,
    blueprints: object,
    carla: object,
    config: CarlaOodFidelityConfig,
    road_frame: RoadFrame,
    spawned: list[object],
    actor_by_ref: dict[str, object],
    alignment_transforms: dict[str, list[TransformPayload]],
    *,
    find_vehicle_blueprint: BlueprintFinderFn,
    find_blueprint: PatternBlueprintFinderFn,
    road_transform: RoadTransformFn,
    carla_transform: CarlaTransformFn,
    spawn_actor_safely: SpawnActorFn,
    disable_actor_physics: ActorSideEffectFn,
) -> list[int]:
    actor_ids: list[int] = []
    for index in range(config.background_vehicle_count):
        blueprint = find_vehicle_blueprint(blueprints)
        spawn = _spawn_background_actor_from_candidates(
            world,
            blueprint,
            carla,
            config,
            road_frame,
            _background_vehicle_candidates(index, config),
            road_transform=road_transform,
            carla_transform=carla_transform,
            spawn_actor_safely=spawn_actor_safely,
        )
        if spawn is None:
            continue
        actor, payload = spawn
        disable_actor_physics(actor)
        spawned.append(actor)
        actor_ref = f"background_vehicle_{index}"
        actor_by_ref[actor_ref] = actor
        alignment_transforms[actor_ref] = [payload]
        actor_ids.append(int(getattr(actor, "id")))
    for index in range(config.background_pedestrian_count):
        try:
            blueprint = find_blueprint(blueprints, "walker.pedestrian.*")
        except Exception:
            blueprint = find_vehicle_blueprint(blueprints)
        spawn = _spawn_background_actor_from_candidates(
            world,
            blueprint,
            carla,
            config,
            road_frame,
            _background_pedestrian_candidates(index, config),
            road_transform=road_transform,
            carla_transform=carla_transform,
            spawn_actor_safely=spawn_actor_safely,
        )
        if spawn is None:
            continue
        actor, payload = spawn
        disable_actor_physics(actor)
        spawned.append(actor)
        actor_ref = f"background_pedestrian_{index}"
        actor_by_ref[actor_ref] = actor
        alignment_transforms[actor_ref] = [payload]
        actor_ids.append(int(getattr(actor, "id")))
    return actor_ids


def fidelity_metrics(
    config: CarlaOodFidelityConfig,
    tracks: list[dict[str, Any]],
    *,
    background_actor_ids: list[int],
) -> dict[str, Any]:
    ood_tracks = _tracks_for_ref(tracks, "ood_actor_0")
    ego_tracks = _tracks_for_ref(tracks, "ego")
    ood_steps = _step_distances(ood_tracks)
    visible_counts: dict[int, set[str]] = {}
    for track in tracks:
        visible_counts.setdefault(int(track["tick"]), set()).add(str(track["actor_ref"]))
    mean_visible = (
        round(sum(len(refs) for refs in visible_counts.values()) / len(visible_counts), 4)
        if visible_counts
        else None
    )
    return {
        "fidelity_mode": config.fidelity_mode,
        "background_vehicle_count": config.background_vehicle_count,
        "background_pedestrian_count": config.background_pedestrian_count,
        "background_actor_count": len(background_actor_ids),
        "background_actor_ids": background_actor_ids,
        "camera_preset": config.camera_preset,
        "ood_motion_smoothing": config.ood_motion_smoothing,
        "mean_ood_step_m": _mean(ood_steps),
        "max_ood_step_m": max(ood_steps, default=0.0),
        "ego_route_progress_m": _route_progress(ego_tracks),
        "visible_actor_count_mean": mean_visible,
    }


def _spawn_background_actor_from_candidates(
    world: object,
    blueprint: object,
    carla: object,
    config: CarlaOodFidelityConfig,
    road_frame: RoadFrame,
    candidates: list[tuple[float, float, float]],
    *,
    road_transform: RoadTransformFn,
    carla_transform: CarlaTransformFn,
    spawn_actor_safely: SpawnActorFn,
) -> tuple[object, TransformPayload] | None:
    for forward_m, lateral_m, yaw_deg in candidates:
        payload = road_transform(
            config,
            road_frame,
            forward_m,
            lateral_m,
            ROAD_ACTOR_SPAWN_Z_M,
            yaw_deg,
        )
        actor = spawn_actor_safely(world, blueprint, carla_transform(carla, payload))
        if actor is None:
            continue
        return actor, payload
    return None


def _background_vehicle_candidates(
    index: int,
    config: CarlaOodFidelityConfig,
) -> list[tuple[float, float, float]]:
    lane = config.road_lane_width_m
    base_forward = -18.0 - index * 11.0
    preferred_lateral = lane if index % 2 == 0 else -lane
    candidates: list[tuple[float, float, float]] = []
    for forward_delta in (0.0, -8.0, 8.0, -16.0, 16.0, -24.0):
        for lateral in (
            preferred_lateral,
            -preferred_lateral,
            0.0,
            preferred_lateral * 1.5,
            -preferred_lateral * 1.5,
        ):
            candidates.append((base_forward + forward_delta, lateral, 0.0))
    return candidates


def _background_pedestrian_candidates(
    index: int,
    config: CarlaOodFidelityConfig,
) -> list[tuple[float, float, float]]:
    lane = config.road_lane_width_m
    base_forward = 16.0 + index * 6.0
    side = -1.0 if index % 2 == 0 else 1.0
    candidates: list[tuple[float, float, float]] = []
    for forward_delta in (0.0, 5.0, -5.0, 10.0, -10.0):
        for lateral in (
            side * lane * 1.4,
            side * lane,
            -side * lane * 1.4,
            -side * lane,
            0.0,
        ):
            candidates.append((base_forward + forward_delta, lateral, 90.0 * side))
    return candidates


def _tracks_for_ref(tracks: list[dict[str, Any]], actor_ref: str) -> list[dict[str, Any]]:
    return [track for track in tracks if track.get("actor_ref") == actor_ref]


def _step_distances(tracks: list[dict[str, Any]]) -> list[float]:
    distances: list[float] = []
    for previous, current in zip(tracks, tracks[1:]):
        prev_location = dict(previous.get("location", {}))
        curr_location = dict(current.get("location", {}))
        dx = float(curr_location.get("x", 0.0)) - float(prev_location.get("x", 0.0))
        dy = float(curr_location.get("y", 0.0)) - float(prev_location.get("y", 0.0))
        distances.append(round((dx * dx + dy * dy) ** 0.5, 4))
    return distances


def _route_progress(tracks: list[dict[str, Any]]) -> float:
    if len(tracks) < 2:
        return 0.0
    start = dict(tracks[0].get("location", {}))
    end = dict(tracks[-1].get("location", {}))
    dx = float(end.get("x", 0.0)) - float(start.get("x", 0.0))
    dy = float(end.get("y", 0.0)) - float(start.get("y", 0.0))
    return round((dx * dx + dy * dy) ** 0.5, 4)


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


__all__ = [
    "ROAD_ACTOR_SPAWN_Z_M",
    "camera_transform",
    "fidelity_metrics",
    "smoothed_ood_pose",
    "spawn_background_actors",
]
