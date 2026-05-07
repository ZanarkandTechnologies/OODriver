from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from driverx.simulators.reasoning_timeline_overlay import (
    ReasoningOverlayEvent,
    build_reasoning_overlay_events,
    render_reasoning_overlay_frame,
)


class ReasoningTimelineOverlayTests(unittest.TestCase):
    def test_builds_events_from_risk_and_alpamayo(self) -> None:
        events = build_reasoning_overlay_events(
            bundle={"scenario_id": "scene-1"},
            risk_timeline={
                "events": [
                    {
                        "time_s": 9.0,
                        "actor_ref": "bike",
                        "risk_label": "motorcycle_filtering",
                        "zone": "front_left",
                        "distance_m": 2.4,
                        "risk_level": "critical",
                        "recommended_behavior": "slow and keep clearance",
                    }
                ]
            },
            alpamayo_batch={
                "records": [
                    {
                        "scenario_id": "scene-1",
                        "memory_ids": ["mem-sample-motorcycle-filtering"],
                        "reasoning_changed": True,
                    }
                ]
            },
            speed_factor=3.0,
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].start_s, 3.0)
        self.assertIn("motorcycle_filtering", events[0].risk)
        self.assertIn("lateral clearance", events[0].memory_principle)
        self.assertEqual(events[0].claim, "sampled_open_loop_reasoning")

    def test_renders_legible_frame(self) -> None:
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError as exc:
            raise unittest.SkipTest(f"Pillow unavailable for overlay frame fixture: {exc}") from exc
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "frame.png"
            image = Image.new("RGB", (1280, 720), color=(30, 45, 60))
            draw = ImageDraw.Draw(image, "RGBA")
            render_reasoning_overlay_frame(
                draw,
                image.size,
                ReasoningOverlayEvent(
                    start_s=0.0,
                    end_s=4.0,
                    source_time_s=0.0,
                    risk="motorcycle_filtering | front_left | 2.4m from bike",
                    memory_id="mem-sample-motorcycle-filtering",
                    memory_principle="leave lateral clearance",
                    vla_reasoning="Keep distance to lead scooter",
                    action_intent="slow and keep clearance",
                ),
                "0xDriver",
                "time-warped demo",
                ImageFont.load_default(),
            )
            image.save(path)

            self.assertGreater(path.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
