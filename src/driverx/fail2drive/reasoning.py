"""Sampled open-loop reasoning timeline for Fail2Drive evidence."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Fail2DriveReasoningRequest:
    evidence_path: Path
    route_path: Path
    output_root: Path
    run_id: str
    mode: str = "fake"
    keyframes: int = 6
    cached_reasoning_path: Path | None = None


def run_fail2drive_reasoning(request: Fail2DriveReasoningRequest) -> dict[str, Any]:
    run_dir = request.output_root / request.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    evidence = _load_optional_json(request.evidence_path)
    scenarios = _route_scenarios(request.route_path)
    cached = _load_optional_json(request.cached_reasoning_path)
    events = _cached_events(cached) or _fake_events(scenarios, max(3, request.keyframes), request.mode)
    payload = {
        "schema_version": "oodrive.fail2drive_reasoning.v1",
        "status": "passed" if events else "blocked",
        "mode": request.mode,
        "evidence_path": str(request.evidence_path),
        "route_path": str(request.route_path),
        "scenario_types": sorted({str(item.get("type")) for item in scenarios if item.get("type")}),
        "events": events,
        "metrics": {
            "reasoning_event_count": len(events),
            "scenario_context_count": len({event.get("route_scenario") for event in events if event.get("route_scenario")}),
            "latency_ms_p50": _median([float(event.get("latency_ms", 0.0)) for event in events if event.get("latency_ms") is not None]),
        },
        "source_evidence_status": evidence.get("status"),
        "claim_boundaries": [
            "sampled_open_loop_reasoning=true",
            "time_warped_offline_demo=true",
            "closed_loop_vla_control=false",
            "real_time_vla_control=false",
            f"reasoning_source={request.mode}",
        ],
        "blockers": [] if events else ["No reasoning events could be produced."],
    }
    json_path = run_dir / "f2d_reasoning.json"
    report_path = run_dir / "f2d_reasoning.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path), "run_dir": str(run_dir)}


def _fake_events(scenarios: list[dict[str, Any]], count: int, mode: str) -> list[dict[str, Any]]:
    if not scenarios:
        scenarios = [{"type": "UnknownRouteHazard", "name": "route_hazard"}]
    events = []
    for index in range(count):
        scenario = scenarios[index % len(scenarios)]
        scenario_type = str(scenario.get("type") or "UnknownRouteHazard")
        risk = "critical" if scenario_type in {"RoadBlocked", "Accident", "DynamicObjectCrossing", "PedestrianCrowd"} else "elevated"
        action = _action_for_scenario(scenario_type)
        events.append(
            {
                "frame_index": index * 12,
                "source_time_s": round(index * 1.25, 3),
                "route_scenario": scenario_type,
                "risk_level": risk,
                "observation": _observation_for_scenario(scenario_type),
                "predicted_action": action,
                "rationale": f"Fail2Drive {scenario_type} stresses minimal-shot hazard reasoning; safest response is {action}.",
                "memory_callout": f"Retrieved rule: handle {scenario_type} by prioritizing clearance, lane discipline, and time-to-collision.",
                "latency_ms": 0.0 if mode == "fake" else None,
                "source": mode,
            }
        )
    return events


def _cached_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
    events = payload.get("events")
    return [dict(event) for event in events] if isinstance(events, list) else []


def _route_scenarios(route_path: Path) -> list[dict[str, Any]]:
    try:
        root = ET.parse(route_path.expanduser()).getroot()
    except Exception:
        return []
    scenarios = []
    for scenario in root.findall(".//scenario"):
        scenarios.append({"name": scenario.get("name"), "type": scenario.get("type")})
    return scenarios


def _action_for_scenario(scenario_type: str) -> str:
    if "Crossing" in scenario_type or "Pedestrian" in scenario_type:
        return "slow down and yield until crossing path is clear"
    if "RoadBlocked" in scenario_type or "Obstacle" in scenario_type:
        return "brake, hold lane, then seek a safe gap or detour"
    if "Accident" in scenario_type:
        return "slow early and prepare a controlled lane change"
    return "reduce speed and preserve a conservative following gap"


def _observation_for_scenario(scenario_type: str) -> str:
    if "RoadBlocked" in scenario_type:
        return "The route ahead is physically blocked by an object cluster."
    if "DynamicObjectCrossing" in scenario_type:
        return "A moving actor may enter the ego lane from an occluded roadside area."
    if "Accident" in scenario_type:
        return "An accident scene creates unpredictable blockage and debris risk."
    if "Pedestrian" in scenario_type:
        return "Pedestrians occupy or approach the drivable corridor."
    return "The scenario introduces a rare interaction requiring defensive control."


def _load_optional_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    expanded = path.expanduser()
    if not expanded.exists():
        return {}
    payload = json.loads(expanded.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Fail2Drive Reasoning",
        "",
        f"- status: {payload.get('status')}",
        f"- mode: {payload.get('mode')}",
        f"- events: {payload.get('metrics', {}).get('reasoning_event_count')}",
        "",
    ]
    for event in payload.get("events", [])[:8]:
        if isinstance(event, dict):
            lines.append(f"- t={event.get('source_time_s')}s `{event.get('route_scenario')}`: {event.get('predicted_action')}")
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["Fail2DriveReasoningRequest", "run_fail2drive_reasoning"]
