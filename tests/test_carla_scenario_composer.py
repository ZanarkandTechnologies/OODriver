from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.scenarios.studio_product_carla_composer_runtime import (
    build_carla_capability_matrix,
    build_default_carla_suite,
    run_studio_carla_catalog,
    run_studio_carla_control,
    run_studio_carla_compose,
    run_studio_carla_matrix,
    run_studio_carla_suite,
    run_studio_score_carla_suite,
)
from driverx.simulators.carla_catalog import resolve_map_name, weather_preset
from driverx.simulators.carla_ood_demo import _apply_world_weather, load_carla_ood_demo_config


class CarlaScenarioComposerTests(unittest.TestCase):
    def test_catalog_exposes_agent_controls_without_world_generation_claim(self) -> None:
        result = run_studio_carla_catalog()
        summary = result.summary

        self.assertEqual(result.status, "passed")
        self.assertGreaterEqual(len(summary["towns"]), 8)
        self.assertIn("Town03", {town["town_id"] for town in summary["towns"]})
        self.assertIn("night_rain_fog", summary["weather_presets"])
        self.assertIn("construction_lane_closure", {item["template_id"] for item in summary["environment_templates"]})
        self.assertIn("motorcycle_filtering", {item["behavior_id"] for item in summary["behavior_templates"]})
        self.assertIn("rolling_object", summary["object_kinds"])
        self.assertIn("carla_world_generation=false", result.claim_boundaries)
        self.assertIn("carla_existing_map_composition=true", result.claim_boundaries)

    def test_capability_matrix_preserves_live_carla_can_and_cannot_boundaries(self) -> None:
        matrix = build_carla_capability_matrix()

        self.assertIn("Town03_Opt", matrix["available_maps"])
        self.assertIn("Town10HD_Opt", matrix["available_maps"])
        self.assertIn("night_rain_fog", matrix["weather_presets"])
        self.assertIn("static.prop.foodcart", matrix["blueprint_families"])
        self.assertIn("move cameras", matrix["can"])
        self.assertIn("prompt-generate brand-new city/map geometry at runtime", matrix["cannot"])
        self.assertFalse(matrix["claim_labels"]["custom_unreal_map_import"])
        self.assertIn("arbitrary_mesh_spawn=false", matrix["claim_boundaries"])

    def test_carla_matrix_command_writes_matrix_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_studio_carla_matrix(output_root=Path(tmp), run_id="matrix")
            matrix_path = Path(result.artifacts["capability_matrix_path"])
            matrix = json.loads(matrix_path.read_text(encoding="utf-8"))

            self.assertEqual(result.status, "passed")
            self.assertTrue(matrix_path.exists())
            self.assertGreaterEqual(matrix["available_maps"].count("Town05_Opt"), 1)
            self.assertIn("custom_unreal_map_import=false", result.claim_boundaries)

    def test_compose_writes_agent_runnable_carla_config_and_runtime_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_studio_carla_compose(
                prompt="Town03 night rain construction lane blocker with rolling object",
                town="Town03",
                load_map=True,
                weather_preset_name="night_rain_fog",
                template_ids=("construction_lane_closure",),
                behavior_ids=("motorcycle_filtering", "no_signal_cut_in"),
                object_kinds=("construction_debris", "rolling_object"),
                road_anchor_spawn_index=7,
                background_vehicle_count=9,
                background_pedestrian_count=3,
                backend="fake-carla",
                output_root=Path(tmp),
                run_id="compose-smoke",
            )
            manifest_path = Path(result.artifacts["composition_manifest_path"])
            config_path = Path(result.artifacts["carla_config_path"])
            runtime_path = Path(result.artifacts["runtime_manifest_path"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
            config = load_carla_ood_demo_config(config_path)

            self.assertEqual(result.status, "passed")
            self.assertEqual(manifest["map_name"], "Town03_Opt")
            self.assertTrue(manifest["load_map"])
            self.assertEqual(config.map_name, "Town03_Opt")
            self.assertTrue(config.load_map)
            self.assertEqual(config.weather["fog_density"], 45.0)
            self.assertEqual(config.road_anchor_spawn_index, 7)
            self.assertEqual(config.background_vehicle_count, 9)
            self.assertEqual(config.background_pedestrian_count, 3)
            self.assertEqual(runtime["backend"], "fake-carla")
            self.assertEqual(runtime["behavior_case_count"], 2)
            self.assertGreaterEqual(runtime["object_spawn_spec_count"], 4)
            self.assertIn("carla_existing_map_composition=true", manifest["claim_boundaries"])

    def test_default_suite_has_ten_diverse_static_and_moving_cases(self) -> None:
        cases = build_default_carla_suite(seed=40)

        self.assertEqual(len(cases), 10)
        self.assertGreaterEqual(len({case["map_name"] for case in cases}), 4)
        self.assertGreaterEqual(len({case["weather_preset"] for case in cases}), 5)
        self.assertGreaterEqual(
            len({item for case in cases for item in case["behavior_ids"]}),
            4,
        )
        self.assertGreaterEqual(
            len({item for case in cases for item in case["object_kinds"]}),
            4,
        )
        self.assertTrue(all(any(hazard["kind"] == "static" for hazard in case["hazards"]) for case in cases))
        self.assertTrue(all(any(hazard["kind"] == "moving" for hazard in case["hazards"]) for case in cases))

    def test_carla_suite_writes_capability_gated_manifest_and_score(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_studio_carla_suite(
                probe_capabilities=True,
                output_root=Path(tmp),
                run_id="suite",
            )
            suite_path = Path(result.artifacts["suite_manifest_path"])
            manifest = json.loads(suite_path.read_text(encoding="utf-8"))
            score = run_studio_score_carla_suite(
                suite_manifest_path=suite_path,
                output_root=Path(tmp),
                run_id="suite-score",
            )

            self.assertEqual(result.status, "passed")
            self.assertEqual(len(manifest["cases"]), 10)
            self.assertFalse(manifest["gallery_ready"])
            self.assertEqual(manifest["gallery_promotion_blocker"], "TASK-167_live_image_diversity_score_required")
            self.assertTrue(Path(manifest["storyboard_path"]).exists())
            self.assertGreaterEqual(score.summary["carla_capability_suite_score"], 90.0)
            self.assertEqual(score.status, "passed")
            self.assertIn("true_flood_physics=false", score.claim_boundaries)

    def test_resolve_map_and_weather_presets(self) -> None:
        self.assertEqual(resolve_map_name("Town05"), "Town05_Opt")
        self.assertEqual(resolve_map_name("Town10HD"), "Town10HD_Opt")
        self.assertEqual(resolve_map_name(None, "Town07"), "Town07")
        self.assertEqual(weather_preset("flooded_surface")["precipitation_deposits"], 100.0)

    def test_direct_carla_control_blocks_cleanly_without_carla_package(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_studio_carla_control(
                town="Town03",
                load_map=True,
                weather_preset_name="night_rain_fog",
                output_root=Path(tmp),
                run_id="control-blocked",
            )

            self.assertEqual(result.status, "blocked")
            self.assertIn("carla_world_generation=false", result.claim_boundaries)
            self.assertTrue(Path(result.artifacts["carla_control_json_path"]).exists())

    def test_apply_world_weather_sets_known_carla_attributes(self) -> None:
        class FakeWeather:
            cloudiness = 0.0
            precipitation = 0.0
            fog_density = 0.0

        class FakeCarla:
            WeatherParameters = FakeWeather

        class FakeWorld:
            def __init__(self) -> None:
                self.weather = FakeWeather()
                self.applied = None

            def get_weather(self) -> FakeWeather:
                return self.weather

            def set_weather(self, weather: FakeWeather) -> None:
                self.applied = weather

        world = FakeWorld()
        _apply_world_weather(
            world,
            FakeCarla(),
            {"cloudiness": 80.0, "precipitation": 20.0, "fog_density": 8.0},
        )

        self.assertIsNotNone(world.applied)
        self.assertEqual(world.applied.cloudiness, 80.0)
        self.assertEqual(world.applied.precipitation, 20.0)
        self.assertEqual(world.applied.fog_density, 8.0)


if __name__ == "__main__":
    unittest.main()
