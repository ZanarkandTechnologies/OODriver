"""Production OODrive scenario-pack contract."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.assets.types import AssetManifest, AssetRequest
from driverx.core.artifacts import prepare_run_dir
from driverx.scenarios.generated_runtime import build_generated_scenario_runtime_spec
from driverx.scenarios.studio_product_helpers import oodrive_command

SCENARIO_PACK_SCHEMA_VERSION = "oodrive.scenario_pack.v1"


@dataclass(frozen=True)
class ScenarioPackValidation:
    passes: bool
    blockers: list[str]
    warnings: list[str]

    def to_jsonable(self) -> dict[str, object]:
        return {"passes": self.passes, "blockers": self.blockers, "warnings": self.warnings}


def build_production_scenario_pack(
    prompt: str,
    *,
    behavior_ids: tuple[str, ...] = (),
    object_kinds: tuple[str, ...] = (),
    template_ids: tuple[str, ...] = (),
    seed: int = 41,
    severity: int = 4,
    config_path: Path = Path("configs/carla_ood_demo.local.sample.yaml"),
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-production-pack",
) -> dict[str, Any]:
    clean_prompt = prompt.strip()
    if not clean_prompt:
        raise ValueError("A prompt is required for a production scenario pack.")
    run_dir = prepare_run_dir(output_root, run_id)
    runtime_spec = build_generated_scenario_runtime_spec(
        prompt=clean_prompt,
        template_ids=template_ids,
        behavior_ids=behavior_ids,
        object_kinds=object_kinds,
        severity=severity,
        seed=seed,
        config_path=config_path,
        output_root=run_dir,
        run_id="runtime-seed",
    )
    asset_requests = [dict(item) for item in list(runtime_spec.get("asset_requests", [])) if isinstance(item, dict)]
    behavior_cases = [dict(item) for item in list(runtime_spec.get("behavior_cases", [])) if isinstance(item, dict)]
    object_spawn_specs = [
        dict(item) for item in list(runtime_spec.get("object_spawn_specs", [])) if isinstance(item, dict)
    ]
    scenario_id = str(runtime_spec.get("scenario_id", run_dir.name))
    claim_boundaries = sorted(
        set(
            [
                "scenario_pack_schema=oodrive.scenario_pack.v1",
                "stock_proxy_asset_ready=true",
                "custom_mesh_generated=false_until_generate_assets_passes",
                "custom_asset_imported_in_carla=false_until_registry_probe_passes",
                "objects_spawned_in_carla=false_until_run_scenario_live_passes",
                "closed_loop_vla_control=false",
                "real_time_vla_control=false",
            ]
        )
    )
    pack: dict[str, Any] = {
        "schema_version": SCENARIO_PACK_SCHEMA_VERSION,
        "scenario_id": scenario_id,
        "run_id": run_dir.name,
        "run_dir": str(run_dir),
        "source_prompt": clean_prompt,
        "seed": int(seed),
        "severity": int(severity),
        "config_path": str(config_path),
        "map_constraints": {
            "town": None,
            "road_features": _road_features(clean_prompt),
            "coordinate_frame": "road_local",
        },
        "weather": _weather_from_prompt(clean_prompt),
        "asset_requests": asset_requests,
        "asset_manifests": list(runtime_spec.get("asset_manifests", [])),
        "asset_readiness": {
            "stock_proxy": bool(object_spawn_specs),
            "custom_mesh": False,
            "carla_import": False,
        },
        "behavior_timelines": [_behavior_timeline(case) for case in behavior_cases],
        "placement_constraints": [dict(item.get("spawn_transform", {})) for item in object_spawn_specs],
        "object_spawn_specs": object_spawn_specs,
        "generated_runtime_spec_path": runtime_spec.get("spec_path"),
        "evidence_requirements": [
            "asset_generation_manifest",
            "carla_asset_registry",
            "scenario_graph",
            "carla_live_spawn_manifest",
            "rgb_frame_or_video",
            "qa_prompt_image_review",
        ],
        "claim_boundaries": claim_boundaries,
        "next_commands": [],
    }
    validation = validate_production_scenario_pack(pack)
    pack["validation"] = validation.to_jsonable()
    pack_path = run_dir / "scenario_pack.json"
    report_path = run_dir / "scenario_pack.md"
    pack["scenario_pack_path"] = str(pack_path)
    pack["scenario_pack_report_path"] = str(report_path)
    pack["next_commands"] = [
        oodrive_command(f"generate-assets --scenario-pack {pack_path} --provider local-procedural"),
        oodrive_command(f"compile-scenario --scenario-pack {pack_path}"),
        oodrive_command(f"run-scenario --scenario-pack {pack_path} --backend fake-carla"),
        oodrive_command(f"run-scenario --scenario-pack {pack_path} --backend carla-live --config {config_path}"),
    ]
    pack_path.write_text(json.dumps(pack, indent=2), encoding="utf-8")
    report_path.write_text(_pack_markdown(pack), encoding="utf-8")
    return pack


def load_production_scenario_pack(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Scenario pack must be a JSON object: {path}")
    return payload


def validate_production_scenario_pack(pack: dict[str, Any]) -> ScenarioPackValidation:
    blockers: list[str] = []
    warnings: list[str] = []
    if pack.get("schema_version") != SCENARIO_PACK_SCHEMA_VERSION:
        blockers.append("Scenario pack schema_version is unsupported or missing.")
    if not str(pack.get("source_prompt", "")).strip():
        blockers.append("Scenario pack source_prompt is required.")
    if not list(pack.get("behavior_timelines", [])):
        blockers.append("At least one behavior timeline is required.")
    if not list(pack.get("asset_requests", [])):
        blockers.append("At least one asset request is required.")
    readiness = pack.get("asset_readiness", {})
    if not isinstance(readiness, dict) or "stock_proxy" not in readiness:
        blockers.append("Scenario pack asset_readiness.stock_proxy is required.")
    claim_boundaries = [str(item) for item in list(pack.get("claim_boundaries", []))]
    if not claim_boundaries:
        blockers.append("Scenario pack claim_boundaries are required.")
    if "custom_asset_imported_in_carla=false_until_registry_probe_passes" not in claim_boundaries:
        warnings.append("Custom CARLA asset import claim boundary is missing.")
    return ScenarioPackValidation(passes=not blockers, blockers=blockers, warnings=warnings)


def asset_requests_from_pack(pack: dict[str, Any]) -> list[AssetRequest]:
    return [
        AssetRequest.from_jsonable(dict(item))
        for item in list(pack.get("asset_requests", []))
        if isinstance(item, dict)
    ]


def asset_manifests_from_pack(pack: dict[str, Any]) -> list[AssetManifest]:
    return [
        AssetManifest.from_request(AssetRequest.from_jsonable(dict(item)), status="planned")
        for item in list(pack.get("asset_requests", []))
        if isinstance(item, dict)
    ]


def patch_pack_with_asset_manifests(pack: dict[str, Any], manifests: list[AssetManifest]) -> dict[str, Any]:
    updated = dict(pack)
    updated["asset_manifests"] = [manifest.to_jsonable() for manifest in manifests]
    updated["asset_readiness"] = {
        **dict(pack.get("asset_readiness", {})),
        "custom_mesh": any(manifest.status == "generated" and manifest.local_path for manifest in manifests),
    }
    updated["claim_boundaries"] = sorted(
        set(
            [
                *[str(item) for item in list(pack.get("claim_boundaries", []))],
                (
                    "custom_mesh_generated=true"
                    if updated["asset_readiness"]["custom_mesh"]
                    else "custom_mesh_generated=false"
                ),
            ]
        )
    )
    updated["validation"] = validate_production_scenario_pack(updated).to_jsonable()
    return updated


def write_production_scenario_pack(run_dir: Path, pack: dict[str, Any], *, stem: str = "scenario_pack") -> dict[str, str]:
    path = run_dir / f"{stem}.json"
    report_path = run_dir / f"{stem}.md"
    pack = dict(pack)
    pack["scenario_pack_path"] = str(path)
    pack["scenario_pack_report_path"] = str(report_path)
    path.write_text(json.dumps(pack, indent=2), encoding="utf-8")
    report_path.write_text(_pack_markdown(pack), encoding="utf-8")
    return {"json_path": str(path), "report_path": str(report_path)}


def _behavior_timeline(case: dict[str, Any]) -> dict[str, Any]:
    actor = dict(case.get("dynamic_actor", {}))
    plan = dict(case.get("behavior_plan", {}))
    return {
        "case_id": case.get("case_id"),
        "behavior_id": case.get("behavior_id"),
        "actor_ref": actor.get("actor_ref"),
        "actor_kind": actor.get("actor_kind"),
        "blueprint_filter": actor.get("blueprint_filter"),
        "trace_path": actor.get("trace_path"),
        "sample_count": actor.get("sample_count", 0),
        "expected_pressure": plan.get("expected_pressure"),
    }


def _weather_from_prompt(prompt: str) -> dict[str, float | str]:
    lowered = prompt.lower()
    return {
        "preset": "wet" if "wet" in lowered or "rain" in lowered else "clear",
        "precipitation": 70.0 if "wet" in lowered or "rain" in lowered else 0.0,
        "cloudiness": 80.0 if "wet" in lowered or "night" in lowered else 20.0,
    }


def _road_features(prompt: str) -> list[str]:
    lowered = prompt.lower()
    features = []
    for key in ("roadwork", "construction", "market", "vendor", "debris", "flood", "night", "wet"):
        if key in lowered:
            features.append(key)
    return features or ["ood"]


def _pack_markdown(pack: dict[str, Any]) -> str:
    lines = [
        "# OODrive Production Scenario Pack",
        "",
        f"- scenario: `{pack.get('scenario_id')}`",
        f"- prompt: {pack.get('source_prompt')}",
        f"- behaviors: {len(list(pack.get('behavior_timelines', [])))}",
        f"- asset requests: {len(list(pack.get('asset_requests', [])))}",
        f"- stock proxy ready: {dict(pack.get('asset_readiness', {})).get('stock_proxy')}",
        f"- custom mesh ready: {dict(pack.get('asset_readiness', {})).get('custom_mesh')}",
        f"- CARLA import ready: {dict(pack.get('asset_readiness', {})).get('carla_import')}",
        "",
        "## Claim Boundaries",
        "",
    ]
    lines.extend(f"- `{item}`" for item in list(pack.get("claim_boundaries", [])))
    lines.extend(["", "## Next Commands", ""])
    lines.extend(f"- `{item}`" for item in list(pack.get("next_commands", [])))
    return "\n".join(lines) + "\n"


__all__ = [
    "SCENARIO_PACK_SCHEMA_VERSION",
    "ScenarioPackValidation",
    "asset_manifests_from_pack",
    "asset_requests_from_pack",
    "build_production_scenario_pack",
    "load_production_scenario_pack",
    "patch_pack_with_asset_manifests",
    "validate_production_scenario_pack",
    "write_production_scenario_pack",
]
