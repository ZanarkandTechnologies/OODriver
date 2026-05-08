import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.simulators.carla_control import (
    CarlaControlConfig,
    control_carla_world,
    write_carla_control_report,
)


class _FakeWeather:
    def __init__(self) -> None:
        self.cloudiness = 0.0
        self.precipitation = 0.0
        self.precipitation_deposits = 0.0
        self.wetness = 0.0
        self.fog_density = 0.0
        self.sun_altitude_angle = 45.0
        self.sun_azimuth_angle = 0.0


class _FakeBlueprint:
    def __init__(self, blueprint_id: str) -> None:
        self.id = blueprint_id
        self.attributes: dict[str, str] = {}

    def set_attribute(self, key: str, value: str) -> None:
        self.attributes[key] = value


class _FakeBlueprints:
    def find(self, blueprint_id: str) -> _FakeBlueprint:
        if blueprint_id != "sensor.camera.rgb":
            raise KeyError(blueprint_id)
        return _FakeBlueprint(blueprint_id)


class _FakeImage:
    def save_to_disk(self, path: str) -> None:
        Path(path).write_bytes(b"fake-live-carla-frame")


class _FakeActor:
    def __init__(self, actor_id: int) -> None:
        self.id = actor_id
        self.destroyed = False

    def listen(self, callback) -> None:
        callback(_FakeImage())

    def destroy(self) -> None:
        self.destroyed = True


class _SilentCameraActor(_FakeActor):
    def listen(self, callback) -> None:
        del callback


class _FakeLocation:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


class _FakeRotation:
    def __init__(self, pitch: float = 0.0, yaw: float = 0.0, roll: float = 0.0) -> None:
        self.pitch = pitch
        self.yaw = yaw
        self.roll = roll


class _FakeTransform:
    def __init__(self, location: _FakeLocation, rotation: _FakeRotation) -> None:
        self.location = location
        self.rotation = rotation


class _FakeMap:
    def __init__(self, name: str) -> None:
        self.name = name

    def get_spawn_points(self) -> list[_FakeTransform]:
        return [
            _FakeTransform(_FakeLocation(10.0, 20.0, 0.0), _FakeRotation(yaw=0.0)),
            _FakeTransform(_FakeLocation(30.0, 40.0, 0.0), _FakeRotation(yaw=90.0)),
        ]


class _FakeWorld:
    def __init__(self, name: str) -> None:
        self._name = name
        self.weather = _FakeWeather()
        self.spawned: list[_FakeActor] = []
        self.tick_count = 0

    def get_map(self) -> _FakeMap:
        return _FakeMap(self._name)

    def set_name(self, name: str) -> None:
        self._name = name

    def get_weather(self) -> _FakeWeather:
        return self.weather

    def set_weather(self, weather: _FakeWeather) -> None:
        self.weather = weather

    def get_blueprint_library(self) -> _FakeBlueprints:
        return _FakeBlueprints()

    def spawn_actor(self, blueprint: _FakeBlueprint, transform: _FakeTransform) -> _FakeActor:
        del blueprint, transform
        actor = _FakeActor(200 + len(self.spawned))
        self.spawned.append(actor)
        return actor

    def tick(self) -> None:
        self.tick_count += 1


class _SilentCameraWorld(_FakeWorld):
    def spawn_actor(self, blueprint: _FakeBlueprint, transform: _FakeTransform) -> _SilentCameraActor:
        del blueprint, transform
        actor = _SilentCameraActor(300 + len(self.spawned))
        self.spawned.append(actor)
        return actor


class _FakeClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.timeout_s = 0.0
        self.world = _FakeWorld("Carla/Maps/Town10HD_Opt")

    def set_timeout(self, timeout_s: float) -> None:
        self.timeout_s = timeout_s

    def get_world(self) -> _FakeWorld:
        return self.world

    def get_available_maps(self) -> list[str]:
        return ["/Game/Carla/Maps/Town03_Opt", "/Game/Carla/Maps/Town10HD_Opt"]

    def load_world(self, map_name: str) -> _FakeWorld:
        self.world.set_name(f"Carla/Maps/{map_name}")
        return self.world


class _FakeCarla:
    Client = _FakeClient
    WeatherParameters = _FakeWeather
    Location = _FakeLocation
    Rotation = _FakeRotation
    Transform = _FakeTransform


class _SilentCameraCarla:
    WeatherParameters = _FakeWeather
    Location = _FakeLocation
    Rotation = _FakeRotation
    Transform = _FakeTransform

    def __init__(self) -> None:
        self.world = _SilentCameraWorld("Carla/Maps/Town10HD_Opt")

    def Client(self, host: str, port: int) -> _FakeClient:
        client = _FakeClient(host, port)
        client.world = self.world
        return client


class CarlaControlTest(unittest.TestCase):
    def test_control_loads_map_sets_weather_captures_and_cleans_camera(self) -> None:
        with TemporaryDirectory() as tmp:
            result = control_carla_world(
                CarlaControlConfig(
                    town="Town03",
                    load_map=True,
                    weather_preset_name="night_rain_fog",
                    capture=True,
                    spawn_index=1,
                    tick_count=2,
                ),
                Path(tmp),
                carla_module=_FakeCarla,
            )
            screenshot_exists = Path(result.screenshot_path or "").exists()

        self.assertTrue(result.connected)
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.requested_map, "Town03_Opt")
        self.assertEqual(result.map_before, "Carla/Maps/Town10HD_Opt")
        self.assertEqual(result.map_after, "Carla/Maps/Town03_Opt")
        self.assertEqual(result.spawned_actor_ids, [200])
        self.assertEqual(result.destroyed_actor_ids, [200])
        self.assertEqual(result.weather_after["sun_altitude_angle"], -12.0)
        self.assertEqual(result.weather_after["fog_density"], 45.0)
        self.assertTrue(screenshot_exists)

    def test_control_reports_connection_failure_as_blocked(self) -> None:
        def failing_client(host: str, port: int) -> object:
            del host, port
            raise RuntimeError("server unavailable")

        with TemporaryDirectory() as tmp:
            result = control_carla_world(
                CarlaControlConfig(town="Town05", load_map=True),
                Path(tmp),
                carla_module=_FakeCarla,
                client_factory=failing_client,
            )

        self.assertFalse(result.connected)
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.requested_map, "Town05_Opt")
        self.assertIn("server unavailable", result.error or "")

    def test_control_destroys_camera_when_capture_times_out(self) -> None:
        with TemporaryDirectory() as tmp:
            carla = _SilentCameraCarla()
            result = control_carla_world(
                CarlaControlConfig(capture=True, timeout_s=0.01, tick_count=1),
                Path(tmp),
                carla_module=carla,
            )

        self.assertFalse(result.connected)
        self.assertEqual(result.status, "blocked")
        self.assertTrue(carla.world.spawned)
        self.assertTrue(carla.world.spawned[0].destroyed)

    def test_write_control_report_includes_boundaries(self) -> None:
        with TemporaryDirectory() as tmp:
            result = control_carla_world(
                CarlaControlConfig(weather_preset_name="clear_day"),
                Path(tmp),
                carla_module=_FakeCarla,
            )
            summary = write_carla_control_report(Path(tmp), result)
            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))
            report_exists = Path(summary["report_path"]).exists()

        self.assertTrue(report_exists)
        self.assertIn("carla_world_generation=false", payload["claim_boundaries"])


if __name__ == "__main__":
    unittest.main()
