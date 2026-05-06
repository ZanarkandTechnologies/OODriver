import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.behaviors import default_behavior_plans, simulate_behavior
from driverx.scenarios import MutationPolicy, generate_scenario_recipes, load_scenario_seeds
from driverx.simulators import compile_carla_script_plan, validate_carla_script_plan
from driverx.simulators import write_carla_script_plan


class CarlaScriptCompilerTest(unittest.TestCase):
    def _recipe(self):
        seeds = load_scenario_seeds(Path("tests/fixtures/fail2drive_like/seeds.json"))
        return generate_scenario_recipes(
            seeds,
            MutationPolicy(mutations=("occlusion",)),
            count=1,
            random_seed=5,
        )[0]

    def test_compile_carla_script_plan_is_valid(self) -> None:
        recipe = self._recipe()
        behavior = simulate_behavior(
            next(plan for plan in default_behavior_plans() if plan.behavior_id == "motorcycle_filtering")
        )
        plan = compile_carla_script_plan(recipe, behavior, Path("artifacts/carla-script-test"))

        self.assertEqual(plan.recipe_id, recipe.recipe_id)
        self.assertEqual(plan.behavior_id, "motorcycle_filtering")
        self.assertEqual(plan.coordinate_frame, "road_local")
        self.assertEqual(plan.road_frame_selector.spawn_index, 0)
        self.assertEqual(validate_carla_script_plan(plan), [])
        self.assertEqual(plan.actors[0].role, "ego")
        self.assertEqual(plan.actors[0].spawn_transform["location"]["x"], 0.0)
        self.assertEqual(plan.actors[1].spawn_transform["location"]["y"], behavior.samples[0].y_m)
        self.assertEqual(plan.actors[1].sample_count, len(behavior.samples))
        self.assertEqual(plan.cleanup_order[-1], "ego")

    def test_compile_carla_script_requires_route_path(self) -> None:
        recipe = self._recipe()
        route_less = type(recipe)(
            recipe_id=recipe.recipe_id,
            parent_seed_id=recipe.parent_seed_id,
            mutation=recipe.mutation,
            actors=recipe.actors,
            environment=recipe.environment,
            expected_failure_mode=recipe.expected_failure_mode,
            memory_query=recipe.memory_query,
            route_path=None,
        )
        behavior = simulate_behavior(default_behavior_plans()[0])

        with self.assertRaisesRegex(ValueError, "route_path is required"):
            compile_carla_script_plan(route_less, behavior, Path("unused"))

    def test_write_carla_script_plan_artifacts(self) -> None:
        recipe = self._recipe()
        behavior = simulate_behavior(default_behavior_plans()[0])
        with TemporaryDirectory() as tmp:
            plan = compile_carla_script_plan(recipe, behavior, Path(tmp))
            summary = write_carla_script_plan(Path(tmp), plan)
            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertEqual(payload["behavior_id"], behavior.plan.behavior_id)
        self.assertEqual(payload["coordinate_frame"], "road_local")
        self.assertIn("road_frame_selector", payload)
        self.assertEqual(summary["validation_errors"], [])
        self.assertIn("# CARLA Script Plan", report)


if __name__ == "__main__":
    unittest.main()
