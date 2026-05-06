import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.scenarios.studio import (
    ScenarioStudioConfig,
    compile_scenario_prompt,
    expand_studio_plan,
    generate_studio_batch,
    score_studio_candidate,
)


class ScenarioStudioTest(unittest.TestCase):
    def test_prompt_compiler_extracts_malaysian_roadwork_case(self) -> None:
        plan = compile_scenario_prompt(
            "Malaysian wet roadwork: motorbike filters between cars while a lorry brakes without signal",
            seed=17,
        )

        self.assertTrue(plan.validation.passes)
        self.assertEqual(plan.environment_template_id, "construction_lane_closure")
        self.assertEqual(plan.behavior_template_id, "motorcycle_filtering")
        self.assertIn("malaysian_driving", plan.ood_tags)
        self.assertIn("motorcycle_filtering", plan.memory_query)
        self.assertIn("slow", plan.safe_behavior_principle)

    def test_unknown_prompt_is_rejected_by_curation(self) -> None:
        plan = compile_scenario_prompt("quantum elevator banana", seed=1)
        candidate = expand_studio_plan(plan, count=1, random_seed=3)[0]
        record = score_studio_candidate(candidate, [])

        self.assertFalse(plan.validation.passes)
        self.assertEqual(record.curation_status, "reject_invalid")
        self.assertIn("unsupported_prompt", plan.validation.errors[0])

    def test_generate_studio_batch_writes_gallery_and_recipes(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = generate_studio_batch(
                ScenarioStudioConfig(
                    prompts=(
                        "School-zone occlusion: parked van hides a child crossing while a dropped bag sits near the lane edge",
                        "Flooded urban road: low obstacle blends into water while traffic creeps around cones",
                    ),
                    output_root=Path(tmp),
                    run_id="studio",
                    count_per_prompt=2,
                    random_seed=11,
                    severity=4,
                )
            )

            self.assertEqual(summary["prompt_count"], 2)
            self.assertEqual(summary["candidate_count"], 4)
            self.assertTrue(Path(summary["json_path"]).exists())
            self.assertTrue(Path(summary["gallery_path"]).exists())
            self.assertTrue(Path(summary["recipes_path"]).exists())
            self.assertIn("accept_partial", summary["curation_counts"])

    def test_scenario_studio_cli_accepts_prompt_override(self) -> None:
        with TemporaryDirectory() as tmp:
            config = Path(tmp) / "studio.json"
            config.write_text(
                json.dumps(
                    {
                        "scenario_studio": {
                            "prompts": ["Night rain glare: reflective sign distracts the policy near a lane closure"],
                            "count_per_prompt": 1,
                            "severity": 3,
                            "random_seed": 5,
                        },
                        "output": {"root": tmp, "run_id": "studio-cli"},
                    }
                ),
                encoding="utf-8",
            )
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "generate-scenario-studio",
                        "--config",
                        str(config),
                        "--prompt",
                        "Dense Malaysian traffic: wrong-way shoulder creep appears beside roadside food stalls",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "override",
                    ]
                )
            summary = json.loads(stream.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["prompt_count"], 1)
        self.assertEqual(summary["candidate_count"], 1)
        self.assertEqual(summary["plans"][0]["behavior_template_id"], "wrong_way_shoulder_creep")


if __name__ == "__main__":
    unittest.main()
