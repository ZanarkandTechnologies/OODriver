from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.pipeline.reasoning_evidence_panel import build_reasoning_evidence_panel


class ReasoningEvidencePanelTests(unittest.TestCase):
    def test_builds_decongested_chaptered_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            overlay = root / "overlay.json"
            overlay.write_text(json.dumps({"event_count": 4, "frame_count": 120, "input_video": "demo.mp4"}), encoding="utf-8")
            diff = root / "diff.json"
            diff.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "scenario_id": "case-1",
                                "reasoning_delta_summary": "memory changed the stop/yield explanation",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            ledger = root / "ledger.json"
            ledger.write_text(
                json.dumps(
                    {
                        "retrieval_backend": "lexical_tag_overlap",
                        "selected_memory_ids": ["mem-obstacle", "mem-market"],
                    }
                ),
                encoding="utf-8",
            )

            report = build_reasoning_evidence_panel(
                overlay_report_path=overlay,
                reasoning_diff_path=diff,
                retrieval_ledger_paths=(ledger,),
                output_root=root,
                run_id="panel",
            )

            self.assertGreaterEqual(len(report["chapters"]), 4)
            self.assertLessEqual(report["max_hud_rows"], 3)
            self.assertGreaterEqual(report["citation_count"], 3)
            self.assertTrue(Path(report["html_path"]).exists())


if __name__ == "__main__":
    unittest.main()
