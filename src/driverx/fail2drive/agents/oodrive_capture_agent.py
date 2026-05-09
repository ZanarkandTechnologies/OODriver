"""Fail2Drive camera capture agent for OODrive evidence runs.

This file is passed directly to Fail2Drive's upstream leaderboard evaluator.
It intentionally depends only on modules exposed by the Fail2Drive checkout's
PYTHONPATH so the evaluator can import it as a standalone agent file.
"""

from __future__ import annotations

import os
from pathlib import Path

import cv2

import carla
from leaderboard.autoagents import autonomous_agent
from leaderboard.autoagents import autonomous_agent_local


def get_entry_point():
    return "OODriveCaptureAgent"


class OODriveCaptureAgent(autonomous_agent_local.AutonomousAgent):
    """Minimal Fail2Drive agent that saves forward RGB frames for video proof."""

    def setup(self, path_to_conf_file, route_index=None, traffic_manager=None):
        self.track = autonomous_agent.Track.MAP
        self._capture_sensor_id = os.environ.get("OODRIVE_RGB_SENSOR_ID", "oodrive_rgb")
        self._capture_every = max(1, int(os.environ.get("OODRIVE_CAPTURE_EVERY", "1")))
        self._drive_ticks = max(1, int(os.environ.get("OODRIVE_DRIVE_TICKS", "90")))
        self._capture_frame = 0
        self.step = -1
        self._capture_path = _capture_path()
        self._capture_path.mkdir(parents=True, exist_ok=True)

    def sensors(self):
        return [
            {
                "type": "sensor.camera.rgb",
                "x": float(os.environ.get("OODRIVE_CAPTURE_X", "-3.5")),
                "y": float(os.environ.get("OODRIVE_CAPTURE_Y", "0.0")),
                "z": float(os.environ.get("OODRIVE_CAPTURE_Z", "2.8")),
                "roll": float(os.environ.get("OODRIVE_CAPTURE_ROLL", "0.0")),
                "pitch": float(os.environ.get("OODRIVE_CAPTURE_PITCH", "-12.0")),
                "yaw": float(os.environ.get("OODRIVE_CAPTURE_YAW", "0.0")),
                "width": int(os.environ.get("OODRIVE_CAPTURE_WIDTH", "1280")),
                "height": int(os.environ.get("OODRIVE_CAPTURE_HEIGHT", "720")),
                "fov": int(os.environ.get("OODRIVE_CAPTURE_FOV", "105")),
                "id": self._capture_sensor_id,
            }
        ]

    def run_step(self, input_data, timestamp, sensors=None):
        self.step += 1
        if self.step % self._capture_every == 0 and self._capture_sensor_id in input_data:
            image = input_data[self._capture_sensor_id][1][:, :, :3]
            cv2.imwrite(str(self._capture_path / f"{self._capture_frame:05d}.jpg"), image)
            self._capture_frame += 1
        control = carla.VehicleControl()
        if self.step < self._drive_ticks:
            control.throttle = float(os.environ.get("OODRIVE_THROTTLE", "0.25"))
            control.brake = 0.0
        else:
            control.throttle = 0.0
            control.brake = float(os.environ.get("OODRIVE_BRAKE", "0.6"))
        return control

    def destroy(self, results=None):
        return None


def _capture_path() -> Path:
    explicit = os.environ.get("VIZ_PATH")
    if explicit:
        return Path(explicit)
    fallback = os.environ.get("SAVE_PATH")
    if fallback:
        return Path(fallback) / "oodrive_rgb"
    return Path.cwd() / "oodrive_rgb"
