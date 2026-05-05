import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.behaviors import default_behavior_plans, simulate_behavior
from driverx.datasets.fixtures import load_fixture_frame
from driverx.policies import PolicyContext, sample_memory_entries, select_policy_adapter
from driverx.policies.trajectory_control import trajectory_to_control_trace
from driverx.scenarios import MutationPolicy, generate_scenario_recipes, load_scenario_seeds
from driverx.simulators.local_ood_sim import run_local_ood_sim, write_local_ood_sim_result


class LocalOodSimTest(unittest.TestCase):
    def test_local_ood_sim_writes_visual_and_timeline_artifacts(self) -> None:
        seeds = load_scenario_seeds(Path("tests/fixtures/fail2drive_like/seeds.json"))
        recipe = generate_scenario_recipes(
            seeds,
            MutationPolicy(mutations=("regional_driving_behavior",)),
            count=1,
            random_seed=7,
        )[0]
        behavior_plan = {
            plan.behavior_id: plan
            for plan in default_behavior_plans()
        }["motorcycle_filtering"]
        behavior = simulate_behavior(behavior_plan)
        frame = load_fixture_frame("construction_merge")
        baseline = select_policy_adapter("mock").decide(PolicyContext(frame=frame, recipe=recipe))
        memory = select_policy_adapter("mock-memory").decide(
            PolicyContext(frame=frame, recipe=recipe, memories=sample_memory_entries())
        )
        decisions = [("policy", baseline), ("policy+memory", memory)]
        controls = [
            (
                label,
                trajectory_to_control_trace(
                    decision.action.trajectory,
                    source_policy_id=label,
                ),
            )
            for label, decision in decisions
            if decision.action.trajectory is not None
        ]
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            result = run_local_ood_sim(
                recipe=recipe,
                behavior=behavior,
                decisions=decisions,
                control_traces=controls,
                output_dir=run_dir,
            )
            summary = write_local_ood_sim_result(run_dir, result)
            timeline = json.loads(Path(summary["timeline_path"]).read_text(encoding="utf-8"))
            svg_exists = Path(summary["svg_path"]).exists()
            html_exists = Path(summary["html_path"]).exists()
            html = Path(summary["html_path"]).read_text(encoding="utf-8")
            json_exists = Path(summary["json_path"]).exists()

        self.assertEqual(result.simulator_kind, "driverx_local_2d_ood_sim")
        self.assertEqual(len(result.policy_tracks), 2)
        self.assertTrue(svg_exists)
        self.assertTrue(html_exists)
        self.assertTrue(json_exists)
        self.assertIn("policy+memory", timeline["policy_paths"])
        self.assertIn("Timeline Tracks", html)
        self.assertIn("OOD actor", html)

    def test_local_ood_sim_records_memory_track_as_slower_yielding_policy(self) -> None:
        seeds = load_scenario_seeds(Path("tests/fixtures/fail2drive_like/seeds.json"))
        recipe = generate_scenario_recipes(
            seeds,
            MutationPolicy(mutations=("regional_driving_behavior",)),
            count=1,
            random_seed=7,
        )[0]
        behavior = simulate_behavior(
            {
                plan.behavior_id: plan
                for plan in default_behavior_plans()
            }["motorcycle_filtering"]
        )
        frame = load_fixture_frame("construction_merge")
        baseline = select_policy_adapter("mock").decide(PolicyContext(frame=frame, recipe=recipe))
        memory = select_policy_adapter("mock-memory").decide(
            PolicyContext(frame=frame, recipe=recipe, memories=sample_memory_entries())
        )
        decisions = [("policy", baseline), ("policy+memory", memory)]
        controls = [
            (
                label,
                trajectory_to_control_trace(
                    decision.action.trajectory,
                    source_policy_id=label,
                ),
            )
            for label, decision in decisions
            if decision.action.trajectory is not None
        ]
        with TemporaryDirectory() as tmp:
            result = run_local_ood_sim(
                recipe=recipe,
                behavior=behavior,
                decisions=decisions,
                control_traces=controls,
                output_dir=Path(tmp),
            )
        controls = {
            track.label: track.decision.action.control
            for track in result.policy_tracks
        }
        risk_levels = {
            track.label: track.risk_level
            for track in result.policy_tracks
        }

        self.assertTrue(controls["policy+memory"]["yield"])
        self.assertLess(
            controls["policy+memory"]["target_speed_mps"],
            controls["policy"]["target_speed_mps"],
        )
        self.assertEqual(risk_levels["policy+memory"], "near_miss_proxy")


if __name__ == "__main__":
    unittest.main()
