import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline.submission_demo_pack import build_submission_demo_pack


class SubmissionDemoPackTest(unittest.TestCase):
    def test_demo_pack_includes_storyboard_failure_and_declarations(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)

            summary = build_submission_demo_pack(
                root / "demo-pack",
                local_demo_path=paths["local_demo"],
                generated_suite_path=paths["suite"],
                policy_matrix_path=paths["policy"],
                alpamayo_probe_path=paths["alpamayo"],
                route_evidence_path=paths["route"],
                alpamayo_comparison_path=paths["comparison"],
                cached_replay_path=paths["cached_replay"],
                blockers_path=paths["blockers"],
                progress_path=paths["progress"],
            )
            report = Path(summary["report_path"]).read_text(encoding="utf-8")
            json_exists = Path(summary["json_path"]).exists()

        self.assertTrue(json_exists)
        self.assertEqual(len(summary["storyboard"]), 7)
        self.assertEqual(summary["failure_case"]["status"], "near_miss_proxy")
        self.assertIn("Baseline `policy` policy", summary["failure_case"]["summary"])
        self.assertIn("1-5 Minute Demo Outline", report)
        self.assertIn("Model Declarations", report)
        self.assertIn("Live Evidence", report)
        self.assertIn("Claim Boundaries", report)
        self.assertIn("Short Write-Up Draft", report)
        self.assertTrue(any(item["name"] == "alpamayo-probe" for item in summary["model_declarations"]))
        self.assertTrue(any(item["name"] == "alpamayo-live-ood-comparison" for item in summary["model_declarations"]))
        self.assertTrue(any(item["name"] == "mock" for item in summary["model_declarations"]))
        self.assertEqual(summary["artifact_map"]["local_sim_html"], "local_ood_sim.html")
        self.assertEqual(summary["live_evidence"]["alpamayo_comparison"]["trajectory_delta"]["final_l2_m"], 2.5)
        self.assertEqual(summary["live_evidence"]["cached_replay"]["command_count"], 20)
        self.assertTrue(any("not real-time VLA steering" in item for item in summary["claim_boundaries"]))

    def test_demo_pack_cli_writes_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)
            stream = StringIO()

            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-demo-pack",
                        "--local-demo",
                        str(paths["local_demo"]),
                        "--generated-suite",
                        str(paths["suite"]),
                        "--policy-matrix",
                        str(paths["policy"]),
                        "--alpamayo-probe",
                        str(paths["alpamayo"]),
                        "--route-evidence",
                        str(paths["route"]),
                        "--alpamayo-comparison",
                        str(paths["comparison"]),
                        "--cached-replay",
                        str(paths["cached_replay"]),
                        "--blockers",
                        str(paths["blockers"]),
                        "--progress",
                        str(paths["progress"]),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "demo",
                    ]
                )
            summary = json.loads(stream.getvalue())
            report_exists = Path(summary["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(report_exists)
        self.assertEqual(summary["artifact_map"]["local_demo_path"], str(paths["local_demo"]))
        self.assertEqual(summary["artifact_map"]["route_pack_path"], "routes/generated.xml")
        self.assertEqual(summary["artifact_map"]["cached_replay_path"], str(paths["cached_replay"]))


def _write_inputs(root: Path) -> dict[str, Path]:
    local_demo = root / "end_to_end_demo.json"
    local_demo.write_text(
        json.dumps(
            {
                "status": "ready",
                "recipe": {
                    "recipe_id": "generated-regional-1",
                    "route_path": "routes/local.xml",
                },
                "local_sim": {
                    "behavior_id": "motorcycle_filtering",
                    "policy_tracks": [
                        {
                            "label": "policy",
                            "closest_actor_distance_m": 1.5,
                            "risk_level": "near_miss_proxy",
                        },
                        {
                            "label": "policy+memory",
                            "closest_actor_distance_m": 4.5,
                            "risk_level": "clearance_ok",
                        },
                    ],
                },
                "artifact_map": {
                    "local_sim_html": "local_ood_sim.html",
                    "local_sim_svg": "local_ood_sim.svg",
                    "local_sim_json": "local_ood_sim.json",
                },
            }
        ),
        encoding="utf-8",
    )
    suite = root / "generated_ood_suite.json"
    suite.write_text(
        json.dumps(
            {
                "status": "blocked",
                "num_recipes": 1,
                "scenario_summary_path": "scenario_summary.json",
                "route_pack_path": "routes/generated.xml",
                "overlay_plan_path": "overlay_plan.json",
                "overlay_evidence_path": "overlay_evidence.json",
                "readiness": {"recipe_count": 1},
                "recipe_records": [
                    {
                        "recipe_id": "recipe-1",
                        "route_path": "fail2drive_split/Route.xml",
                        "route_evidence_status": "blocked",
                        "route_evidence_path": "route-evidence/run_evidence.json",
                        "video_smoke_plan_path": "video-plan.json",
                        "blockers": ["Missing route video"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    policy = root / "policy_runtime_matrix.json"
    policy.write_text(
        json.dumps(
            {
                "ready_count": 5,
                "rows": [
                    {"policy": "mock", "runtime_kind": "local", "ready_state": "ready"},
                    {"policy": "alpamayo", "runtime_kind": "vla", "ready_state": "blocked"},
                ],
            }
        ),
        encoding="utf-8",
    )
    alpamayo = root / "alpamayo_probe_report.json"
    alpamayo.write_text(
        json.dumps(
            {
                "status": "not_run",
                "model_id": "nvidia/Alpamayo-1.5-10B",
                "blockers": ["No Alpamayo probe artifacts found."],
            }
        ),
        encoding="utf-8",
    )
    route = root / "run_evidence.json"
    route.write_text(
        json.dumps(
            {
                "status": "partial",
                "video": {"exists": True, "path": "route.mp4", "duration_s": 4.1, "size_bytes": 1234},
                "metrics": {"driving_score": None, "route_completion": None},
                "blockers": [],
            }
        ),
        encoding="utf-8",
    )
    comparison = root / "alpamayo_ood_comparison.json"
    comparison.write_text(
        json.dumps(
            {
                "open_loop_policy_evaluation": True,
                "closed_loop_control": False,
                "trajectory_delta": {"available": True, "final_l2_m": 2.5},
                "reasoning_delta": {"available": True, "changed": True},
                "safety_flags": {"memory_augmented_live_run_available": True},
                "records": [
                    {"latency_ms": 1000.0, "vram_peak_mb": 23000.0},
                    {"latency_ms": 1010.0, "vram_peak_mb": 23100.0},
                ],
            }
        ),
        encoding="utf-8",
    )
    cached_replay = root / "carla_policy_replay.json"
    cached_replay.write_text(
        json.dumps(
            {
                "closed_loop_control": "cached_replay",
                "command_count": 20,
                "applied_count": 0,
                "dry_run": True,
                "safety_clamps": ["tick 0: target behind ego, braking instead of steering"],
                "trace": {"trajectory_frame": "ego"},
            }
        ),
        encoding="utf-8",
    )
    blockers = root / "blockers.md"
    blockers.write_text("# Blockers\n\n## Open\n\n- Missing route video\n", encoding="utf-8")
    progress = root / "progress.md"
    progress.write_text("# Progress\n\n- TASK evidence\n", encoding="utf-8")
    return {
        "local_demo": local_demo,
        "suite": suite,
        "policy": policy,
        "alpamayo": alpamayo,
        "route": route,
        "comparison": comparison,
        "cached_replay": cached_replay,
        "blockers": blockers,
        "progress": progress,
    }


if __name__ == "__main__":
    unittest.main()
