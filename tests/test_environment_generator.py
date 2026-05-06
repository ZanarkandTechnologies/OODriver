import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.assets import environment_recipe_to_asset_requests, generate_assets_dry_run
from driverx.cli import main
from driverx.environments import (
    EnvironmentSuiteConfig,
    RoadFrameHint,
    environment_to_asset_requests,
    environment_to_carla_weather,
    generate_environment_recipe,
    generate_environment_suite,
    load_environment_pack,
    run_environment_forge,
)
from driverx.scenarios import ScenarioRecipe
from driverx.environments import attach_environment_to_recipe


class EnvironmentGeneratorTest(unittest.TestCase):
    def test_default_pack_contains_six_submission_families(self) -> None:
        templates = load_environment_pack()
        families = {template.family for template in templates}

        self.assertGreaterEqual(len(families), 6)
        self.assertIn("pedestrian_occlusion", families)

    def test_environment_generation_is_deterministic(self) -> None:
        first = generate_environment_recipe(
            "construction_lane_closure",
            severity=4,
            random_seed=42,
        )
        second = generate_environment_recipe(
            "construction_lane_closure",
            severity=4,
            random_seed=42,
        )

        self.assertEqual(first.to_jsonable(), second.to_jsonable())
        self.assertEqual(first.family, "construction")
        self.assertEqual(first.severity, 4)
        self.assertGreaterEqual(len(first.assets), 2)
        self.assertIn("construction", first.tags)

    def test_environment_to_assets_and_weather_are_carla_ready(self) -> None:
        recipe = generate_environment_recipe("flooded_road", severity=5, random_seed=3)
        requests = environment_to_asset_requests(
            recipe,
            RoadFrameHint(right_shoulder_y_m=-4.5),
        )
        manifests = generate_assets_dry_run(requests)
        weather = environment_to_carla_weather(recipe)

        self.assertGreaterEqual(float(weather["precipitation"]), 80.0)
        self.assertTrue(all(request.source_recipe_id == recipe.recipe_id for request in requests))
        self.assertTrue(all(request.intended_placement["coordinate_frame"] == "road_local" for request in requests))
        self.assertEqual(len(manifests), len(requests))
        self.assertTrue(all(manifest.status == "planned" for manifest in manifests))

    def test_assets_pipeline_exposes_environment_conversion(self) -> None:
        recipe = generate_environment_recipe("roadside_market_occlusion", severity=3, random_seed=8)
        direct = environment_to_asset_requests(recipe)
        via_assets = environment_recipe_to_asset_requests(recipe)

        self.assertEqual([item.to_jsonable() for item in direct], [item.to_jsonable() for item in via_assets])

    def test_environment_attaches_to_scenario_recipe(self) -> None:
        environment = generate_environment_recipe("dense_regional_traffic", severity=3, random_seed=11)
        recipe = ScenarioRecipe(
            recipe_id="generated-test",
            parent_seed_id="seed",
            mutation="regional_driving_behavior",
            actors=[],
            environment={},
            expected_failure_mode="misses motorbike",
            memory_query=["motorcycle"],
        )
        attached = attach_environment_to_recipe(recipe, environment)

        self.assertEqual(attached.environment["environment_recipe_id"], environment.recipe_id)
        self.assertIn("malaysian_driving", attached.memory_query)
        self.assertTrue(any(actor["kind"] == "static_asset" for actor in attached.actors))

    def test_environment_forge_writes_reports(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = run_environment_forge(
                EnvironmentSuiteConfig(
                    template_ids=("night_rain_fog", "flooded_road", "school_zone_unstructured_crossing"),
                    severity=2,
                    count=4,
                    random_seed=4,
                    output_root=Path(tmp),
                    run_id="env",
                )
            )

            self.assertEqual(summary["num_recipes"], 4)
            self.assertTrue(Path(summary["recipes_path"]).exists())
            self.assertTrue(Path(summary["report_path"]).exists())
            self.assertIn("weather_surface", summary["families"])
            self.assertIn("pedestrian_occlusion", summary["families"])

    def test_forge_environments_cli_writes_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "forge-environments",
                        "--config",
                        "configs/environment_forge.sample.yaml",
                        "--template-id",
                        "construction_lane_closure",
                        "--count",
                        "1",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "env-cli",
                    ]
                )
            summary = json.loads(stream.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["num_recipes"], 1)
        self.assertEqual(summary["families"], ["construction"])


if __name__ == "__main__":
    unittest.main()
