from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.pipeline.alpamayo_reasoning_diff import build_alpamayo_reasoning_diff, extract_reasoning_diff_events


class AlpamayoReasoningDiffTests(unittest.TestCase):
    def test_builds_case_level_reasoning_delta(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = root / "comparison.json"
            comparison.write_text(
                json.dumps(
                    {
                        "records": [
                            {"mode": "alpamayo", "cot_snippet": "continue but monitor"},
                            {"mode": "alpamayo+memory", "cot_snippet": "slow because obstacle memory applies"},
                        ],
                        "memory_ids": ["mem-obstacle"],
                    }
                ),
                encoding="utf-8",
            )
            batch = root / "batch.json"
            batch.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "scenario_id": "case-1",
                                "comparison_path": str(comparison),
                                "reasoning_changed": True,
                                "memory_ids": ["mem-obstacle"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = build_alpamayo_reasoning_diff(batch, output_root=root, run_id="diff")
            events = extract_reasoning_diff_events(report)

            self.assertEqual(report["case_count"], 1)
            self.assertEqual(report["memory_case_count"], 1)
            self.assertIn("slow because obstacle", report["cases"][0]["memory_reasoning_snippet"])
            self.assertEqual(events[0]["scenario_id"], "case-1")


if __name__ == "__main__":
    unittest.main()
