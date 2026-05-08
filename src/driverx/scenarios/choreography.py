"""Scenario choreography plans for timed OOD actors and hazards."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.behaviors import generate_behavior_variants, simulate_behavior, validate_behavior_plan
from driverx.core.artifacts import prepare_run_dir
from driverx.scenarios.generated_runtime import build_generated_scenario_runtime_spec
from driverx.scenarios.studio_product_helpers import oodrive_command

CHOREOGRAPHY_SCHEMA_VERSION = "oodrive.scenario_choreography.v1"


@dataclass(frozen=True)
class ChoreographyCaseSpec:
    case_id: str
    title: str
    behavior_ids: tuple[str, ...]
    object_kinds: tuple[str, ...]
    expected_responses: tuple[str, ...]
    trigger_offset_s: float
    static_hazard: bool = True
    moving_hazard: bool = True


DEFAULT_CHOREOGRAPHY_CASES: tuple[ChoreographyCaseSpec, ...] = (
    ChoreographyCaseSpec(
        case_id="static-blocker-stop-creep",
        title="Static object blocks lane; ego should stop, then creep only when safe.",
        behavior_ids=("wrong_way_shoulder_creep",),
        object_kinds=("construction_debris", "lane_cone"),
        expected_responses=("stop", "creep", "yield"),
        trigger_offset_s=0.0,
    ),
    ChoreographyCaseSpec(
        case_id="moving-cut-in-slow-yield",
        title="Moving vehicle cuts in without signal; ego should slow and yield.",
        behavior_ids=("no_signal_cut_in", "motorcycle_filtering"),
        object_kinds=("roadside_vendor",),
        expected_responses=("slow", "yield", "hold_lane"),
        trigger_offset_s=1.0,
    ),
    ChoreographyCaseSpec(
        case_id="rolling-object-avoid",
        title="Accident object rolls into lane; ego should avoid inside drivable corridor.",
        behavior_ids=("unsignaled_u_turn",),
        object_kinds=("rolling_object", "lane_cone"),
        expected_responses=("slow", "swerve_within_lane", "recover"),
        trigger_offset_s=2.0,
    ),
    ChoreographyCaseSpec(
        case_id="compound-detour-replan",
        title="Compound obstruction with debris, cut-in, and U-turn pressure; ego should stop and replan.",
        behavior_ids=("no_signal_cut_in", "unsignaled_u_turn", "double_parked_door_swerve"),
        object_kinds=("construction_debris", "roadside_vendor", "rolling_object", "lane_cone"),
        expected_responses=("stop", "slow", "yield", "replan", "recover"),
        trigger_offset_s=3.0,
    ),
)


def build_choreography_plan(
    prompt: str,
    *,
    case_ids: tuple[str, ...] = (),
    behavior_ids: tuple[str, ...] = (),
    object_kinds: tuple[str, ...] = (),
    template_ids: tuple[str, ...] = ("construction_lane_closure",),
    seed: int = 41,
    severity: int = 4,
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-choreography",
) -> dict[str, Any]:
    """Build and write a choreographed bad-path scenario plan."""

    clean_prompt = prompt.strip()
    if not clean_prompt:
        raise ValueError("A choreography prompt is required.")
    run_dir = prepare_run_dir(output_root, run_id)
    selected_cases = _select_cases(case_ids)
    if behavior_ids or object_kinds:
        selected_cases = (
            ChoreographyCaseSpec(
                case_id="custom-choreography",
                title="Custom timed OOD choreography from CLI behavior/object selections.",
                behavior_ids=behavior_ids or ("no_signal_cut_in",),
                object_kinds=object_kinds or ("construction_debris",),
                expected_responses=("stop", "slow", "yield", "replan"),
                trigger_offset_s=0.0,
            ),
        )
    actors: list[dict[str, Any]] = []
    objects: list[dict[str, Any]] = []
    triggers: list[dict[str, Any]] = []
    expected_responses: list[str] = []
    behavior_trace_paths: list[str] = []
    all_behaviors: list[str] = []
    all_objects: list[str] = []
    entity_tracks: list[dict[str, Any]] = []
    spawned_ids: list[int] = []
    next_actor_id = 1000

    for case_index, case in enumerate(selected_cases):
        expected_responses.extend(case.expected_responses)
        all_behaviors.extend(case.behavior_ids)
        all_objects.extend(case.object_kinds)
        runtime_spec = build_generated_scenario_runtime_spec(
            prompt=f"{clean_prompt}; {case.title}",
            template_ids=template_ids,
            behavior_ids=case.behavior_ids,
            object_kinds=case.object_kinds,
            severity=severity,
            seed=seed + case_index,
            output_root=run_dir / "runtime_specs",
            run_id=case.case_id,
        )
        spec_path = str(runtime_spec["spec_path"])
        for obj_index, object_kind in enumerate(case.object_kinds):
            actor_id = next_actor_id
            next_actor_id += 1
            spawned_ids.append(actor_id)
            object_id = f"{case.case_id}-object-{obj_index:02d}"
            motion = "moving" if object_kind == "rolling_object" else "static"
            objects.append(
                {
                    "object_id": object_id,
                    "case_id": case.case_id,
                    "kind": object_kind,
                    "motion": motion,
                    "role": _object_role(object_kind),
                    "trigger_at_s": round(case.trigger_offset_s + obj_index * 0.5, 3),
                    "coordinate_frame": "road_local",
                    "spawn_transform": {"x": 12.0 + obj_index * 4.0, "y": 0.4 * obj_index, "z": 0.2, "yaw": 0.0},
                }
            )
            entity_tracks.append(
                _track(
                    actor_id=actor_id,
                    actor_ref=object_id,
                    case_id=case.case_id,
                    kind="object",
                    tick=0,
                    t_s=case.trigger_offset_s,
                    x_m=12.0 + obj_index * 4.0,
                    y_m=0.4 * obj_index,
                    speed_mps=0.0 if motion == "static" else 1.5,
                    heading_deg=0.0,
                )
            )
        for behavior_index, behavior_id in enumerate(case.behavior_ids):
            plan = generate_behavior_variants(
                behavior_id,
                count=1,
                random_seed=seed + case_index + behavior_index,
                severity=severity,
            )[0]
            trace = simulate_behavior(plan)
            validation = validate_behavior_plan(plan)
            trace_dir = run_dir / "behavior_traces" / case.case_id
            trace_dir.mkdir(parents=True, exist_ok=True)
            trace_path = trace_dir / f"{behavior_index:02d}_{behavior_id}.json"
            trace_path.write_text(json.dumps(trace.to_jsonable(), indent=2), encoding="utf-8")
            behavior_trace_paths.append(str(trace_path))
            actor_id = next_actor_id
            next_actor_id += 1
            spawned_ids.append(actor_id)
            actor_ref = f"{case.case_id}-actor-{behavior_index:02d}"
            actors.append(
                {
                    "actor_id": actor_ref,
                    "case_id": case.case_id,
                    "kind": plan.actor_kind,
                    "behavior_id": behavior_id,
                    "trigger_at_s": round(case.trigger_offset_s + behavior_index * 0.75, 3),
                    "trace_path": str(trace_path),
                    "sample_count": len(trace.samples),
                    "validation": validation.to_jsonable(),
                }
            )
            triggers.append(
                {
                    "at_s": round(case.trigger_offset_s + behavior_index * 0.75, 3),
                    "event": f"start_behavior:{behavior_id}",
                    "target": actor_ref,
                    "case_id": case.case_id,
                }
            )
            for sample_index, sample in enumerate(trace.samples):
                entity_tracks.append(
                    _track(
                        actor_id=actor_id,
                        actor_ref=actor_ref,
                        case_id=case.case_id,
                        kind=plan.actor_kind,
                        tick=sample_index,
                        t_s=round(case.trigger_offset_s + sample.t_s, 3),
                        x_m=sample.x_m,
                        y_m=sample.y_m,
                        speed_mps=sample.speed_mps,
                        heading_deg=sample.heading_deg,
                    )
            )
        triggers.append(
            {
                "at_s": round(case.trigger_offset_s, 3),
                "event": "hazard_visible",
                "target": case.case_id,
                "case_id": case.case_id,
            }
        )
        if "roadside_vendor" in case.object_kinds:
            actor_id = next_actor_id
            next_actor_id += 1
            spawned_ids.append(actor_id)
            actor_ref = f"{case.case_id}-pedestrian-occlusion-proxy"
            trigger_at = round(case.trigger_offset_s + 1.25, 3)
            actors.append(
                {
                    "actor_id": actor_ref,
                    "case_id": case.case_id,
                    "kind": "pedestrian",
                    "behavior_id": "pedestrian_occlusion_proxy",
                    "trigger_at_s": trigger_at,
                    "trace_path": None,
                    "sample_count": 9,
                    "validation": {"passes": True, "warnings": ["pedestrian proxy uses direct choreography samples"]},
                }
            )
            triggers.append(
                {
                    "at_s": trigger_at,
                    "event": "start_behavior:pedestrian_occlusion_proxy",
                    "target": actor_ref,
                    "case_id": case.case_id,
                }
            )
            for sample_index in range(9):
                t_s = trigger_at + sample_index * 0.5
                entity_tracks.append(
                    _track(
                        actor_id=actor_id,
                        actor_ref=actor_ref,
                        case_id=case.case_id,
                        kind="pedestrian",
                        tick=sample_index,
                        t_s=t_s,
                        x_m=8.0 + sample_index * 0.35,
                        y_m=-3.2 + sample_index * 0.8,
                        speed_mps=1.4,
                        heading_deg=88.0,
                    )
                )
            all_behaviors.append("pedestrian_occlusion_proxy")

    tracks_path = run_dir / "entity_tracks.json"
    tracks_path.write_text(json.dumps(entity_tracks, indent=2), encoding="utf-8")
    manifest_path = run_dir / "choreography_manifest.json"
    report_path = run_dir / "choreography_report.md"
    manifest: dict[str, Any] = {
        "schema_version": CHOREOGRAPHY_SCHEMA_VERSION,
        "kind": "oodrive_scenario_choreography",
        "status": "passed",
        "run_id": run_dir.name,
        "prompt": clean_prompt,
        "seed": seed,
        "severity": severity,
        "case_count": len(selected_cases),
        "cases": [_case_to_jsonable(case) for case in selected_cases],
        "actors": actors,
        "objects": objects,
        "triggers": sorted(triggers, key=lambda item: float(item.get("at_s", 0.0))),
        "expected_responses": sorted(set(expected_responses)),
        "behavior_ids": sorted(set(all_behaviors)),
        "object_kinds": sorted(set(all_objects)),
        "behavior_trace_paths": behavior_trace_paths,
        "runtime_spec_root": str(run_dir / "runtime_specs"),
        "proof": {
            "backend": "fake-carla",
            "status": "passed",
            "entity_track_count": len(entity_tracks),
            "tracks_path": str(tracks_path),
            "spawned_actor_ids": spawned_ids,
            "destroyed_actor_ids": list(spawned_ids),
            "live_carla_execution": False,
        },
        "claim_boundaries": [
            "scenario_choreography=true",
            "live_carla_execution=false",
            "closed_loop_vla_control=false",
            "real_time_vla_control=false",
            "custom_unreal_map_import=false",
        ],
        "next_commands": [
            oodrive_command(f"score-choreography --choreography-manifest {manifest_path} --metric-only"),
            oodrive_command(f"choreograph-video --choreography-manifest {manifest_path} --backend carla-live"),
        ],
        "json_path": str(manifest_path),
        "report_path": str(report_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report_path.write_text(_manifest_markdown(manifest), encoding="utf-8")
    return manifest


def _select_cases(case_ids: tuple[str, ...]) -> tuple[ChoreographyCaseSpec, ...]:
    if not case_ids:
        return DEFAULT_CHOREOGRAPHY_CASES
    by_id = {case.case_id: case for case in DEFAULT_CHOREOGRAPHY_CASES}
    missing = [case_id for case_id in case_ids if case_id not in by_id]
    if missing:
        raise ValueError(f"Unknown choreography case id(s): {', '.join(missing)}")
    return tuple(by_id[case_id] for case_id in case_ids)


def _case_to_jsonable(case: ChoreographyCaseSpec) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "title": case.title,
        "behavior_ids": list(case.behavior_ids),
        "object_kinds": list(case.object_kinds),
        "expected_responses": list(case.expected_responses),
        "trigger_offset_s": case.trigger_offset_s,
        "static_hazard": case.static_hazard,
        "moving_hazard": case.moving_hazard,
    }


def _object_role(object_kind: str) -> str:
    return {
        "construction_debris": "static lane blocker",
        "lane_cone": "lane narrowing marker",
        "roadside_vendor": "occlusion proxy",
        "rolling_object": "moving accident object",
    }.get(object_kind, "OOD object")


def _track(
    *,
    actor_id: int,
    actor_ref: str,
    case_id: str,
    kind: str,
    tick: int,
    t_s: float,
    x_m: float,
    y_m: float,
    speed_mps: float,
    heading_deg: float,
) -> dict[str, Any]:
    return {
        "actor_id": actor_id,
        "actor_ref": actor_ref,
        "case_id": case_id,
        "kind": kind,
        "tick": tick,
        "t_s": round(t_s, 3),
        "transform": {"x": round(x_m, 4), "y": round(y_m, 4), "z": 0.2, "yaw": round(heading_deg, 4)},
        "velocity": {"x": round(speed_mps, 4), "y": 0.0, "z": 0.0},
    }


def _manifest_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# OODrive Scenario Choreography",
        "",
        f"- run_id: `{manifest.get('run_id')}`",
        f"- status: `{manifest.get('status')}`",
        f"- cases: `{manifest.get('case_count')}`",
        f"- actors: `{len(list(manifest.get('actors', [])))}`",
        f"- objects: `{len(list(manifest.get('objects', [])))}`",
        f"- triggers: `{len(list(manifest.get('triggers', [])))}`",
        f"- tracks: `{dict(manifest.get('proof', {})).get('entity_track_count')}`",
        "",
        "## Cases",
    ]
    for case in list(manifest.get("cases", [])):
        if isinstance(case, dict):
            lines.append(f"- `{case.get('case_id')}`: {case.get('title')}")
    lines.extend(["", "## Expected Responses"])
    lines.extend([f"- `{item}`" for item in list(manifest.get("expected_responses", []))])
    lines.extend(["", "## Claim Boundaries"])
    lines.extend([f"- `{item}`" for item in list(manifest.get("claim_boundaries", []))])
    return "\n".join(lines) + "\n"


__all__ = [
    "CHOREOGRAPHY_SCHEMA_VERSION",
    "DEFAULT_CHOREOGRAPHY_CASES",
    "build_choreography_plan",
]
