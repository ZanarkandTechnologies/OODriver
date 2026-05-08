from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.scenarios.studio_product_environment_runtime import (
    build_environment_visual_candidate,
    run_studio_generate_envs,
    run_studio_render_env,
    select_environment_recipe,
    write_environment_carla_visual_proof,
)


class EnvironmentToCarlaVisualProofTests(unittest.TestCase):
    def test_render_env_dry_run_writes_same_lineage_artifacts_without_carla(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated = run_studio_generate_envs(
                template_ids=("roadside_market_occlusion",),
                severity=4,
                count=1,
                random_seed=32,
                output_root=root,
                run_id="envs",
            )
            summary_path = Path(generated.artifacts["environment_summary_path"])

            result = run_studio_render_env(
                environment_summary_path=summary_path,
                template_id="roadside_market_occlusion",
                prompt="wet Malaysian roadside market occlusion with scooter filtering",
                output_root=root,
                run_id="proof",
                live=False,
            )
            manifest_path = Path(result.artifacts["env_carla_proof_manifest_path"])
            placement_path = Path(result.artifacts["placement_plan_path"])
            run_manifest_path = Path(result.artifacts["run_manifest_path"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            placement = json.loads(placement_path.read_text(encoding="utf-8"))
            run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(result.command, "oodrive render-env")
            self.assertEqual(result.status, "planned")
            self.assertTrue(manifest_path.exists())
            self.assertTrue(placement_path.exists())
            self.assertTrue(run_manifest_path.exists())
            self.assertEqual(manifest["status"], "planned")
            self.assertFalse(manifest["live"])
            self.assertFalse(manifest["same_lineage"])
            self.assertIsNone(manifest["preview_image_path"])
            self.assertEqual(placement["recipe"]["environment"]["environment_recipe_id"], manifest["environment_recipe_id"])
            self.assertEqual(run_manifest["scenario_id"], manifest["scenario_id"])
            self.assertEqual(run_manifest["status"], "planned")
            self.assertIn("environment_to_carla_visual_proof=true", manifest["claim_boundaries"])
            self.assertIn("closed_loop_vla_control=false", manifest["claim_boundaries"])
            self.assertTrue(any("analyze-keyframes" in command for command in result.next_commands))

    def test_visual_proof_manifest_marks_same_lineage_only_with_preview_frame(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated = run_studio_generate_envs(
                template_ids=("roadside_market_occlusion",),
                severity=4,
                count=1,
                random_seed=32,
                output_root=root,
                run_id="envs",
            )
            summary_path = Path(generated.artifacts["environment_summary_path"])
            render = run_studio_render_env(
                environment_summary_path=summary_path,
                template_id="roadside_market_occlusion",
                output_root=root,
                run_id="proof",
                live=False,
            )
            environment = select_environment_recipe(summary_path, template_id="roadside_market_occlusion")
            candidate = build_environment_visual_candidate(
                environment=environment,
                prompt="visual proof",
                run_id="proof",
            )
            preview = root / "preview.png"
            preview.write_bytes(b"fake-png")
            payload = write_environment_carla_visual_proof(
                run_dir=root / "lineage",
                environment=environment,
                environment_summary_path=summary_path,
                db_path=Path(render.artifacts["db_path"]),
                placement_plan_path=Path(render.artifacts["placement_plan_path"]),
                run_manifest_path=Path(render.artifacts["run_manifest_path"]),
                carla_report_path=None,
                preview_frame_path=preview,
                preview_source_frame=preview,
                status="passed",
                blockers=[],
                live=True,
                config_path=Path("configs/carla_ood_demo.local.sample.yaml"),
                candidate=candidate,
            )

            self.assertEqual(payload["status"], "passed")
            self.assertTrue(payload["same_lineage"])
            self.assertEqual(payload["preview_image_path"], str(preview))
            self.assertIn("carla_visual_evidence=true", payload["claim_boundaries"])

    def test_select_environment_recipe_rejects_unknown_selector(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated = run_studio_generate_envs(
                template_ids=("roadside_market_occlusion",),
                severity=4,
                count=1,
                random_seed=32,
                output_root=root,
                run_id="envs",
            )

            with self.assertRaisesRegex(ValueError, "Unknown environment template id"):
                select_environment_recipe(
                    Path(generated.artifacts["environment_summary_path"]),
                    template_id="not-real",
                )


if __name__ == "__main__":
    unittest.main()
