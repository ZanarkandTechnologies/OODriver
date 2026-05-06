import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from driverx.assets import default_asset_requests, generate_assets_dry_run
from driverx.behaviors import default_behavior_plans, simulate_behavior
from driverx.scenarios import ScenarioRecipe
from driverx.simulators import (
    CarlaOodDemoConfig,
    build_carla_ood_demo_plan,
    run_carla_ood_demo,
    write_carla_ood_demo,
)


class _FakeBlueprint:
    def __init__(self, blueprint_id: str) -> None:
        self.id = blueprint_id
        self.attributes: dict[str, str] = {}

    def set_attribute(self, key: str, value: str) -> None:
        self.attributes[key] = value


class _FakeBlueprints:
    known = {
        "sensor.camera.rgb",
        "vehicle.lincoln.mkz_2020",
        "vehicle.kawasaki.ninja",
        "static.prop.trafficcone",
        "static.prop.streetbarrier",
        "static.prop.constructioncone",
    }

    def find(self, blueprint_id: str) -> _FakeBlueprint:
        if blueprint_id not in self.known:
            raise KeyError(blueprint_id)
        return _FakeBlueprint(blueprint_id)

    def filter(self, pattern: str):
        if pattern == "vehicle.*":
            return [_FakeBlueprint("vehicle.lincoln.mkz_2020")]
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return [_FakeBlueprint(item) for item in sorted(self.known) if item.startswith(prefix)]
        return []


class _FakeImage:
    def __init__(self, label: str) -> None:
        self.label = label

    def save_to_disk(self, path: str) -> None:
        Path(path).write_bytes(f"fake-frame:{self.label}".encode("utf-8"))


class _FakeActor:
    def __init__(self, actor_id: int, type_id: str, transform: object) -> None:
        self.id = actor_id
        self.type_id = type_id
        self.transform = transform
        self.velocity = _FakeVector3D(0.0, 0.0, 0.0)
        self.destroyed = False

    def listen(self, callback) -> None:
        for index in range(16):
            callback(_FakeImage(f"{self.id}-{index}"))

    def set_transform(self, transform: object) -> None:
        self.transform = transform

    def get_transform(self):
        return self.transform

    def get_velocity(self):
        return self.velocity

    def destroy(self) -> None:
        self.destroyed = True


class _FakeMap:
    name = "Carla/Maps/Town13/Town13"

    def get_spawn_points(self):
        return [_FakeTransform(_FakeLocation(0.0, 0.0, 0.2), _FakeRotation(0.0, 0.0, 0.0))]


class _FakeWorld:
    def __init__(self) -> None:
        self.next_id = 10
        self.spawned: list[_FakeActor] = []
        self.waits = 0

    def get_map(self):
        return _FakeMap()

    def get_blueprint_library(self):
        return _FakeBlueprints()

    def try_spawn_actor(self, blueprint, transform):
        return self.spawn_actor(blueprint, transform)

    def spawn_actor(self, blueprint, transform, attach_to=None):
        self.next_id += 1
        actor = _FakeActor(self.next_id, blueprint.id, transform)
        self.spawned.append(actor)
        return actor

    def wait_for_tick(self, timeout_s=None):
        self.waits += 1
        return None


class _FakeClient:
    def __init__(self, world: _FakeWorld) -> None:
        self.world = world
        self.timeout_s = None

    def set_timeout(self, timeout_s: float) -> None:
        self.timeout_s = timeout_s

    def get_world(self):
        return self.world


class _FakeVector3D:
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.z = z


class _FakeLocation(_FakeVector3D):
    pass


class _FakeRotation:
    def __init__(self, pitch: float = 0.0, yaw: float = 0.0, roll: float = 0.0) -> None:
        self.pitch = pitch
        self.yaw = yaw
        self.roll = roll


class _FakeTransform:
    def __init__(self, location, rotation) -> None:
        self.location = location
        self.rotation = rotation


class _FakeCarla:
    Location = _FakeLocation
    Rotation = _FakeRotation
    Transform = _FakeTransform

    def __init__(self) -> None:
        self.world = _FakeWorld()

    def Client(self, host: str, port: int):
        return _FakeClient(self.world)


def _recipe() -> ScenarioRecipe:
    return ScenarioRecipe(
        recipe_id="generated-demo-regional-driving-000",
        parent_seed_id="base-demo",
        mutation="regional_driving_behavior",
        actors=[],
        environment={"traffic_style": "dense_asian_urban"},
        expected_failure_mode="lateral filtering surprises the policy",
        memory_query=["motorcycle_filtering"],
    )


def _behavior():
    plan = {plan.behavior_id: plan for plan in default_behavior_plans()}["motorcycle_filtering"]
    return simulate_behavior(plan)


class CarlaOodDemoTest(unittest.TestCase):
    def test_build_plan_includes_generated_asset_spawn_specs(self) -> None:
        plan = build_carla_ood_demo_plan(
            _recipe(),
            _behavior(),
            CarlaOodDemoConfig(tick_count=8, fps=4),
            asset_manifests=generate_assets_dry_run(default_asset_requests()),
        )

        self.assertEqual(plan.recipe_id, "generated-demo-regional-driving-000")
        self.assertEqual(plan.tick_count, 8)
        self.assertEqual(len(plan.object_spawn_specs), 3)
        self.assertIn("generated_asset_asset_fallen_cargo_sack", plan.actor_refs)

    def test_run_carla_ood_demo_records_frames_tracks_and_cleanup(self) -> None:
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            carla = _FakeCarla()
            result = run_carla_ood_demo(
                CarlaOodDemoConfig(tick_count=6, fps=3, camera_width=160, camera_height=90),
                run_dir,
                recipe=_recipe(),
                behavior=_behavior(),
                asset_manifests=generate_assets_dry_run(default_asset_requests()),
                carla_module=carla,
            )
            summary = write_carla_ood_demo(run_dir, result)
            tracks = json.loads(Path(result.tracks_path or "").read_text(encoding="utf-8"))
            frames = sorted(Path(result.rgb_folder or "").glob("*.png"))
            json_exists = Path(summary["json_path"]).exists()
            report_exists = Path(summary["report_path"]).exists()

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.frame_count, 6)
        self.assertEqual(result.duration_s, 2.0)
        self.assertEqual(len(frames), 6)
        self.assertEqual(len(tracks), 6 * 5)
        self.assertEqual(result.generated_asset_ids, [
            "asset-fallen-cargo-sack",
            "asset-roadside-food-cart",
            "asset-reflective-flood-barrier",
        ])
        self.assertTrue(all(actor.destroyed for actor in carla.world.spawned))
        self.assertTrue(json_exists)
        self.assertTrue(report_exists)

    def test_missing_carla_package_reports_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_carla_ood_demo(
                CarlaOodDemoConfig(),
                Path(tmp),
                recipe=_recipe(),
                behavior=_behavior(),
                carla_module=SimpleNamespace(),
            )

        self.assertEqual(result.status, "blocked")
        self.assertIn("CARLA OOD demo failed", result.blockers[0])


if __name__ == "__main__":
    unittest.main()
