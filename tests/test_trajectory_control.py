import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.core.types import TrajectoryCandidate
from driverx.policies import (
    EgoPose,
    TrajectoryControlConfig,
    load_policy_decision_trajectory,
    trajectory_to_control_trace,
)


def _trajectory(points: list[tuple[float, float]]) -> TrajectoryCandidate:
    return TrajectoryCandidate(
        points_xy=points,
        source="fixture",
        score=0.0,
    )


class TrajectoryControlTest(unittest.TestCase):
    def test_straight_trajectory_has_near_zero_steer(self) -> None:
        trace = trajectory_to_control_trace(
            _trajectory([(float(i + 1), 0.0) for i in range(20)]),
            source_policy_id="alpamayo-live",
        )

        self.assertEqual(len(trace.commands), 20)
        self.assertEqual(trace.trajectory_frame, "ego")
        self.assertTrue(all(abs(command.steer) < 1e-6 for command in trace.commands[:5]))
        self.assertGreater(trace.commands[0].throttle, 0.0)

    def test_left_and_right_trajectories_have_signed_steer(self) -> None:
        left = trajectory_to_control_trace(
            _trajectory([(float(i + 1), 1.0) for i in range(20)]),
            source_policy_id="left",
        )
        right = trajectory_to_control_trace(
            _trajectory([(float(i + 1), -1.0) for i in range(20)]),
            source_policy_id="right",
        )

        self.assertGreater(left.commands[0].steer, 0.0)
        self.assertLess(right.commands[0].steer, 0.0)

    def test_stop_trajectory_brakes_after_lookahead(self) -> None:
        trace = trajectory_to_control_trace(
            _trajectory([(0.0, 0.0) for _ in range(20)]),
            source_policy_id="stop",
        )

        self.assertEqual(trace.commands[3].brake, 0.5)
        self.assertEqual(trace.commands[3].throttle, 0.0)

    def test_speed_and_steer_clamps_are_reported(self) -> None:
        trace = trajectory_to_control_trace(
            _trajectory([(20.0, 20.0) for _ in range(20)]),
            source_policy_id="clamp",
            config=TrajectoryControlConfig(max_speed_mps=2.0, max_steer=0.2),
        )

        self.assertTrue(trace.safety_clamps)
        self.assertLessEqual(max(command.target_speed_mps for command in trace.commands), 2.0)
        self.assertLessEqual(max(abs(command.steer) for command in trace.commands), 0.2)

    def test_points_behind_ego_brake_instead_of_steering(self) -> None:
        trace = trajectory_to_control_trace(
            _trajectory([(-float(i + 1), 0.0) for i in range(20)]),
            source_policy_id="reverse",
        )

        self.assertEqual(trace.commands[0].throttle, 0.0)
        self.assertEqual(trace.commands[0].brake, 0.5)
        self.assertEqual(trace.commands[0].steer, 0.0)
        self.assertIn("target behind ego", trace.safety_clamps[0])

    def test_load_policy_decision_trajectory_accepts_live_bundle_shape(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "decision.json"
            points = [(float(i + 1), 0.0) for i in range(20)]
            path.write_text(
                json.dumps(
                    {
                        "policy_decision": {
                            "policy_id": "alpamayo-live",
                            "action": {
                                "trajectory": {
                                    "points_xy": points,
                                    "source": "alpamayo_live_open_loop",
                                    "score": 0.0,
                                }
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )

            policy_id, trajectory = load_policy_decision_trajectory(path)

        self.assertEqual(policy_id, "alpamayo-live")
        self.assertEqual(trajectory.points_xy[0], (1.0, 0.0))

    def test_ego_pose_rotation_is_applied(self) -> None:
        trace = trajectory_to_control_trace(
            _trajectory([(0.0, 5.0) for _ in range(20)]),
            source_policy_id="pose",
            ego_pose=EgoPose(yaw_deg=90.0),
            config=TrajectoryControlConfig(trajectory_frame="world"),
        )

        self.assertAlmostEqual(trace.commands[0].target_y, 0.0, places=3)

    def test_ego_frame_trajectory_ignores_world_pose(self) -> None:
        trace = trajectory_to_control_trace(
            _trajectory([(1.0, 0.0) for _ in range(20)]),
            source_policy_id="pose",
            ego_pose=EgoPose(x=100.0, y=100.0, yaw_deg=180.0),
        )

        self.assertGreater(trace.commands[0].throttle, 0.0)
        self.assertEqual(trace.commands[0].brake, 0.0)


if __name__ == "__main__":
    unittest.main()
