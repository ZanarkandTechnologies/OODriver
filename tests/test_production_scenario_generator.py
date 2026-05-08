from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.evaluation.research_scenario_generator_score import score_research_scenario_generator
from driverx.scenarios.studio_product_production_runtime import (
    run_studio_compile_scenario,
    run_studio_generate_assets,
    run_studio_install_assets,
    run_studio_run_scenario,
    run_studio_scenario_pack,
    run_studio_score_research_generator,
)


PROMPT = "wet Malaysian roadwork with scooter filtering around debris and a roadside vendor"


class ProductionScenarioGeneratorTests(unittest.TestCase):
    def test_scenario_pack_to_fake_carla_to_metric_flow(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack_result = run_studio_scenario_pack(
                prompt=PROMPT,
                template_ids=("construction_lane_closure",),
                behavior_ids=("motorcycle_filtering",),
                object_kinds=("construction_debris", "roadside_vendor"),
                output_root=root,
                run_id="pack",
            )
            pack_path = Path(pack_result.artifacts["scenario_pack_path"])
            asset_result = run_studio_generate_assets(
                scenario_pack_path=pack_path,
                output_root=root,
                run_id="assets",
            )
            asset_pack_path = Path(asset_result.artifacts["scenario_pack_path"])
            registry_result = run_studio_install_assets(
                scenario_pack_path=asset_pack_path,
                output_root=root,
                run_id="registry",
            )
            graph_result = run_studio_compile_scenario(
                scenario_pack_path=asset_pack_path,
                asset_registry_path=Path(registry_result.artifacts["asset_registry_path"]),
                output_root=root,
                run_id="graph",
            )
            run_result = run_studio_run_scenario(
                scenario_pack_path=asset_pack_path,
                scenario_graph_path=Path(graph_result.artifacts["scenario_graph_path"]),
                asset_registry_path=Path(registry_result.artifacts["asset_registry_path"]),
                output_root=root,
                run_id="fake-run",
            )
            score = score_research_scenario_generator(
                scenario_pack_path=asset_pack_path,
                asset_manifest_paths=(Path(asset_result.artifacts["asset_generation_manifest_path"]),),
                asset_registry_path=Path(registry_result.artifacts["asset_registry_path"]),
                scenario_graph_path=Path(graph_result.artifacts["scenario_graph_path"]),
                run_manifest_paths=(Path(run_result.artifacts["run_manifest_path"]),),
            )
            tracks_exists = Path(run_result.artifacts["tracks_path"]).exists()

        self.assertEqual(pack_result.status, "passed")
        self.assertEqual(asset_result.status, "passed")
        self.assertEqual(registry_result.status, "passed")
        self.assertEqual(graph_result.status, "passed")
        self.assertEqual(run_result.status, "passed")
        self.assertGreaterEqual(score["research_scenario_generator_score"], 70.0)
        self.assertEqual(score["components"]["carla_asset_import"], 5.0)
        self.assertTrue(tracks_exists)

    def test_live_backend_blocks_cleanly_without_local_carla(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack_result = run_studio_scenario_pack(
                prompt=PROMPT,
                template_ids=("construction_lane_closure",),
                behavior_ids=("motorcycle_filtering",),
                object_kinds=("construction_debris", "roadside_vendor"),
                output_root=root,
                run_id="pack",
            )
            run_result = run_studio_run_scenario(
                scenario_pack_path=Path(pack_result.artifacts["scenario_pack_path"]),
                backend="carla-live",
                output_root=root,
                run_id="live",
            )

        self.assertIn(run_result.status, {"blocked", "passed", "partial"})
        if run_result.status == "blocked":
            self.assertTrue(any("CARLA Python package" in item or "CARLA" in item for item in run_result.blockers))
            self.assertIn("objects_spawned_in_carla=false", run_result.claim_boundaries)
        else:
            self.assertEqual(run_result.summary["backend"], "carla-live")

    def test_score_command_writes_metric_artifact(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack_result = run_studio_scenario_pack(
                prompt=PROMPT,
                behavior_ids=("motorcycle_filtering",),
                object_kinds=("construction_debris",),
                output_root=root,
                run_id="pack",
            )
            score_result = run_studio_score_research_generator(
                scenario_pack_path=Path(pack_result.artifacts["scenario_pack_path"]),
                output_root=root,
                run_id="score",
            )
            score_json = json.loads(Path(score_result.artifacts["json_path"]).read_text(encoding="utf-8"))

        self.assertEqual(score_result.command, "oodrive score-research-generator")
        self.assertIn(score_result.status, {"partial", "blocked"})
        self.assertIn("research_scenario_generator_score", score_json)

    def test_partial_image_qa_caps_flagship_score(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack_result = run_studio_scenario_pack(
                prompt=PROMPT,
                behavior_ids=("motorcycle_filtering",),
                object_kinds=("construction_debris",),
                output_root=root,
                run_id="pack",
            )
            image_qa = root / "image_qa.json"
            image_qa.write_text(
                json.dumps(
                    {
                        "schema_version": "oodrive.prompt_image_qa.v1",
                        "verdict": "partial",
                        "real_carla_evidence": {"verdict": "likely_real_carla"},
                    }
                ),
                encoding="utf-8",
            )
            score = score_research_scenario_generator(
                scenario_pack_path=Path(pack_result.artifacts["scenario_pack_path"]),
                image_qa_report_path=image_qa,
                workbench_summary_path=image_qa,
                library_path=image_qa,
            )

        self.assertLessEqual(score["research_scenario_generator_score"], 92.0)
        self.assertEqual(score["status"], "partial")
        self.assertEqual(score["components"]["prompt_image_match"], 4.0)


if __name__ == "__main__":
    unittest.main()
