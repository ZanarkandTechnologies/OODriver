"""Fail2Drive asset catalog and prompt-to-route asset QA."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


BLUEPRINT_RE = re.compile(
    r"\b(?:static\.prop\.[A-Za-z0-9_*.-]+|walker\.animal\.\d+|walker\.pedestrian\.\*|vehicle\.[A-Za-z0-9_*.-]+)\b"
)


@dataclass(frozen=True)
class Fail2DriveAsset:
    blueprint_id: str
    kind: str
    labels: tuple[str, ...]
    sources: tuple[str, ...]
    route_usage_count: int = 0
    installed_content_hint: bool = False

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "kind": self.kind,
            "labels": list(self.labels),
            "sources": list(self.sources),
            "route_usage_count": self.route_usage_count,
            "installed_content_hint": self.installed_content_hint,
        }


@dataclass(frozen=True)
class Fail2DriveAssetCatalog:
    fail2drive_root: Path
    scenario_hub_root: Path | None
    assets: tuple[Fail2DriveAsset, ...]
    content_hints: dict[str, Any]
    source_paths: tuple[str, ...]

    def by_blueprint(self) -> dict[str, Fail2DriveAsset]:
        return {asset.blueprint_id: asset for asset in self.assets}

    def to_jsonable(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for asset in self.assets:
            counts[asset.kind] = counts.get(asset.kind, 0) + 1
        return {
            "schema_version": "oodrive.fail2drive_asset_catalog.v1",
            "fail2drive_root": str(self.fail2drive_root),
            "scenario_hub_root": str(self.scenario_hub_root) if self.scenario_hub_root else None,
            "asset_count": len(self.assets),
            "kind_counts": dict(sorted(counts.items())),
            "assets": [asset.to_jsonable() for asset in self.assets],
            "content_hints": self.content_hints,
            "source_paths": list(self.source_paths),
            "claim_boundaries": [
                "fail2drive_assets_cataloged_from_static_files=true",
                "live_carla_blueprint_probe=false",
                "rendered_visual_asset_detection=false",
            ],
        }


@dataclass(frozen=True)
class AssetRequirement:
    name: str
    expected_kinds: tuple[str, ...] = ()
    expected_blueprints: tuple[str, ...] = ()
    source: str = "prompt"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "expected_kinds": list(self.expected_kinds),
            "expected_blueprints": list(self.expected_blueprints),
            "source": self.source,
        }


@dataclass(frozen=True)
class Fail2DriveAssetQA:
    route_path: Path
    status: str
    prompt: str
    prompt_requirements: tuple[AssetRequirement, ...]
    route_blueprints: tuple[str, ...]
    matched_requirements: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    unknown_route_blueprints: tuple[str, ...]
    evidence_frames: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    claim_boundaries: tuple[str, ...] = field(default_factory=tuple)

    def to_jsonable(self) -> dict[str, Any]:
        visual_status = "provided" if self.evidence_frames else "missing"
        return {
            "schema_version": "oodrive.fail2drive_asset_qa.v1",
            "route_path": str(self.route_path),
            "status": self.status,
            "prompt": self.prompt,
            "prompt_requirements": [item.to_jsonable() for item in self.prompt_requirements],
            "route_blueprints": list(self.route_blueprints),
            "matched_requirements": list(self.matched_requirements),
            "missing_requirements": list(self.missing_requirements),
            "unknown_route_blueprints": list(self.unknown_route_blueprints),
            "evidence_frame_count": len(self.evidence_frames),
            "evidence_frames": list(self.evidence_frames),
            "visual_proof_status": visual_status,
            "blockers": list(self.blockers),
            "claim_boundaries": list(self.claim_boundaries),
        }


def load_fail2drive_asset_catalog(
    root: Path,
    *,
    scenario_hub_root: Path | None = None,
) -> Fail2DriveAssetCatalog:
    fail2drive_root = root.expanduser().resolve()
    hub_root = scenario_hub_root.expanduser().resolve() if scenario_hub_root else None
    entries: dict[str, dict[str, Any]] = {}
    source_paths: list[str] = []

    props_dir = fail2drive_root / "toolbox" / "images" / "carla_props_0.9.15"
    if props_dir.exists():
        source_paths.append(str(props_dir))
        for path in sorted(props_dir.iterdir()):
            if not path.is_file():
                continue
            blueprint = _blueprint_from_prop_preview(path)
            if blueprint:
                _record_asset(entries, blueprint, source=str(path), route_usage=False)

    route_roots = [fail2drive_root / "fail2drive_split"]
    if hub_root and hub_root.exists():
        route_roots.extend(sorted(path for path in hub_root.iterdir() if path.is_dir()))
    for route_root in route_roots:
        for route_path in _route_files(route_root):
            source_paths.append(str(route_path))
            for blueprint in extract_route_blueprints(route_path):
                _record_asset(entries, blueprint, source=str(route_path), route_usage=True)

    scenario_dir = fail2drive_root / "scenario_runner" / "srunner" / "scenarios"
    if scenario_dir.exists():
        source_paths.append(str(scenario_dir))
        for path in sorted(scenario_dir.glob("*.py")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for blueprint in _extract_blueprints(text):
                _record_asset(entries, blueprint, source=str(path), route_usage=False)

    content_hints = _content_hints(fail2drive_root)
    assets = tuple(
        Fail2DriveAsset(
            blueprint_id=blueprint,
            kind=_asset_kind(blueprint),
            labels=tuple(sorted(_labels_for_blueprint(blueprint))),
            sources=tuple(sorted(data["sources"])),
            route_usage_count=int(data["route_usage_count"]),
            installed_content_hint=_installed_hint(blueprint, content_hints),
        )
        for blueprint, data in sorted(entries.items())
    )
    return Fail2DriveAssetCatalog(
        fail2drive_root=fail2drive_root,
        scenario_hub_root=hub_root,
        assets=assets,
        content_hints=content_hints,
        source_paths=tuple(sorted(set(source_paths))),
    )


def write_fail2drive_asset_catalog_report(
    run_dir: Path,
    catalog: Fail2DriveAssetCatalog,
    *,
    fmt: str = "both",
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = catalog.to_jsonable()
    result: dict[str, Any] = {**payload}
    if fmt in ("json", "both"):
        json_path = run_dir / "fail2drive_asset_catalog.json"
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        result["json_path"] = str(json_path)
    if fmt in ("md", "markdown", "both"):
        report_path = run_dir / "fail2drive_asset_catalog.md"
        report_path.write_text(_asset_catalog_markdown(catalog), encoding="utf-8")
        result["report_path"] = str(report_path)
    return result


def qa_fail2drive_route_assets(
    route_path: Path,
    *,
    prompt: str,
    catalog: Fail2DriveAssetCatalog,
    evidence_frames: tuple[Path, ...] = (),
    required_assets: tuple[str, ...] = (),
) -> Fail2DriveAssetQA:
    route_file = route_path.expanduser().resolve()
    route_blueprints = tuple(sorted(set(extract_route_blueprints(route_file)))) if route_file.exists() else ()
    route_set = set(route_blueprints)
    catalog_by_blueprint = catalog.by_blueprint()
    requirements = tuple([*_requirements_from_prompt(prompt), *(_manual_requirement(item) for item in required_assets)])
    matched: list[str] = []
    missing: list[str] = []
    for requirement in requirements:
        if _requirement_matches_route(requirement, route_set):
            matched.append(requirement.name)
        else:
            missing.append(requirement.name)
    unknown = tuple(sorted(blueprint for blueprint in route_set if blueprint not in catalog_by_blueprint))
    frame_paths = tuple(str(path) for path in evidence_frames if path.exists())
    blockers: list[str] = []
    if not route_file.exists():
        blockers.append(f"Route XML not found: {route_file}")
    if missing:
        blockers.append("Prompt-required assets are missing from route XML: " + ", ".join(missing))
    if unknown:
        blockers.append("Route references blueprints not found in asset catalog: " + ", ".join(unknown))
    if evidence_frames and len(frame_paths) != len(evidence_frames):
        blockers.append("One or more evidence frame paths do not exist.")
    if not frame_paths:
        blockers.append("Rendered visual evidence frame is missing; route/catalog proof only.")
    status = "passed" if not blockers else "blocked"
    return Fail2DriveAssetQA(
        route_path=route_file,
        status=status,
        prompt=prompt,
        prompt_requirements=requirements,
        route_blueprints=route_blueprints,
        matched_requirements=tuple(sorted(matched)),
        missing_requirements=tuple(sorted(missing)),
        unknown_route_blueprints=unknown,
        evidence_frames=frame_paths,
        blockers=tuple(blockers),
        claim_boundaries=(
            "route_asset_xml_alignment=true",
            "fail2drive_asset_catalog_static_scan=true",
            "live_carla_blueprint_probe=false",
            "rendered_visual_asset_detection=false",
            f"rendered_visual_evidence_provided={'true' if frame_paths else 'false'}",
        ),
    )


def write_fail2drive_asset_qa(run_dir: Path, qa: Fail2DriveAssetQA) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = qa.to_jsonable()
    json_path = run_dir / "fail2drive_asset_qa.json"
    report_path = run_dir / "fail2drive_asset_qa.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_asset_qa_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def extract_route_blueprints(route_path: Path) -> tuple[str, ...]:
    if not route_path.exists():
        return ()
    try:
        root = ET.parse(route_path).getroot()
    except ET.ParseError:
        text = route_path.read_text(encoding="utf-8", errors="ignore")
        return tuple(sorted(set(_extract_blueprints(text))))
    blueprints: set[str] = set()
    for elem in root.iter():
        for value in elem.attrib.values():
            blueprints.update(_extract_blueprints(value))
        if elem.text:
            blueprints.update(_extract_blueprints(elem.text))
    return tuple(sorted(blueprints))


def _record_asset(entries: dict[str, dict[str, Any]], blueprint: str, *, source: str, route_usage: bool) -> None:
    entry = entries.setdefault(blueprint, {"sources": set(), "route_usage_count": 0})
    entry["sources"].add(source)
    if route_usage:
        entry["route_usage_count"] += 1


def _route_files(root: Path) -> tuple[Path, ...]:
    if not root.exists():
        return ()
    if root.name == "routes":
        return tuple(sorted(root.glob("*.xml")))
    return tuple(sorted([*root.glob("*.xml"), *root.glob("**/routes/*.xml")]))


def _blueprint_from_prop_preview(path: Path) -> str | None:
    stem = path.stem
    if not stem.startswith("static_prop_"):
        return None
    clean = stem.removeprefix("static_prop_").lower()
    if clean.startswith("screenshot"):
        return None
    return f"static.prop.{clean}"


def _extract_blueprints(text: str) -> tuple[str, ...]:
    return tuple(sorted(set(match.group(0).strip(".,;:'\"") for match in BLUEPRINT_RE.finditer(text))))


def _asset_kind(blueprint: str) -> str:
    if blueprint.startswith("walker.animal."):
        return "animal_walker"
    if blueprint.startswith("walker.pedestrian"):
        return "pedestrian_walker"
    if blueprint.startswith("vehicle."):
        return "vehicle"
    if blueprint.startswith("static.prop."):
        return "static_prop"
    return "unknown"


def _labels_for_blueprint(blueprint: str) -> set[str]:
    labels = {_asset_kind(blueprint)}
    suffix = blueprint.split(".")[-1].lower()
    labels.update(part for part in re.split(r"[_\-.]+", suffix) if part)
    if blueprint.startswith("walker.animal."):
        labels.add("animal")
    if "haybale" in suffix:
        labels.update({"hay", "haybale", "farm"})
    if "warningaccident" in suffix:
        labels.update({"accident", "warning"})
    if "foodcart" in suffix:
        labels.update({"food_cart", "vendor", "stall"})
    if "barrier" in suffix or "cone" in suffix:
        labels.update({"barrier", "roadblock"})
    if "debris" in suffix or "garbage" in suffix or "trash" in suffix:
        labels.update({"debris", "trash"})
    return labels


def _content_hints(root: Path) -> dict[str, Any]:
    content = root / "f2d_carla" / "CarlaUE4" / "Content"
    animal_dirs = sorted(
        path.name
        for parent in (content / "FarmAnimalsPack", content / "AnimalVarietyPack")
        if parent.exists()
        for path in parent.iterdir()
        if path.is_dir()
    )
    return {
        "fail2drive_carla_content_exists": content.exists(),
        "animal_content_families": animal_dirs,
        "stock_props_preview_exists": (root / "toolbox" / "images" / "carla_props_0.9.15").exists(),
        "carla_blueprint_probe_required_for_runtime_truth": True,
    }


def _installed_hint(blueprint: str, content_hints: dict[str, Any]) -> bool:
    if blueprint.startswith("walker.animal."):
        return bool(content_hints.get("animal_content_families"))
    if blueprint.startswith("static.prop."):
        return bool(content_hints.get("stock_props_preview_exists"))
    if blueprint.startswith(("vehicle.", "walker.pedestrian.")):
        return bool(content_hints.get("fail2drive_carla_content_exists"))
    return False


def _requirements_from_prompt(prompt: str) -> list[AssetRequirement]:
    text = prompt.lower()
    requirements: list[AssetRequirement] = []
    checks = [
        (("animal", "deer", "cow", "sheep", "goat", "pig", "fox", "wolf", "chicken"), AssetRequirement("animal", expected_kinds=("animal_walker",))),
        (("hay", "haybale", "hay bale"), AssetRequirement("haybale", expected_blueprints=("static.prop.haybale", "static.prop.haybalelb"))),
        (("food cart", "vendor", "stall", "roadside cart"), AssetRequirement("food_cart", expected_blueprints=("static.prop.foodcart",))),
        (("roadblock", "road block", "blocked", "barrier"), AssetRequirement("roadblock", expected_blueprints=("static.prop.streetbarrier", "static.prop.constructioncone", "static.prop.chainbarrier"), expected_kinds=("vehicle", "static_prop"))),
        (("debris", "trash", "garbage", "plastic bag", "fallen object"), AssetRequirement("debris", expected_blueprints=("static.prop.dirtdebris01", "static.prop.dirtdebris02", "static.prop.dirtdebris03", "static.prop.trashbag", "static.prop.garbage01"), expected_kinds=("static_prop",))),
        (("accident", "crash", "collision"), AssetRequirement("accident", expected_blueprints=("static.prop.warningaccident",), expected_kinds=("vehicle",))),
        (("pedestrian", "person", "people", "crowd"), AssetRequirement("pedestrian", expected_kinds=("pedestrian_walker",))),
        (("vehicle", "car", "jeep", "truck", "van"), AssetRequirement("vehicle", expected_kinds=("vehicle",))),
    ]
    for needles, requirement in checks:
        if any(needle in text for needle in needles):
            requirements.append(requirement)
    return requirements


def _manual_requirement(value: str) -> AssetRequirement:
    if "." in value:
        return AssetRequirement(value, expected_blueprints=(value,), source="manual")
    return AssetRequirement(value, expected_kinds=(value,), source="manual")


def _requirement_matches_route(requirement: AssetRequirement, route_blueprints: set[str]) -> bool:
    for expected in requirement.expected_blueprints:
        if expected in route_blueprints:
            return True
    for blueprint in route_blueprints:
        if _asset_kind(blueprint) in requirement.expected_kinds:
            return True
    return False


def _asset_catalog_markdown(catalog: Fail2DriveAssetCatalog) -> str:
    lines = [
        "# Fail2Drive Asset Catalog",
        "",
        f"- assets: `{len(catalog.assets)}`",
        f"- fail2drive_root: `{catalog.fail2drive_root}`",
        f"- scenario_hub_root: `{catalog.scenario_hub_root}`",
        f"- animal families: `{', '.join(catalog.content_hints.get('animal_content_families', []))}`",
        "",
        "| blueprint | kind | usage | installed hint | labels |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for asset in catalog.assets:
        lines.append(
            f"| `{asset.blueprint_id}` | {asset.kind} | {asset.route_usage_count} | "
            f"{asset.installed_content_hint} | {', '.join(asset.labels[:8])} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _asset_qa_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Fail2Drive Asset QA",
        "",
        f"- status: `{payload.get('status')}`",
        f"- route: `{payload.get('route_path')}`",
        f"- visual proof: `{payload.get('visual_proof_status')}`",
        f"- evidence frames: `{payload.get('evidence_frame_count')}`",
        "",
        "## Requirements",
    ]
    for req in payload.get("prompt_requirements", []):
        if isinstance(req, dict):
            lines.append(f"- `{req.get('name')}`")
    lines.append("")
    lines.append("## Route Blueprints")
    for blueprint in payload.get("route_blueprints", []):
        lines.append(f"- `{blueprint}`")
    blockers = payload.get("blockers", [])
    if blockers:
        lines.append("")
        lines.append("## Blockers")
        for blocker in blockers:
            lines.append(f"- {blocker}")
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "AssetRequirement",
    "Fail2DriveAsset",
    "Fail2DriveAssetCatalog",
    "Fail2DriveAssetQA",
    "extract_route_blueprints",
    "load_fail2drive_asset_catalog",
    "qa_fail2drive_route_assets",
    "write_fail2drive_asset_catalog_report",
    "write_fail2drive_asset_qa",
]
