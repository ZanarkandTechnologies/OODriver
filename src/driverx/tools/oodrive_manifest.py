"""Machine-readable OODrive tool manifest for coding agents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir

TOOL_MANIFEST_SCHEMA_VERSION = "oodrive.tools_manifest.v1"


def build_oodrive_tools_manifest(*, include_experimental: bool = True) -> dict[str, Any]:
    tools = [
        _tool("validate-osc2", "Validate an agent-authored ASAM OpenSCENARIO 2.0 file.", ["--osc2"], ["osc2_validation.json"], ["writes_artifacts"]),
        _tool("run-osc2", "Run an OpenSCENARIO 2.0 file through ScenarioRunner when installed.", ["--osc2"], ["osc2_run_result.json"], ["may_connect_carla", "may_run_scenario_runner"]),
        _tool("scenario-runner-package", "Package OODrive/OSC2 artifacts for CARLA ScenarioRunner.", ["--osc2|--scenario-graph"], ["scenario_runner_package.json"], ["writes_artifacts"]),
        _tool("scenario-runner-run", "Run a ScenarioRunner package when ScenarioRunner is installed.", ["--package"], ["scenario_runner_run.json"], ["may_connect_carla", "may_run_scenario_runner"]),
        _tool("carla-control", "Probe/control CARLA map, weather, and screenshots.", [], ["carla_control.json"], ["may_connect_carla"]),
        _tool("prepare-map-import", "Create a CARLA custom map import manifest from FBX/XODR.", ["--fbx", "--xodr", "--map-name"], ["custom_map_import_manifest.json"], ["writes_artifacts"]),
        _tool("validate-map-import", "Validate a custom map import manifest.", ["--manifest"], ["custom_map_validation.json"], ["writes_artifacts"]),
        _tool("carla-map-probe", "Probe whether a CARLA map is installed and loadable.", ["--map"], ["carla_map_probe.json"], ["may_connect_carla"]),
        _tool("package-asset", "Build a CARLA packaging plan for an asset manifest.", ["--asset-manifest"], ["asset_package_plan.json"], ["writes_artifacts"]),
        _tool("probe-asset-blueprint", "Probe live CARLA for a blueprint id.", ["--blueprint-id"], ["blueprint_probe.json"], ["may_connect_carla"]),
        _tool("spawn-custom-asset", "Spawn a registered custom blueprint and capture proof.", ["--blueprint-id"], ["custom_asset_spawn_proof.json"], ["may_connect_carla"]),
        _tool("score-visual-fidelity", "Score prompt-to-CARLA visual/media proof.", ["--media-manifest"], ["visual_fidelity_score.json"], ["writes_artifacts"], experimental=True),
        _tool("f2d-catalog", "Emit Fail2Drive scenario metadata for agent-authored routes.", ["--fail2drive-root"], ["fail2drive_catalog.json"], ["writes_artifacts"]),
        _tool("f2d-validate-route", "Validate agent-authored Fail2Drive route XML.", ["--route"], ["fail2drive_route_validation.json"], ["writes_artifacts"]),
        _tool("f2d-write-route", "Compile a JSON route spec into Fail2Drive XML.", ["--spec|--example"], ["route.xml", "fail2drive_route_write.json"], ["writes_artifacts"]),
        _tool("f2d-run-route", "Plan or run a Fail2Drive evaluator route with evidence bundling.", ["--route"], ["fail2drive_route_run_workflow.json", "run_evidence.json"], ["may_connect_carla", "may_run_fail2drive"]),
        _tool("f2d-reason", "Attach sampled open-loop Alpamayo-style reasoning to Fail2Drive evidence.", ["--evidence", "--route"], ["f2d_reasoning.json"], ["writes_artifacts"]),
        _tool("f2d-demo-video", "Export a judge-visible Fail2Drive reasoning demo video/report.", ["--evidence", "--reasoning", "--route"], ["f2d_hero_demo.mp4", "f2d_demo_video.json"], ["may_encode_video"]),
        _tool("f2d-evaluate-model", "Build a model-reaction matrix over Fail2Drive route XML files.", ["--routes"], ["model_reaction_matrix.json"], ["may_connect_carla"]),
        _tool("tools-manifest", "Emit the agent-facing OODrive CLI/tool contract.", [], ["tools_manifest.json"], ["writes_artifacts"]),
        _tool("artifacts-list", "Index recent OODrive artifacts by kind and proof level.", [], ["artifacts_index.json"], ["reads_artifacts"]),
    ]
    if not include_experimental:
        tools = [tool for tool in tools if not tool.get("experimental")]
    return {
        "schema_version": TOOL_MANIFEST_SCHEMA_VERSION,
        "product": "OODrive",
        "operating_model": "Codex skill authors scenarios; OODrive validates, runs, probes, indexes, and scores.",
        "tools": tools,
        "claim_boundaries": [
            "agent_authored_scenario=true",
            "oodrive_internal_prompt_resolver=false",
            "closed_loop_vla_control=false_unless_trace_score_passes",
        ],
    }


def write_oodrive_tools_manifest(run_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "tools_manifest.json"
    report_path = run_dir / "tools_manifest.md"
    json_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(manifest), encoding="utf-8")
    return {**manifest, "json_path": str(json_path), "report_path": str(report_path)}


def build_and_write_tools_manifest(output_root: Path | None, run_id: str, *, include_experimental: bool = True) -> dict[str, Any]:
    run_dir = prepare_run_dir(output_root or Path("artifacts/runs"), run_id)
    return write_oodrive_tools_manifest(run_dir, build_oodrive_tools_manifest(include_experimental=include_experimental))


def _tool(name: str, purpose: str, inputs: list[str], outputs: list[str], side_effects: list[str], *, experimental: bool = False) -> dict[str, Any]:
    return {
        "name": name,
        "purpose": purpose,
        "inputs": inputs,
        "outputs": outputs,
        "side_effects": side_effects,
        "claim_boundaries": ["does_not_upgrade_claims_without_score_or_probe"],
        "example": f"PYTHONPATH=src python3 -m oodrive {name} --help",
        "experimental": experimental,
    }


def _markdown(manifest: dict[str, Any]) -> str:
    lines = ["# OODrive Tool Manifest", "", f"- tools: {len(list(manifest.get('tools', [])))}", ""]
    for tool in list(manifest.get("tools", [])):
        if isinstance(tool, dict):
            lines.append(f"- `{tool.get('name')}`: {tool.get('purpose')}")
    return "\n".join(lines) + "\n"


__all__ = ["build_and_write_tools_manifest", "build_oodrive_tools_manifest", "write_oodrive_tools_manifest"]
