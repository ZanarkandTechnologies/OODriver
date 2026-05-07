from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from driverx.perception.risk_timeline import (
    RiskTimelineConfig,
    build_risk_timeline,
    load_entity_tracks,
    write_risk_timeline,
)


class RiskTimelineTests(unittest.TestCase):
    def test_classifies_front_left_side_behind_and_nearest(self) -> None:
        tracks = load_entity_tracks(_write_tracks_fixture())

        timeline = build_risk_timeline(
            tracks,
            RiskTimelineConfig(scenario_id="scene", behavior_id="motorcycle_filtering"),
        )
        events = timeline.to_jsonable()["events"]
        zones = {event["actor_ref"]: event["zone"] for event in events}

        self.assertEqual(zones["front_car"], "front")
        self.assertEqual(zones["front_left_bike"], "front_left")
        self.assertEqual(zones["side_prop"], "side_left")
        self.assertEqual(zones["behind_car"], "behind")
        self.assertEqual(timeline.nearest_event["actor_ref"], "front_car")
        self.assertIn("two_wheeler_clearance", _event(events, "front_left_bike")["memory_query"])

    def test_writes_report(self) -> None:
        tracks = load_entity_tracks(_write_tracks_fixture())
        timeline = build_risk_timeline(tracks, RiskTimelineConfig(scenario_id="scene"))
        with tempfile.TemporaryDirectory() as tmp:
            summary = write_risk_timeline(Path(tmp), timeline)

            self.assertTrue(Path(summary["json_path"]).exists())
            self.assertIn("Risk Timeline", Path(summary["report_path"]).read_text(encoding="utf-8"))


def _write_tracks_fixture() -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    path = Path(tmp.name)
    tmp.close()
    rows = [
        _track("ego", 0, 0.0, 0.0, 0.0, yaw=0.0),
        _track("front_car", 0, 3.0, 0.0, 0.0, type_id="vehicle.audi.a2"),
        _track("front_left_bike", 0, 6.0, 3.0, 0.0, type_id="vehicle.kawasaki.ninja"),
        _track("side_prop", 0, 0.0, 7.0, 0.0, type_id="static.prop.foodcart"),
        _track("behind_car", 0, -3.0, 0.0, 0.0, type_id="vehicle.tesla.model3"),
    ]
    path.write_text(json.dumps(rows), encoding="utf-8")
    return path


def _track(
    actor_ref: str,
    tick: int,
    x: float,
    y: float,
    z: float,
    *,
    yaw: float = 0.0,
    type_id: str = "vehicle.test",
) -> dict[str, object]:
    return {
        "actor_ref": actor_ref,
        "actor_id": tick,
        "type_id": type_id,
        "tick": tick,
        "t_s": tick * 0.25,
        "location": {"x": x, "y": y, "z": z},
        "rotation": {"yaw": yaw},
        "velocity": {"x": 0.0, "y": 0.0, "z": 0.0},
    }


def _event(events: list[dict[str, object]], actor_ref: str) -> dict[str, object]:
    return next(event for event in events if event["actor_ref"] == actor_ref)


if __name__ == "__main__":
    unittest.main()
