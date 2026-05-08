from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.evaluation.closed_loop_integration_score import score_closed_loop_integration


class ClosedLoopIntegrationScoreTests(unittest.TestCase):
    def test_missing_sensor_sync_blocks(self) -> None:
        with TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "mode": "paused_receding_horizon",
                        "claim_boundaries": [
                            "closed_loop_vla_control=paused_receding_horizon",
                            "real_time_vla_control=false",
                        ],
                        "steps": [
                            {
                                "input_frame_id": 10,
                                "post_action_frame_id": 14,
                                "applied_control_count": 4,
                                "prediction_path": "prediction.json",
                                "control_trace_path": "control.json",
                                "safety_report": {"lane_departure_proxy": False, "unsafe_control_conflict": False},
                            },
                            {
                                "input_frame_id": 14,
                                "post_action_frame_id": 18,
                                "applied_control_count": 4,
                                "prediction_path": "prediction.json",
                                "control_trace_path": "control.json",
                                "safety_report": {"lane_departure_proxy": False, "unsafe_control_conflict": False},
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = score_closed_loop_integration(trace)

            self.assertEqual(report.status, "blocked")
            self.assertIn("sensor", " ".join(report.blockers))


if __name__ == "__main__":
    unittest.main()
