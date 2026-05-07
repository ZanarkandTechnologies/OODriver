from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from driverx.workbench.bundle import ScenarioRunBundleInputs, build_scenario_run_bundle
from driverx.workbench.report import write_scenario_run_bundle


class ScenarioWorkbenchBundleTests(unittest.TestCase):
    def test_builds_bundle_from_linked_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            studio_path = root / "studio.json"
            video_path = root / "video.json"
            alpamayo_path = root / "alpamayo.json"
            risk_path = root / "risk.json"
            studio_path.write_text(
                json.dumps(
                    {
                        "prompt_count": 1,
                        "candidate_count": 1,
                        "plans": [
                            {
                                "plan_id": "plan-malaysia",
                                "brief": {"prompt": "wet Malaysian motorbike filter"},
                            }
                        ],
                        "candidates": [
                            {
                                "candidate_id": "scenario-001-v00",
                                "parent_plan_id": "plan-malaysia",
                                "behavior_template_id": "motorcycle_filtering",
                            }
                        ],
                        "curation": [
                            {
                                "candidate_id": "scenario-001-v00",
                                "status": "accept_partial",
                                "score": 0.87,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            video_path.write_text(
                json.dumps(
                    {
                        "scenario_id": "scenario-001",
                        "behavior_id": "motorcycle_filtering",
                        "local_video_path": "artifacts/exported/demo.mp4",
                        "video_export_status": "local_file",
                        "duration_s": 84,
                        "fps": 5,
                        "frame_count": 420,
                        "tracks_path": "tracks.json",
                        "claim_boundaries": ["closed_loop_vla_control=false"],
                    }
                ),
                encoding="utf-8",
            )
            alpamayo_path.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "scenario_id": "scenario-001",
                                "reasoning_changed": True,
                                "memory_ids": ["mem-motorbike"],
                                "latency_ms": [100.0],
                            }
                        ],
                        "claim_boundaries": ["open_loop_case_count=1"],
                    }
                ),
                encoding="utf-8",
            )
            risk_path.write_text(
                json.dumps({"scenario_id": "scenario-001", "event_count": 2, "max_risk_level": "critical"}),
                encoding="utf-8",
            )

            bundle = build_scenario_run_bundle(
                ScenarioRunBundleInputs(
                    studio_batch_path=studio_path,
                    video_evidence_path=video_path,
                    alpamayo_batch_path=alpamayo_path,
                    risk_timeline_path=risk_path,
                )
            )

            payload = bundle.to_jsonable()
            self.assertEqual(payload["scenario_id"], "scenario-001")
            self.assertEqual(payload["behavior_id"], "motorcycle_filtering")
            self.assertEqual(payload["carla_video"]["path"], "artifacts/exported/demo.mp4")
            self.assertEqual(payload["linkage_warnings"], [])
            self.assertEqual(payload["product_loop"][2]["status"], "proved")
            self.assertIn("real_time_vla_control=false", payload["claim_boundaries"])

    def test_reports_linkage_warning_for_fallback_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            studio_path = root / "studio.json"
            video_path = root / "video.json"
            studio_path.write_text(
                json.dumps(
                    {
                        "candidates": [
                            {
                                "candidate_id": "different-scenario-v00",
                                "parent_plan_id": "plan-1",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            video_path.write_text(json.dumps({"scenario_id": "wanted-scenario"}), encoding="utf-8")

            bundle = build_scenario_run_bundle(
                ScenarioRunBundleInputs(studio_batch_path=studio_path, video_evidence_path=video_path)
            )

            self.assertTrue(any("fallback" in warning for warning in bundle.linkage_warnings))

    def test_writes_json_markdown_and_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video_path = root / "video.json"
            video_path.write_text(json.dumps({"scenario_id": "scene", "local_video_path": "demo.mp4"}), encoding="utf-8")
            bundle = build_scenario_run_bundle(ScenarioRunBundleInputs(video_evidence_path=video_path))

            summary = write_scenario_run_bundle(root / "out", bundle)

            self.assertTrue(Path(summary["json_path"]).exists())
            self.assertTrue(Path(summary["report_path"]).read_text(encoding="utf-8").startswith("# Scenario Workbench"))
            self.assertIn("<table>", Path(summary["html_path"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
