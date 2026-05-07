from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from driverx.pipeline.final_submission_pack_v8 import (
    FinalSubmissionPackV8Inputs,
    run_final_submission_pack_v8,
)


class FinalSubmissionPackV8Tests(unittest.TestCase):
    def test_builds_v8_pack_from_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = _write(root / "bundle.json", {"scenario_id": "scene", "product_loop": [{"stage": "generate"}]})
            loop = _write(root / "loop.json", {"brief_count": 2, "candidate_count": 3, "accepted_count": 1})
            risk = _write(root / "risk.json", {"event_count": 4, "max_risk_level": "critical"})
            overlay = _write(root / "overlay.json", {"status": "passed", "event_count": 4, "frame_count": 20})
            timewarp = _write(root / "timewarp.json", {"status": "passed", "input_duration_s": 84, "output_duration_s": 28})
            alpamayo = _write(
                root / "alpamayo.json",
                {
                    "status": "passed",
                    "case_count": 1,
                    "passed_count": 1,
                    "reasoning_changed_count": 1,
                    "mean_latency_ms": 10,
                },
            )

            summary = run_final_submission_pack_v8(
                FinalSubmissionPackV8Inputs(
                    workbench_bundle_path=bundle,
                    agentic_loop_path=loop,
                    risk_timeline_path=risk,
                    reasoning_overlay_path=overlay,
                    timewarp_path=timewarp,
                    alpamayo_batch_path=alpamayo,
                    output_root=root,
                    run_id="pack",
                )
            )

            self.assertEqual(summary["submission_status"], "submission_ready_with_claim_boundaries")
            self.assertTrue(Path(summary["json_path"]).exists())
            self.assertTrue(Path(summary["browser_path"]).exists())
            self.assertIn("real_time_vla_control=false", summary["claim_boundaries"])
            self.assertEqual(len(summary["evidence_rows"]), 6)


def _write(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
