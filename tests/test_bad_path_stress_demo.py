from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.pipeline.bad_path_stress_demo import DEFAULT_CASE_IDS, build_bad_path_stress_demo
from driverx.scenarios.studio_product_stress_runtime import run_studio_stress_demo


class BadPathStressDemoTests(unittest.TestCase):
    def test_stress_demo_builds_default_bad_path_cases(self) -> None:
        with TemporaryDirectory() as tmp:
            output = build_bad_path_stress_demo(
                output_root=Path(tmp),
                run_id="stress",
                target_duration_s=9.0,
                fps=2,
            )

            self.assertEqual(output["status"], "passed")
            self.assertEqual([case["case_id"] for case in output["cases"]], list(DEFAULT_CASE_IDS))
            self.assertGreaterEqual(output["bad_path_stress_score"], 90.0)
            self.assertTrue(Path(output["json_path"]).exists())
            self.assertTrue(Path(output["report_path"]).exists())
            self.assertTrue(Path(output["html_path"]).exists())
            self.assertIn("closed_loop_vla_control=false", output["claim_boundaries"])
            for case in output["cases"]:
                self.assertTrue(case["baseline"]["collision_proxy"], case["case_id"])
                self.assertFalse(case["guarded"]["collision_proxy"], case["case_id"])
                self.assertFalse(case["guarded"]["lane_departure_proxy"], case["case_id"])
                self.assertLessEqual(case["guarded"]["max_abs_y_m"], 3.25, case["case_id"])
                self.assertTrue(case["guarded"]["task_pass"], case["case_id"])
                first_state = case["guarded"]["trace"][0]
                self.assertIn("speed_mps", first_state)
                self.assertIn("throttle", first_state)
                self.assertIn("brake", first_state)
                self.assertIn("steer", first_state)
                self.assertIn("decision", first_state)

    def test_static_blocker_guarded_response_stops_before_obstacle(self) -> None:
        with TemporaryDirectory() as tmp:
            output = build_bad_path_stress_demo(
                output_root=Path(tmp),
                run_id="stress",
                case_ids=("static_blocker_stop",),
                target_duration_s=9.0,
                fps=2,
            )
            case = output["cases"][0]

            self.assertTrue(case["guarded"]["task_checks"]["stopped_before_blocker"])
            self.assertEqual(case["guarded"]["trace"][-1]["speed_mps"], 0.0)
            self.assertGreater(case["guarded"]["trace"][-1]["brake"], 0.0)

    def test_road_hole_guarded_response_swerve_and_recovers(self) -> None:
        with TemporaryDirectory() as tmp:
            output = build_bad_path_stress_demo(
                output_root=Path(tmp),
                run_id="stress",
                case_ids=("road_hole_swerve_recover",),
                target_duration_s=9.0,
                fps=2,
            )
            case = output["cases"][0]

            self.assertTrue(case["guarded"]["task_checks"]["swerved_around_hole"])
            self.assertTrue(case["guarded"]["task_checks"]["continued_beyond_hole"])
            self.assertTrue(case["guarded"]["task_checks"]["recovered_lane"])
            self.assertTrue(case["guarded"]["task_checks"]["stayed_in_drivable_corridor"])
            self.assertFalse(case["guarded"]["lane_departure_proxy"])

    def test_rolling_object_guarded_response_slows_and_resumes(self) -> None:
        with TemporaryDirectory() as tmp:
            output = build_bad_path_stress_demo(
                output_root=Path(tmp),
                run_id="stress",
                case_ids=("rolling_object_yield_swerve",),
                target_duration_s=9.0,
                fps=2,
            )
            case = output["cases"][0]

            self.assertTrue(case["guarded"]["task_checks"]["slowed_before_conflict"])
            self.assertTrue(case["guarded"]["task_checks"]["swerved_from_collision_course"])
            self.assertTrue(case["guarded"]["task_checks"]["resumed_after_clear"])
            self.assertTrue(case["guarded"]["task_checks"]["stayed_in_drivable_corridor"])
            self.assertFalse(case["guarded"]["lane_departure_proxy"])

    def test_runtime_returns_product_command_result(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_studio_stress_demo(
                output_root=Path(tmp),
                run_id="stress",
                target_duration_s=9.0,
                fps=2,
            )

            self.assertEqual(result.command, "oodrive stress-demo")
            self.assertEqual(result.status, "passed")
            self.assertEqual(result.summary["case_count"], len(DEFAULT_CASE_IDS))
            self.assertTrue(Path(result.artifacts["json_path"]).exists())

    def test_compound_case_stops_detours_slows_and_recovers(self) -> None:
        with TemporaryDirectory() as tmp:
            output = build_bad_path_stress_demo(
                output_root=Path(tmp),
                run_id="stress",
                case_ids=("compound_obstacle_detour",),
                target_duration_s=12.0,
                fps=2,
            )
            case = output["cases"][0]

            self.assertTrue(case["guarded"]["task_checks"]["stopped_before_replan"])
            self.assertTrue(case["guarded"]["task_checks"]["found_alternative_route"])
            self.assertTrue(case["guarded"]["task_checks"]["slowed_in_detour"])
            self.assertTrue(case["guarded"]["task_checks"]["recovered_forward"])
            self.assertTrue(case["guarded"]["task_checks"]["stayed_in_drivable_corridor"])
            self.assertFalse(case["guarded"]["collision_proxy"])
            self.assertFalse(case["guarded"]["lane_departure_proxy"])


if __name__ == "__main__":
    unittest.main()
