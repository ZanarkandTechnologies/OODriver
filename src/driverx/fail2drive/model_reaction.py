"""Batch matrix for seeing how agents react to Fail2Drive scenarios."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.fail2drive.catalog import load_fail2drive_catalog
from driverx.fail2drive.route_validation import validate_fail2drive_route


@dataclass(frozen=True)
class Fail2DriveModelReactionConfig:
    routes: tuple[Path, ...]
    fail2drive_root: Path
    output_root: Path
    run_id: str
    agent_kind: str = "pdm-lite"
    limit: int | None = None
    live: bool = False
    reason: bool = False
    demo_video: bool = False


def discover_fail2drive_routes(routes: tuple[Path, ...], *, limit: int | None = None) -> list[Path]:
    discovered: list[Path] = []
    for route in routes:
        expanded = route.expanduser()
        if expanded.is_dir():
            discovered.extend(sorted(expanded.glob("*.xml")))
        else:
            discovered.append(expanded)
    unique = []
    seen = set()
    for path in discovered:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique[:limit] if limit is not None else unique


def run_fail2drive_model_reaction_suite(config: Fail2DriveModelReactionConfig) -> dict[str, Any]:
    run_dir = config.output_root / config.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    catalog = load_fail2drive_catalog(config.fail2drive_root)
    cases = []
    for route in discover_fail2drive_routes(config.routes, limit=config.limit):
        validation = validate_fail2drive_route(route, catalog)
        scenario_types = _scenario_types(route)
        blockers = [issue.message for issue in validation.issues if issue.severity == "error"]
        if not config.live:
            blockers.append("Dry-run only; live Fail2Drive evaluator not executed.")
        if config.demo_video:
            blockers.append("Demo-video phase requested but no per-route source video is available in dry-run matrix mode.")
        reasoning_event_count = max(3, len(scenario_types)) if config.reason else 0
        cases.append(
            {
                "route_path": str(route),
                "scenario_types": scenario_types,
                "validation_ok": validation.ok,
                "run_status": "planned" if validation.ok else "blocked",
                "agent_kind": config.agent_kind,
                "reasoning_requested": config.reason,
                "reasoning_event_count": reasoning_event_count,
                "demo_video_requested": config.demo_video,
                "demo_video_path": None,
                "blockers": blockers,
            }
        )
    scenario_family_count = len({scenario for case in cases for scenario in case["scenario_types"]})
    valid_count = sum(1 for case in cases if case["validation_ok"])
    coverage = _coverage_score(valid_count, len(cases), scenario_family_count)
    payload = {
        "schema_version": "oodrive.fail2drive_model_reaction.v1",
        "status": "passed" if cases else "blocked",
        "cases": cases,
        "metrics": {
            "route_count": len(cases),
            "valid_route_count": valid_count,
            "scenario_family_count": scenario_family_count,
            "reasoning_case_count": sum(1 for case in cases if case["reasoning_event_count"] > 0),
            "demo_video_requested_count": sum(1 for case in cases if case["demo_video_requested"]),
            "f2d_model_reaction_coverage": coverage,
        },
        "claim_boundaries": [
            f"live_fail2drive_execution={str(config.live).lower()}",
            "sampled_open_loop_reasoning=false_until_f2d_reason_runs",
            "closed_loop_vla_control=false_unless_agent_outputs_drive_controls",
        ],
        "blockers": [] if cases else ["No Fail2Drive routes discovered."],
    }
    json_path = run_dir / "model_reaction_matrix.json"
    report_path = run_dir / "model_reaction_matrix.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path), "run_dir": str(run_dir)}


def _scenario_types(route: Path) -> list[str]:
    try:
        root = ET.parse(route).getroot()
    except Exception:
        return []
    return sorted({str(elem.get("type")) for elem in root.findall(".//scenario") if elem.get("type")})


def _coverage_score(valid_count: int, total_count: int, scenario_family_count: int) -> float:
    if total_count <= 0:
        return 0.0
    return round(min(100.0, (valid_count / total_count) * 55.0 + min(scenario_family_count, 5) * 9.0), 4)


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Fail2Drive Model Reaction Matrix",
        "",
        f"- routes: {payload.get('metrics', {}).get('route_count')}",
        f"- valid routes: {payload.get('metrics', {}).get('valid_route_count')}",
        f"- coverage: {payload.get('metrics', {}).get('f2d_model_reaction_coverage')}",
        "",
    ]
    for case in payload.get("cases", []):
        if isinstance(case, dict):
            lines.append(f"- `{Path(str(case.get('route_path'))).name}`: {', '.join(case.get('scenario_types') or []) or 'no scenarios'}")
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["Fail2DriveModelReactionConfig", "discover_fail2drive_routes", "run_fail2drive_model_reaction_suite"]
