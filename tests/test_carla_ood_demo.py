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
    load_carla_ood_demo_config,
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
        "static.prop.dirtdebris01",
        "static.prop.foodcart",
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
        self.physics_enabled = True
        self.autopilot_enabled = None

    def listen(self, callback) -> None:
        for index in range(16):
            callback(_FakeImage(f"{self.id}-{index}"))

    def set_transform(self, transform: object) -> None:
        self.transform = transform

    def get_transform(self):
        return self.transform

    def get_velocity(self):
        return self.velocity

    def set_simulate_physics(self, enabled: bool) -> None:
        self.physics_enabled = enabled

    def set_autopilot(self, enabled: bool) -> None:
        self.autopilot_enabled = enabled

    def destroy(self) -> None:
        self.destroyed = True


class _FakeMap:
    name = "Carla/Maps/Town13/Town13"

    def get_spawn_points(self):
        return [_FakeTransform(_FakeLocation(100.0, 200.0, 0.2), _FakeRotation(0.0, 90.0, 0.0))]


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


class _RetryFakeMap:
    name = "Carla/Maps/Town10HD_Opt"

    def get_spawn_points(self):
        return [
            _FakeTransform(_FakeLocation(100.0, 200.0, 0.2), _FakeRotation(0.0, 90.0, 0.0)),
            _FakeTransform(_FakeLocation(120.0, 240.0, 0.2), _FakeRotation(0.0, 0.0, 0.0)),
        ]


class _RetryFakeWorld(_FakeWorld):
    def __init__(self) -> None:
        super().__init__()
        self.try_count = 0

    def get_map(self):
        return _RetryFakeMap()

    def try_spawn_actor(self, blueprint, transform):
        self.try_count += 1
        if blueprint.id.startswith("vehicle.") and self.try_count == 1:
            return None
        return self.spawn_actor(blueprint, transform)


class _OodCollisionRetryWorld(_FakeWorld):
    def __init__(self) -> None:
        super().__init__()
        self.ood_try_count = 0

    def try_spawn_actor(self, blueprint, transform):
        if blueprint.id == "vehicle.kawasaki.ninja":
            self.ood_try_count += 1
            if self.ood_try_count == 1:
                return None
        return self.spawn_actor(blueprint, transform)


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


class _RetryFakeCarla(_FakeCarla):
    def __init__(self) -> None:
        self.world = _RetryFakeWorld()


class _OodCollisionRetryCarla(_FakeCarla):
    def __init__(self) -> None:
        self.world = _OodCollisionRetryWorld()


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
            alignment = json.loads(Path(result.road_alignment_path or "").read_text(encoding="utf-8"))
            frames = sorted(Path(result.rgb_folder or "").glob("*.png"))
            json_exists = Path(summary["json_path"]).exists()
            report_exists = Path(summary["report_path"]).exists()

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.frame_count, 6)
        self.assertEqual(result.duration_s, 2.0)
        self.assertEqual(alignment["coordinate_frame"], "road_local")
        self.assertTrue(alignment["actors"]["ego"]["starts_on_road"])
        self.assertTrue(alignment["actors"]["ood_actor_0"]["starts_on_road"])
        self.assertAlmostEqual(alignment["road_frame"]["origin"]["x"], 100.0)
        self.assertAlmostEqual(alignment["road_frame"]["origin"]["y"], 200.0)
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

    def test_high_fidelity_mode_records_density_and_smoothness_metrics(self) -> None:
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            carla = _FakeCarla()
            result = run_carla_ood_demo(
                CarlaOodDemoConfig(
                    tick_count=6,
                    fps=3,
                    background_vehicle_count=2,
                    background_pedestrian_count=1,
                    camera_preset="wide_context",
                    fidelity_mode="high_fidelity",
                    ood_motion_smoothing="limit_step",
                    ood_max_step_m=0.5,
                ),
                run_dir,
                recipe=_recipe(),
                behavior=_behavior(),
                asset_manifests=generate_assets_dry_run(default_asset_requests()),
                carla_module=carla,
            )
            summary = write_carla_ood_demo(run_dir, result)
            report = Path(summary["report_path"]).read_text(encoding="utf-8")
            tracks = json.loads(Path(result.tracks_path or "").read_text(encoding="utf-8"))

        self.assertEqual(result.status, "passed")
        self.assertEqual(len(result.background_actor_ids), 3)
        self.assertEqual(len(tracks), 6 * 8)
        self.assertEqual(result.fidelity_metrics["fidelity_mode"], "high_fidelity")
        self.assertEqual(result.fidelity_metrics["camera_preset"], "wide_context")
        self.assertEqual(result.fidelity_metrics["background_actor_count"], 3)
        self.assertLessEqual(result.fidelity_metrics["max_ood_step_m"], 0.5)
        self.assertEqual(result.fidelity_metrics["visible_actor_count_mean"], 8.0)
        self.assertIn("fidelity_metrics", report)
        scripted_actor_types = {
            "vehicle.lincoln.mkz_2020",
            "vehicle.kawasaki.ninja",
            "static.prop.dirtdebris01",
            "static.prop.foodcart",
            "static.prop.constructioncone",
        }
        self.assertTrue(
            all(
                not actor.physics_enabled
                for actor in carla.world.spawned
                if actor.type_id in scripted_actor_types
            )
        )

    def test_load_carla_ood_demo_config_accepts_high_fidelity_fields(self) -> None:
        with TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "carla_ood_demo.json"
            config_path.write_text(
                json.dumps(
                    {
                        "carla_ood_demo": {
                            "fidelity_mode": "high_fidelity",
                            "background_vehicle_count": 4,
                            "background_pedestrian_count": 2,
                            "camera_preset": "chase",
                            "ood_motion_smoothing": "limit_step",
                            "ood_max_step_m": 0.75,
                        }
                    }
                ),
                encoding="utf-8",
            )

            config = load_carla_ood_demo_config(config_path)

        self.assertEqual(config.fidelity_mode, "high_fidelity")
        self.assertEqual(config.background_vehicle_count, 4)
        self.assertEqual(config.background_pedestrian_count, 2)
        self.assertEqual(config.camera_preset, "chase")
        self.assertEqual(config.ood_motion_smoothing, "limit_step")
        self.assertEqual(config.ood_max_step_m, 0.75)

    def test_run_carla_ood_demo_uses_road_local_not_absolute_xy(self) -> None:
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            carla = _FakeCarla()
            result = run_carla_ood_demo(
                CarlaOodDemoConfig(tick_count=1, fps=1),
                run_dir,
                recipe=_recipe(),
                behavior=_behavior(),
                carla_module=carla,
            )
            tracks = json.loads(Path(result.tracks_path or "").read_text(encoding="utf-8"))

        ood_track = next(track for track in tracks if track["actor_ref"] == "ood_actor_0")
        self.assertNotEqual(ood_track["location"]["x"], 0.0)
        self.assertAlmostEqual(ood_track["location"]["x"], 98.25)
        self.assertAlmostEqual(ood_track["location"]["y"], 200.0)

    def test_run_carla_ood_demo_retries_blocked_ego_spawn_points(self) -> None:
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            carla = _RetryFakeCarla()
            result = run_carla_ood_demo(
                CarlaOodDemoConfig(tick_count=1, fps=1),
                run_dir,
                recipe=_recipe(),
                behavior=_behavior(),
                carla_module=carla,
            )
            alignment = json.loads(Path(result.road_alignment_path or "").read_text(encoding="utf-8"))

        self.assertEqual(result.status, "passed")
        self.assertGreater(carla.world.try_count, 1)
        self.assertEqual(alignment["road_frame"]["spawn_index"], 1)

    def test_run_carla_ood_demo_retries_blocked_ood_spawn_pose(self) -> None:
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            carla = _OodCollisionRetryCarla()
            result = run_carla_ood_demo(
                CarlaOodDemoConfig(
                    tick_count=2,
                    fps=1,
                    ood_motion_smoothing="limit_step",
                    ood_max_step_m=1.0,
                ),
                run_dir,
                recipe=_recipe(),
                behavior=_behavior(),
                carla_module=carla,
            )

        self.assertEqual(result.status, "passed")
        self.assertGreater(carla.world.ood_try_count, 1)
        self.assertLessEqual(result.fidelity_metrics["max_ood_step_m"], 1.0)

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
