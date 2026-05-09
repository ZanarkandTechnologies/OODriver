"""CARLA custom asset packaging, blueprint probe, and spawn proof helpers."""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from driverx.assets.carla_registry import expected_generated_blueprint_id
from driverx.core.artifacts import prepare_run_dir

ASSET_PACKAGE_SCHEMA_VERSION = "oodrive.custom_asset_package.v1"


@dataclass(frozen=True)
class AssetPackagePlan:
    status: str
    asset_manifest_path: str
    asset_id: str
    expected_blueprint_id: str
    mesh_path: str | None
    commands: list[str]
    blockers: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": ASSET_PACKAGE_SCHEMA_VERSION,
            "status": self.status,
            "asset_manifest_path": self.asset_manifest_path,
            "asset_id": self.asset_id,
            "expected_blueprint_id": self.expected_blueprint_id,
            "mesh_path": self.mesh_path,
            "commands": self.commands,
            "blockers": self.blockers,
            "claim_boundaries": self.claim_boundaries,
        }


@dataclass(frozen=True)
class BlueprintProbeResult:
    status: str
    blueprint_id: str
    connected: bool
    blueprint_registered: bool = False
    matching_blueprints: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": "oodrive.blueprint_probe.v1",
            "status": self.status,
            "blueprint_id": self.blueprint_id,
            "connected": self.connected,
            "blueprint_registered": self.blueprint_registered,
            "matching_blueprints": self.matching_blueprints,
            "blockers": self.blockers,
            "claim_boundaries": self.claim_boundaries,
        }


@dataclass(frozen=True)
class CustomAssetSpawnProof:
    status: str
    blueprint_id: str
    connected: bool
    blueprint_registered: bool = False
    spawned_actor_id: int | None = None
    screenshot_path: str | None = None
    blockers: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": "oodrive.custom_asset_spawn_proof.v1",
            "status": self.status,
            "blueprint_id": self.blueprint_id,
            "connected": self.connected,
            "blueprint_registered": self.blueprint_registered,
            "spawned_actor_id": self.spawned_actor_id,
            "screenshot_path": self.screenshot_path,
            "blockers": self.blockers,
            "claim_boundaries": self.claim_boundaries,
        }


def build_asset_package_plan(asset_manifest_path: Path) -> AssetPackagePlan:
    blockers: list[str] = []
    if not asset_manifest_path.exists():
        blockers.append(f"Asset manifest not found: {asset_manifest_path}")
        payload: dict[str, Any] = {}
    else:
        payload = json.loads(asset_manifest_path.read_text(encoding="utf-8"))
    asset_id = str(payload.get("asset_id") or payload.get("scenario_id") or "oodrive_asset")
    expected_blueprint = str(payload.get("expected_blueprint_id") or expected_generated_blueprint_id(asset_id))
    mesh_path = payload.get("local_path") or payload.get("mesh_path")
    if mesh_path and not Path(str(mesh_path)).exists():
        blockers.append(f"Mesh path does not exist locally: {mesh_path}")
    commands = [
        "# CARLA custom assets require Unreal/CARLA packaging before blueprint spawn.",
        f"# asset_id: {asset_id}",
        f"# expected blueprint: {expected_blueprint}",
        f"# mesh: {mesh_path or '<missing>'}",
        f"PackageAsset.sh --asset-id {asset_id} --blueprint-id {expected_blueprint}",
    ]
    return AssetPackagePlan(
        status="passed" if not blockers else "blocked",
        asset_manifest_path=str(asset_manifest_path),
        asset_id=asset_id,
        expected_blueprint_id=expected_blueprint,
        mesh_path=str(mesh_path) if mesh_path else None,
        commands=commands,
        blockers=blockers,
        claim_boundaries=[
            "custom_asset_package_plan=true",
            "arbitrary_mesh_spawn=false_until_blueprint_probe_and_spawn_pass",
        ],
    )


def probe_asset_blueprint(
    blueprint_id: str,
    *,
    host: str = "127.0.0.1",
    port: int = 2000,
    timeout_s: float = 20.0,
    carla_module: object | None = None,
) -> BlueprintProbeResult:
    if carla_module is None:
        try:
            carla_module = importlib.import_module("carla")
        except ImportError as exc:
            return BlueprintProbeResult(
                status="blocked",
                blueprint_id=blueprint_id,
                connected=False,
                blockers=[f"CARLA Python package is unavailable: {exc}"],
                claim_boundaries=["arbitrary_mesh_spawn=false"],
            )
    try:
        client = carla_module.Client(host, port)
        if hasattr(client, "set_timeout"):
            client.set_timeout(timeout_s)
        world = client.get_world()
        blueprints = world.get_blueprint_library()
        matches = [str(item.id) for item in blueprints.filter(blueprint_id)]
        registered = blueprint_id in matches or bool(matches)
        return BlueprintProbeResult(
            status="passed" if registered else "blocked",
            blueprint_id=blueprint_id,
            connected=True,
            blueprint_registered=registered,
            matching_blueprints=matches,
            blockers=[] if registered else [f"Blueprint {blueprint_id!r} is not registered in CARLA."],
            claim_boundaries=[
                f"carla_blueprint_registered={'true' if registered else 'false'}",
                "arbitrary_mesh_spawn=false_until_spawn_custom_asset_passes",
            ],
        )
    except Exception as exc:
        return BlueprintProbeResult(
            status="blocked",
            blueprint_id=blueprint_id,
            connected=False,
            blockers=[f"CARLA blueprint probe failed: {exc}"],
            claim_boundaries=["arbitrary_mesh_spawn=false"],
        )


def spawn_custom_asset(
    blueprint_id: str,
    *,
    host: str = "127.0.0.1",
    port: int = 2000,
    timeout_s: float = 20.0,
) -> CustomAssetSpawnProof:
    probe = probe_asset_blueprint(blueprint_id, host=host, port=port, timeout_s=timeout_s)
    if probe.status != "passed":
        return CustomAssetSpawnProof(
            status="blocked",
            blueprint_id=blueprint_id,
            connected=probe.connected,
            blueprint_registered=probe.blueprint_registered,
            blockers=probe.blockers,
            claim_boundaries=["arbitrary_mesh_spawn=false", "stock_proxy_fallback=false"],
        )
    return CustomAssetSpawnProof(
        status="blocked",
        blueprint_id=blueprint_id,
        connected=True,
        blueprint_registered=True,
        blockers=["Live custom asset spawning requires a placement transform and CARLA capture path; implement after blueprint probe passes."],
        claim_boundaries=["arbitrary_mesh_spawn=false_until_live_spawn_proof_exists"],
    )


def write_asset_package_plan(run_dir: Path, plan: AssetPackagePlan) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = plan.to_jsonable()
    json_path = run_dir / "asset_package_plan.json"
    report_path = run_dir / "asset_package_plan.md"
    commands_path = run_dir / "asset_package_commands.sh"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown("Asset Package Plan", payload), encoding="utf-8")
    commands_path.write_text("\n".join(plan.commands) + "\n", encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path), "commands_path": str(commands_path)}


def write_blueprint_probe(run_dir: Path, result: BlueprintProbeResult) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = result.to_jsonable()
    json_path = run_dir / "blueprint_probe.json"
    report_path = run_dir / "blueprint_probe.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown("Blueprint Probe", payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def write_custom_asset_spawn_proof(run_dir: Path, proof: CustomAssetSpawnProof) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = proof.to_jsonable()
    json_path = run_dir / "custom_asset_spawn_proof.json"
    report_path = run_dir / "custom_asset_spawn_proof.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown("Custom Asset Spawn Proof", payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def custom_asset_run_dir(output_root: Path | None, run_id: str) -> Path:
    return prepare_run_dir(output_root or Path("artifacts/runs"), run_id)


def _markdown(title: str, payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"- status: `{payload.get('status')}`",
            "",
            "## Blockers",
            *([f"- {item}" for item in list(payload.get("blockers", []))] or ["- none"]),
        ]
    ) + "\n"


__all__ = [
    "AssetPackagePlan",
    "BlueprintProbeResult",
    "CustomAssetSpawnProof",
    "build_asset_package_plan",
    "custom_asset_run_dir",
    "probe_asset_blueprint",
    "spawn_custom_asset",
    "write_asset_package_plan",
    "write_blueprint_probe",
    "write_custom_asset_spawn_proof",
]
