import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from driverx.simulators import (
    CarlaAlpamayoCaptureConfig,
    run_carla_alpamayo_capture,
    write_carla_alpamayo_capture,
)


class _FakeBlueprint:
    def __init__(self, blueprint_id: str) -> None:
        self.id = blueprint_id
        self.attributes: dict[str, str] = {}

    def set_attribute(self, key: str, value: str) -> None:
        self.attributes[key] = value


class _FakeBlueprints:
    def find(self, blueprint_id: str) -> _FakeBlueprint:
        return _FakeBlueprint(blueprint_id)

    def filter(self, pattern: str):
        return [_FakeBlueprint("vehicle.tesla.model3")]


class _FakeImage:
    def __init__(self, label: str) -> None:
        self.label = label

    def save_to_disk(self, path: str) -> None:
        Path(path).write_bytes(f"fake-image:{self.label}".encode("utf-8"))


class _FakeActor:
    def __init__(self, actor_id: int, type_id: str) -> None:
        self.id = actor_id
        self.type_id = type_id
        self.destroyed = False
        self.tick = 0

    def listen(self, callback) -> None:
        for index in range(4):
            callback(_FakeImage(f"{self.id}-{index}"))

    def get_transform(self):
        self.tick += 1
        return SimpleNamespace(
            location=SimpleNamespace(x=float(self.tick), y=2.0, z=0.5),
            rotation=SimpleNamespace(pitch=0.0, yaw=90.0, roll=0.0),
        )

    def get_velocity(self):
        return SimpleNamespace(x=1.0, y=0.0, z=0.0)

    def destroy(self) -> None:
        self.destroyed = True


class _FakeMap:
    name = "Carla/Maps/Town10HD_Opt"

    def get_spawn_points(self):
        return [object()]


class _FakeWorld:
    def __init__(self) -> None:
        self.next_id = 100
        self.actors: list[_FakeActor] = []

    def get_map(self):
        return _FakeMap()

    def get_blueprint_library(self):
        return _FakeBlueprints()

    def try_spawn_actor(self, blueprint, spawn_point):
        return self._actor(blueprint.id)

    def spawn_actor(self, blueprint, transform, attach_to=None):
        return self._actor(blueprint.id)

    def wait_for_tick(self, timeout_s=None):
        return None

    def _actor(self, type_id: str) -> _FakeActor:
        self.next_id += 1
        actor = _FakeActor(self.next_id, type_id)
        self.actors.append(actor)
        return actor


class _FakeClient:
    def __init__(self, host: str, port: int) -> None:
        self.world = _FakeWorld()

    def set_timeout(self, timeout_s: float) -> None:
        self.timeout_s = timeout_s

    def get_world(self):
        return self.world


class _FakeCarla:
    Client = _FakeClient

    class Location:
        def __init__(self, x=0.0, y=0.0, z=0.0) -> None:
            self.x = x
            self.y = y
            self.z = z

    class Rotation:
        def __init__(self, pitch=0.0, yaw=0.0, roll=0.0) -> None:
            self.pitch = pitch
            self.yaw = yaw
            self.roll = roll

    class Transform:
        def __init__(self, location, rotation) -> None:
            self.location = location
            self.rotation = rotation


class CarlaAlpamayoCaptureTest(unittest.TestCase):
    def test_capture_writes_images_package_tracks_and_cleans_up(self) -> None:
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            result = run_carla_alpamayo_capture(
                CarlaAlpamayoCaptureConfig("host.docker.internal", 2000, 1.0),
                run_dir,
                carla_module=_FakeCarla,
            )
            summary = write_carla_alpamayo_capture(run_dir, result)
            package = json.loads(Path(result.package_path or "").read_text(encoding="utf-8"))
            tracks = json.loads(Path(result.tracks_path or "").read_text(encoding="utf-8"))
            json_exists = Path(summary["json_path"]).exists()

        self.assertTrue(result.connected)
        self.assertEqual(result.image_count, 12)
        self.assertEqual(package["camera_indices"], [0, 1, 2])
        self.assertEqual(package["tensor_shapes"]["image_frames"], "3 x 4 x 3 x 180 x 320")
        self.assertEqual(len(package["ego_history_xyz"]), 16)
        self.assertEqual(len(tracks), 4)
        self.assertEqual(result.destroyed_actor_ids, [104, 103, 102, 101])
        self.assertTrue(json_exists)

    def test_missing_carla_package_is_actionable(self) -> None:
        with patch.dict(sys.modules):
            sys.modules.pop("carla", None)
            with patch("importlib.import_module", side_effect=ImportError("no carla")):
                result = run_carla_alpamayo_capture(
                    CarlaAlpamayoCaptureConfig("127.0.0.1", 2000, 0.1),
                    Path("unused"),
                )

        self.assertFalse(result.connected)
        self.assertIn("carla==0.9.16", result.error)


if __name__ == "__main__":
    unittest.main()
