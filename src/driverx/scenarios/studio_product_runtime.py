"""OODrive product runtime commands for placement and reasoning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.perception.risk_timeline import (
    RiskTimelineConfig,
    build_risk_timeline,
    load_entity_tracks,
    write_risk_timeline,
)
from driverx.scenarios.run_manifest import ScenarioRunManifest, write_run_manifest
from driverx.scenarios.studio_db import (
    OODRIVE_PRODUCT_NAME,
    append_command,
    append_run,
    load_studio_db,
    replace_db,
    write_studio_db,
)
from driverx.scenarios.studio_product import (
    StudioCommandResult,
    run_studio_ai_generate,
    run_studio_evaluate,
    run_studio_replay,
)
from driverx.scenarios.studio_product_helpers import (
    artifact_paths,
    load_or_latest_run,
    oodrive_command,
    select_queue_record,
    update_queue_record,
)
from driverx.scenarios.studio_runtime import (
    asset_manifests_from_candidate,
    behavior_trace_from_candidate,
    build_studio_placement_plan,
    candidate_for_queue_record,
    load_studio_placement_plan,
    recipe_from_candidate,
)


def run_studio_generate(
    *,
    prompt: str,
    db_path: Path | None = None,
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-generated",
    count: int = 4,
    provider: str = "codex-template",
    seed: int = 7,
    force: bool = False,
    severity: int = 4,
    accept: str = "top:3",
    config_path: Path = Path("configs/carla_ood_demo.local.sample.yaml"),
) -> StudioCommandResult:
    """Generate a scenario and immediately write a CARLA placement plan."""

    generate_result = run_studio_ai_generate(
        prompts=[prompt],
        db_path=db_path,
        output_root=output_root,
        run_id=run_id,
        count=count,
        provider=provider,
        seed=seed,
        force=force,
        compile_candidates=True,
        queue_candidates=True,
        severity=severity,
        accept=accept,
    )
    resolved_db_path = Path(generate_result.artifacts["db_path"])
    placement = build_studio_placement_plan(
        resolved_db_path,
        config_path=config_path,
        output_root=resolved_db_path.parent / "placements",
        run_id=f"{run_id}-placement",
    )
    placement_artifacts = {
        "placement_plan_path": str(placement["json_path"]),
        "placement_report_path": str(placement["report_path"]),
    }
    db = load_studio_db(resolved_db_path)
    db = replace_db(
        db,
        artifacts={**db.artifacts, **placement_artifacts},
        claim_boundaries=sorted(
            set(
                [
                    *db.claim_boundaries,
                    "oodrive_generate_to_carla_placement_plan=true",
                    "objects_placed_in_carla=false_until_oodrive_place_live_passes",
                ]
            )
        ),
    )
    db = append_command(
        db,
        command="oodrive generate",
        status="passed",
        artifacts={"db_path": str(resolved_db_path), **placement_artifacts},
        summary={
            "prompt": prompt,
            "candidate_count": generate_result.summary.get("candidate_count", 0),
            "queue_count": generate_result.summary.get("queue_count", 0),
            "placement_id": placement.get("placement_id"),
            "object_count": len(list(placement.get("object_spawn_specs", []))),
        },
    )
    db_artifacts = artifact_paths(write_studio_db(resolved_db_path, db))
    next_commands = [
        oodrive_command(
            f"place --db {resolved_db_path} --placement {placement['json_path']} --config {config_path} --live"
        ),
        oodrive_command(
            f"place --db {resolved_db_path} --placement {placement['json_path']} --config {config_path}"
        ),
        oodrive_command(
            f"reason --db {resolved_db_path} --run <run_manifest_path> --prediction-json <alpamayo_prediction.json>"
        ),
    ]
    return StudioCommandResult(
        command="oodrive generate",
        run_id=db.run_id,
        status="passed",
        artifacts={**generate_result.artifacts, **db_artifacts, **placement_artifacts},
        next_commands=next_commands,
        summary={
            "prompt": prompt,
            "generated_count": generate_result.summary.get("generated_count", 0),
            "candidate_count": generate_result.summary.get("candidate_count", 0),
            "queue_count": generate_result.summary.get("queue_count", 0),
            "placement": {
                "placement_id": placement.get("placement_id"),
                "scenario_id": placement.get("scenario_id"),
                "candidate_id": placement.get("candidate_id"),
                "object_count": len(list(placement.get("object_spawn_specs", []))),
                "behavior_sample_count": placement.get("behavior_sample_count"),
            },
        },
        claim_boundaries=sorted(set([*db.claim_boundaries, *placement.get("claim_boundaries", [])])),
    )


def run_studio_place(
    db_path: Path,
    *,
    scenario_id: str | None = None,
    placement_path: Path | None = None,
    config_path: Path = Path("configs/carla_ood_demo.local.sample.yaml"),
    output_root: Path | None = None,
    run_id: str | None = None,
    live: bool = False,
) -> StudioCommandResult:
    """Place a generated OOD scenario in CARLA, or write a dry-run manifest."""

    db = load_studio_db(db_path)
    placement = load_studio_placement_plan(placement_path) if placement_path is not None else None
    selected_scenario = scenario_id or (str(placement.get("scenario_id")) if placement else None)
    if placement is None:
        placement = build_studio_placement_plan(
            db_path,
            scenario_id=selected_scenario,
            config_path=config_path,
            output_root=db_path.parent / "placements",
            run_id=run_id or "placement",
        )
        placement_path = Path(str(placement["json_path"]))
    record = select_queue_record(db, selected_scenario)
    candidate = candidate_for_queue_record(db, record)
    recipe = recipe_from_candidate(candidate)
    behavior = behavior_trace_from_candidate(candidate)
    asset_manifests = asset_manifests_from_candidate(candidate)
    scenario_id = str(record.get("scenario_id") or recipe.recipe_id)
    candidate_id = str(candidate.get("candidate_id") or recipe.recipe_id)
    run_id = run_id or f"{scenario_id}-carla-place"
    run_dir = prepare_run_dir(output_root or (db_path.parent / "runs"), run_id)
    artifacts: dict[str, str | None] = {
        "placement_plan_path": str(placement_path),
        "placement_report_path": str(placement.get("report_path", "")),
        "carla_config_path": str(config_path),
    }
    blockers: list[str] = []
    timings = {"load_ms": 1.0, "place_ms": 0.0, "write_ms": 1.0}
    status = "planned"
    runtime = "carla-placement-dry-run"
    claim_boundaries = [
        f"product_name={OODRIVE_PRODUCT_NAME}",
        "carla_placement_plan=true",
        "objects_placed_in_carla=false_dry_run",
        "scripted_carla_ood_demo=false_until_live_place_passes",
        "closed_loop_vla_control=false",
        "real_time_vla_control=false",
    ]
    if live:
        from driverx.simulators.carla_ood_demo import (
            load_carla_ood_demo_config,
            run_carla_ood_demo,
            write_carla_ood_demo,
        )

        runtime = "carla-scripted-ood-demo"
        config = load_carla_ood_demo_config(config_path)
        result = run_carla_ood_demo(
            config,
            run_dir,
            recipe=recipe,
            behavior=behavior,
            asset_manifests=asset_manifests,
        )
        demo_payload = write_carla_ood_demo(run_dir, result)
        artifacts = {
            **artifacts,
            "carla_ood_demo_json": str(demo_payload["json_path"]),
            "carla_ood_demo_report": str(demo_payload["report_path"]),
            "rgb_folder": demo_payload.get("rgb_folder"),
            "tracks_path": demo_payload.get("tracks_path"),
            "carla_plan_path": demo_payload.get("plan_path"),
            "road_alignment_path": demo_payload.get("road_alignment_path"),
        }
        blockers.extend(list(result.blockers))
        status = result.status
        timings["place_ms"] = round(result.duration_s * 1000.0, 3)
        claim_boundaries = [
            f"product_name={OODRIVE_PRODUCT_NAME}",
            "carla_placement_plan=true",
            "objects_placed_in_carla=true" if result.connected else "objects_placed_in_carla=false",
            "scripted_carla_ood_demo=true",
            "closed_loop_vla_control=false",
            "real_time_vla_control=false",
            *result.to_jsonable().get("claim_boundaries", []),
        ]
    trace_path = run_dir / "placement_trace.json"
    trace_path.write_text(
        json.dumps(
            {
                "scenario_id": scenario_id,
                "candidate_id": candidate_id,
                "live": live,
                "object_spawn_specs": placement.get("object_spawn_specs", []),
                "behavior_preview": placement.get("behavior_preview", []),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    artifacts["placement_trace_path"] = str(trace_path)
    manifest = ScenarioRunManifest(
        run_id=run_dir.name,
        scenario_id=scenario_id,
        candidate_id=candidate_id,
        policy="carla-scripted-ood-demo",
        runtime=runtime,
        status=status,
        artifacts=artifacts,
        timings_ms=timings,
        actions=list(placement.get("behavior_preview", [])),
        claim_boundaries=sorted(set(claim_boundaries)),
        blockers=blockers,
    )
    manifest_payload = write_run_manifest(run_dir, manifest)
    manifest_artifacts = artifact_paths(manifest_payload)
    db = update_queue_record(db, candidate_id, status)
    db = append_run(db, {**manifest.to_jsonable(), **manifest_artifacts})
    db = append_command(
        db,
        command="oodrive place",
        status="passed" if status in {"planned", "passed", "partial"} else status,
        artifacts=manifest_artifacts,
        summary={
            "scenario_id": scenario_id,
            "live": live,
            "status": status,
            "object_count": len(list(placement.get("object_spawn_specs", []))),
        },
    )
    db_artifacts = artifact_paths(write_studio_db(db_path, db))
    return StudioCommandResult(
        command="oodrive place",
        run_id=db.run_id,
        status="passed" if status in {"planned", "passed", "partial"} else status,
        artifacts={**db_artifacts, **manifest_artifacts},
        next_commands=[
            oodrive_command(
                f"reason --db {db_path} --run {manifest_artifacts['json_path']} --prediction-json <alpamayo_prediction.json>"
            )
        ],
        summary={
            **manifest.to_jsonable(),
            "objects_placed": bool(live and status in {"passed", "partial"}),
            "live": live,
        },
        claim_boundaries=manifest.claim_boundaries,
        blockers=blockers,
    )


def run_studio_reason(
    db_path: Path,
    *,
    run_manifest_path: Path | None = None,
    prediction_json: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
    memory: str = "auto",
    package_path: Path | None = None,
) -> StudioCommandResult:
    """Attach Alpamayo reasoning evidence and build a replay bundle."""

    db = load_studio_db(db_path)
    run_payload = load_or_latest_run(db, run_manifest_path)
    scenario_id = str(run_payload.get("scenario_id", "scenario"))
    run_id = run_id or f"{scenario_id}-reason"
    reason_root = output_root or (db_path.parent / "reasoning")
    package_artifacts: dict[str, str] = {}
    policy_artifacts: dict[str, str] = {}
    blockers: list[str] = []
    resolved_package_path = package_path or _package_path_from_run(run_payload)
    if resolved_package_path is None:
        package_payload = _try_build_package_from_run(
            run_payload,
            reason_root,
            run_id=run_id,
            blockers=blockers,
        )
        if package_payload:
            package_artifacts = artifact_paths(package_payload)
            resolved_package_path = Path(str(package_payload["json_path"]))
    elif resolved_package_path.exists():
        package_artifacts["alpamayo_package_path"] = str(resolved_package_path)
    else:
        blockers.append(f"Alpamayo package path does not exist: {resolved_package_path}")
        resolved_package_path = None

    evaluation_result = run_studio_evaluate(
        db_path,
        run_manifest_path=run_manifest_path,
        policy="alpamayo-trajectory",
        memory=memory,
        prediction_json=prediction_json,
        output_root=reason_root / "evaluations",
        run_id=f"{run_id}-evaluation",
    )
    if resolved_package_path is not None and prediction_json is not None:
        from driverx.policies.alpamayo_live import run_alpamayo_live_package

        try:
            policy_payload = run_alpamayo_live_package(
                package_path=resolved_package_path,
                prediction_json=prediction_json,
                output_root=reason_root / "policy-decisions",
                run_id=f"{run_id}-policy",
            )
            policy_artifacts = {
                "alpamayo_policy_decision_path": str(policy_payload["json_path"]),
                "alpamayo_policy_report_path": str(policy_payload["report_path"]),
            }
        except (FileNotFoundError, OSError, ValueError) as exc:
            blockers.append(f"Could not build Alpamayo policy decision from cached prediction: {exc}")

    replay_result = run_studio_replay(
        db_path,
        run_manifest_path=run_manifest_path,
        evaluation_path=Path(evaluation_result.artifacts["json_path"]),
        output_root=reason_root / "bundles",
        run_id=f"{run_id}-bundle",
    )
    db = load_studio_db(db_path)
    artifacts = {
        "db_path": str(db_path),
        "run_manifest_path": str(run_manifest_path) if run_manifest_path else str(run_payload.get("json_path", "")),
        "evaluation_path": str(evaluation_result.artifacts.get("json_path", "")),
        "bundle_path": str(replay_result.artifacts.get("json_path", "")),
        **package_artifacts,
        **policy_artifacts,
    }
    status = (
        "blocked"
        if evaluation_result.status == "blocked" and prediction_json is None
        else "partial"
        if blockers
        else "passed"
    )
    db = replace_db(
        db,
        artifacts={**db.artifacts, **artifacts},
        claim_boundaries=sorted(
            set(
                [
                    *db.claim_boundaries,
                    "oodrive_reasoning_trace=true",
                    "sampled_open_loop_reasoning=true" if prediction_json else "sampled_open_loop_reasoning=false",
                    "closed_loop_vla_control=false",
                    "real_time_vla_control=false",
                ]
            )
        ),
    )
    db = append_command(
        db,
        command="oodrive reason",
        status=status,
        artifacts=artifacts,
        summary={
            "scenario_id": scenario_id,
            "prediction_attached": prediction_json is not None,
            "package_ready": resolved_package_path is not None,
            "policy_decision_ready": bool(policy_artifacts),
        },
    )
    db_artifacts = artifact_paths(write_studio_db(db_path, db))
    claim_boundaries = sorted(
        set(
            [
                *evaluation_result.claim_boundaries,
                *replay_result.claim_boundaries,
                *db.claim_boundaries,
                "closed_loop_vla_control=false",
                "real_time_vla_control=false",
            ]
        )
    )
    return StudioCommandResult(
        command="oodrive reason",
        run_id=db.run_id,
        status=status,
        artifacts={**db_artifacts, **artifacts},
        next_commands=[oodrive_command(f"export --db {db_path}")],
        summary={
            "scenario_id": scenario_id,
            "evaluation": evaluation_result.summary,
            "bundle_id": replay_result.summary.get("bundle_id"),
            "alpamayo_package_path": str(resolved_package_path) if resolved_package_path else None,
            "alpamayo_policy_decision_path": policy_artifacts.get("alpamayo_policy_decision_path"),
            "sampled_open_loop_reasoning": prediction_json is not None,
            "blockers": blockers + evaluation_result.blockers,
        },
        claim_boundaries=claim_boundaries,
        blockers=blockers + evaluation_result.blockers,
    )


def run_studio_score_demo(
    db_path: Path | None = None,
    *,
    run_manifest_path: Path | None = None,
    evaluation_path: Path | None = None,
    video_path: Path | None = None,
    overlay_report_path: Path | None = None,
    score_input_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
    metric_only: bool = False,
) -> StudioCommandResult:
    """Score whether a hero demo video is submission-visible enough."""

    from driverx.evaluation.hero_demo_score import (
        load_demo_score_inputs,
        score_hero_demo,
        write_hero_demo_score,
    )

    if db_path is None and score_input_path is None:
        raise ValueError("Pass either --db or --score-input.")
    db = load_studio_db(db_path) if db_path is not None and db_path.exists() else None
    run_payload = load_or_latest_run(db, run_manifest_path) if db is not None and score_input_path is None else {}
    resolved_run_manifest_path = run_manifest_path or _json_path_from_payload(run_payload)
    score_id = run_id or f"{run_payload.get('scenario_id', 'hero-demo')}-score"
    run_dir = prepare_run_dir(output_root or ((db_path.parent / "demo-scores") if db_path else Path("artifacts/runs")), score_id)
    inputs = load_demo_score_inputs(
        db_path=db_path,
        run_manifest_path=resolved_run_manifest_path,
        evaluation_path=evaluation_path,
        video_path=video_path,
        overlay_report_path=overlay_report_path,
        score_input_path=score_input_path,
    )
    report = score_hero_demo(inputs)
    artifacts = artifact_paths(write_hero_demo_score(run_dir, report))
    if metric_only:
        print(f"METRIC hero_demo_score={report.hero_demo_score:.4f}")
    if db is not None and db_path is not None:
        db = replace_db(
            db,
            artifacts={**db.artifacts, **artifacts},
            claim_boundaries=sorted(
                set(
                    [
                        *db.claim_boundaries,
                        "hero_demo_score_required_for_promotion=true",
                        "raw_video_presence_is_not_submission_quality=true",
                    ]
                )
            ),
        )
        db = append_command(
            db,
            command="oodrive score-demo",
            status=report.status,
            artifacts=artifacts,
            summary={
                "candidate_id": inputs.candidate_id,
                "hero_demo_score": report.hero_demo_score,
                "threshold": report.threshold,
                "blocker_count": len(report.blockers),
            },
        )
        artifacts = {**artifact_paths(write_studio_db(db_path, db)), **artifacts}
        claim_boundaries = db.claim_boundaries
        command_run_id = db.run_id
    else:
        claim_boundaries = report.claim_boundaries
        command_run_id = score_id
    next_commands = []
    if report.status != "passed" and db_path is not None:
        next_commands.append(
            oodrive_command(
                f"demo-video --db {db_path} --run <run_manifest_path> --evaluation <policy_evaluation.json> --input-video <video.mp4>"
            )
        )
    return StudioCommandResult(
        command="oodrive score-demo",
        run_id=command_run_id,
        status=report.status,
        artifacts=artifacts,
        next_commands=next_commands,
        summary={
            "candidate_id": inputs.candidate_id,
            "hero_demo_score": report.hero_demo_score,
            "threshold": report.threshold,
            "metrics": report.metrics,
            "components": report.components,
        },
        claim_boundaries=claim_boundaries,
        blockers=report.blockers,
    )


def run_studio_demo_video(
    db_path: Path,
    *,
    input_video: Path,
    run_manifest_path: Path | None = None,
    evaluation_path: Path | None = None,
    output_video: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
    fps: int = 15,
    speed_factor: float = 4.0,
    show_frame_time: bool = True,
    show_reasoning: bool = True,
    show_rag: bool = True,
    layout: str = "dense",
) -> StudioCommandResult:
    """Build a time-warped reasoning/RAG overlay video for the hero demo."""

    from driverx.simulators.reasoning_timeline_overlay import (
        ReasoningOverlayConfig,
        build_reasoning_overlay_events,
        render_reasoning_timeline_overlay,
    )
    from driverx.simulators.video_timewarp import timewarp_video, write_video_timewarp

    db = load_studio_db(db_path)
    run_payload = load_or_latest_run(db, run_manifest_path)
    evaluation_payload = _load_json(evaluation_path) if evaluation_path is not None and evaluation_path.exists() else {}
    scenario_id = str(run_payload.get("scenario_id", "hero-demo"))
    demo_id = run_id or f"{scenario_id}-hero-demo"
    run_dir = prepare_run_dir(output_root or (db_path.parent / "demo-videos"), demo_id)
    artifacts = _mapping(run_payload.get("artifacts"))
    tracks_path = _optional_path(artifacts.get("tracks_path"))
    risk_payload = _risk_payload_for_demo(run_dir, tracks_path, run_payload)
    working_input = input_video
    timewarp_payload: dict[str, Any] = {}
    if speed_factor > 0 and speed_factor != 1.0:
        timewarped_video = run_dir / "timewarped_source.mp4"
        timewarp_result = timewarp_video(input_video, timewarped_video, speed_factor=speed_factor, fps=fps)
        timewarp_payload = write_video_timewarp(run_dir / "timewarp", timewarp_result)
        if timewarp_result.status == "passed":
            working_input = timewarped_video
    output_video = output_video or (run_dir / "oodrive_hero_demo.mp4")
    events = build_reasoning_overlay_events(
        bundle={"scenario_id": scenario_id},
        risk_timeline=risk_payload,
        alpamayo_batch={"records": [_alpamayo_record_from_evaluation(scenario_id, evaluation_payload)]},
        speed_factor=speed_factor,
        limit=8,
    )
    result = render_reasoning_timeline_overlay(
        ReasoningOverlayConfig(
            input_video=working_input,
            output_video=output_video,
            output_frame_dir=run_dir / "overlay",
            events=events,
            fps=fps,
            speed_factor=speed_factor,
            title="OODrive Scenario Generator",
            subtitle="generated CARLA OOD case + sampled VLA reasoning + RAG memory",
            show_frame_time=show_frame_time,
            show_reasoning=show_reasoning,
            show_rag=show_rag,
            layout=layout,
        )
    )
    payload = {
        **result.to_jsonable(),
        "scenario_id": scenario_id,
        "layout": layout,
        "events": [event.to_jsonable() for event in events],
        "risk_timeline": risk_payload,
        "timewarp": timewarp_payload,
        "score_next_command": oodrive_command(
            f"score-demo --db {db_path} --run {run_manifest_path or run_payload.get('json_path', '')} --evaluation {evaluation_path or ''} --video {output_video} --overlay-report {run_dir / 'hero_demo_video.json'}"
        ),
    }
    json_path = run_dir / "hero_demo_video.json"
    report_path = run_dir / "hero_demo_video.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_hero_demo_video_markdown(payload), encoding="utf-8")
    video_artifacts = {
        "hero_demo_video_path": str(output_video),
        "hero_demo_video_json_path": str(json_path),
        "hero_demo_video_report_path": str(report_path),
    }
    db = replace_db(
        db,
        artifacts={**db.artifacts, **video_artifacts},
        claim_boundaries=sorted(
            set(
                [
                    *db.claim_boundaries,
                    "time_warped_offline_demo=true",
                    "sampled_open_loop_reasoning=true",
                    "real_time_vla_control=false",
                    "hero_demo_frame_time_overlay=true" if show_frame_time else "hero_demo_frame_time_overlay=false",
                    "hero_demo_rag_overlay=true" if show_rag else "hero_demo_rag_overlay=false",
                    "hero_demo_reasoning_overlay=true" if show_reasoning else "hero_demo_reasoning_overlay=false",
                    f"hero_demo_overlay_layout={layout}",
                ]
            )
        ),
    )
    db = append_command(
        db,
        command="oodrive demo-video",
        status=result.status,
        artifacts=video_artifacts,
        summary={
            "scenario_id": scenario_id,
            "output_video": str(output_video),
            "event_count": len(events),
            "frame_count": result.frame_count,
            "frame_time_overlay_coverage": result.frame_time_overlay_coverage,
        },
    )
    db_artifacts = artifact_paths(write_studio_db(db_path, db))
    return StudioCommandResult(
        command="oodrive demo-video",
        run_id=db.run_id,
        status=result.status,
        artifacts={**db_artifacts, **video_artifacts},
        next_commands=[payload["score_next_command"]],
        summary=payload,
        claim_boundaries=db.claim_boundaries,
        blockers=result.blockers,
    )


def _package_path_from_run(run_payload: dict[str, Any]) -> Path | None:
    artifacts = run_payload.get("artifacts")
    if not isinstance(artifacts, dict):
        return None
    for key in ("alpamayo_package_path", "alpamayo_package", "package_path"):
        value = artifacts.get(key)
        if isinstance(value, str) and value:
            return Path(value)
    return None


def _try_build_package_from_run(
    run_payload: dict[str, Any],
    output_root: Path,
    *,
    run_id: str,
    blockers: list[str],
) -> dict[str, Any]:
    artifacts = run_payload.get("artifacts")
    if not isinstance(artifacts, dict):
        blockers.append("Run manifest has no artifacts mapping for Alpamayo package construction.")
        return {}
    demo_path = artifacts.get("carla_ood_demo_json")
    if not isinstance(demo_path, str) or not demo_path:
        blockers.append("Run manifest has no carla_ood_demo_json artifact; package construction skipped.")
        return {}
    try:
        demo_payload = json.loads(Path(demo_path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        blockers.append(f"Could not load CARLA OOD demo artifact for Alpamayo package: {exc}")
        return {}
    rgb_folder = demo_payload.get("rgb_folder")
    tracks_path = demo_payload.get("tracks_path")
    if not isinstance(rgb_folder, str) or not isinstance(tracks_path, str):
        blockers.append("CARLA OOD demo artifact is missing rgb_folder or tracks_path.")
        return {}
    from driverx.policies.alpamayo_ood_package import (
        AlpamayoOodPackageInputs,
        build_alpamayo_package_from_ood_demo,
        write_alpamayo_ood_package,
    )

    package_dir = prepare_run_dir(output_root / "packages", f"{run_id}-package")
    try:
        package = build_alpamayo_package_from_ood_demo(
            AlpamayoOodPackageInputs(
                rgb_folder=Path(rgb_folder),
                tracks_path=Path(tracks_path),
                scenario_report_path=Path(demo_path),
                scenario_id=str(run_payload.get("scenario_id", "")),
                behavior_id=str(demo_payload.get("behavior_id", "")),
            )
        )
        return write_alpamayo_ood_package(
            package_dir,
            package,
            source={
                "run_manifest_id": run_payload.get("run_id"),
                "carla_ood_demo_json": demo_path,
                "product_command": "oodrive reason",
            },
        )
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
        blockers.append(f"Could not build Alpamayo package from CARLA run: {exc}")
        return {}


def _json_path_from_payload(payload: dict[str, Any]) -> Path | None:
    value = payload.get("json_path")
    return Path(value) if isinstance(value, str) and value else None


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _optional_path(value: object) -> Path | None:
    return Path(value) if isinstance(value, str) and value else None


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _risk_payload_for_demo(run_dir: Path, tracks_path: Path | None, run_payload: dict[str, Any]) -> dict[str, Any]:
    if tracks_path is not None and tracks_path.exists():
        try:
            timeline = build_risk_timeline(
                load_entity_tracks(tracks_path),
                RiskTimelineConfig(scenario_id=str(run_payload.get("scenario_id", ""))),
            )
            return write_risk_timeline(run_dir / "risk", timeline)
        except (OSError, ValueError):
            pass
    return {
        "scenario_id": run_payload.get("scenario_id"),
        "event_count": 0,
        "events": [],
        "tick_summaries": [],
        "claim_boundaries": ["risk_timeline_missing=true"],
    }


def _alpamayo_record_from_evaluation(scenario_id: str, evaluation_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "memory_ids": list(evaluation_payload.get("memory_ids", []))
        if isinstance(evaluation_payload.get("memory_ids"), list)
        else [],
        "cot_snippet": evaluation_payload.get("cot_summary"),
        "reasoning_changed": bool(evaluation_payload.get("cot_summary")),
    }


def _hero_demo_video_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OODrive Hero Demo Video",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Scenario: `{payload.get('scenario_id')}`",
        f"- Output video: `{payload.get('output_video')}`",
        f"- Sample frame: `{payload.get('sample_frame_path')}`",
        f"- Events: `{payload.get('event_count')}`",
        f"- Frame/time coverage: `{payload.get('frame_time_overlay_coverage')}`",
        "",
        "## Next",
        "",
        f"`{payload.get('score_next_command')}`",
        "",
        "## Claim Boundaries",
        "",
    ]
    lines.extend(f"- `{item}`" for item in list(payload.get("claim_boundaries", [])))
    return "\n".join(lines) + "\n"


__all__ = [
    "run_studio_demo_video",
    "run_studio_generate",
    "run_studio_place",
    "run_studio_reason",
    "run_studio_score_demo",
]
