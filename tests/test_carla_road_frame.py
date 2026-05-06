from types import SimpleNamespace
import unittest

from driverx.simulators import (
    RoadFrameSelector,
    local_pose_to_payload,
    payload_to_local_xy,
    resolve_road_frame,
    validate_road_aligned_track,
)


class CarlaRoadFrameTest(unittest.TestCase):
    def test_local_pose_uses_anchor_yaw(self) -> None:
        frame = resolve_road_frame(
            _FakeMap(
                _transform(100.0, 200.0, 0.2, 90.0),
            )
        )

        payload = local_pose_to_payload(frame, 10.0, 2.0, 0.0, 15.0)

        self.assertAlmostEqual(payload["location"]["x"], 98.0)
        self.assertAlmostEqual(payload["location"]["y"], 210.0)
        self.assertAlmostEqual(payload["rotation"]["yaw"], 105.0)

    def test_payload_round_trips_to_local_xy(self) -> None:
        frame = resolve_road_frame(_FakeMap(_transform(50.0, -4.0, 0.2, 30.0)))
        payload = local_pose_to_payload(frame, 12.0, -3.0, 0.0, 0.0)

        local_x, local_y = payload_to_local_xy(frame, payload)

        self.assertAlmostEqual(local_x, 12.0, places=5)
        self.assertAlmostEqual(local_y, -3.0, places=5)

    def test_alignment_report_flags_out_of_corridor_samples(self) -> None:
        frame = resolve_road_frame(
            _FakeMap(_transform(0.0, 0.0, 0.2, 0.0)),
            RoadFrameSelector(max_lateral_offset_m=4.0),
        )
        transforms = [
            local_pose_to_payload(frame, 0.0, 0.0, 0.0, 0.0),
            local_pose_to_payload(frame, 4.0, 4.5, 0.0, 0.0),
        ]

        report = validate_road_aligned_track(frame, transforms, actor_ref="ood_actor_0")

        self.assertTrue(report.starts_on_road)
        self.assertEqual(report.offroad_samples, 1)
        self.assertFalse(report.passes)


class _FakeMap:
    def __init__(self, spawn_point) -> None:
        self.spawn_point = spawn_point

    def get_spawn_points(self):
        return [self.spawn_point]


def _transform(x: float, y: float, z: float, yaw: float):
    return SimpleNamespace(
        location=SimpleNamespace(x=x, y=y, z=z),
        rotation=SimpleNamespace(pitch=0.0, yaw=yaw, roll=0.0),
    )


if __name__ == "__main__":
    unittest.main()
