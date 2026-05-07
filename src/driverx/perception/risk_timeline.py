"""Build risk timelines from CARLA simulator ground-truth actor tracks."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EntityTrackPoint:
    actor_ref: str
    actor_id: int | None
    type_id: str
    tick: int
    t_s: float
    location: dict[str, float]
    rotation: dict[str, float]
    velocity: dict[str, float]

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "EntityTrackPoint":
        return cls(
            actor_ref=str(payload.get("actor_ref", "")),
            actor_id=_optional_int(payload.get("actor_id")),
            type_id=str(payload.get("type_id", "")),
            tick=int(payload.get("tick", 0)),
            t_s=float(payload.get("t_s", payload.get("time_s", 0.0))),
            location=_float_map(payload.get("location")),
            rotation=_float_map(payload.get("rotation")),
            velocity=_float_map(payload.get("velocity")),
        )


@dataclass(frozen=True)
class RiskTimelineConfig:
    scenario_id: str | None = None
    behavior_id: str | None = None
    front_width_m: float = 4.0
    side_width_m: float = 8.0
    max_event_distance_m: float = 35.0
    critical_distance_m: float = 5.0
    high_distance_m: float = 10.0
    medium_distance_m: float = 18.0


@dataclass(frozen=True)
class RiskTimeline:
    scenario_id: str | None
    behavior_id: str | None
    tick_count: int
    actor_count: int
    event_count: int
    max_risk_level: str
    nearest_event: dict[str, Any] | None
    events: list[dict[str, Any]]
    tick_summaries: list[dict[str, Any]]
    claim_boundaries: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "behavior_id": self.behavior_id,
            "tick_count": self.tick_count,
            "actor_count": self.actor_count,
            "event_count": self.event_count,
            "max_risk_level": self.max_risk_level,
            "nearest_event": self.nearest_event,
            "events": self.events,
            "tick_summaries": self.tick_summaries,
            "claim_boundaries": self.claim_boundaries,
        }


def load_entity_tracks(path: Path) -> list[EntityTrackPoint]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected entity track list in {path}")
    return [EntityTrackPoint.from_jsonable(item) for item in payload if isinstance(item, dict)]


def build_risk_timeline(tracks: list[EntityTrackPoint], config: RiskTimelineConfig) -> RiskTimeline:
    by_tick = _group_by_tick(tracks)
    actor_refs = {track.actor_ref for track in tracks if track.actor_ref}
    events: list[dict[str, Any]] = []
    tick_summaries: list[dict[str, Any]] = []
    for tick in sorted(by_tick):
        records = by_tick[tick]
        ego = next((track for track in records if track.actor_ref == "ego"), None)
        if ego is None:
            continue
        tick_events = [
            _risk_event(track, ego, config)
            for track in records
            if track.actor_ref not in {"ego", "ego_rgb"}
        ]
        tick_events = [
            event
            for event in tick_events
            if event["distance_m"] <= config.max_event_distance_m or event["risk_level"] in {"critical", "high"}
        ]
        tick_events.sort(key=lambda item: (item["distance_m"], _zone_priority(item["zone"]), item["actor_ref"]))
        nearest = tick_events[0] if tick_events else None
        front = next((event for event in tick_events if event["zone"].startswith("front")), None)
        if nearest:
            events.extend(tick_events)
        tick_summaries.append(
            {
                "tick": tick,
                "time_s": round(ego.t_s, 3),
                "nearest_actor": nearest,
                "front_hazard": front,
                "event_count": len(tick_events),
            }
        )
    deduped_events = _dedupe_events(events)
    nearest_event = min(deduped_events, key=lambda item: item["distance_m"], default=None)
    max_risk_level = _max_risk_level(deduped_events)
    return RiskTimeline(
        scenario_id=config.scenario_id,
        behavior_id=config.behavior_id,
        tick_count=len(by_tick),
        actor_count=len(actor_refs),
        event_count=len(deduped_events),
        max_risk_level=max_risk_level,
        nearest_event=nearest_event,
        events=deduped_events,
        tick_summaries=tick_summaries,
        claim_boundaries=[
            "simulator_ground_truth_tracks=true",
            "image_based_object_detection=false",
            "risk_timeline_for_demo_explanation=true",
        ],
    )


def write_risk_timeline(run_dir: Path, timeline: RiskTimeline) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = timeline.to_jsonable()
    json_path = run_dir / "risk_timeline.json"
    markdown_path = run_dir / "risk_timeline.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(_timeline_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(markdown_path)}


def _risk_event(track: EntityTrackPoint, ego: EntityTrackPoint, config: RiskTimelineConfig) -> dict[str, Any]:
    forward_m, lateral_m = _ego_relative(track, ego)
    distance_m = _distance(track.location, ego.location)
    relative_speed_mps = _relative_speed(track, ego)
    zone = _zone(forward_m, lateral_m, config)
    risk_label = _risk_label(track, zone, distance_m, config)
    risk_level = _risk_level(distance_m, zone, config)
    memory_query = _memory_query(track, zone, risk_label, config)
    return {
        "tick": track.tick,
        "time_s": round(track.t_s, 3),
        "actor_ref": track.actor_ref,
        "actor_id": track.actor_id,
        "type_id": track.type_id,
        "zone": zone,
        "distance_m": round(distance_m, 3),
        "forward_m": round(forward_m, 3),
        "lateral_m": round(lateral_m, 3),
        "relative_speed_mps": round(relative_speed_mps, 3),
        "risk_label": risk_label,
        "risk_level": risk_level,
        "memory_query": memory_query,
        "recommended_behavior": _recommended_behavior(risk_label, risk_level, zone),
    }


def _ego_relative(track: EntityTrackPoint, ego: EntityTrackPoint) -> tuple[float, float]:
    dx = track.location.get("x", 0.0) - ego.location.get("x", 0.0)
    dy = track.location.get("y", 0.0) - ego.location.get("y", 0.0)
    yaw = math.radians(ego.rotation.get("yaw", 0.0))
    forward = math.cos(yaw) * dx + math.sin(yaw) * dy
    lateral = -math.sin(yaw) * dx + math.cos(yaw) * dy
    return forward, lateral


def _zone(forward_m: float, lateral_m: float, config: RiskTimelineConfig) -> str:
    half_front = config.front_width_m / 2.0
    half_side = config.side_width_m / 2.0
    if forward_m >= 0 and abs(lateral_m) <= half_front:
        return "front"
    if forward_m >= 0 and 0 < lateral_m <= half_side:
        return "front_left"
    if forward_m >= 0 and -half_side <= lateral_m < 0:
        return "front_right"
    if abs(lateral_m) <= half_side:
        return "behind"
    return "side_left" if lateral_m > 0 else "side_right"


def _risk_label(track: EntityTrackPoint, zone: str, distance_m: float, config: RiskTimelineConfig) -> str:
    text = f"{track.actor_ref} {track.type_id} {config.behavior_id or ''}".lower()
    if "motorcycle" in text or "kawasaki" in text or "ninja" in text:
        return "motorcycle_filtering" if zone.startswith("front") else "nearby_motorcycle"
    if "pedestrian" in text or "walker" in text:
        return "pedestrian_occlusion" if zone.startswith("front") else "nearby_pedestrian"
    if "wrong_way" in text:
        return "wrong_way_vehicle"
    if "generated_asset" in text or "static.prop" in text:
        return "road_obstacle" if zone.startswith("front") else "visual_or_side_obstacle"
    if zone.startswith("front") and distance_m <= config.high_distance_m:
        return "front_conflict"
    return "nearby_actor"


def _risk_level(distance_m: float, zone: str, config: RiskTimelineConfig) -> str:
    if zone.startswith("front") and distance_m <= config.critical_distance_m:
        return "critical"
    if zone.startswith("front") and distance_m <= config.high_distance_m:
        return "high"
    if distance_m <= config.medium_distance_m:
        return "medium"
    return "low"


def _memory_query(track: EntityTrackPoint, zone: str, risk_label: str, config: RiskTimelineConfig) -> list[str]:
    query = [risk_label, zone]
    if config.behavior_id:
        query.append(config.behavior_id)
    if "motorcycle" in risk_label:
        query.extend(["two_wheeler_clearance", "malaysian_driving"])
    if "pedestrian" in risk_label:
        query.extend(["occlusion", "yield"])
    if "obstacle" in risk_label:
        query.extend(["unknown_object", "slow_down"])
    return list(dict.fromkeys(query))


def _recommended_behavior(risk_label: str, risk_level: str, zone: str) -> str:
    if risk_level == "critical":
        return "brake smoothly, hold lane, leave escape gap"
    if "motorcycle" in risk_label:
        return "slow and keep lateral clearance for filtering two-wheeler"
    if "pedestrian" in risk_label:
        return "yield and creep until occlusion clears"
    if "obstacle" in risk_label:
        return "reduce speed and plan a gentle offset around obstacle"
    if zone.startswith("front"):
        return "increase following gap and prepare to yield"
    return "monitor while maintaining route"


def _relative_speed(track: EntityTrackPoint, ego: EntityTrackPoint) -> float:
    dx = track.velocity.get("x", 0.0) - ego.velocity.get("x", 0.0)
    dy = track.velocity.get("y", 0.0) - ego.velocity.get("y", 0.0)
    dz = track.velocity.get("z", 0.0) - ego.velocity.get("z", 0.0)
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _distance(left: dict[str, float], right: dict[str, float]) -> float:
    dx = left.get("x", 0.0) - right.get("x", 0.0)
    dy = left.get("y", 0.0) - right.get("y", 0.0)
    dz = left.get("z", 0.0) - right.get("z", 0.0)
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _group_by_tick(tracks: list[EntityTrackPoint]) -> dict[int, list[EntityTrackPoint]]:
    by_tick: dict[int, list[EntityTrackPoint]] = {}
    for track in tracks:
        by_tick.setdefault(track.tick, []).append(track)
    return by_tick


def _dedupe_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[int, str]] = set()
    out: list[dict[str, Any]] = []
    for event in events:
        key = (int(event["tick"]), str(event["actor_ref"]))
        if key in seen:
            continue
        seen.add(key)
        out.append(event)
    return out


def _max_risk_level(events: list[dict[str, Any]]) -> str:
    order = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    best = "none"
    for event in events:
        level = str(event.get("risk_level", "none"))
        if order.get(level, 0) > order.get(best, 0):
            best = level
    return best


def _zone_priority(zone: str) -> int:
    if zone == "front":
        return 0
    if zone.startswith("front_"):
        return 1
    if zone.startswith("side"):
        return 2
    return 3


def _timeline_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Risk Timeline: {payload.get('scenario_id') or 'unknown'}",
        "",
        f"- Behavior: `{payload.get('behavior_id')}`",
        f"- Ticks: `{payload.get('tick_count')}`",
        f"- Actors: `{payload.get('actor_count')}`",
        f"- Events: `{payload.get('event_count')}`",
        f"- Max risk: `{payload.get('max_risk_level')}`",
        "",
        "## Top Events",
        "",
        "| Time | Actor | Zone | Distance | Risk | Recommended behavior |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for event in payload.get("events", [])[:20]:
        lines.append(
            f"| {event['time_s']} | `{event['actor_ref']}` | {event['zone']} | {event['distance_m']}m | {event['risk_label']} / {event['risk_level']} | {event['recommended_behavior']} |"
        )
    return "\n".join(lines) + "\n"


def _float_map(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    return {str(key): float(raw) for key, raw in value.items() if _is_number(raw)}


def _is_number(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
