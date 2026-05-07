"""OODrive product runtime commands for placement and reasoning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
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


__all__ = ["run_studio_generate", "run_studio_place", "run_studio_reason"]
