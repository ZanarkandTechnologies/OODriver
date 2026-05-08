from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.evaluation.scenario_choreography_score import (
    load_scenario_choreography_score_inputs,
    score_scenario_choreography,
)
from driverx.scenarios.choreography import build_choreography_plan
from driverx.scenarios.studio_product_choreography_runtime import (
    run_studio_choreograph,
    run_studio_score_choreography,
)


class ScenarioChoreographyTests(unittest.TestCase):
    def test_choreograph_writes_default_bad_path_task_suite(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_studio_choreograph(
                prompt="compound bad-path driving tasks",
                output_root=Path(tmp),
                run_id="choreo",
            )
            manifest_path = Path(result.artifacts["choreography_manifest_path"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            tracks_exists = Path(manifest["proof"]["tracks_path"]).exists()

        self.assertEqual(result.status, "passed")
        self.assertEqual(manifest["case_count"], 4)
        self.assertGreaterEqual(len(manifest["behavior_ids"]), 4)
        self.assertGreaterEqual(len(manifest["object_kinds"]), 4)
        self.assertIn("stop", manifest["expected_responses"])
        self.assertIn("replan", manifest["expected_responses"])
        self.assertIn("live_carla_execution=false", manifest["claim_boundaries"])
        self.assertTrue(tracks_exists)
        self.assertGreaterEqual(manifest["proof"]["entity_track_count"], 50)

    def test_score_choreography_passes_default_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            manifest = build_choreography_plan(
                "crane blocks road, scooter cuts in, rolling debris crosses",
                output_root=Path(tmp),
                run_id="choreo",
            )
            manifest_path = Path(manifest["json_path"])
            score = score_scenario_choreography(load_scenario_choreography_score_inputs(manifest_path))
            score_result = run_studio_score_choreography(
                choreography_manifest_path=manifest_path,
                output_root=Path(tmp),
                run_id="score",
            )
            score_json_exists = Path(score_result.artifacts["json_path"]).exists()

        self.assertEqual(score.status, "passed")
        self.assertGreaterEqual(score.scenario_choreography_score, 90.0)
        self.assertEqual(score_result.status, "passed")
        self.assertIn("scenario_choreography_score", score_result.summary)
        self.assertTrue(score_json_exists)

    def test_custom_choreography_keeps_no_live_overclaim(self) -> None:
        with TemporaryDirectory() as tmp:
            manifest = build_choreography_plan(
                "single custom moving object pressure",
                behavior_ids=("no_signal_cut_in",),
                object_kinds=("rolling_object",),
                output_root=Path(tmp),
                run_id="custom",
            )

        self.assertEqual(manifest["case_count"], 1)
        self.assertIn("custom_unreal_map_import=false", manifest["claim_boundaries"])
        self.assertEqual(manifest["proof"]["live_carla_execution"], False)


if __name__ == "__main__":
    unittest.main()
