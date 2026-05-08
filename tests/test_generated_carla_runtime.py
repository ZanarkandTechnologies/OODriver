from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.evaluation.generator_runtime_score import (
    load_generator_runtime_score_inputs,
    score_generator_runtime,
)
from driverx.scenarios.generated_runtime import (
    build_generated_scenario_runtime_spec,
    run_generated_scenario_runtime,
)
from driverx.scenarios.studio_product_generated_runtime import (
    run_studio_generate_run,
    run_studio_score_generator_runtime,
)


PROMPT = "wet Malaysian roadwork, scooter cut-in, lane debris"
BEHAVIORS = ("motorcycle_filtering", "no_signal_cut_in", "unsignaled_u_turn")
OBJECTS = ("construction_debris", "roadside_vendor")


class GeneratedCarlaRuntimeTests(unittest.TestCase):
    def test_dry_run_writes_runtime_spec_without_carla(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_studio_generate_run(
                prompt=PROMPT,
                template_ids=("construction_lane_closure",),
                behavior_ids=("motorcycle_filtering",),
                object_kinds=OBJECTS,
                backend="dry-run",
                config_path=Path(tmp) / "missing-carla-config.yaml",
                output_root=Path(tmp),
                run_id="dry",
            )
            manifest = json.loads(Path(result.artifacts["json_path"]).read_text(encoding="utf-8"))
            spec = json.loads(Path(result.artifacts["spec_path"]).read_text(encoding="utf-8"))

        self.assertEqual(result.command, "oodrive generate-run")
        self.assertEqual(result.status, "passed")
        self.assertEqual(manifest["backend"], "dry-run")
        self.assertEqual(manifest["runtime_proof"]["backend"], "dry-run")
        self.assertGreaterEqual(manifest["object_spawn_spec_count"], 2)
        self.assertIn("generated_vehicle_behaviors=true", manifest["claim_boundaries"])
        self.assertIn("objects_spawned_in_carla=false", manifest["claim_boundaries"])
        self.assertTrue(spec["validation"]["passes"])

    def test_fake_carla_runtime_proves_behavior_object_spawns_and_scores(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_studio_generate_run(
                prompt=PROMPT,
                template_ids=("construction_lane_closure",),
                behavior_ids=BEHAVIORS,
                object_kinds=OBJECTS,
                backend="fake-carla",
                output_root=Path(tmp),
                run_id="fake",
            )
            manifest_path = Path(result.artifacts["json_path"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            proof = manifest["runtime_proof"]
            score = score_generator_runtime(load_generator_runtime_score_inputs(manifest_path))
            tracks_exists = Path(proof["tracks_path"]).exists()

        self.assertEqual(result.status, "passed")
        self.assertEqual(manifest["behavior_case_count"], 3)
        self.assertGreaterEqual(manifest["object_spawn_spec_count"], 2)
        self.assertEqual(proof["backend"], "fake-carla")
        self.assertEqual(proof["status"], "passed")
        self.assertGreaterEqual(proof["static_object_spawn_count"], 2)
        self.assertEqual(proof["dynamic_actor_spawn_count"], 3)
        self.assertTrue(set(proof["spawned_actor_ids"]).issubset(set(proof["destroyed_actor_ids"])))
        self.assertTrue(tracks_exists)
        self.assertGreaterEqual(score.generator_runtime_score, 90.0)
        self.assertEqual(score.status, "passed")

    def test_live_backend_blocks_cleanly_without_carla_package(self) -> None:
        with TemporaryDirectory() as tmp:
            spec = build_generated_scenario_runtime_spec(
                prompt=PROMPT,
                template_ids=("construction_lane_closure",),
                behavior_ids=("motorcycle_filtering",),
                object_kinds=OBJECTS,
                output_root=Path(tmp),
                run_id="live",
            )
            result = run_generated_scenario_runtime(
                spec,
                backend="carla-live",
                output_root=Path(spec["run_dir"]),
                run_id=spec["run_id"],
            )

        self.assertIn(result["status"], {"blocked", "passed", "partial"})
        self.assertEqual(result["runtime_proof"]["backend"], "carla-live")
        if result["status"] == "blocked":
            self.assertTrue(
                any("CARLA Python package" in item or "CARLA" in item for item in result["blockers"])
            )
            self.assertIn("objects_spawned_in_carla=false", result["claim_boundaries"])
        else:
            self.assertTrue(
                any(
                    item in result["claim_boundaries"]
                    for item in ("objects_spawned_in_carla=true", "objects_spawned_in_carla=false")
                )
            )

    def test_score_runtime_command_emits_artifact_summary(self) -> None:
        with TemporaryDirectory() as tmp:
            run = run_studio_generate_run(
                prompt=PROMPT,
                template_ids=("construction_lane_closure",),
                behavior_ids=BEHAVIORS,
                object_kinds=OBJECTS,
                backend="fake-carla",
                output_root=Path(tmp),
                run_id="fake",
            )
            score = run_studio_score_generator_runtime(
                runtime_manifest_path=Path(run.artifacts["json_path"]),
                output_root=Path(tmp),
                run_id="score",
            )
            score_json_exists = Path(score.artifacts["json_path"]).exists()

        self.assertEqual(score.command, "oodrive score-generator-runtime")
        self.assertEqual(score.status, "passed")
        self.assertGreaterEqual(score.summary["generator_runtime_score"], 90.0)
        self.assertTrue(score_json_exists)

    def test_live_score_accepts_case_result_tracks_path(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            tracks_path = root / "entity_tracks.json"
            tracks_path.write_text(json.dumps([{"tick": 0}, {"tick": 1}]), encoding="utf-8")
            manifest_path = root / "generated_scenario_runtime.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "status": "passed",
                        "prompt": PROMPT,
                        "scenario_id": "live-score-fallback",
                        "environment_recipe_id": "env",
                        "behavior_case_count": 1,
                        "object_spawn_spec_count": 2,
                        "behavior_cases": [
                            {
                                "behavior_id": "motorcycle_filtering",
                                "validation": {"passes": True},
                            }
                        ],
                        "object_spawn_specs": [
                            {"blueprint_filter": "static.prop.dirtdebris01", "spawn_transform": {}},
                            {"blueprint_filter": "static.prop.foodcart", "spawn_transform": {}},
                        ],
                        "asset_requests": [{}, {}],
                        "validation": {"passes": True},
                        "runtime_proof": {
                            "backend": "carla-live",
                            "status": "passed",
                            "static_object_spawn_count": 2,
                            "dynamic_actor_spawn_count": 1,
                            "applied_behavior_tick_count": 12,
                            "track_count": 2,
                            "spawned_actor_ids": [1],
                            "destroyed_actor_ids": [1],
                            "json_path": str(root / "generated_runtime_live_carla_proof.json"),
                            "case_results": [{"tracks_path": str(tracks_path)}],
                        },
                        "claim_boundaries": [
                            "generated_vehicle_behaviors=true",
                            "objects_spawned_in_carla=true",
                            "generator_runtime_backend=carla-live",
                            "closed_loop_vla_control=false",
                            "real_time_vla_control=false",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (root / "generated_runtime_live_carla_proof.json").write_text("{}", encoding="utf-8")

            score = score_generator_runtime(load_generator_runtime_score_inputs(manifest_path))

        self.assertNotIn("missing runtime entity tracks", score.blockers)


if __name__ == "__main__":
    unittest.main()
