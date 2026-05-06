import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline.final_submission_pack import build_final_submission_pack


class FinalSubmissionPackTest(unittest.TestCase):
    def test_final_pack_builds_scorecard_rows_script_and_writeup(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)

            summary = build_final_submission_pack(
                root / "pack",
                eval_matrix_path=paths["matrix"],
                scenario_studio_path=paths["studio"],
                alpamayo_rag_batch_path=paths["alpamayo"],
                fail2drive_extension_path=paths["fail2drive"],
                hero_video_evidence_path=paths["video"],
                scenario_browser_path=paths["browser"],
                blockers_path=paths["blockers"],
            )
            report = Path(summary["report_path"]).read_text(encoding="utf-8")
            script = Path(summary["video_script_path"]).read_text(encoding="utf-8")
            writeup = Path(summary["writeup_path"]).read_text(encoding="utf-8")
            browser = Path(summary["browser_path"]).read_text(encoding="utf-8")

            self.assertEqual(summary["submission_status"], "submission_ready")
            self.assertEqual(summary["scorecard"]["scenario_studio_candidates"], 20)
            self.assertEqual(summary["scorecard"]["alpamayo_reasoning_changed"], 2)
            self.assertEqual(len(summary["evidence_rows"]), 5)
            self.assertTrue(Path(summary["artifact_map_path"]).exists())
            self.assertIn("Scenario Studio", script)
            self.assertIn("official Fail2Drive route score", report)
            self.assertIn("Frozen Alpamayo", writeup)
            self.assertIn("Evidence Rows", browser)
            self.assertEqual(summary["scorecard"]["hero_video_path"], "/remote/hero.mp4")
            self.assertIn("/remote/hero.mp4", browser)

    def test_final_pack_cli(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-final-submission-pack",
                        "--eval-matrix",
                        str(paths["matrix"]),
                        "--scenario-studio",
                        str(paths["studio"]),
                        "--alpamayo-rag-batch",
                        str(paths["alpamayo"]),
                        "--fail2drive-extension",
                        str(paths["fail2drive"]),
                        "--hero-video-evidence",
                        str(paths["video"]),
                        "--scenario-browser",
                        str(paths["browser"]),
                        "--blockers",
                        str(paths["blockers"]),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "pack",
                    ]
                )
            summary = json.loads(stream.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["scorecard"]["selected_cases"], 6)
        self.assertTrue(summary["writeup_path"].endswith("writeup_2page_draft.md"))
        self.assertTrue(summary["browser_path"].endswith("scenario_browser_v7.html"))


def _write_inputs(root: Path) -> dict[str, Path]:
    matrix = root / "matrix.json"
    matrix.write_text(json.dumps({"case_count": 6, "hero_count": 1}), encoding="utf-8")
    studio = root / "studio.json"
    studio.write_text(
        json.dumps(
            {
                "prompt_count": 10,
                "candidate_count": 20,
                "claim_boundaries": ["deterministic_reproducible_generation=true"],
            }
        ),
        encoding="utf-8",
    )
    alpamayo = root / "alpamayo.json"
    alpamayo.write_text(
        json.dumps(
            {
                "status": "passed",
                "case_count": 3,
                "passed_count": 3,
                "reasoning_changed_count": 2,
                "memory_case_count": 3,
                "mean_latency_ms": 92000.0,
                "max_vram_peak_mb": 23500.0,
                "claim_boundaries": ["closed_loop_carla_control=false"],
            }
        ),
        encoding="utf-8",
    )
    fail2drive = root / "fail2drive.json"
    fail2drive.write_text(
        json.dumps(
            {
                "generated_case_count": 26,
                "reference_count": 4,
                "memory_entry_count": 2,
                "reference_sources": ["fixture_seed"],
                "claim_boundaries": ["official_fail2drive_score_claim=false"],
            }
        ),
        encoding="utf-8",
    )
    video = root / "video.json"
    video.write_text(
        json.dumps(
            {
                "video_path": "hero.mp4",
                "remote_video_path": "/remote/hero.mp4",
                "duration_s": 60.0,
            }
        ),
        encoding="utf-8",
    )
    browser = root / "scenario_browser.html"
    browser.write_text("<html></html>", encoding="utf-8")
    blockers = root / "blockers.md"
    blockers.write_text("# Blockers\n\n## Open\n\n- blocker one\n", encoding="utf-8")
    return {
        "matrix": matrix,
        "studio": studio,
        "alpamayo": alpamayo,
        "fail2drive": fail2drive,
        "video": video,
        "browser": browser,
        "blockers": blockers,
    }


if __name__ == "__main__":
    unittest.main()
