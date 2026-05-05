import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.behaviors import default_behavior_plans, simulate_behavior, write_behavior_suite


class BehaviorLibraryTest(unittest.TestCase):
    def test_default_behavior_suite_has_regional_ood_cases(self) -> None:
        plans = default_behavior_plans()
        behavior_ids = {plan.behavior_id for plan in plans}

        self.assertIn("no_signal_cut_in", behavior_ids)
        self.assertIn("sudden_brake", behavior_ids)
        self.assertIn("motorcycle_filtering", behavior_ids)
        self.assertIn("wrong_way_shoulder_creep", behavior_ids)
        self.assertIn("informal_right_of_way_push", behavior_ids)
        self.assertIn("stunt_motorcycle_proxy", behavior_ids)
        self.assertIn("double_parked_door_swerve", behavior_ids)
        self.assertIn("unsignaled_u_turn", behavior_ids)

    def test_no_signal_cut_in_has_large_lateral_displacement(self) -> None:
        plan = next(plan for plan in default_behavior_plans() if plan.behavior_id == "no_signal_cut_in")
        trace = simulate_behavior(plan)

        self.assertGreaterEqual(trace.metrics["lateral_displacement_m"], 3.0)
        self.assertIn("no_signal", plan.tags)

    def test_sudden_brake_has_hard_deceleration(self) -> None:
        plan = next(plan for plan in default_behavior_plans() if plan.behavior_id == "sudden_brake")
        trace = simulate_behavior(plan)

        self.assertGreaterEqual(trace.metrics["max_deceleration_mps2"], 8.0)

    def test_motorcycle_filtering_has_lateral_uncertainty(self) -> None:
        plan = next(plan for plan in default_behavior_plans() if plan.behavior_id == "motorcycle_filtering")
        trace = simulate_behavior(plan)

        self.assertGreaterEqual(trace.metrics["max_lateral_speed_mps"], 4.0)
        self.assertIn("lateral_uncertainty", plan.tags)

    def test_wrong_way_shoulder_creep_moves_against_route(self) -> None:
        plan = next(plan for plan in default_behavior_plans() if plan.behavior_id == "wrong_way_shoulder_creep")
        trace = simulate_behavior(plan)

        self.assertGreater(trace.metrics["wrong_way_distance_m"], 5.0)
        self.assertIn("wrong_way", plan.tags)

    def test_double_parked_door_swerve_intrudes_laterally(self) -> None:
        plan = next(plan for plan in default_behavior_plans() if plan.behavior_id == "double_parked_door_swerve")
        trace = simulate_behavior(plan)
        y_values = [sample.y_m for sample in trace.samples]

        self.assertLess(min(y_values), 0.6)
        self.assertGreater(trace.metrics["max_lateral_speed_mps"], 3.0)
        self.assertIn("urban_clutter", plan.tags)

    def test_unsignaled_u_turn_reverses_heading(self) -> None:
        plan = next(plan for plan in default_behavior_plans() if plan.behavior_id == "unsignaled_u_turn")
        trace = simulate_behavior(plan)

        self.assertGreaterEqual(trace.metrics["max_heading_abs_deg"], 170.0)
        self.assertIn("heading_reversal", plan.tags)

    def test_write_behavior_suite_artifacts(self) -> None:
        traces = [simulate_behavior(plan) for plan in default_behavior_plans()]
        with TemporaryDirectory() as tmp:
            summary = write_behavior_suite(Path(tmp), traces)
            payload = json.loads(Path(summary["summary_path"]).read_text(encoding="utf-8"))
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertEqual(payload["num_behaviors"], 8)
        self.assertIn("stunt_motorcycle_proxy", report)
        self.assertIn("unsignaled_u_turn", report)


if __name__ == "__main__":
    unittest.main()
