"""Paused receding-horizon closed-loop runner for fake/local CARLA proof."""

from __future__ import annotations

import json
import queue
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

from driverx.core.types import TrajectoryCandidate
from driverx.policies.alpamayo_inference_bridge import (
    run_alpamayo_inference_bridge,
    write_alpamayo_inference_result,
)
from driverx.policies.closed_loop_types import claim_for_mode, normalize_closed_loop_trace
from driverx.policies.control_safety import SafetyContext, validate_control_chunk
from driverx.policies.alpamayo_trajectory import alpamayo_prediction_to_trajectory
from driverx.policies.trajectory_control import (
    EgoPose,
    TrajectoryControlConfig,
    load_policy_decision_trajectory,
    trajectory_to_control_trace,
)
from driverx.simulators.carla_policy_replay import apply_control_trace
from driverx.simulators.carla_sync import (
    CarlaSyncConfig,
    CarlaSyncSession,
    build_alpamayo_package_from_synced_checkpoint,
    capture_aligned_checkpoint,
)

ClosedLoopBackend = Literal["fake-carla", "carla-live"]
ClosedLoopPolicy = Literal["fake-trajectory", "cached-decision", "alpamayo-remote"]


@dataclass(frozen=True)
class PausedClosedLoopConfig:
    backend: ClosedLoopBackend = "fake-carla"
    policy: ClosedLoopPolicy = "fake-trajectory"
    steps: int = 3
    control_ticks_per_step: int = 4
    fixed_delta_seconds: float = 0.25
    run_id: str = "paused-closed-loop"
    scenario_id: str = "fake-static-blocker"
    host: str = "127.0.0.1"
    port: int = 2000
    timeout_s: float = 45.0
    town: str | None = None
    map_name: str | None = None
    load_map: bool = False
    weather_preset: str | None = None
    camera_width: int = 640
    camera_height: int = 360
    camera_fov: float = 90.0
    cache_root: Path | None = None
    remote_output_root: str | None = None
    alpamayo_python: Path | None = None
    alpamayo_command: str | None = None
    spawn_index: int = 0


def run_paused_closed_loop(
    config: PausedClosedLoopConfig,
    run_dir: Path,
    *,
    carla_module: object | None = None,
    client_factory: Callable[[str, int], object] | None = None,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    if config.backend != "fake-carla":
        return _run_live_closed_loop(
            config,
            run_dir,
            carla_module=carla_module,
            client_factory=client_factory,
        )
    return _run_fake_closed_loop(config, run_dir)


def _run_fake_closed_loop(config: PausedClosedLoopConfig, run_dir: Path) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    rgb_dir = run_dir / "rgb"
    rgb_dir.mkdir(parents=True, exist_ok=True)
    ego_x = 0.0
    frame = 100
    for step_index in range(config.steps):
        step_dir = run_dir / f"step_{step_index:03d}"
        step_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = run_dir / f"step_{step_index:03d}_checkpoint.json"
        prediction_path = run_dir / f"step_{step_index:03d}_prediction.json"
        control_trace_path = run_dir / f"step_{step_index:03d}_control_trace.json"
        inference_result_path = step_dir / "alpamayo_inference_result.json"
        trajectory = _fake_trajectory(step_index)
        prediction_path.write_text(json.dumps(_fake_prediction(step_index, trajectory), indent=2), encoding="utf-8")
        inference_result_path.write_text(
            json.dumps(
                {
                    "status": "passed",
                    "mode": config.policy,
                    "prediction_json_path": str(prediction_path),
                    "latency_ms": 12.0,
                    "vram_peak_mb": 0.0,
                    "reasoning_snippet": f"Step {step_index}: conservative fake trajectory for closed-loop contract testing.",
                    "cache_key": f"fake-{step_index}",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        trace = trajectory_to_control_trace(
            trajectory,
            source_policy_id="fake-trajectory",
            ego_pose=EgoPose(x=ego_x, y=0.0, yaw_deg=0.0),
            config=TrajectoryControlConfig(max_speed_mps=3.0, max_throttle=0.25),
        )
        safe = validate_control_chunk(
            trace,
            SafetyContext(nearest_object_distance_m=0.8 if step_index == 0 else 4.0, corridor_half_width_m=1.5),
        )
        limited_commands = safe.control_trace.commands[: config.control_ticks_per_step]
        control_payload = {
            **safe.control_trace.to_jsonable(),
            "commands": [command.to_jsonable() for command in limited_commands],
            "safety_report": safe.to_jsonable(),
        }
        control_trace_path.write_text(json.dumps(control_payload, indent=2), encoding="utf-8")
        input_frame = frame
        applied = len(limited_commands)
        frame += applied
        ego_x += sum(command.throttle for command in limited_commands) * 0.8
        checkpoint = {
            "checkpoint_id": f"{config.run_id}-step-{step_index:03d}",
            "world_frame_id": input_frame,
            "post_action_frame_id": frame,
            "sensor_frame_ids": [input_frame, input_frame, input_frame],
            "sim_time_s": round(input_frame * config.fixed_delta_seconds, 4),
        }
        pre_frames = _write_fake_step_images(step_dir / "pre", step_index, "pre", input_frame)
        post_frames = _write_fake_step_images(step_dir / "post", step_index, "post", frame)
        frame_copy = rgb_dir / f"frame_{step_index * 2:06d}.png"
        post_copy = rgb_dir / f"frame_{step_index * 2 + 1:06d}.png"
        shutil.copyfile(pre_frames[1], frame_copy)
        shutil.copyfile(post_frames[1], post_copy)
        checkpoint_path.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
        steps.append(
            {
                "step_index": step_index,
                "input_frame_id": input_frame,
                "post_action_frame_id": frame,
                "applied_control_count": applied,
                "model_latency_ms": 12.0,
                "prediction_path": str(prediction_path),
                "control_trace_path": str(control_trace_path),
                "checkpoint_path": str(checkpoint_path),
                "pre_rgb_frame_paths": [str(path) for path in pre_frames],
                "post_rgb_frame_paths": [str(path) for path in post_frames],
                "inference_result_path": str(inference_result_path),
                "selected_trajectory": [[point[0], point[1]] for point in trajectory.points_xy],
                "applied_control_summary": {"status": "passed", "applied_count": applied},
                "safety_summary": safe.to_jsonable(),
                "planned_vs_actual_error_m": _planned_error(safe.planned_vs_actual_error_m),
                "source_video_segment": {"rgb_folder": str(rgb_dir), "start_frame": step_index * 2, "end_frame": step_index * 2 + 1},
                "sensor_frame_ids": checkpoint["sensor_frame_ids"],
                "planned_path": [{"x": point[0], "y": point[1]} for point in trajectory.points_xy[: applied]],
                "actual_path": [{"x": round(ego_x, 4), "y": 0.0, "frame": frame}],
                "safety_report": safe.to_jsonable(),
            }
        )
    trace_payload = normalize_closed_loop_trace(
        {
            "run_id": config.run_id,
            "scenario_id": config.scenario_id,
            "mode": "paused_receding_horizon",
            "backend": config.backend,
            "policy": config.policy,
            "steps": steps,
            "latency_ms": {"mean": 12.0, "max": 12.0},
            "control_applied_count": sum(int(step["applied_control_count"]) for step in steps),
            "observed_after_action_count": len(steps),
            "rgb_folder": str(rgb_dir),
            "entity_tracks_path": str(_write_fake_tracks(run_dir, steps)),
            "claim_boundaries": _closed_loop_claim_boundaries(config),
        }
    )
    return write_closed_loop_trace(run_dir, trace_payload)


def _run_live_closed_loop(
    config: PausedClosedLoopConfig,
    run_dir: Path,
    *,
    carla_module: object | None,
    client_factory: Callable[[str, int], object] | None,
) -> dict[str, Any]:
    try:
        carla = carla_module or __import__("carla")
    except Exception as exc:
        return write_closed_loop_trace(run_dir, _blocked_live_trace(config, f"CARLA Python module unavailable: {exc}"))
    try:
        factory = client_factory or getattr(carla, "Client")
        client = factory(config.host, int(config.port))
        if hasattr(client, "set_timeout"):
            client.set_timeout(float(config.timeout_s))
        world = _load_or_get_world(client, config)
        _apply_weather(world, carla, config.weather_preset)
        ego, sensors, sensor_queues, visual_queues, spawned = _spawn_live_actors(world, carla, config)
    except Exception as exc:
        return write_closed_loop_trace(run_dir, _blocked_live_trace(config, f"CARLA live setup failed: {type(exc).__name__}: {exc}"))
    steps: list[dict[str, Any]] = []
    rgb_dir = run_dir / "rgb"
    rgb_dir.mkdir(parents=True, exist_ok=True)
    tracks: list[dict[str, Any]] = []
    last_frame: int | None = None
    rgb_frame_index = 0
    action_rgb_frame_count = 0
    ego_vehicle_visible = False
    try:
        with CarlaSyncSession(
            world,
            CarlaSyncConfig(fixed_delta_seconds=config.fixed_delta_seconds, timeout_s=min(config.timeout_s, 10.0)),
        ) as session:
            for step_index in range(config.steps):
                step_dir = run_dir / f"step_{step_index:03d}"
                pre_dir = step_dir / "pre"
                post_dir = step_dir / "post"
                infer_dir = step_dir / "inference"
                step_dir.mkdir(parents=True, exist_ok=True)
                pre = capture_aligned_checkpoint(
                    session,
                    sensor_queues,
                    pre_dir,
                    checkpoint_id=f"{config.run_id}-step-{step_index:03d}-pre",
                    min_frame_id=last_frame,
                )
                if pre.blockers:
                    raise RuntimeError("; ".join(pre.blockers))
                visual_pre_paths = _drain_visual_frames(
                    visual_queues,
                    step_dir / "visual_pre",
                    min_frame_id=pre.world_frame_id,
                    label="pre",
                )
                package_path = step_dir / "alpamayo_checkpoint_package.json"
                package = build_alpamayo_package_from_synced_checkpoint(
                    pre,
                    route_context={"scenario_id": config.scenario_id, "town": config.map_name or config.town},
                )
                package.update(_alpamayo_motion_stub(ego))
                _absolutize_package_frame_paths(package)
                package_path.write_text(json.dumps(package, indent=2), encoding="utf-8")
                prediction_path, inference_result, policy_id, trajectory = _infer_step(config, package_path, infer_dir, step_index)
                trace = trajectory_to_control_trace(
                    trajectory,
                    source_policy_id=policy_id,
                    ego_pose=_ego_pose(ego),
                    config=TrajectoryControlConfig(
                        max_speed_mps=5.0,
                        max_throttle=0.45,
                        min_throttle_when_moving=0.24,
                        max_steer=0.28,
                        dt_s=config.fixed_delta_seconds,
                    ),
                )
                safe = validate_control_chunk(
                    trace,
                    SafetyContext(nearest_object_distance_m=4.0, corridor_half_width_m=1.75),
                )
                control_trace_path = step_dir / "control_trace.json"
                limited_commands = safe.control_trace.commands[: config.control_ticks_per_step]
                control_trace_path.write_text(
                    json.dumps(
                        {
                            **safe.control_trace.to_jsonable(),
                            "commands": [command.to_jsonable() for command in limited_commands],
                            "safety_report": safe.to_jsonable(),
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                application = apply_control_trace(
                    ego,
                    safe.control_trace,
                    world=world,
                    carla_module=carla,
                    tick_timeout_s=config.timeout_s,
                    limit=config.control_ticks_per_step,
                )
                visual_action_paths = _drain_visual_frames(
                    visual_queues,
                    step_dir / "action",
                    min_frame_id=pre.world_frame_id + 1,
                    label="action",
                )
                post = capture_aligned_checkpoint(
                    session,
                    sensor_queues,
                    post_dir,
                    checkpoint_id=f"{config.run_id}-step-{step_index:03d}-post",
                    min_frame_id=max(pre.world_frame_id + application.tick_count, pre.world_frame_id + 1),
                )
                if post.blockers:
                    raise RuntimeError("; ".join(post.blockers))
                visual_post_paths = _drain_visual_frames(
                    visual_queues,
                    step_dir / "visual_post",
                    min_frame_id=post.world_frame_id,
                    label="post",
                )
                pre_checkpoint_path = step_dir / "pre_checkpoint.json"
                post_checkpoint_path = step_dir / "post_checkpoint.json"
                pre_checkpoint_path.write_text(json.dumps(pre.to_jsonable(), indent=2), encoding="utf-8")
                post_checkpoint_path.write_text(json.dumps(post.to_jsonable(), indent=2), encoding="utf-8")
                pre_paths = _camera_paths(pre)
                post_paths = _camera_paths(post)
                visual_source_paths = [*visual_pre_paths, *visual_action_paths, *visual_post_paths]
                if visual_source_paths:
                    copied, rgb_frame_index = _copy_rgb_sequence(visual_source_paths, rgb_dir, rgb_frame_index)
                    action_rgb_frame_count += len(visual_action_paths)
                    ego_vehicle_visible = True
                else:
                    copied, rgb_frame_index = _copy_rgb_sequence(
                        [_center_frame(pre_paths), _center_frame(post_paths)],
                        rgb_dir,
                        rgb_frame_index,
                    )
                segment_start = rgb_frame_index - copied
                segment_end = rgb_frame_index - 1
                tracks.append(_actor_track(ego, "ego", step_index, post.world_frame_id))
                steps.append(
                    {
                        "step_index": step_index,
                        "input_frame_id": pre.world_frame_id,
                        "post_action_frame_id": post.world_frame_id,
                        "applied_control_count": application.applied_count,
                        "model_latency_ms": inference_result.get("latency_ms"),
                        "prediction_path": str(prediction_path),
                        "control_trace_path": str(control_trace_path),
                        "checkpoint_path": str(pre_checkpoint_path),
                        "pre_checkpoint_path": str(pre_checkpoint_path),
                        "post_checkpoint_path": str(post_checkpoint_path),
                        "sensor_frame_ids": pre.to_jsonable().get("sensor_frame_ids", []),
                        "pre_rgb_frame_paths": [str(path) for path in pre_paths],
                        "post_rgb_frame_paths": [str(path) for path in post_paths],
                        "visual_rgb_frame_paths": [str(path) for path in visual_source_paths],
                        "action_rgb_frame_paths": [str(path) for path in visual_action_paths],
                        "inference_result_path": str(infer_dir / "alpamayo_inference_result.json"),
                        "selected_trajectory": [[point[0], point[1]] for point in trajectory.points_xy],
                        "applied_control_summary": application.to_jsonable(),
                        "safety_summary": safe.to_jsonable(),
                        "planned_vs_actual_error_m": _planned_error(safe.planned_vs_actual_error_m),
                        "source_video_segment": {"rgb_folder": str(rgb_dir), "start_frame": segment_start, "end_frame": segment_end},
                        "planned_path": [{"x": point[0], "y": point[1]} for point in trajectory.points_xy[: application.applied_count]],
                        "actual_path": [_actor_track(ego, "ego", step_index, post.world_frame_id)],
                        "safety_report": safe.to_jsonable(),
                        "ego_vehicle_visible": bool(visual_source_paths),
                        "visual_camera_role": "spectator_chase" if visual_source_paths else "front_ego_fallback",
                    }
                )
                last_frame = post.world_frame_id
        tracks_path = _write_tracks(run_dir, tracks)
        trace_payload = normalize_closed_loop_trace(
            {
                "run_id": config.run_id,
                "scenario_id": config.scenario_id,
                "mode": "paused_receding_horizon",
                "backend": config.backend,
                "policy": config.policy,
                "steps": steps,
                "latency_ms": _latency_summary(steps),
                "control_applied_count": sum(int(step["applied_control_count"]) for step in steps),
                "observed_after_action_count": len(steps),
                "rgb_folder": str(rgb_dir),
                "source_frame_count": rgb_frame_index,
                "action_rgb_frame_count": action_rgb_frame_count,
                "ego_vehicle_visible": ego_vehicle_visible,
                "visual_camera_role": "spectator_chase" if ego_vehicle_visible else "front_ego_fallback",
                "visible_ood_object": True,
                "entity_tracks_path": str(tracks_path),
                "carla_endpoint": {"host": config.host, "port": config.port},
                "map_name": config.map_name or config.town,
                "weather_preset": config.weather_preset,
                "claim_boundaries": _closed_loop_claim_boundaries(config),
            }
        )
        return write_closed_loop_trace(run_dir, trace_payload)
    except Exception as exc:
        return write_closed_loop_trace(run_dir, _blocked_live_trace(config, f"CARLA live loop failed: {type(exc).__name__}: {exc}"))
    finally:
        for actor in [*sensors, *spawned, ego]:
            try:
                actor.destroy()
            except Exception:
                pass


def write_closed_loop_trace(run_dir: Path, trace: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = normalize_closed_loop_trace(trace)
    json_path = run_dir / "closed_loop_trace.json"
    report_path = run_dir / "closed_loop_trace.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _fake_trajectory(step_index: int) -> TrajectoryCandidate:
    lateral = 0.0 if step_index != 1 else 0.35
    return TrajectoryCandidate(
        points_xy=[(0.25 * index, lateral) for index in range(20)],
        source="fake_closed_loop_policy",
        score=0.8,
        metadata={"step_index": step_index},
    )


def _fake_prediction(step_index: int, trajectory: TrajectoryCandidate) -> dict[str, Any]:
    return {
        "policy_id": "fake-trajectory",
        "cot": f"Step {step_index}: obstacle pressure ahead; keep a conservative lane-centered trajectory.",
        "policy_decision": {
            "policy_id": "fake-trajectory",
            "action": {
                "trajectory": {
                    "points_xy": [list(point) for point in trajectory.points_xy],
                    "source": trajectory.source,
                    "score": trajectory.score,
                }
            },
        },
    }


def _blocked_live_trace(config: PausedClosedLoopConfig, reason: str) -> dict[str, Any]:
    return normalize_closed_loop_trace(
        {
            "run_id": config.run_id,
            "scenario_id": config.scenario_id,
            "mode": "none",
            "backend": config.backend,
            "policy": config.policy,
            "steps": [],
            "claim_boundaries": ["closed_loop_vla_control=false", "real_time_vla_control=false"],
            "blockers": [reason],
        }
    )


def _closed_loop_claim_boundaries(config: PausedClosedLoopConfig) -> list[str]:
    claims = [
        claim_for_mode("paused_receding_horizon"),
        "real_time_vla_control=false",
        f"closed_loop_backend={config.backend}",
    ]
    if config.backend == "carla-live":
        claims.extend(["time_warped_offline_demo=true", "live_carla_provenance=true"])
    if config.policy == "alpamayo-remote":
        claims.append("alpamayo_outputs_applied_to_carla_controls=true")
    else:
        claims.extend(
            [
                "alpamayo_outputs_applied_to_carla_controls=false",
                f"closed_loop_policy={config.policy}",
            ]
        )
    return claims


def _infer_step(
    config: PausedClosedLoopConfig,
    package_path: Path,
    infer_dir: Path,
    step_index: int,
) -> tuple[Path, dict[str, Any], str, TrajectoryCandidate]:
    mode = "remote-kasm" if config.policy == "alpamayo-remote" else "fake"
    result = run_alpamayo_inference_bridge(
        package_path=package_path,
        mode=mode,
        output_root=infer_dir.parent,
        run_id=infer_dir.name,
        cache_root=config.cache_root,
        remote_output_root=config.remote_output_root,
        alpamayo_python=config.alpamayo_python,
        alpamayo_command=config.alpamayo_command,
        timeout_s=config.timeout_s,
    )
    inference_payload = write_alpamayo_inference_result(infer_dir, result)
    if result.prediction_json_path is None:
        if config.policy == "alpamayo-remote":
            raise RuntimeError("Alpamayo remote inference did not produce prediction JSON: " + "; ".join(result.blockers))
        fallback_path = infer_dir / "fallback_fake_prediction.json"
        trajectory = _fake_trajectory(step_index)
        fallback_path.write_text(json.dumps(_fake_prediction(step_index, trajectory), indent=2), encoding="utf-8")
        return fallback_path, inference_payload, "fake-trajectory", trajectory
    prediction_path = Path(result.prediction_json_path)
    try:
        policy_id, trajectory = load_policy_decision_trajectory(prediction_path)
    except Exception:
        payload = json.loads(prediction_path.read_text(encoding="utf-8"))
        pred_xyz = payload.get("pred_xyz")
        if pred_xyz is None and isinstance(payload.get("outputs"), dict):
            pred_xyz = payload["outputs"].get("pred_xyz")
        trajectory = alpamayo_prediction_to_trajectory(
            pred_xyz,
            source="alpamayo_remote_closed_loop",
            score=0.9,
            reasoning=str(payload.get("cot_summary") or payload.get("cot") or ""),
        )
        policy_id = "alpamayo-remote"
    return prediction_path, inference_payload, policy_id, trajectory


def _load_or_get_world(client: object, config: PausedClosedLoopConfig) -> object:
    map_name = config.map_name or config.town
    if config.load_map and map_name and hasattr(client, "load_world"):
        return client.load_world(map_name)
    if hasattr(client, "get_world"):
        return client.get_world()
    raise RuntimeError("CARLA client does not expose get_world/load_world")


def _apply_weather(world: object, carla: object, preset: str | None) -> None:
    if not preset or not hasattr(world, "set_weather"):
        return
    weather = getattr(getattr(carla, "WeatherParameters", object), preset, None)
    if weather is None:
        return
    world.set_weather(weather)


def _spawn_live_actors(
    world: object,
    carla: object,
    config: PausedClosedLoopConfig,
) -> tuple[object, list[object], dict[int, "queue.Queue[object]"], dict[int, "queue.Queue[object]"], list[object]]:
    library = world.get_blueprint_library()
    spawn_points = world.get_map().get_spawn_points()
    if not spawn_points:
        raise RuntimeError("CARLA map has no spawn points")
    spawn_point = spawn_points[config.spawn_index % len(spawn_points)]
    vehicle_bp = _first_blueprint(library, ["vehicle.lincoln.mkz_2020", "vehicle.tesla.model3", "vehicle.*"])
    ego = world.try_spawn_actor(vehicle_bp, spawn_point) if hasattr(world, "try_spawn_actor") else None
    if ego is None:
        ego = world.spawn_actor(vehicle_bp, spawn_point)
    spawned = _spawn_simple_blocker(world, carla, library, spawn_point)
    sensors: list[object] = []
    sensor_queues: dict[int, queue.Queue[object]] = {}
    visual_queues: dict[int, queue.Queue[object]] = {}
    camera_bp = _first_blueprint(library, ["sensor.camera.rgb"])
    _set_attribute(camera_bp, "image_size_x", str(config.camera_width))
    _set_attribute(camera_bp, "image_size_y", str(config.camera_height))
    _set_attribute(camera_bp, "fov", str(config.camera_fov))
    for camera_index, yaw in enumerate((-25.0, 0.0, 25.0)):
        transform = carla.Transform(carla.Location(x=1.6, z=1.7), carla.Rotation(pitch=-8.0, yaw=yaw))
        camera = world.spawn_actor(camera_bp, transform, attach_to=ego)
        images: "queue.Queue[object]" = queue.Queue()
        camera.listen(images.put)
        sensors.append(camera)
        sensor_queues[camera_index] = images
    chase_transform = _spectator_chase_transform(carla, spawn_point)
    chase_camera = world.spawn_actor(camera_bp, chase_transform)
    chase_images: "queue.Queue[object]" = queue.Queue()
    chase_camera.listen(chase_images.put)
    sensors.append(chase_camera)
    visual_queues[3] = chase_images
    return ego, sensors, sensor_queues, visual_queues, spawned


def _spawn_simple_blocker(world: object, carla: object, library: object, spawn_point: object) -> list[object]:
    spawned: list[object] = []
    try:
        bp = _first_blueprint(library, ["static.prop.constructioncone", "static.prop.dirtdebris01", "static.prop.foodcart"])
        loc = spawn_point.location
        yaw_rad = float(spawn_point.rotation.yaw) * 3.141592653589793 / 180.0
        blocker_location = carla.Location(x=loc.x + 10.0 * __import__("math").cos(yaw_rad), y=loc.y + 10.0 * __import__("math").sin(yaw_rad), z=loc.z + 0.05)
        blocker_transform = carla.Transform(blocker_location, spawn_point.rotation)
        blocker = world.try_spawn_actor(bp, blocker_transform) if hasattr(world, "try_spawn_actor") else world.spawn_actor(bp, blocker_transform)
        if blocker is not None:
            spawned.append(blocker)
    except Exception:
        pass
    return spawned


def _spectator_chase_transform(carla: object, spawn_point: object) -> object:
    yaw_deg = float(spawn_point.rotation.yaw)
    yaw_rad = yaw_deg * 3.141592653589793 / 180.0
    cos_yaw = __import__("math").cos(yaw_rad)
    sin_yaw = __import__("math").sin(yaw_rad)
    loc = spawn_point.location
    camera_location = carla.Location(
        x=loc.x - 7.5 * cos_yaw,
        y=loc.y - 7.5 * sin_yaw,
        z=loc.z + 2.6,
    )
    camera_rotation = carla.Rotation(pitch=-9.0, yaw=yaw_deg)
    return carla.Transform(camera_location, camera_rotation)


def _first_blueprint(library: object, patterns: list[str]) -> object:
    for pattern in patterns:
        try:
            if hasattr(library, "find") and "*" not in pattern:
                return library.find(pattern)
            matches = library.filter(pattern)
            if matches:
                return matches[0]
        except Exception:
            continue
    raise RuntimeError(f"no CARLA blueprint matched {patterns}")


def _set_attribute(blueprint: object, key: str, value: str) -> None:
    if hasattr(blueprint, "set_attribute"):
        blueprint.set_attribute(key, value)


def _ego_pose(actor: object) -> EgoPose:
    try:
        transform = actor.get_transform()
        speed_mps = 0.0
        try:
            velocity = actor.get_velocity()
            speed_mps = float((velocity.x**2 + velocity.y**2 + velocity.z**2) ** 0.5)
        except Exception:
            speed_mps = 0.0
        return EgoPose(
            x=float(transform.location.x),
            y=float(transform.location.y),
            yaw_deg=float(transform.rotation.yaw),
            speed_mps=speed_mps,
        )
    except Exception:
        return EgoPose()


def _actor_track(actor: object, role: str, step_index: int, frame: int) -> dict[str, Any]:
    try:
        transform = actor.get_transform()
        return {
            "role": role,
            "step_index": step_index,
            "frame": frame,
            "x": round(float(transform.location.x), 4),
            "y": round(float(transform.location.y), 4),
            "z": round(float(transform.location.z), 4),
            "yaw": round(float(transform.rotation.yaw), 4),
        }
    except Exception:
        return {"role": role, "step_index": step_index, "frame": frame}


def _alpamayo_motion_stub(ego: object) -> dict[str, Any]:
    pose = _ego_pose(ego)
    history = [[round(pose.x - (15 - index) * 0.2, 4), round(pose.y, 4), 0.0] for index in range(16)]
    identity_rot = [
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        for _ in range(16)
    ]
    return {
        "ego_history_xyz": history,
        "ego_history_rot": identity_rot,
    }


def _absolutize_package_frame_paths(package: dict[str, Any]) -> None:
    for window in package.get("camera_windows", []):
        if not isinstance(window, dict):
            continue
        for frame in window.get("frames", []):
            if isinstance(frame, dict) and frame.get("path"):
                frame["path"] = str(Path(str(frame["path"])).expanduser().resolve())


def _camera_paths(checkpoint: object) -> list[Path]:
    values: list[Path] = []
    for frame in getattr(checkpoint, "camera_frames", []):
        path = getattr(frame, "path", None)
        if path:
            values.append(Path(str(path)))
    return values


def _copy_center_frame(paths: list[Path], target: Path) -> None:
    if not paths:
        return
    source = paths[min(1, len(paths) - 1)]
    if source.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def _center_frame(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return paths[min(1, len(paths) - 1)]


def _copy_rgb_sequence(paths: list[Path | None], rgb_dir: Path, start_index: int) -> tuple[int, int]:
    copied = 0
    index = start_index
    for source in paths:
        if source is None or not source.exists():
            continue
        target = rgb_dir / f"frame_{index:06d}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied += 1
        index += 1
    return copied, index


def _drain_visual_frames(
    visual_queues: dict[int, "queue.Queue[object]"],
    output_dir: Path,
    *,
    min_frame_id: int,
    label: str,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for camera_index, images in sorted(visual_queues.items()):
        while True:
            try:
                image = images.get_nowait()
            except queue.Empty:
                break
            frame_id = int(getattr(image, "frame", getattr(image, "frame_number", -1)))
            if frame_id < min_frame_id:
                continue
            path = output_dir / f"{label}_camera_{camera_index}_frame_{frame_id}.png"
            if hasattr(image, "save_to_disk"):
                image.save_to_disk(str(path))
                paths.append(path)
    return paths


def _latency_summary(steps: list[dict[str, Any]]) -> dict[str, float]:
    values = [float(step["model_latency_ms"]) for step in steps if isinstance(step.get("model_latency_ms"), int | float)]
    if not values:
        return {"mean": 0.0, "max": 0.0}
    return {"mean": round(sum(values) / len(values), 3), "max": round(max(values), 3)}


def _planned_error(value: float | None) -> float:
    return round(float(value), 4) if value is not None else 0.0


def _write_tracks(run_dir: Path, tracks: list[dict[str, Any]]) -> Path:
    path = run_dir / "entity_tracks.json"
    path.write_text(json.dumps({"tracks": tracks}, indent=2), encoding="utf-8")
    return path


def _write_fake_tracks(run_dir: Path, steps: list[dict[str, Any]]) -> Path:
    tracks = []
    for step in steps:
        tracks.extend(step.get("actual_path", []))
    return _write_tracks(run_dir, tracks)


def _write_fake_step_images(output_dir: Path, step_index: int, phase: str, frame: int) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for camera_index in range(3):
        path = output_dir / f"camera_{camera_index}_frame_{frame}.png"
        _write_fake_png(path, step_index, phase, camera_index)
        paths.append(path)
    return paths


def _write_fake_png(path: Path, step_index: int, phase: str, camera_index: int) -> None:
    try:
        from PIL import Image, ImageDraw

        color = (34 + step_index * 20, 68 + camera_index * 30, 92 if phase == "pre" else 128)
        image = Image.new("RGB", (640, 360), color=color)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 250, 640, 360), fill=(42, 44, 46))
        draw.line((0, 295, 640, 285), fill=(235, 218, 120), width=4)
        draw.rectangle((300, 220, 340, 260), fill=(210, 88, 54))
        draw.text((18, 18), f"fake CARLA {phase} step {step_index} cam {camera_index}", fill=(255, 255, 255))
        image.save(path)
    except Exception:
        path.write_bytes(_TINY_PNG_BYTES)


_TINY_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?"
    b"\x00\x05\xfe\x02\xfeA\xe2!\xbc\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Closed-Loop Trace",
        "",
        f"- Run id: `{payload.get('run_id')}`",
        f"- Mode: `{payload.get('mode')}`",
        f"- Backend: `{payload.get('backend')}`",
        f"- Steps: `{len(list(payload.get('steps', [])))}`",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "ClosedLoopBackend",
    "ClosedLoopPolicy",
    "PausedClosedLoopConfig",
    "run_paused_closed_loop",
    "write_closed_loop_trace",
]
