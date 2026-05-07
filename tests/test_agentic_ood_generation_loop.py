from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from driverx.scenarios.agentic_loop import (
    AgenticOodLoopConfig,
    generate_ood_briefs,
    run_agentic_ood_generation_loop,
)


class AgenticOodGenerationLoopTests(unittest.TestCase):
    def test_generates_deterministic_briefs(self) -> None:
        first = generate_ood_briefs(["Malaysian chaos"], count=4, random_seed=9)
        second = generate_ood_briefs(["Malaysian chaos"], count=4, random_seed=9)

        self.assertEqual([brief.to_jsonable() for brief in first], [brief.to_jsonable() for brief in second])
        self.assertEqual(len(first), 4)
        self.assertEqual(first[0].author, "agent")
        self.assertTrue(first[0].requested_tags)

    def test_loop_scores_accepts_and_rejects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_agentic_ood_generation_loop(
                AgenticOodLoopConfig(
                    count=8,
                    random_seed=3,
                    output_root=Path(tmp),
                    run_id="agentic-loop-test",
                    min_accept_score=0.1,
                )
            )

            self.assertEqual(summary["candidate_count"], 8)
            self.assertGreater(summary["accepted_count"], 0)
            self.assertGreater(summary["rejected_count"], 0)
            self.assertTrue(Path(summary["json_path"]).exists())
            self.assertTrue(Path(summary["queue_path"]).exists())
            self.assertTrue(Path(summary["gallery_path"]).exists())
            self.assertIn("dataset_curation_queue=true", summary["claim_boundaries"])


if __name__ == "__main__":
    unittest.main()
