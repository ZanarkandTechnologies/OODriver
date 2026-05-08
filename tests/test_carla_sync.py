from __future__ import annotations

import queue
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest

from driverx.simulators.carla_sync import CarlaSyncConfig, CarlaSyncSession, capture_aligned_checkpoint


@dataclass
class _Settings:
    synchronous_mode: bool = False
    fixed_delta_seconds: float | None = None


class _World:
    def __init__(self) -> None:
        self.frame = 10
        self.settings = _Settings()
        self.applied: list[_Settings] = []

    def get_settings(self) -> _Settings:
        return _Settings(self.settings.synchronous_mode, self.settings.fixed_delta_seconds)

    def apply_settings(self, settings: _Settings) -> None:
        self.settings = _Settings(settings.synchronous_mode, settings.fixed_delta_seconds)
        self.applied.append(self.settings)

    def tick(self) -> int:
        self.frame += 1
        return self.frame


@dataclass
class _Image:
    frame: int
    width: int = 320
    height: int = 180

    def save_to_disk(self, path: str) -> None:
        Path(path).write_bytes(b"fake")


class CarlaSyncTests(unittest.TestCase):
    def test_session_applies_and_restores_settings(self) -> None:
        world = _World()
        with CarlaSyncSession(world, CarlaSyncConfig(fixed_delta_seconds=0.2)) as session:
            self.assertTrue(world.settings.synchronous_mode)
            self.assertEqual(world.settings.fixed_delta_seconds, 0.2)
            self.assertEqual(session.tick(), 11)

        self.assertFalse(world.settings.synchronous_mode)
        self.assertIsNone(world.settings.fixed_delta_seconds)
        self.assertTrue(session.settings_restored)

    def test_checkpoint_drains_stale_sensor_frames(self) -> None:
        world = _World()
        queues = {0: queue.Queue(), 1: queue.Queue(), 2: queue.Queue()}
        for images in queues.values():
            images.put(_Image(frame=8))
            images.put(_Image(frame=12))

        with TemporaryDirectory() as tmp:
            with CarlaSyncSession(world) as session:
                checkpoint = capture_aligned_checkpoint(
                    session,
                    queues,
                    Path(tmp),
                    checkpoint_id="step",
                    min_frame_id=11,
                )

        self.assertEqual(checkpoint.queue_drain_count, 3)
        self.assertEqual([frame.sensor_frame_id for frame in checkpoint.camera_frames], [12, 12, 12])
        self.assertFalse(checkpoint.blockers)


if __name__ == "__main__":
    unittest.main()
