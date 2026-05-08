from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.evaluation.closed_loop_control_score import score_closed_loop_control
from driverx.policies.closed_loop_types import validate_closed_loop_trace


class ClosedLoopControlScoreTests(unittest.TestCase):
    def test_paused_receding_horizon_trace_passes(self) -> None:
        with TemporaryDirectory() as tmp:
            trace_path = Path(tmp) / "trace.json"
            trace_path.write_text(json.dumps(_paused_trace(tmp)), encoding="utf-8")

            report = score_closed_loop_control(trace_path)

            self.assertEqual(report.status, "passed")
            self.assertGreaterEqual(report.closed_loop_score, 72.0)
            self.assertEqual(report.mode, "paused_receding_horizon")

    def test_cached_replay_does_not_get_full_closed_loop_credit(self) -> None:
        payload = {
            "mode": "cached_replay",
            "steps": [
                {"input_frame_id": 1, "post_action_frame_id": 5, "applied_control_count": 4},
            ],
            "claim_boundaries": ["closed_loop_vla_control=cached_replay", "real_time_vla_control=false"],
        }

        validation = validate_closed_loop_trace(payload)

        self.assertEqual(validation.status, "passed")
        self.assertIn("cached_replay", " ".join(validation.warnings))

    def test_real_time_overclaim_blocks(self) -> None:
        validation = validate_closed_loop_trace(
            {
                "mode": "real_time",
                "steps": [
                    {"input_frame_id": 1, "post_action_frame_id": 5, "applied_control_count": 4},
                    {"input_frame_id": 5, "post_action_frame_id": 9, "applied_control_count": 4},
                ],
                "latency_ms": {"max": 120000.0},
                "real_time_tick_budget_ms": 250.0,
                "claim_boundaries": ["closed_loop_vla_control=real_time", "real_time_vla_control=true"],
            }
        )

        self.assertEqual(validation.status, "blocked")
        self.assertIn("real_time claim", " ".join(validation.blockers))


def _paused_trace(tmp: str) -> dict[str, object]:
    steps = []
    for index in range(3):
        steps.append(
            {
                "step_index": index,
                "input_frame_id": 100 + index * 4,
                "post_action_frame_id": 104 + index * 4,
                "applied_control_count": 4,
                "prediction_path": f"{tmp}/prediction_{index}.json",
                "control_trace_path": f"{tmp}/control_{index}.json",
                "checkpoint_path": f"{tmp}/checkpoint_{index}.json",
                "sensor_frame_ids": [100 + index * 4] * 3,
                "safety_report": {"lane_departure_proxy": False, "unsafe_control_conflict": False},
            }
        )
    return {
        "mode": "paused_receding_horizon",
        "steps": steps,
        "claim_boundaries": [
            "closed_loop_vla_control=paused_receding_horizon",
            "real_time_vla_control=false",
        ],
    }


if __name__ == "__main__":
    unittest.main()
