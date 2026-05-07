"""Runtime materialization helpers for OODrive product commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driverx.assets import (
    AssetManifest,
    AssetRequest,
    default_asset_requests,
    generate_assets_dry_run,
)
from driverx.behaviors import BehaviorPlan, BehaviorTrace, simulate_behavior
from driverx.core.artifacts import prepare_run_dir
from driverx.scenarios import ScenarioRecipe
from driverx.scenarios.studio_db import ScenarioStudioDb, load_studio_db
from driverx.scenarios.studio_product_helpers import oodrive_command, select_queue_record
from driverx.simulators.carla_ood_demo import (
    CarlaOodDemoConfig,
    build_carla_ood_demo_plan,
    load_carla_ood_demo_config,
)


def build_studio_placement_plan(
    db_path: Path,
    *,
    scenario_id: str | None = None,
    config_path: Path = Path("configs/carla_ood_demo.local.sample.yaml"),
    output_root: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Write a CARLA placement plan for a queued Studio candidate."""

    db = load_studio_db(db_path)
    record = select_queue_record(db, scenario_id)
    candidate = candidate_for_queue_record(db, record)
    recipe = recipe_from_candidate(candidate)
    behavior = behavior_trace_from_candidate(candidate)
    asset_manifests = asset_manifests_from_candidate(candidate)
    config = load_carla_ood_demo_config(config_path)
    placement_id = run_id or f"{recipe.recipe_id}-placement"
    run_dir = prepare_run_dir(output_root or (db_path.parent / "placements"), placement_id)
    payload = placement_payload(
        db_path=db_path,
        config_path=config_path,
        record=record,
        candidate=candidate,
        recipe=recipe,
        behavior=behavior,
        config=config,
        asset_manifests=asset_manifests,
        placement_id=run_dir.name,
    )
    return write_studio_placement_plan(run_dir, payload)


def placement_payload(
    *,
    db_path: Path,
    config_path: Path,
    record: dict[str, Any],
    candidate: dict[str, Any],
    recipe: ScenarioRecipe,
    behavior: BehaviorTrace,
    config: CarlaOodDemoConfig,
    asset_manifests: list[AssetManifest],
    placement_id: str,
) -> dict[str, Any]:
    """Build the JSON payload describing what OODrive will place in CARLA."""

    carla_plan = build_carla_ood_demo_plan(
        recipe,
        behavior,
        config,
        asset_manifests=asset_manifests,
    )
    candidate_id = str(candidate.get("candidate_id") or recipe.recipe_id)
    object_specs = [spec.to_jsonable() for spec in carla_plan.object_spawn_specs]
    return {
        "placement_id": placement_id,
        "scenario_id": str(record.get("scenario_id") or recipe.recipe_id),
        "candidate_id": candidate_id,
        "db_path": str(db_path),
        "config_path": str(config_path),
        "recipe": recipe.to_jsonable(),
        "behavior_plan": behavior.plan.to_jsonable(),
        "behavior_metrics": dict(behavior.metrics),
        "behavior_sample_count": len(behavior.samples),
        "behavior_preview": [sample.to_jsonable() for sample in behavior.samples[:8]],
        "asset_manifests": [manifest.to_jsonable() for manifest in asset_manifests],
        "object_spawn_specs": object_specs,
        "dynamic_actor_refs": [
            str(actor.get("actor_id"))
            for actor in recipe.actors
            if str(actor.get("role", "")).endswith("ood_actor")
            or str(actor.get("role", "")) == "dynamic_ood_actor"
        ],
        "carla_plan": carla_plan.to_jsonable(),
        "claim_boundaries": [
            "carla_placement_plan=true",
            "objects_placed_in_carla=false_until_oodrive_place_live_passes",
            "asset_generation_provider=dry_run_stock_carla_proxy",
            "closed_loop_vla_control=false",
        ],
        "next_commands": [
            oodrive_command(
                f"place --db {db_path} --placement <placement_path> --config {config_path} --live"
            ),
            oodrive_command(
                f"reason --db {db_path} --run <run_manifest_path> --prediction-json <alpamayo_prediction.json>"
            ),
        ],
    }


def write_studio_placement_plan(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "carla_placement_plan.json"
    report_path = run_dir / "carla_placement_plan.md"
    payload = {
        **payload,
        "run_dir": str(run_dir),
        "json_path": str(json_path),
        "report_path": str(report_path),
    }
    payload["next_commands"] = [
        str(command).replace("<placement_path>", str(json_path))
        for command in list(payload.get("next_commands", []))
    ]
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_placement_markdown(payload), encoding="utf-8")
    return payload


def candidate_for_queue_record(db: ScenarioStudioDb, record: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(record.get("candidate_id") or record.get("scenario_id") or "")
    for candidate in db.candidates:
        if candidate_id in {
            str(candidate.get("candidate_id", "")),
            str(candidate.get("scenario_id", "")),
            str(dict(candidate.get("compiled_recipe", {})).get("recipe_id", "")),
        }:
            return dict(candidate)
    raise ValueError(f"Queued candidate is missing from Studio DB: {candidate_id}")


def recipe_from_candidate(candidate: dict[str, Any]) -> ScenarioRecipe:
    raw = candidate.get("compiled_recipe")
    if not isinstance(raw, dict):
        raise ValueError("Studio candidate has no compiled_recipe mapping.")
    return ScenarioRecipe.from_jsonable(raw)


def behavior_plan_from_candidate(candidate: dict[str, Any]) -> BehaviorPlan:
    raw = candidate.get("behavior_plan")
    if not isinstance(raw, dict):
        raise ValueError("Studio candidate has no behavior_plan mapping.")
    return BehaviorPlan(
        behavior_id=str(raw["behavior_id"]),
        actor_kind=str(raw.get("actor_kind", "vehicle")),
        duration_s=float(raw.get("duration_s", 6.0)),
        dt_s=float(raw.get("dt_s", 0.25)),
        parameters=dict(raw.get("parameters", {})),
        tags=[str(tag) for tag in list(raw.get("tags", []))],
        expected_pressure=str(raw.get("expected_pressure", "")),
    )


def behavior_trace_from_candidate(candidate: dict[str, Any]) -> BehaviorTrace:
    return simulate_behavior(behavior_plan_from_candidate(candidate))


def asset_manifests_from_candidate(candidate: dict[str, Any]) -> list[AssetManifest]:
    raw_requests = candidate.get("asset_requests")
    requests: list[AssetRequest]
    if isinstance(raw_requests, list) and raw_requests:
        requests = [
            AssetRequest.from_jsonable(item)
            for item in raw_requests
            if isinstance(item, dict)
        ]
    else:
        requests = default_asset_requests()
    return generate_assets_dry_run(requests)


def load_studio_placement_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Placement plan must be a JSON object: {path}")
    return payload


def _placement_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OODrive CARLA Placement Plan",
        "",
        f"- Placement: `{payload.get('placement_id')}`",
        f"- Scenario: `{payload.get('scenario_id')}`",
        f"- Candidate: `{payload.get('candidate_id')}`",
        f"- Config: `{payload.get('config_path')}`",
        f"- Behavior samples: `{payload.get('behavior_sample_count')}`",
        "",
        "## Objects To Place",
        "",
        "| actor ref | blueprint | x | y | tags |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for spec in list(payload.get("object_spawn_specs", [])):
        transform = dict(spec.get("spawn_transform", {}))
        location = dict(transform.get("location", {}))
        lines.append(
            "| "
            + " | ".join(
                [
                    str(spec.get("actor_ref", "")),
                    str(spec.get("blueprint_filter", "")),
                    str(location.get("x", "")),
                    str(location.get("y", "")),
                    ", ".join(str(tag) for tag in list(spec.get("semantic_tags", []))[:5]),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Next Commands", ""])
    for command in list(payload.get("next_commands", [])):
        lines.append(f"- `{command}`")
    lines.extend(["", "## Claim Boundaries", ""])
    for boundary in list(payload.get("claim_boundaries", [])):
        lines.append(f"- `{boundary}`")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "asset_manifests_from_candidate",
    "behavior_plan_from_candidate",
    "behavior_trace_from_candidate",
    "build_studio_placement_plan",
    "candidate_for_queue_record",
    "load_studio_placement_plan",
    "placement_payload",
    "recipe_from_candidate",
    "write_studio_placement_plan",
]
