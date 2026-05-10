"""CARLA custom asset packaging, blueprint probe, and spawn proof helpers."""

from __future__ import annotations

import importlib
import json
import queue
import shutil
import subprocess
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
    fbx_source_path: str | None
    import_package_name: str
    prop_name: str
    import_bundle_relpath: str
    package_json_name: str
    carla_root: str | None
    carla_root_capabilities: dict[str, Any]
    commands: list[str]
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": ASSET_PACKAGE_SCHEMA_VERSION,
            "status": self.status,
            "asset_manifest_path": self.asset_manifest_path,
            "asset_id": self.asset_id,
            "expected_blueprint_id": self.expected_blueprint_id,
            "mesh_path": self.mesh_path,
            "fbx_source_path": self.fbx_source_path,
            "import_package_name": self.import_package_name,
            "prop_name": self.prop_name,
            "import_bundle_relpath": self.import_bundle_relpath,
            "package_json_name": self.package_json_name,
            "carla_root": self.carla_root,
            "carla_root_capabilities": self.carla_root_capabilities,
            "commands": self.commands,
            "blockers": self.blockers,
            "warnings": self.warnings,
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


@dataclass(frozen=True)
class RuntimeMeshSpawnProof:
    status: str
    mesh_path: str
    connected: bool
    runtime_mesh_blueprint_id: str = "static.prop.mesh"
    blueprint_registered: bool = False
    spawned_actor_id: int | None = None
    screenshot_path: str | None = None
    scale: float = 1.0
    blockers: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": "oodrive.runtime_mesh_spawn_proof.v1",
            "status": self.status,
            "mesh_path": self.mesh_path,
            "runtime_mesh_blueprint_id": self.runtime_mesh_blueprint_id,
            "connected": self.connected,
            "blueprint_registered": self.blueprint_registered,
            "spawned_actor_id": self.spawned_actor_id,
            "screenshot_path": self.screenshot_path,
            "scale": self.scale,
            "blockers": self.blockers,
            "claim_boundaries": self.claim_boundaries,
        }


@dataclass(frozen=True)
class AssetCookPlan:
    status: str
    package_plan_path: str
    import_package_name: str
    import_bundle_path: str | None
    mode: str
    carla_source_root: str | None
    carla_package_root: str | None
    cooked_package_path: str | None
    output_dir: str | None
    capabilities: dict[str, Any]
    commands: list[str]
    executed: bool = False
    execution_log: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": "oodrive.asset_cook_plan.v1",
            "status": self.status,
            "package_plan_path": self.package_plan_path,
            "import_package_name": self.import_package_name,
            "import_bundle_path": self.import_bundle_path,
            "mode": self.mode,
            "carla_source_root": self.carla_source_root,
            "carla_package_root": self.carla_package_root,
            "cooked_package_path": self.cooked_package_path,
            "output_dir": self.output_dir,
            "capabilities": self.capabilities,
            "commands": self.commands,
            "executed": self.executed,
            "execution_log": self.execution_log,
            "blockers": self.blockers,
            "warnings": self.warnings,
            "claim_boundaries": self.claim_boundaries,
        }


def build_asset_package_plan(
    asset_manifest_path: Path,
    *,
    carla_root: Path | None = None,
    import_package_name: str | None = None,
) -> AssetPackagePlan:
    blockers: list[str] = []
    warnings: list[str] = []
    if not asset_manifest_path.exists():
        blockers.append(f"Asset manifest not found: {asset_manifest_path}")
        payload: dict[str, Any] = {}
    else:
        payload = json.loads(asset_manifest_path.read_text(encoding="utf-8"))
    asset_id = str(payload.get("asset_id") or payload.get("scenario_id") or "oodrive_asset")
    expected_blueprint = str(payload.get("expected_blueprint_id") or expected_generated_blueprint_id(asset_id))
    mesh_path = payload.get("local_path") or payload.get("mesh_path")
    mesh = _resolve_existing_path(mesh_path, asset_manifest_path.parent) if mesh_path else None
    alternate_formats = _alternate_formats(payload)
    fbx = _resolve_existing_path(alternate_formats.get("fbx"), asset_manifest_path.parent)
    if fbx is None and mesh is not None and mesh.suffix.lower() == ".fbx":
        fbx = mesh
    if mesh_path and mesh is None:
        blockers.append(f"Mesh path does not exist locally: {mesh_path}")
    if fbx is None:
        blockers.append("CARLA prop import requires an FBX mesh; no existing FBX path was found in manifest metadata.alternate_formats.fbx or local_path.")
    prop_name = _safe_unreal_name(asset_id)
    package_name = _safe_package_name(import_package_name or f"OODrive_{prop_name}")
    package_json_name = f"{package_name}.json"
    capabilities = _carla_root_capabilities(carla_root) if carla_root is not None else {}
    if carla_root is not None:
        if not capabilities.get("exists"):
            blockers.append(f"CARLA root does not exist: {carla_root}")
        elif not capabilities.get("has_source_make_import") and not capabilities.get("has_package_import_assets"):
            blockers.append(f"CARLA root has neither Makefile/make import nor ImportAssets.sh: {carla_root}")
        elif capabilities.get("has_package_import_assets") and not capabilities.get("has_source_make_import"):
            warnings.append(
                "This CARLA root can only unpack already-cooked asset packages; it cannot cook a raw FBX into a blueprint on this host."
            )
    commands = [
        "# CARLA custom prop registration follows the official Import/<Package>/Props/<Prop> bundle format.",
        f"# asset_id: {asset_id}",
        f"# expected OODrive blueprint alias: {expected_blueprint}",
        f"# expected CARLA prop blueprint after import: static.prop.{prop_name.lower()}",
        f"# source FBX: {str(fbx) if fbx is not None else '<missing>'}",
        f"# import bundle: carla_import/{package_name}",
        f"cp -R carla_import/{package_name} $CARLA_ROOT/Import/{package_name}",
        "cd $CARLA_ROOT",
        "# Source-build CARLA path: make import",
        "# Packaged CARLA path after cooking elsewhere: ./ImportAssets.sh",
        f"# Then verify: PYTHONPATH=src python3 -m oodrive probe-asset-blueprint --blueprint-id static.prop.{prop_name.lower()}",
    ]
    return AssetPackagePlan(
        status="passed" if not blockers else "blocked",
        asset_manifest_path=str(asset_manifest_path),
        asset_id=asset_id,
        expected_blueprint_id=expected_blueprint,
        mesh_path=str(mesh) if mesh is not None else (str(mesh_path) if mesh_path else None),
        fbx_source_path=str(fbx) if fbx is not None else None,
        import_package_name=package_name,
        prop_name=prop_name,
        import_bundle_relpath=f"carla_import/{package_name}",
        package_json_name=package_json_name,
        carla_root=str(carla_root) if carla_root is not None else None,
        carla_root_capabilities=capabilities,
        commands=commands,
        blockers=blockers,
        warnings=warnings,
        claim_boundaries=[
            "custom_asset_package_plan=true",
            "carla_import_bundle_prepared=true",
            "arbitrary_mesh_spawn=false_until_blueprint_probe_and_spawn_pass",
        ],
    )


def build_asset_cook_plan(
    package_plan_path: Path,
    *,
    carla_source_root: Path | None = None,
    carla_package_root: Path | None = None,
    cooked_package_path: Path | None = None,
    output_dir: Path | None = None,
    mode: str = "auto",
    execute: bool = False,
) -> AssetCookPlan:
    blockers: list[str] = []
    warnings: list[str] = []
    execution_log: list[str] = []
    if mode not in {"auto", "source", "docker", "import_cooked"}:
        blockers.append(f"Unsupported cook mode: {mode}")
    payload: dict[str, Any] = {}
    if package_plan_path.exists():
        payload = json.loads(package_plan_path.read_text(encoding="utf-8"))
    else:
        blockers.append(f"Asset package plan not found: {package_plan_path}")
    package_name = str(payload.get("import_package_name") or "")
    bundle_value = payload.get("import_bundle_path") or payload.get("import_bundle_relpath")
    bundle_path = _resolve_existing_path(bundle_value, package_plan_path.parent) if bundle_value else None
    if not package_name:
        blockers.append("Package plan does not include import_package_name.")
    if bundle_value and bundle_path is None:
        blockers.append(f"Import bundle path does not exist: {bundle_value}")
    capabilities = {
        "carla_source_root": _carla_root_capabilities(carla_source_root) if carla_source_root else {},
        "carla_package_root": _carla_root_capabilities(carla_package_root) if carla_package_root else {},
        "docker_available": bool(shutil.which("docker")),
    }
    source_ready = bool(carla_source_root and (carla_source_root / "Makefile").exists())
    docker_tools = (carla_source_root / "Util" / "Docker" / "docker_tools.py") if carla_source_root else None
    docker_ready = bool(docker_tools and docker_tools.exists() and shutil.which("docker"))
    cooked_ready = bool(cooked_package_path and cooked_package_path.exists())
    package_import_ready = bool(carla_package_root and ((carla_package_root / "ImportAssets.sh").exists() or (carla_package_root / "Util" / "ImportAssets.sh").exists()))
    selected_mode = mode
    if selected_mode == "auto":
        if source_ready:
            selected_mode = "source"
        elif docker_ready:
            selected_mode = "docker"
        elif cooked_ready and package_import_ready:
            selected_mode = "import_cooked"
        else:
            selected_mode = "blocked"
    commands: list[str] = []
    if selected_mode == "source":
        if not source_ready:
            blockers.append(f"CARLA source root with Makefile is required for source mode: {carla_source_root}")
        if bundle_path is None:
            blockers.append("Source cook requires an existing CARLA Import/<Package> bundle.")
        source = str(carla_source_root) if carla_source_root else "$CARLA_SOURCE_ROOT"
        commands.extend(
            [
                f"mkdir -p {source}/Import",
                f"rsync -a {bundle_path or '<import-bundle>'} {source}/Import/{package_name}",
                f"cd {source}",
                "make import",
                f"make package ARGS=\"--packages={package_name}\"",
                f"# Expected cooked package: {source}/Dist/{package_name}.tar.gz",
            ]
        )
    elif selected_mode == "docker":
        if not docker_ready:
            blockers.append("Docker cook mode requires Docker plus CARLA `Util/Docker/docker_tools.py` from a source checkout.")
        if bundle_path is None:
            blockers.append("Docker cook requires an existing CARLA Import/<Package> bundle.")
        out = output_dir or Path("artifacts/runs/carla-cooked-assets")
        commands.append(
            f"python3 {docker_tools or '$CARLA_SOURCE_ROOT/Util/Docker/docker_tools.py'} "
            f"--input {bundle_path.parent if bundle_path else '<input-dir>'} --output {out} --packages {package_name}"
        )
    elif selected_mode == "import_cooked":
        if not cooked_ready:
            blockers.append(f"Cooked package tar/zip does not exist: {cooked_package_path}")
        if not package_import_ready:
            blockers.append(f"Packaged CARLA root with ImportAssets.sh is required: {carla_package_root}")
        package_root = str(carla_package_root) if carla_package_root else "$CARLA_PACKAGE_ROOT"
        package = str(cooked_package_path) if cooked_package_path else f"<{package_name}.tar.gz>"
        commands.extend(
            [
                f"mkdir -p {package_root}/Import",
                f"cp {package} {package_root}/Import/",
                f"cd {package_root}",
                "./ImportAssets.sh",
            ]
        )
    else:
        blockers.append(
            "No programmatic cook/import lane is available on this host. Need CARLA source Makefile, CARLA Docker cook tooling, or a prebuilt cooked .tar.gz/.zip package."
        )
    if execute and blockers:
        warnings.append("Execution skipped because blockers are present.")
    elif execute and selected_mode == "import_cooked" and cooked_package_path and carla_package_root:
        execution_log = _execute_cooked_package_import(cooked_package_path, carla_package_root)
    elif execute:
        warnings.append("Execution is only implemented for import_cooked mode; source/docker cook commands are emitted for a proper cook host.")
    return AssetCookPlan(
        status="passed" if not blockers else "blocked",
        package_plan_path=str(package_plan_path),
        import_package_name=package_name,
        import_bundle_path=str(bundle_path) if bundle_path else (str(bundle_value) if bundle_value else None),
        mode=selected_mode,
        carla_source_root=str(carla_source_root) if carla_source_root else None,
        carla_package_root=str(carla_package_root) if carla_package_root else None,
        cooked_package_path=str(cooked_package_path) if cooked_package_path else None,
        output_dir=str(output_dir) if output_dir else None,
        capabilities=capabilities,
        commands=commands,
        executed=bool(execution_log),
        execution_log=execution_log,
        blockers=blockers,
        warnings=warnings,
        claim_boundaries=[
            "asset_cook_plan=true",
            f"programmatic_asset_cook_available={'true' if not blockers and selected_mode in {'source', 'docker'} else 'false'}",
            f"cooked_package_import_available={'true' if not blockers and selected_mode == 'import_cooked' else 'false'}",
            "raw_fbx_runtime_import=false",
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
    run_dir: Path | None = None,
    spawn_index: int = 0,
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
    spawned: list[object] = []
    destroyed: list[int] = []
    try:
        carla_module = importlib.import_module("carla")
        client = carla_module.Client(host, port)
        if hasattr(client, "set_timeout"):
            client.set_timeout(timeout_s)
        world = client.get_world()
        blueprints = world.get_blueprint_library()
        blueprint = blueprints.find(blueprint_id)
        spawn_points = list(world.get_map().get_spawn_points())
        if not spawn_points:
            raise RuntimeError("CARLA map has no spawn points.")
        transform = spawn_points[max(0, min(spawn_index, len(spawn_points) - 1))]
        transform = carla_module.Transform(
            carla_module.Location(
                x=float(transform.location.x),
                y=float(transform.location.y),
                z=float(transform.location.z) + 0.15,
            ),
            transform.rotation,
        )
        actor = world.try_spawn_actor(blueprint, transform) if hasattr(world, "try_spawn_actor") else None
        if actor is None:
            actor = world.spawn_actor(blueprint, transform)
        spawned.append(actor)
        screenshot_path = _capture_spawn_screenshot(world, carla_module, actor, run_dir, timeout_s)
        actor_id = int(getattr(actor, "id"))
        return CustomAssetSpawnProof(
            status="passed",
            blueprint_id=blueprint_id,
            connected=True,
            blueprint_registered=True,
            spawned_actor_id=actor_id,
            screenshot_path=str(screenshot_path) if screenshot_path else None,
            claim_boundaries=["arbitrary_mesh_spawn=true", "stock_proxy_fallback=false", "live_spawn_proof_exists=true"],
        )
    except Exception as exc:
        return CustomAssetSpawnProof(
            status="blocked",
            blueprint_id=blueprint_id,
            connected=True,
            blueprint_registered=True,
            blockers=[f"Live custom asset spawn failed: {type(exc).__name__}: {exc}"],
            claim_boundaries=["arbitrary_mesh_spawn=false_until_live_spawn_proof_exists", "stock_proxy_fallback=false"],
        )
    finally:
        for actor in reversed(spawned):
            try:
                actor_id = int(getattr(actor, "id"))
                actor.destroy()
                destroyed.append(actor_id)
            except Exception:
                pass


def spawn_runtime_mesh_path(
    mesh_path: str,
    *,
    host: str = "127.0.0.1",
    port: int = 2000,
    timeout_s: float = 20.0,
    scale: float = 1.0,
    run_dir: Path | None = None,
    spawn_index: int = 0,
    x: float | None = None,
    y: float | None = None,
    z: float | None = None,
    yaw: float = 0.0,
) -> RuntimeMeshSpawnProof:
    blueprint_id = "static.prop.mesh"
    spawned: list[object] = []
    try:
        carla_module = importlib.import_module("carla")
    except ImportError as exc:
        return RuntimeMeshSpawnProof(
            status="blocked",
            mesh_path=mesh_path,
            connected=False,
            scale=scale,
            blockers=[f"CARLA Python package is unavailable: {exc}"],
            claim_boundaries=["runtime_mesh_actor_spawned=false", "custom_mesh_render_visible=false"],
        )
    try:
        client = carla_module.Client(host, port)
        if hasattr(client, "set_timeout"):
            client.set_timeout(timeout_s)
        world = client.get_world()
        blueprints = world.get_blueprint_library()
        matches = [str(item.id) for item in blueprints.filter(blueprint_id)]
        if blueprint_id not in matches:
            return RuntimeMeshSpawnProof(
                status="blocked",
                mesh_path=mesh_path,
                connected=True,
                blueprint_registered=False,
                scale=scale,
                blockers=[f"Runtime mesh blueprint {blueprint_id!r} is not registered in CARLA."],
                claim_boundaries=["runtime_mesh_actor_spawned=false", "custom_mesh_render_visible=false"],
            )
        blueprint = blueprints.find(blueprint_id)
        _set_blueprint_attribute(blueprint, "mesh_path", mesh_path)
        _set_blueprint_attribute(blueprint, "scale", str(scale))
        if x is not None and y is not None:
            transform = carla_module.Transform(
                carla_module.Location(x=float(x), y=float(y), z=float(0.6 if z is None else z)),
                carla_module.Rotation(yaw=float(yaw)),
            )
        else:
            spawn_points = list(world.get_map().get_spawn_points())
            if not spawn_points:
                raise RuntimeError("CARLA map has no spawn points.")
            base = spawn_points[max(0, min(spawn_index, len(spawn_points) - 1))]
            transform = carla_module.Transform(
                carla_module.Location(
                    x=float(base.location.x),
                    y=float(base.location.y),
                    z=float(base.location.z) + 0.2,
                ),
                base.rotation,
            )
        actor = world.try_spawn_actor(blueprint, transform) if hasattr(world, "try_spawn_actor") else None
        if actor is None:
            actor = world.spawn_actor(blueprint, transform)
        spawned.append(actor)
        screenshot_path = _capture_spawn_screenshot(
            world,
            carla_module,
            actor,
            run_dir,
            timeout_s,
            focus_transform=transform,
        )
        return RuntimeMeshSpawnProof(
            status="passed",
            mesh_path=mesh_path,
            connected=True,
            blueprint_registered=True,
            spawned_actor_id=int(getattr(actor, "id")),
            screenshot_path=str(screenshot_path) if screenshot_path else None,
            scale=scale,
            claim_boundaries=[
                "runtime_mesh_actor_spawned=true",
                "custom_mesh_render_visible=requires_visual_qa",
                "raw_mesh_filesystem_import=false_until_visible_live_frame",
            ],
        )
    except Exception as exc:
        return RuntimeMeshSpawnProof(
            status="blocked",
            mesh_path=mesh_path,
            connected=True,
            blueprint_registered=True,
            scale=scale,
            blockers=[f"Runtime mesh spawn failed: {type(exc).__name__}: {exc}"],
            claim_boundaries=["runtime_mesh_actor_spawned=false", "custom_mesh_render_visible=false"],
        )
    finally:
        for actor in reversed(spawned):
            try:
                actor.destroy()
            except Exception:
                pass


def write_asset_package_plan(run_dir: Path, plan: AssetPackagePlan) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    bundle_artifacts = _write_import_bundle(run_dir, plan)
    payload = plan.to_jsonable()
    payload.update(bundle_artifacts)
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


def write_runtime_mesh_spawn_proof(run_dir: Path, proof: RuntimeMeshSpawnProof) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = proof.to_jsonable()
    json_path = run_dir / "runtime_mesh_spawn_proof.json"
    report_path = run_dir / "runtime_mesh_spawn_proof.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown("Runtime Mesh Spawn Proof", payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def write_asset_cook_plan(run_dir: Path, plan: AssetCookPlan) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = plan.to_jsonable()
    json_path = run_dir / "asset_cook_plan.json"
    report_path = run_dir / "asset_cook_plan.md"
    commands_path = run_dir / "asset_cook_commands.sh"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown("Asset Cook Plan", payload), encoding="utf-8")
    commands_path.write_text("\n".join(plan.commands) + "\n", encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path), "commands_path": str(commands_path)}


def custom_asset_run_dir(output_root: Path | None, run_id: str) -> Path:
    return prepare_run_dir(output_root or Path("artifacts/runs"), run_id)


def _capture_spawn_screenshot(
    world: object,
    carla: object,
    actor: object,
    run_dir: Path | None,
    timeout_s: float,
    *,
    focus_transform: object | None = None,
) -> Path | None:
    if run_dir is None:
        return None
    try:
        transform = focus_transform if focus_transform is not None else actor.get_transform()
        camera_bp = world.get_blueprint_library().find("sensor.camera.rgb")
        if hasattr(camera_bp, "set_attribute"):
            camera_bp.set_attribute("image_size_x", "1280")
            camera_bp.set_attribute("image_size_y", "720")
            camera_bp.set_attribute("fov", "80")
        camera_transform = carla.Transform(
            carla.Location(
                x=float(transform.location.x) - 7.0,
                y=float(transform.location.y) - 7.0,
                z=float(transform.location.z) + 4.0,
            ),
            carla.Rotation(pitch=-22.0, yaw=45.0, roll=0.0),
        )
        camera = world.spawn_actor(camera_bp, camera_transform)
        images: "queue.Queue[object]" = queue.Queue()
        camera.listen(images.put)
        try:
            for _ in range(3):
                _tick_world(world, timeout_s)
            image = images.get(timeout=timeout_s)
            path = run_dir / "custom_asset_spawn.png"
            if hasattr(image, "save_to_disk"):
                image.save_to_disk(str(path))
                return path
        finally:
            try:
                camera.destroy()
            except Exception:
                pass
    except Exception:
        return None
    return None


def _tick_world(world: object, timeout_s: float) -> None:
    if hasattr(world, "tick"):
        try:
            world.tick()
            return
        except Exception:
            pass
    try:
        world.wait_for_tick(timeout_s)
    except TypeError:
        world.wait_for_tick()


def _set_blueprint_attribute(blueprint: object, name: str, value: str) -> None:
    if hasattr(blueprint, "has_attribute") and not blueprint.has_attribute(name):
        return
    if hasattr(blueprint, "set_attribute"):
        blueprint.set_attribute(name, value)


def _execute_cooked_package_import(cooked_package_path: Path, carla_package_root: Path) -> list[str]:
    import_dir = carla_package_root / "Import"
    import_dir.mkdir(parents=True, exist_ok=True)
    target = import_dir / cooked_package_path.name
    shutil.copyfile(cooked_package_path, target)
    script = carla_package_root / "ImportAssets.sh"
    if not script.exists():
        script = carla_package_root / "Util" / "ImportAssets.sh"
    result = subprocess.run(
        [str(script)],
        cwd=str(carla_package_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return [f"copied {cooked_package_path} -> {target}", result.stdout, f"exit_code={result.returncode}"]


def _markdown(title: str, payload: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- status: `{payload.get('status')}`",
    ]
    if payload.get("mesh_path") is not None:
        lines.append(f"- mesh path: `{payload.get('mesh_path')}`")
    if payload.get("runtime_mesh_blueprint_id") is not None:
        lines.append(f"- runtime mesh blueprint: `{payload.get('runtime_mesh_blueprint_id')}`")
    if payload.get("expected_blueprint_id") is not None:
        lines.append(f"- expected OODrive alias: `{payload.get('expected_blueprint_id')}`")
    if payload.get("prop_name") is not None:
        lines.append(f"- expected CARLA prop id: `static.prop.{str(payload.get('prop_name', '')).lower()}`")
    if payload.get("import_bundle_path") or payload.get("import_bundle_relpath"):
        lines.append(f"- import bundle: `{payload.get('import_bundle_path') or payload.get('import_bundle_relpath')}`")
    lines.extend(["", "## Host Capability", ""])
    capabilities = payload.get("carla_root_capabilities") or payload.get("capabilities")
    if isinstance(capabilities, dict) and capabilities:
        lines.extend(f"- `{key}`: `{value}`" for key, value in capabilities.items())
    else:
        lines.append("- not probed")
    lines.extend(["", "## Commands", ""])
    lines.extend(f"```bash\n{item}\n```" for item in list(payload.get("commands", [])))
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in list(payload.get("warnings", [])) or ["none"])
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in list(payload.get("blockers", [])) or ["none"])
    return "\n".join(lines) + "\n"


def _write_import_bundle(run_dir: Path, plan: AssetPackagePlan) -> dict[str, Any]:
    bundle_root = run_dir / plan.import_bundle_relpath
    prop_root = bundle_root / "Props" / plan.prop_name
    prop_root.mkdir(parents=True, exist_ok=True)
    copied_fbx: str | None = None
    if plan.fbx_source_path:
        source = Path(plan.fbx_source_path)
        if source.exists():
            target = prop_root / f"{plan.prop_name}.fbx"
            shutil.copyfile(source, target)
            copied_fbx = str(target)
    package_json = bundle_root / plan.package_json_name
    package_payload = {
        "maps": [],
        "props": [
            {
                "name": plan.prop_name,
                "size": _size_from_mesh_name(plan.asset_id),
                "source": f"./Props/{plan.prop_name}/{plan.prop_name}.fbx",
                "tag": "Static",
            }
        ],
    }
    package_json.write_text(json.dumps(package_payload, indent=2), encoding="utf-8")
    readme = bundle_root / "README.md"
    readme.write_text(
        "\n".join(
            [
                f"# {plan.import_package_name}",
                "",
                "This is an OODrive-generated CARLA prop import bundle.",
                "",
                f"- asset id: `{plan.asset_id}`",
                f"- CARLA prop name: `{plan.prop_name}`",
                f"- expected runtime blueprint: `static.prop.{plan.prop_name.lower()}`",
                "",
                "Copy this folder into `$CARLA_ROOT/Import/` on a CARLA source checkout and run `make import`,",
                "or cook it into a standalone package first and unpack it with `ImportAssets.sh` on a packaged simulator.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "import_bundle_path": str(bundle_root),
        "package_json_path": str(package_json),
        "copied_fbx_path": copied_fbx,
    }


def _alternate_formats(payload: dict[str, Any]) -> dict[str, str]:
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        return {}
    alternate = metadata.get("alternate_formats")
    if not isinstance(alternate, dict):
        return {}
    return {str(key): str(value) for key, value in alternate.items() if value}


def _resolve_existing_path(value: object, base_dir: Path) -> Path | None:
    if value is None:
        return None
    path = Path(str(value)).expanduser()
    candidates = [path]
    if not path.is_absolute():
        candidates.append(base_dir / path)
        candidates.append(Path.cwd() / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _safe_unreal_name(value: str) -> str:
    clean = "".join(ch if ch.isalnum() else "_" for ch in value).strip("_")
    if not clean:
        return "OODriveAsset"
    if clean[0].isdigit():
        clean = f"Asset_{clean}"
    return clean


def _safe_package_name(value: str) -> str:
    clean = _safe_unreal_name(value)
    return clean[:64]


def _carla_root_capabilities(carla_root: Path | None) -> dict[str, Any]:
    if carla_root is None:
        return {}
    root = carla_root.expanduser()
    return {
        "path": str(root),
        "exists": root.exists(),
        "has_import_dir": (root / "Import").exists(),
        "has_package_import_assets": (root / "ImportAssets.sh").exists() or (root / "Util" / "ImportAssets.sh").exists(),
        "has_source_make_import": (root / "Makefile").exists(),
        "has_unreal_project": bool(list(root.glob("**/*.uproject"))) if root.exists() else False,
        "has_editor_binary": bool(list(root.glob("**/UE4Editor")) or list(root.glob("**/UnrealEditor"))) if root.exists() else False,
    }


def _size_from_mesh_name(asset_id: str) -> str:
    lower = asset_id.lower()
    if any(token in lower for token in ("crane", "truck", "bus", "bridge")):
        return "huge"
    if any(token in lower for token in ("cart", "barrier", "drum")):
        return "medium"
    return "small"


__all__ = [
    "AssetPackagePlan",
    "AssetCookPlan",
    "BlueprintProbeResult",
    "CustomAssetSpawnProof",
    "RuntimeMeshSpawnProof",
    "build_asset_cook_plan",
    "build_asset_package_plan",
    "custom_asset_run_dir",
    "probe_asset_blueprint",
    "spawn_custom_asset",
    "spawn_runtime_mesh_path",
    "write_asset_package_plan",
    "write_asset_cook_plan",
    "write_blueprint_probe",
    "write_custom_asset_spawn_proof",
    "write_runtime_mesh_spawn_proof",
]
