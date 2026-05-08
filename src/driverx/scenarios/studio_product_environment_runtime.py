"""OODrive environment demo runtime commands."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.behaviors import generate_behavior_variants
from driverx.environments import (
    EnvironmentRecipe,
    EnvironmentSuiteConfig,
    attach_environment_to_recipe,
    environment_to_asset_requests,
    run_environment_forge,
)
from driverx.scenarios import ScenarioRecipe
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_db import (
    OODRIVE_PRODUCT_NAME,
    append_command,
    new_studio_db,
    replace_db,
    write_studio_db,
)
from driverx.scenarios.studio_product_helpers import artifact_paths, oodrive_command
from driverx.scenarios.studio_product_runtime import run_studio_place
from driverx.scenarios.studio_runtime import build_studio_placement_plan


def run_studio_generate_envs(
    *,
    template_ids: tuple[str, ...] = (),
    severity: int = 4,
    count: int = 6,
    random_seed: int = 31,
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-environments",
) -> StudioCommandResult:
    """Generate deterministic CARLA environment variants from OODrive."""

    summary = run_environment_forge(
        EnvironmentSuiteConfig(
            template_ids=template_ids,
            severity=severity,
            count=count,
            random_seed=random_seed,
            output_root=output_root,
            run_id=run_id,
        )
    )
    artifacts = {
        "environment_recipes_path": str(summary["recipes_path"]),
        "environment_summary_path": str(summary["summary_path"]),
        "environment_report_path": str(summary["report_path"]),
    }
    next_command = oodrive_command(
        f"export-env-demo --environment-summary {summary['summary_path']} --run-id {run_id}"
    )
    return StudioCommandResult(
        command="oodrive generate-envs",
        run_id=run_id,
        status="passed",
        artifacts=artifacts,
        next_commands=[next_command],
        summary={
            "num_recipes": summary["num_recipes"],
            "num_asset_requests": summary["num_asset_requests"],
            "families": summary["families"],
            "severity": severity,
            "random_seed": random_seed,
        },
        claim_boundaries=[
            "environment_generation=true",
            "randomized_scenario_generation=true",
            "carla_environment_recipe=true",
            "closed_loop_vla_control=false",
            "real_time_vla_control=false",
        ],
    )


def run_studio_export_env_demo(
    *,
    environment_summary_path: Path,
    submission_pack_path: Path | None = None,
    hero_video_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
) -> StudioCommandResult:
    """Build a recordable Environment Studio HTML demo pack."""

    from driverx.pipeline.environment_demo_pack import build_environment_demo_pack

    pack_id = run_id or f"{environment_summary_path.parent.name}-environment-demo"
    pack = build_environment_demo_pack(
        environment_summary_path=environment_summary_path,
        submission_pack_path=submission_pack_path,
        hero_video_path=hero_video_path,
        output_root=output_root or (environment_summary_path.parent / "environment-demo-packs"),
        run_id=pack_id,
    )
    artifacts = {
        "environment_demo_index_path": str(pack["environment_demo_index_path"]),
        "environment_demo_manifest_path": str(pack["environment_demo_manifest_path"]),
        "environment_demo_commands_path": str(pack["environment_demo_commands_path"]),
        "environment_demo_storyboard_path": str(pack["environment_demo_storyboard_path"]),
    }
    next_command = oodrive_command(
        f"score-env-demo --environment-summary {environment_summary_path} "
        f"--demo-manifest {pack['environment_demo_manifest_path']} --metric-only"
    )
    return StudioCommandResult(
        command="oodrive export-env-demo",
        run_id=pack["pack_id"],
        status="passed",
        artifacts=artifacts,
        next_commands=[next_command],
        summary={
            "family_count": pack["family_count"],
            "recipe_count": pack["recipe_count"],
            "asset_request_count": pack["asset_request_count"],
            "card_count": len(pack["cards"]),
            "index_html_path": pack["environment_demo_index_path"],
        },
        claim_boundaries=pack["claim_boundaries"],
    )


def run_studio_score_env_demo(
    *,
    environment_summary_path: Path | None = None,
    demo_manifest_path: Path | None = None,
    score_input_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
    metric_only: bool = False,
) -> StudioCommandResult:
    """Score whether the environment-generation surface is judge-demo-ready."""

    from driverx.evaluation.environment_demo_score import (
        load_environment_demo_readiness_inputs,
        score_environment_demo_readiness,
        write_environment_demo_score,
    )

    if environment_summary_path is None and score_input_path is None:
        raise ValueError("Pass either --environment-summary or --score-input.")
    score_id = run_id or (
        f"{score_input_path.stem}-environment-demo-score"
        if score_input_path is not None
        else f"{Path(environment_summary_path).parent.name}-environment-demo-score"
    )
    default_root = (
        demo_manifest_path.parent / "environment-demo-scores"
        if demo_manifest_path is not None
        else Path("artifacts/runs/environment-demo-scores")
    )
    run_dir = prepare_run_dir(output_root or default_root, score_id)
    inputs = load_environment_demo_readiness_inputs(
        environment_summary_path=environment_summary_path,
        demo_manifest_path=demo_manifest_path,
        score_input_path=score_input_path,
    )
    report = score_environment_demo_readiness(inputs)
    artifacts = artifact_paths(write_environment_demo_score(run_dir, report))
    if metric_only:
        print(f"METRIC environment_demo_readiness_score={report.environment_demo_readiness_score:.4f}")
        for key, value in report.components.items():
            print(f"METRIC {key}={value:.4f}")
    return StudioCommandResult(
        command="oodrive score-env-demo",
        run_id=score_id,
        status=report.status,
        artifacts=artifacts,
        summary={
            "environment_demo_readiness_score": report.environment_demo_readiness_score,
            "threshold": report.threshold,
            "components": report.components,
            "recommendations": report.recommendations,
        },
        claim_boundaries=report.claim_boundaries,
        blockers=report.blockers,
    )


def select_environment_recipe(
    environment_summary_path: Path,
    *,
    recipe_id: str | None = None,
    template_id: str | None = None,
    family: str | None = None,
) -> EnvironmentRecipe:
    """Select one generated environment recipe from an Environment Studio summary."""

    payload = _load_json(environment_summary_path)
    recipes = [
        EnvironmentRecipe.from_jsonable(dict(item))
        for item in list(payload.get("recipes", []))
        if isinstance(item, dict)
    ]
    if not recipes:
        raise ValueError(f"No recipes found in environment summary: {environment_summary_path}")
    if recipe_id:
        for recipe in recipes:
            if recipe.recipe_id == recipe_id:
                return recipe
        raise ValueError(f"Unknown environment recipe id: {recipe_id}")
    if template_id:
        for recipe in recipes:
            if recipe.template_id == template_id:
                return recipe
        raise ValueError(f"Unknown environment template id in summary: {template_id}")
    if family:
        for recipe in recipes:
            if recipe.family == family:
                return recipe
        raise ValueError(f"Unknown environment family in summary: {family}")
    return recipes[0]


def run_studio_render_env(
    *,
    environment_summary_path: Path,
    recipe_id: str | None = None,
    template_id: str | None = None,
    family: str | None = None,
    prompt: str = "Generated OODrive environment visual proof",
    config_path: Path = Path("configs/carla_ood_demo.local.sample.yaml"),
    output_root: Path | None = None,
    run_id: str = "oodrive-environment-carla-proof",
    live: bool = False,
) -> StudioCommandResult:
    """Turn one generated environment recipe into same-lineage CARLA visual proof."""

    environment = select_environment_recipe(
        environment_summary_path,
        recipe_id=recipe_id,
        template_id=template_id,
        family=family,
    )
    run_dir = prepare_run_dir(output_root or Path("artifacts/runs"), run_id)
    candidate = build_environment_visual_candidate(
        environment=environment,
        prompt=prompt,
        run_id=run_dir.name,
    )
    db_path = run_dir / "scenario_studio_db.json"
    db_artifacts = _write_environment_visual_db(
        db_path=db_path,
        environment_summary_path=environment_summary_path,
        config_path=config_path,
        candidate=candidate,
    )
    placement = build_studio_placement_plan(
        db_path,
        scenario_id=str(candidate["scenario_id"]),
        config_path=config_path,
        output_root=run_dir / "placements",
        run_id=f"{run_dir.name}-placement",
    )
    place_result = run_studio_place(
        db_path,
        scenario_id=str(candidate["scenario_id"]),
        placement_path=Path(str(placement["json_path"])),
        config_path=config_path,
        output_root=run_dir / "runs",
        run_id=run_dir.name,
        live=live,
    )
    run_manifest_path = Path(str(place_result.artifacts.get("json_path", "")))
    run_manifest = _load_json(run_manifest_path) if run_manifest_path.exists() else {}
    preview = _copy_preview_frame(run_manifest, run_dir / "carla_environment_preview.png")
    visual_payload = write_environment_carla_visual_proof(
        run_dir=run_dir,
        environment=environment,
        environment_summary_path=environment_summary_path,
        db_path=db_path,
        placement_plan_path=Path(str(placement["json_path"])),
        run_manifest_path=run_manifest_path if run_manifest_path.exists() else None,
        carla_report_path=_optional_path(_mapping(run_manifest.get("artifacts")).get("carla_ood_demo_json")),
        preview_frame_path=preview["preview_image_path"],
        preview_source_frame=preview["preview_source_frame"],
        status=_visual_status(live=live, place_status=place_result.status, preview_image_path=preview["preview_image_path"]),
        blockers=list(place_result.blockers),
        live=live,
        config_path=config_path,
        candidate=candidate,
    )
    artifacts = {
        **db_artifacts,
        "placement_plan_path": str(placement["json_path"]),
        "placement_report_path": str(placement["report_path"]),
        "run_manifest_path": str(run_manifest_path) if run_manifest_path.exists() else "",
        "env_carla_proof_manifest_path": str(visual_payload["json_path"]),
        "env_carla_visual_report_path": str(visual_payload["report_path"]),
        "commands_path": str(visual_payload["commands_path"]),
    }
    if preview["preview_image_path"] is not None:
        artifacts["preview_image_path"] = str(preview["preview_image_path"])
    status = str(visual_payload["status"])
    return StudioCommandResult(
        command="oodrive render-env",
        run_id=run_dir.name,
        status=status,
        artifacts=artifacts,
        next_commands=[
            oodrive_command(
                f"analyze-keyframes --visual-proof {visual_payload['json_path']} "
                f"--db {db_path} --run {run_manifest_path if run_manifest_path.exists() else '<run_manifest.json>'} "
                f"--backend fake --keyframes 8 --run-id task137-keyframe-analysis-v1"
            )
        ],
        summary={
            "environment_recipe_id": environment.recipe_id,
            "template_id": environment.template_id,
            "family": environment.family,
            "scenario_id": candidate["scenario_id"],
            "live": live,
            "same_lineage": visual_payload["same_lineage"],
            "preview_image_path": str(preview["preview_image_path"]) if preview["preview_image_path"] else None,
            "place_status": place_result.status,
        },
        claim_boundaries=list(visual_payload["claim_boundaries"]),
        blockers=list(visual_payload["blockers"]),
    )


def build_environment_visual_candidate(
    *,
    environment: EnvironmentRecipe,
    prompt: str,
    run_id: str,
) -> dict[str, Any]:
    """Build the single queued OODrive candidate used by `render-env`."""

    behavior_id = _behavior_id_for_environment(environment)
    behavior = generate_behavior_variants(
        behavior_id,
        count=1,
        random_seed=environment.random_seed,
        severity=environment.severity,
    )[0]
    scenario_id = f"{_slug(environment.recipe_id)}-carla-visual"
    base = ScenarioRecipe(
        recipe_id=scenario_id,
        parent_seed_id=f"environment-{environment.template_id}",
        mutation=f"{environment.family}_carla_visual_proof",
        actors=[
            {
                "actor_id": f"behavior_actor_{behavior.behavior_id}",
                "kind": behavior.actor_kind,
                "role": "dynamic_ood_actor",
                "behavior_id": behavior.behavior_id,
                "expected_pressure": behavior.expected_pressure,
            }
        ],
        environment={
            "studio_plan_id": f"{run_id}-environment-visual",
            "environment_recipe_id": environment.recipe_id,
            "environment_template_id": environment.template_id,
            "environment_family": environment.family,
            "environment_tags": environment.tags,
            "weather": environment.weather,
            "lighting": environment.lighting,
            "traffic": environment.traffic,
            "behavior_id": behavior.behavior_id,
            "behavior_tags": behavior.tags,
            "quality_targets": {
                "require_visual_preview": True,
                "require_same_lineage": True,
                "require_road_local_assets": True,
            },
        },
        expected_failure_mode=(
            f"Visual proof for generated environment `{environment.recipe_id}`. "
            f"Policy pressure: {environment.expected_policy_pressure}"
        ),
        memory_query=sorted(set([*environment.tags, environment.family, behavior.behavior_id, "environment_visual_proof"])),
        solvability_assumption="Safe behavior: slow, preserve clearance, and do not overfit to known CARLA routes.",
        route_path="generated-environment-visual-proof",
    )
    compiled = attach_environment_to_recipe(base, environment)
    return {
        "scenario_id": compiled.recipe_id,
        "candidate_id": compiled.recipe_id,
        "environment_recipe_id": environment.recipe_id,
        "template_id": environment.template_id,
        "family": environment.family,
        "random_seed": environment.random_seed,
        "prompt": prompt,
        "compiled_recipe": compiled.to_jsonable(),
        "environment_recipe": environment.to_jsonable(),
        "behavior_plan": behavior.to_jsonable(),
        "asset_requests": [
            request.to_jsonable()
            for request in environment_to_asset_requests(environment)
        ],
        "carla_run_ready": True,
        "alpamayo_package_ready": False,
    }


def write_environment_carla_visual_proof(
    *,
    run_dir: Path,
    environment: EnvironmentRecipe,
    environment_summary_path: Path,
    db_path: Path,
    placement_plan_path: Path,
    run_manifest_path: Path | None,
    carla_report_path: Path | None,
    preview_frame_path: Path | None,
    preview_source_frame: Path | None,
    status: str,
    blockers: list[str],
    live: bool,
    config_path: Path,
    candidate: dict[str, Any],
) -> dict[str, Any]:
    """Write the manifest proving one environment recipe reached CARLA visual evidence."""

    run_dir.mkdir(parents=True, exist_ok=True)
    same_lineage = _same_lineage(
        environment=environment,
        candidate=candidate,
        placement_plan_path=placement_plan_path,
        run_manifest_path=run_manifest_path,
        preview_frame_path=preview_frame_path,
    )
    claim_boundaries = [
        "environment_generation=true",
        "randomized_scenario_generation=true",
        "environment_to_carla_visual_proof=true",
        f"carla_visual_evidence={'true' if preview_frame_path is not None else 'false'}",
        "closed_loop_vla_control=false",
        "real_time_vla_control=false",
    ]
    proof_blockers = list(blockers)
    setup_commands: list[str] = []
    if status == "blocked" and live and preview_frame_path is None:
        proof_blockers.append(
            "Live preview needs the Kasm RunPod CARLA graphics path: "
            "`/workspace/carla/CARLA_0.9.16`, `DISPLAY=`, "
            "`VK_ICD_FILENAMES=/workspace/carla/nvidia_icd.json`, and the "
            "`/workspace/driverx_py312` CARLA client."
        )
        setup_commands.extend(
            [
                "ssh -tt -i ~/.ssh/id_ed25519_runpod <kasm-user>@ssh.runpod.io",
                "cd /workspace/0xDriver && bash scripts/setup_runpod_carla_0916_graphics.sh",
            ]
        )
    payload = {
        "status": status,
        "same_lineage": same_lineage,
        "live": live,
        "product_name": OODRIVE_PRODUCT_NAME,
        "environment_recipe_id": environment.recipe_id,
        "template_id": environment.template_id,
        "family": environment.family,
        "random_seed": environment.random_seed,
        "scenario_id": candidate["scenario_id"],
        "candidate_id": candidate["candidate_id"],
        "environment_summary_path": str(environment_summary_path),
        "db_path": str(db_path),
        "config_path": str(config_path),
        "placement_plan_path": str(placement_plan_path),
        "run_manifest_path": str(run_manifest_path) if run_manifest_path else None,
        "carla_report_path": str(carla_report_path) if carla_report_path else None,
        "preview_image_path": str(preview_frame_path) if preview_frame_path else None,
        "preview_source_frame": str(preview_source_frame) if preview_source_frame else None,
        "asset_count": len(list(candidate.get("asset_requests", []))),
        "claim_boundaries": claim_boundaries,
        "blockers": proof_blockers,
        "setup_commands": setup_commands,
    }
    if status == "blocked" and not proof_blockers:
        payload["blockers"] = ["CARLA visual proof is blocked because no preview frame was produced."]
    payload["next_commands"] = [
        oodrive_command(
            f"analyze-keyframes --visual-proof {run_dir / 'env_carla_proof_manifest.json'} "
            f"--db {db_path} --run {run_manifest_path or '<run_manifest.json>'} --backend fake --keyframes 8"
        )
    ]
    json_path = run_dir / "env_carla_proof_manifest.json"
    report_path = run_dir / "env_carla_visual_report.md"
    commands_path = run_dir / "commands.sh"
    payload.update(
        {
            "json_path": str(json_path),
            "report_path": str(report_path),
            "commands_path": str(commands_path),
        }
    )
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_visual_proof_markdown(payload), encoding="utf-8")
    commands_path.write_text(_visual_proof_commands(payload), encoding="utf-8")
    return payload


def _write_environment_visual_db(
    *,
    db_path: Path,
    environment_summary_path: Path,
    config_path: Path,
    candidate: dict[str, Any],
) -> dict[str, str]:
    brief = {
        "brief_id": "brief-0001",
        "prompt": candidate["prompt"],
        "author": "fixture",
        "requested_tags": [
            str(candidate["family"]),
            str(candidate["template_id"]),
            "carla_visual_proof",
        ],
        "target_policy_pressure": "render generated environment in CARLA for judge-visible proof",
    }
    plan = {
        "plan_id": f"{candidate['candidate_id']}-plan",
        "brief": brief,
        "environment_template_id": candidate["template_id"],
        "environment_recipe_id": candidate["environment_recipe_id"],
        "environment_family": candidate["family"],
        "behavior_template_id": candidate["behavior_plan"]["behavior_id"],
        "mutation": "environment_to_carla_visual_proof",
        "asset_tags": [
            tag
            for asset in candidate["asset_requests"]
            for tag in list(asset.get("semantic_tags", []))
        ],
        "ood_tags": list(candidate["compiled_recipe"].get("memory_query", [])),
        "memory_query": list(candidate["compiled_recipe"].get("memory_query", [])),
        "expected_failure_mode": candidate["compiled_recipe"].get("expected_failure_mode"),
        "provider": "deterministic",
        "validation": {"passes": True, "errors": [], "warnings": []},
    }
    curation = {
        "candidate_id": candidate["candidate_id"],
        "curation_status": "accept_partial",
        "score": 0.75,
        "gate_results": {
            "environment_recipe_selected": True,
            "carla_visual_proof_required": True,
            "model_value": False,
        },
        "novelty_tags": list(candidate["compiled_recipe"].get("memory_query", [])),
        "evidence_paths": {
            "environment_summary": str(environment_summary_path),
            "carla_visual_proof": None,
        },
        "model_eval_status": "not_run",
        "why_keep": "Selected for same-lineage generated-environment CARLA visual proof.",
        "next_action": "Run oodrive render-env with --live on Kasm/CARLA or keep blocked proof locally.",
    }
    queue = {
        "scenario_id": candidate["scenario_id"],
        "candidate_id": candidate["candidate_id"],
        "plan_id": plan["plan_id"],
        "environment_recipe_id": candidate["environment_recipe_id"],
        "curation_status": "accept_partial",
        "run_status": "needs_runtime",
        "priority": 1,
        "score": 0.75,
        "policy_targets": ["carla-scripted-ood-demo", "alpamayo-trajectory"],
        "memory_query": list(candidate["compiled_recipe"].get("memory_query", [])),
        "next_command": oodrive_command(
            f"place --db {db_path} --scenario-id {candidate['scenario_id']} --config {config_path} --live"
        ),
    }
    db = new_studio_db(db_path.parent.name)
    db = replace_db(
        db,
        briefs=[brief],
        plans=[plan],
        candidates=[candidate],
        curation=[curation],
        queue=[queue],
        artifacts={
            "environment_summary_path": str(environment_summary_path),
        },
        claim_boundaries=sorted(
            set(
                [
                    *db.claim_boundaries,
                    "environment_generation=true",
                    "randomized_scenario_generation=true",
                    "same_lineage_carla_visual_required=true",
                    "closed_loop_vla_control=false",
                    "real_time_vla_control=false",
                ]
            )
        ),
    )
    db = append_command(
        db,
        command="oodrive render-env.prepare",
        status="passed",
        artifacts={"db_path": str(db_path), "environment_summary_path": str(environment_summary_path)},
        summary={
            "environment_recipe_id": candidate["environment_recipe_id"],
            "scenario_id": candidate["scenario_id"],
            "asset_count": len(candidate["asset_requests"]),
        },
    )
    return artifact_paths(write_studio_db(db_path, db))


def _copy_preview_frame(run_manifest: dict[str, Any], target_path: Path) -> dict[str, Path | None]:
    artifacts = _mapping(run_manifest.get("artifacts"))
    rgb_folder = _optional_path(artifacts.get("rgb_folder"))
    if rgb_folder is None or not rgb_folder.exists():
        return {"preview_image_path": None, "preview_source_frame": None}
    frames = sorted(
        [
            *rgb_folder.glob("frame_*.png"),
            *rgb_folder.glob("*.png"),
            *rgb_folder.glob("*.jpg"),
            *rgb_folder.glob("*.jpeg"),
        ]
    )
    frames = [frame for frame in frames if frame.is_file()]
    if not frames:
        return {"preview_image_path": None, "preview_source_frame": None}
    source = frames[len(frames) // 2]
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target_path)
    return {"preview_image_path": target_path, "preview_source_frame": source}


def _same_lineage(
    *,
    environment: EnvironmentRecipe,
    candidate: dict[str, Any],
    placement_plan_path: Path,
    run_manifest_path: Path | None,
    preview_frame_path: Path | None,
) -> bool:
    if preview_frame_path is None or not preview_frame_path.exists():
        return False
    if run_manifest_path is None or not run_manifest_path.exists():
        return False
    if not placement_plan_path.exists():
        return False
    placement = _load_json(placement_plan_path)
    run_manifest = _load_json(run_manifest_path)
    placement_recipe = _mapping(placement.get("recipe"))
    placement_env = _mapping(placement_recipe.get("environment"))
    scenario_id = str(candidate.get("scenario_id", ""))
    return (
        str(candidate.get("environment_recipe_id")) == environment.recipe_id
        and str(placement_env.get("environment_recipe_id")) == environment.recipe_id
        and str(placement.get("scenario_id")) == scenario_id
        and str(run_manifest.get("scenario_id")) == scenario_id
    )


def _visual_status(*, live: bool, place_status: str, preview_image_path: Path | None) -> str:
    if preview_image_path is not None:
        return "passed"
    if live:
        return "blocked" if place_status == "blocked" else "partial"
    return "planned"


def _behavior_id_for_environment(environment: EnvironmentRecipe) -> str:
    by_template = {
        "roadside_market_occlusion": "motorcycle_filtering",
        "dense_regional_traffic": "motorcycle_filtering",
        "school_zone_unstructured_crossing": "informal_right_of_way_push",
        "construction_lane_closure": "no_signal_cut_in",
        "flooded_road": "sudden_brake",
        "night_rain_fog": "wrong_way_shoulder_creep",
    }
    return by_template.get(environment.template_id, "motorcycle_filtering")


def _visual_proof_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OODrive Environment To CARLA Visual Proof",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Same lineage: `{payload.get('same_lineage')}`",
        f"- Environment recipe: `{payload.get('environment_recipe_id')}`",
        f"- Scenario: `{payload.get('scenario_id')}`",
        f"- Preview image: `{payload.get('preview_image_path')}`",
        f"- Source frame: `{payload.get('preview_source_frame')}`",
        "",
        "## Artifacts",
        "",
    ]
    for key in (
        "environment_summary_path",
        "db_path",
        "placement_plan_path",
        "run_manifest_path",
        "carla_report_path",
    ):
        lines.append(f"- `{key}`: `{payload.get(key)}`")
    blockers = list(payload.get("blockers", []))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        for blocker in blockers:
            lines.append(f"- {blocker}")
    lines.extend(["", "## Claim Boundaries", ""])
    for claim in list(payload.get("claim_boundaries", [])):
        lines.append(f"- `{claim}`")
    lines.extend(["", "## Next Commands", ""])
    for command in list(payload.get("next_commands", [])):
        lines.append(f"- `{command}`")
    lines.append("")
    return "\n".join(lines)


def _visual_proof_commands(payload: dict[str, Any]) -> str:
    lines = ["#!/usr/bin/env bash", "set -euo pipefail", ""]
    lines.append(
        oodrive_command(
            "render-env "
            f"--environment-summary {payload.get('environment_summary_path')} "
            f"--recipe-id {payload.get('environment_recipe_id')} "
            f"--config {payload.get('config_path')} "
            f"--run-id {payload.get('scenario_id')}"
        )
    )
    lines.extend(str(command) for command in list(payload.get("next_commands", [])))
    return "\n".join(lines) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _optional_path(value: object) -> Path | None:
    if value in (None, ""):
        return None
    return Path(str(value))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:96] or "environment"


__all__ = [
    "run_studio_export_env_demo",
    "run_studio_generate_envs",
    "run_studio_render_env",
    "run_studio_score_env_demo",
    "select_environment_recipe",
    "write_environment_carla_visual_proof",
]
