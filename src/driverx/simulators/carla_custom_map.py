"""Custom CARLA map import manifests, validation, and load probes."""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir

CUSTOM_MAP_SCHEMA_VERSION = "oodrive.custom_map_import.v1"


@dataclass(frozen=True)
class CustomMapImportManifest:
    status: str
    map_name: str
    geometry_fbx: str
    opendrive_xodr: str
    import_mode: str
    commands: list[str]
    blockers: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": CUSTOM_MAP_SCHEMA_VERSION,
            "status": self.status,
            "map_name": self.map_name,
            "geometry_fbx": self.geometry_fbx,
            "opendrive_xodr": self.opendrive_xodr,
            "import_mode": self.import_mode,
            "commands": self.commands,
            "blockers": self.blockers,
            "claim_boundaries": self.claim_boundaries,
        }


@dataclass(frozen=True)
class CustomMapValidation:
    status: str
    manifest_path: str
    blockers: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": CUSTOM_MAP_SCHEMA_VERSION,
            "status": self.status,
            "manifest_path": self.manifest_path,
            "blockers": self.blockers,
            "claim_boundaries": self.claim_boundaries,
        }


@dataclass(frozen=True)
class CarlaMapProbe:
    status: str
    map_name: str
    connected: bool
    available_maps: list[str] = field(default_factory=list)
    map_loaded: bool = False
    blockers: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": "oodrive.carla_map_probe.v1",
            "status": self.status,
            "map_name": self.map_name,
            "connected": self.connected,
            "available_maps": self.available_maps,
            "map_loaded": self.map_loaded,
            "blockers": self.blockers,
            "claim_boundaries": self.claim_boundaries,
        }


def prepare_custom_map_import(
    *,
    fbx_path: Path,
    xodr_path: Path,
    map_name: str,
    import_mode: str = "package",
) -> CustomMapImportManifest:
    blockers: list[str] = []
    if not map_name.strip():
        blockers.append("Map name is required.")
    if import_mode not in {"package", "source_build", "manual_unreal"}:
        blockers.append(f"Unsupported import mode: {import_mode}")
    commands = [
        "# CARLA custom maps require Unreal/CARLA packaging; this is an import plan, not runtime generation.",
        f"# geometry: {fbx_path}",
        f"# OpenDRIVE: {xodr_path}",
        f"# target map: {map_name}",
    ]
    if import_mode == "package":
        commands.append(f"ImportAssets.sh --package --map-name {map_name} --fbx {fbx_path} --xodr {xodr_path}")
    elif import_mode == "source_build":
        commands.append(f"make import ARGS='--map {map_name} --fbx {fbx_path} --xodr {xodr_path}'")
    else:
        commands.append("Open Unreal Editor, import FBX/OpenDRIVE, cook/package CARLA map, then probe with oodrive carla-map-probe.")
    claims = [
        "custom_map_import_manifest=true",
        "custom_unreal_map_import=false_until_carla_map_probe_passes",
        "runtime_prompt_generated_city=false",
    ]
    return CustomMapImportManifest(
        status="passed" if not blockers else "blocked",
        map_name=map_name,
        geometry_fbx=str(fbx_path),
        opendrive_xodr=str(xodr_path),
        import_mode=import_mode,
        commands=commands,
        blockers=blockers,
        claim_boundaries=claims,
    )


def validate_custom_map_import(manifest_path: Path) -> CustomMapValidation:
    blockers: list[str] = []
    if not manifest_path.exists():
        blockers.append(f"Custom map manifest not found: {manifest_path}")
        payload: dict[str, Any] = {}
    else:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    fbx = Path(str(payload.get("geometry_fbx", "")))
    xodr = Path(str(payload.get("opendrive_xodr", "")))
    if not fbx.exists():
        blockers.append(f"FBX geometry file not found: {fbx}")
    if fbx.suffix.lower() != ".fbx":
        blockers.append("Geometry file must use .fbx suffix.")
    if not xodr.exists():
        blockers.append(f"OpenDRIVE file not found: {xodr}")
    if xodr.suffix.lower() != ".xodr":
        blockers.append("OpenDRIVE file must use .xodr suffix.")
    if xodr.exists() and "<OpenDRIVE" not in xodr.read_text(encoding="utf-8", errors="ignore"):
        blockers.append("OpenDRIVE file does not contain an <OpenDRIVE> root marker.")
    if not str(payload.get("map_name", "")).strip():
        blockers.append("Map name is required.")
    claims = [
        "custom_map_import_manifest=true",
        f"custom_map_import_validated={'true' if not blockers else 'false'}",
        "custom_unreal_map_import=false_until_carla_map_probe_passes",
    ]
    return CustomMapValidation(
        status="passed" if not blockers else "blocked",
        manifest_path=str(manifest_path),
        blockers=blockers,
        claim_boundaries=claims,
    )


def probe_carla_map(
    *,
    map_name: str,
    host: str = "127.0.0.1",
    port: int = 2000,
    timeout_s: float = 20.0,
    carla_module: object | None = None,
) -> CarlaMapProbe:
    if carla_module is None:
        try:
            carla_module = importlib.import_module("carla")
        except ImportError as exc:
            return CarlaMapProbe(
                status="blocked",
                map_name=map_name,
                connected=False,
                blockers=[f"CARLA Python package is unavailable: {exc}"],
                claim_boundaries=["custom_unreal_map_import=false"],
            )
    try:
        client = carla_module.Client(host, port)
        if hasattr(client, "set_timeout"):
            client.set_timeout(timeout_s)
        available = [str(item) for item in client.get_available_maps()]
        loaded = False
        if any(item.endswith(map_name) or item == map_name for item in available):
            world = client.load_world(map_name)
            loaded = str(getattr(world.get_map(), "name", "")).endswith(map_name)
        blockers = [] if loaded else [f"Map {map_name!r} is not available/loadable in this CARLA install."]
        return CarlaMapProbe(
            status="passed" if loaded else "blocked",
            map_name=map_name,
            connected=True,
            available_maps=available,
            map_loaded=loaded,
            blockers=blockers,
            claim_boundaries=[
                f"custom_unreal_map_import={'true' if loaded else 'false'}",
                "carla_existing_map_composition=true",
            ],
        )
    except Exception as exc:
        return CarlaMapProbe(
            status="blocked",
            map_name=map_name,
            connected=False,
            blockers=[f"CARLA map probe failed: {exc}"],
            claim_boundaries=["custom_unreal_map_import=false"],
        )


def write_custom_map_import(run_dir: Path, manifest: CustomMapImportManifest) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = manifest.to_jsonable()
    json_path = run_dir / "custom_map_import_manifest.json"
    report_path = run_dir / "custom_map_import_report.md"
    commands_path = run_dir / "custom_map_import_commands.sh"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown("Custom Map Import", payload), encoding="utf-8")
    commands_path.write_text("\n".join(manifest.commands) + "\n", encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path), "commands_path": str(commands_path)}


def write_custom_map_validation(run_dir: Path, validation: CustomMapValidation) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = validation.to_jsonable()
    json_path = run_dir / "custom_map_validation.json"
    report_path = run_dir / "custom_map_validation.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown("Custom Map Validation", payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def write_carla_map_probe(run_dir: Path, probe: CarlaMapProbe) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = probe.to_jsonable()
    json_path = run_dir / "carla_map_probe.json"
    report_path = run_dir / "carla_map_probe.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown("CARLA Map Probe", payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def custom_map_run_dir(output_root: Path | None, run_id: str) -> Path:
    return prepare_run_dir(output_root or Path("artifacts/runs"), run_id)


def _markdown(title: str, payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"- status: `{payload.get('status')}`",
            f"- map: `{payload.get('map_name')}`",
            "",
            "## Blockers",
            *([f"- {item}" for item in list(payload.get("blockers", []))] or ["- none"]),
        ]
    ) + "\n"


__all__ = [
    "CarlaMapProbe",
    "CustomMapImportManifest",
    "CustomMapValidation",
    "custom_map_run_dir",
    "prepare_custom_map_import",
    "probe_carla_map",
    "validate_custom_map_import",
    "write_carla_map_probe",
    "write_custom_map_import",
    "write_custom_map_validation",
]
