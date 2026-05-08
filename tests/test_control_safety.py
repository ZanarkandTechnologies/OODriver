from __future__ import annotations

import unittest

from driverx.core.types import TrajectoryCandidate
from driverx.policies.control_safety import SafetyContext, validate_control_chunk
from driverx.policies.trajectory_control import TrajectoryControlConfig, trajectory_to_control_trace


class ControlSafetyTests(unittest.TestCase):
    def test_corridor_clamps_wide_swerve(self) -> None:
        trace = trajectory_to_control_trace(
            TrajectoryCandidate(points_xy=[(1.0 + index * 0.2, 4.0) for index in range(20)], source="test", score=1.0),
            source_policy_id="test",
            config=TrajectoryControlConfig(max_speed_mps=5.0),
        )

        safe = validate_control_chunk(trace, SafetyContext(corridor_half_width_m=1.5))

        self.assertFalse(safe.lane_departure_proxy)
        self.assertLessEqual(safe.max_abs_y_m, 1.5)
        self.assertIn("corridor clamp", " ".join(safe.interventions))

    def test_near_blocker_forces_emergency_stop(self) -> None:
        trace = trajectory_to_control_trace(
            TrajectoryCandidate(points_xy=[(1.0 + index * 0.2, 0.0) for index in range(20)], source="test", score=1.0),
            source_policy_id="test",
        )

        safe = validate_control_chunk(trace, SafetyContext(nearest_object_distance_m=0.5))

        self.assertTrue(safe.emergency_stop_applied)
        self.assertTrue(all(command.throttle == 0.0 for command in safe.control_trace.commands))
        self.assertTrue(all(command.brake > 0.0 for command in safe.control_trace.commands))


if __name__ == "__main__":
    unittest.main()
