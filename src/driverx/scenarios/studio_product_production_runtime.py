"""Product commands for production OODrive scenario generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driverx.assets.carla_registry import build_carla_asset_registry, write_carla_asset_registry
from driverx.assets.local_procedural import generate_local_procedural_assets
from driverx.assets.quality import validate_generated_asset_artifact
from driverx.core.artifacts import prepare_run_dir
from driverx.evaluation.research_scenario_generator_score import (
    score_research_scenario_generator,
    write_research_scenario_generator_score,
)
from driverx.scenarios.production_pack import (
    asset_manifests_from_pack,
    asset_requests_from_pack,
    build_production_scenario_pack,
    load_production_scenario_pack,
    patch_pack_with_asset_manifests,
    write_production_scenario_pack,
)
from driverx.scenarios.scenario_graph import build_scenario_graph_from_pack_path, compile_scenario_graph
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths, oodrive_command
from driverx.simulators.carla_scenario_runner import run_carla_scenario_graph, write_carla_scenario_run


def run_studio_scenario_pack(
    *,
    prompt: str,
    behavior_ids: tuple[str, ...] = (),
    object_kinds: tuple[str, ...] = (),
    template_ids: tuple[str, ...] = (),
    seed: int = 41,
    severity: int = 4,
    config_path: Path = Path("configs/carla_ood_demo.local.sample.yaml"),
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-production-pack",
) -> StudioCommandResult:
    pack = build_production_scenario_pack(
        prompt,
        behavior_ids=behavior_ids,
        object_kinds=object_kinds,
        template_ids=template_ids,
        seed=seed,
        severity=severity,
        config_path=config_path,
        output_root=output_root,
        run_id=run_id,
    )
    return StudioCommandResult(
        command="oodrive scenario-pack",
        run_id=str(pack["run_id"]),
        status="passed" if pack["validation"]["passes"] else "blocked",
        artifacts={
            "scenario_pack_path": str(pack["scenario_pack_path"]),
            "scenario_pack_report_path": str(pack["scenario_pack_report_path"]),
            "generated_runtime_spec_path": str(pack["generated_runtime_spec_path"]),
        },
        next_commands=[str(item) for item in list(pack.get("next_commands", []))],
        summary={
            "scenario_id": pack["scenario_id"],
            "asset_request_count": len(list(pack.get("asset_requests", []))),
            "behavior_count": len(list(pack.get("behavior_timelines", []))),
            "asset_readiness": pack.get("asset_readiness"),
        },
        claim_boundaries=[str(item) for item in list(pack.get("claim_boundaries", []))],
        blockers=[str(item) for item in list(pack["validation"].get("blockers", []))],
    )


def run_studio_generate_assets(
    *,
    scenario_pack_path: Path,
    provider: str = "local-procedural",
    output_root: Path | None = None,
    run_id: str = "oodrive-generated-assets",
) -> StudioCommandResult:
    pack = load_production_scenario_pack(scenario_pack_path)
    run_dir = prepare_run_dir(output_root or scenario_pack_path.parent, run_id)
    requests = asset_requests_from_pack(pack)
    if provider not in {"local-procedural", "local_procedural"}:
        manifests = [
            manifest
            for manifest in asset_manifests_from_pack(pack)
        ]
        blockers = [f"Provider {provider!r} is not configured; use local-procedural or install a provider plugin."]
        status = "blocked"
    else:
        manifests = generate_local_procedural_assets(requests, run_dir)
        blockers = []
        status = "passed"
    quality_reports = [validate_generated_asset_artifact(manifest).to_jsonable() for manifest in manifests]
    asset_manifest_path = run_dir / "asset_generation_manifest.json"
    asset_report_path = run_dir / "asset_generation_report.md"
    patched_pack = patch_pack_with_asset_manifests(pack, manifests)
    patched_paths = write_production_scenario_pack(run_dir, patched_pack, stem="scenario_pack.assets")
    payload = {
        "schema_version": "oodrive.asset_generation.v1",
        "scenario_id": pack.get("scenario_id"),
        "provider": provider,
        "status": status,
        "asset_manifests": [manifest.to_jsonable() for manifest in manifests],
        "quality_reports": quality_reports,
        "blockers": blockers,
        "patched_scenario_pack_path": patched_paths["json_path"],
    }
    asset_manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    asset_report_path.write_text(_asset_generation_markdown(payload), encoding="utf-8")
    artifacts = {
        "asset_generation_manifest_path": str(asset_manifest_path),
        "asset_generation_report_path": str(asset_report_path),
        "scenario_pack_path": patched_paths["json_path"],
        "scenario_pack_report_path": patched_paths["report_path"],
    }
    return StudioCommandResult(
        command="oodrive generate-assets",
        run_id=run_dir.name,
        status=status,
        artifacts=artifacts,
        next_commands=[
            oodrive_command(f"install-assets --scenario-pack {patched_paths['json_path']} --mode plan"),
            oodrive_command(f"compile-scenario --scenario-pack {patched_paths['json_path']}"),
        ],
        summary={
            "asset_count": len(manifests),
            "generated_count": sum(1 for manifest in manifests if manifest.status == "generated"),
            "patched_scenario_pack_path": patched_paths["json_path"],
        },
        claim_boundaries=[
            "custom_mesh_generated=true" if status == "passed" else "custom_mesh_generated=false",
            "custom_asset_imported_in_carla=false_until_install_assets_probe_passes",
        ],
        blockers=blockers,
    )


def run_studio_install_assets(
    *,
    scenario_pack_path: Path,
    mode: str = "plan",
    output_root: Path | None = None,
    run_id: str = "oodrive-carla-asset-registry",
) -> StudioCommandResult:
    pack = load_production_scenario_pack(scenario_pack_path)
    run_dir = prepare_run_dir(output_root or scenario_pack_path.parent, run_id)
    manifests = [
        _manifest_from_jsonable(dict(item))
        for item in list(pack.get("asset_manifests", []))
        if isinstance(item, dict)
    ]
    if not manifests:
        manifests = asset_manifests_from_pack(pack)
    registry = build_carla_asset_registry(manifests)
    registry_paths = write_carla_asset_registry(run_dir, registry)
    status = "passed" if mode == "plan" else "blocked"
    blockers = [] if mode == "plan" else ["Live CARLA/Unreal asset package installation is not enabled in this local run."]
    return StudioCommandResult(
        command="oodrive install-assets",
        run_id=run_dir.name,
        status=status,
        artifacts={"asset_registry_path": registry_paths["json_path"], "asset_registry_report_path": registry_paths["report_path"]},
        next_commands=[oodrive_command(f"compile-scenario --scenario-pack {scenario_pack_path} --asset-registry {registry_paths['json_path']}")],
        summary={
            "installed_blueprint_count": registry.get("installed_blueprint_count"),
            "stock_proxy_fallback_count": registry.get("stock_proxy_fallback_count"),
            "mode": mode,
        },
        claim_boundaries=[str(item) for item in list(registry.get("claim_boundaries", []))],
        blockers=blockers,
    )


def run_studio_compile_scenario(
    *,
    scenario_pack_path: Path,
    asset_registry_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str = "oodrive-scenario-graph",
) -> StudioCommandResult:
    graph = build_scenario_graph_from_pack_path(
        scenario_pack_path,
        asset_registry_path=asset_registry_path,
        output_root=output_root or scenario_pack_path.parent,
        run_id=run_id,
    )
    return StudioCommandResult(
        command="oodrive compile-scenario",
        run_id=Path(str(graph["json_path"])).parent.name,
        status="passed" if graph["validation"]["passes"] else "blocked",
        artifacts={
            "scenario_graph_path": str(graph["json_path"]),
            "scenario_graph_report_path": str(graph["report_path"]),
            "open_scenario_path": str(graph["open_scenario_path"]),
            "scenario_sidecar_path": str(graph["sidecar_path"]),
        },
        next_commands=[oodrive_command(f"run-scenario --scenario-pack {scenario_pack_path} --scenario-graph {graph['json_path']} --backend fake-carla")],
        summary={
            "actor_count": len(list(graph.get("actors", []))),
            "static_object_count": len(list(graph.get("static_objects", []))),
            "action_count": len(list(graph.get("actions", []))),
        },
        claim_boundaries=[str(item) for item in list(graph.get("claim_boundaries", []))],
        blockers=[str(item) for item in list(graph["validation"].get("blockers", []))],
    )


def run_studio_run_scenario(
    *,
    scenario_pack_path: Path,
    scenario_graph_path: Path | None = None,
    asset_registry_path: Path | None = None,
    backend: str = "fake-carla",
    config_path: Path = Path("configs/carla_ood_demo.local.sample.yaml"),
    output_root: Path | None = None,
    run_id: str = "oodrive-scenario-run",
) -> StudioCommandResult:
    pack = load_production_scenario_pack(scenario_pack_path)
    if scenario_graph_path is None:
        registry = json.loads(asset_registry_path.read_text(encoding="utf-8")) if asset_registry_path else None
        graph = compile_scenario_graph(pack, registry)
    else:
        graph = json.loads(scenario_graph_path.read_text(encoding="utf-8"))
    run_dir = prepare_run_dir(output_root or scenario_pack_path.parent, run_id)
    result = run_carla_scenario_graph(
        graph,
        pack=pack,
        run_dir=run_dir,
        backend="carla-live" if backend == "carla-live" else "fake-carla",
        config_path=config_path,
    )
    paths = write_carla_scenario_run(run_dir, graph=graph, pack=pack, result=result)
    artifacts = {"run_manifest_path": paths["json_path"], "run_manifest_report_path": paths["report_path"]}
    if result.tracks_path:
        artifacts["tracks_path"] = result.tracks_path
    if result.rgb_folder:
        artifacts["rgb_folder"] = result.rgb_folder
    if result.action_trace_path:
        artifacts["action_trace_path"] = result.action_trace_path
    return StudioCommandResult(
        command="oodrive run-scenario",
        run_id=run_dir.name,
        status=result.status,
        artifacts=artifacts,
        next_commands=[oodrive_command(f"score-research-generator --scenario-pack {scenario_pack_path} --run-manifest {paths['json_path']} --metric-only")],
        summary={
            "backend": result.backend,
            "spawned_static_count": result.spawned_static_count,
            "spawned_dynamic_count": result.spawned_dynamic_count,
            "custom_asset_spawn_count": result.custom_asset_spawn_count,
            "stock_proxy_spawn_count": result.stock_proxy_spawn_count,
            "rgb_folder": result.rgb_folder,
            "tracks_path": result.tracks_path,
        },
        claim_boundaries=result.claim_boundaries,
        blockers=result.blockers,
    )


def run_studio_score_research_generator(
    *,
    scenario_pack_path: Path | None = None,
    asset_manifest_paths: tuple[Path, ...] = (),
    asset_registry_path: Path | None = None,
    scenario_graph_path: Path | None = None,
    run_manifest_paths: tuple[Path, ...] = (),
    workbench_summary_path: Path | None = None,
    library_path: Path | None = None,
    video_path: Path | None = None,
    image_qa_report_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str = "oodrive-research-generator-score",
    metric_only: bool = False,
) -> StudioCommandResult:
    report = score_research_scenario_generator(
        scenario_pack_path=scenario_pack_path,
        asset_manifest_paths=asset_manifest_paths,
        asset_registry_path=asset_registry_path,
        scenario_graph_path=scenario_graph_path,
        run_manifest_paths=run_manifest_paths,
        workbench_summary_path=workbench_summary_path,
        library_path=library_path,
        video_path=video_path,
        image_qa_report_path=image_qa_report_path,
    )
    root = output_root or (scenario_pack_path.parent if scenario_pack_path else Path("artifacts/runs"))
    run_dir = prepare_run_dir(root, run_id)
    artifacts = artifact_paths(write_research_scenario_generator_score(run_dir, report))
    if metric_only:
        print(f"METRIC research_scenario_generator_score={report['score']:.4f}")
        for key, value in dict(report.get("components", {})).items():
            print(f"METRIC {key}={float(value):.4f}")
    return StudioCommandResult(
        command="oodrive score-research-generator",
        run_id=run_dir.name,
        status=str(report["status"]),
        artifacts=artifacts,
        summary={
            "research_scenario_generator_score": report["score"],
            "threshold": report["threshold"],
            "components": report["components"],
            "recommendations": report["recommendations"],
        },
        claim_boundaries=[str(item) for item in list(report.get("claim_boundaries", []))],
        blockers=[str(item) for item in list(report.get("blockers", []))],
    )


def run_studio_workbench(
    *,
    scenario_pack_path: Path,
    run_manifest_paths: tuple[Path, ...] = (),
    score_report_paths: tuple[Path, ...] = (),
    output_root: Path | None = None,
    run_id: str = "oodrive-research-workbench",
) -> StudioCommandResult:
    pack = load_production_scenario_pack(scenario_pack_path)
    run_dir = prepare_run_dir(output_root or scenario_pack_path.parent, run_id)
    summary = {
        "schema_version": "oodrive.workbench_summary.v1",
        "scenario_id": pack.get("scenario_id"),
        "source_prompt": pack.get("source_prompt"),
        "asset_readiness": pack.get("asset_readiness", {}),
        "run_manifest_paths": [str(path) for path in run_manifest_paths],
        "score_report_paths": [str(path) for path in score_report_paths],
        "curation_status": "needs_review",
        "claim_boundaries": pack.get("claim_boundaries", []),
    }
    summary_path = run_dir / "workbench_summary.json"
    html_path = run_dir / "scenario_workbench.html"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    html_path.write_text(_workbench_html(summary), encoding="utf-8")
    return StudioCommandResult(
        command="oodrive workbench",
        run_id=run_dir.name,
        status="passed",
        artifacts={"workbench_summary_path": str(summary_path), "html_path": str(html_path)},
        next_commands=[oodrive_command(f"export-library --workbench {summary_path}")],
        summary=summary,
        claim_boundaries=["research_workbench_static_html=true", *[str(item) for item in list(pack.get("claim_boundaries", []))]],
    )


def run_studio_export_library(
    *,
    workbench_summary_path: Path,
    include_media: str = "refs",
    output_root: Path | None = None,
    run_id: str = "oodrive-scenario-library",
) -> StudioCommandResult:
    workbench = json.loads(workbench_summary_path.read_text(encoding="utf-8"))
    run_dir = prepare_run_dir(output_root or workbench_summary_path.parent, run_id)
    library = {
        "schema_version": "oodrive.scenario_library.v1",
        "include_media": include_media,
        "records": [
            {
                "scenario_id": workbench.get("scenario_id"),
                "curation_status": workbench.get("curation_status", "needs_review"),
                "prompt": workbench.get("source_prompt"),
                "run_manifest_paths": workbench.get("run_manifest_paths", []),
                "score_report_paths": workbench.get("score_report_paths", []),
                "media": [{"kind": "video_or_frames", "availability": "referenced", "path": None}],
                "claim_boundaries": workbench.get("claim_boundaries", []),
            }
        ],
    }
    path = run_dir / "scenario_library.json"
    report_path = run_dir / "scenario_library.md"
    path.write_text(json.dumps(library, indent=2), encoding="utf-8")
    report_path.write_text(
        f"# OODrive Scenario Library\n\n- records: {len(library['records'])}\n- include media: {include_media}\n",
        encoding="utf-8",
    )
    return StudioCommandResult(
        command="oodrive export-library",
        run_id=run_dir.name,
        status="passed",
        artifacts={"library_path": str(path), "library_report_path": str(report_path)},
        summary={"record_count": len(library["records"]), "include_media": include_media},
        claim_boundaries=["scenario_library_export=true", "media_policy_explicit=true"],
    )


def _manifest_from_jsonable(payload: dict[str, Any]):
    from driverx.assets.types import AssetManifest

    return AssetManifest(
        asset_id=str(payload["asset_id"]),
        provider=payload.get("provider", "dry_run"),
        status=payload.get("status", "planned"),
        prompt=str(payload.get("prompt", "")),
        semantic_tags=[str(item) for item in list(payload.get("semantic_tags", []))],
        dimensions_m={str(k): float(v) for k, v in dict(payload.get("dimensions_m", {})).items()},
        collision_proxy=dict(payload.get("collision_proxy", {})),
        intended_placement=dict(payload.get("intended_placement", {})),
        license=str(payload.get("license", "")),
        source_recipe_id=str(payload["source_recipe_id"]) if payload.get("source_recipe_id") else None,
        local_path=str(payload["local_path"]) if payload.get("local_path") else None,
        external_uri=str(payload["external_uri"]) if payload.get("external_uri") else None,
        setup_guidance=str(payload["setup_guidance"]) if payload.get("setup_guidance") else None,
        metadata=dict(payload.get("metadata", {})),
    )


def _asset_generation_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OODrive Asset Generation",
            "",
            f"- status: {payload.get('status')}",
            f"- provider: {payload.get('provider')}",
            f"- assets: {len(list(payload.get('asset_manifests', [])))}",
            f"- patched pack: `{payload.get('patched_scenario_pack_path')}`",
            "",
        ]
    )


def _workbench_html(summary: dict[str, Any]) -> str:
    prompt = str(summary.get("source_prompt", ""))
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>OODrive Scenario Workbench</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f7f7f4; color: #20242a; }}
main {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
section {{ border-top: 1px solid #d8d8d2; padding: 18px 0; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
.cell {{ background: white; border: 1px solid #deded8; border-radius: 6px; padding: 12px; }}
code {{ white-space: normal; }}
</style>
<main>
  <h1>OODrive Scenario Workbench</h1>
  <section><strong>Prompt</strong><p>{_esc(prompt)}</p></section>
  <section class="grid">
    <div class="cell"><strong>Scenario</strong><br><code>{_esc(str(summary.get("scenario_id")))}</code></div>
    <div class="cell"><strong>Curation</strong><br>{_esc(str(summary.get("curation_status")))}</div>
    <div class="cell"><strong>Asset readiness</strong><br><code>{_esc(json.dumps(summary.get("asset_readiness", {})))}</code></div>
  </section>
  <section><strong>Run manifests</strong><ul>{''.join(f'<li><code>{_esc(str(path))}</code></li>' for path in summary.get('run_manifest_paths', []))}</ul></section>
  <section><strong>Claim boundaries</strong><ul>{''.join(f'<li><code>{_esc(str(item))}</code></li>' for item in summary.get('claim_boundaries', []))}</ul></section>
</main>
</html>
"""


def _esc(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


__all__ = [
    "run_studio_compile_scenario",
    "run_studio_generate_assets",
    "run_studio_install_assets",
    "run_studio_run_scenario",
    "run_studio_score_research_generator",
    "run_studio_scenario_pack",
    "run_studio_workbench",
    "run_studio_export_library",
]
