from __future__ import annotations

import unittest

from driverx.memory import MemoryBank, MemoryEntry, retrieve_memory, retrieve_memory_with_ledger
from driverx.scenarios.types import ScenarioRecipe


class MemoryRetrievalLedgerTests(unittest.TestCase):
    def test_ledger_preserves_retrieve_memory_selection(self) -> None:
        recipe = ScenarioRecipe(
            recipe_id="wet-roadwork-obstacle",
            parent_seed_id="Base_Animals_0076",
            mutation="obstacle_substitution",
            actors=[],
            environment={},
            expected_failure_mode="blocked lane with unknown obstacle",
            memory_query=["obstacle", "blocked", "wet"],
        )
        bank = MemoryBank(
            entries=[
                MemoryEntry(
                    entry_id="mem-obstacle",
                    situation="blocked wet lane",
                    observed_failure="policy drove toward occupied space",
                    principle="Unknown objects on route are occupied space.",
                    recommended_behavior="Slow and stop before the blocker.",
                    source_scenario="Base_Animals_0076",
                    confidence=0.9,
                    tags=["obstacle", "blocked", "wet"],
                ),
                MemoryEntry(
                    entry_id="mem-market",
                    situation="market clutter",
                    observed_failure="ignored shoulder clutter",
                    principle="Visual clutter is not always route-blocking.",
                    recommended_behavior="Monitor but stay route relevant.",
                    source_scenario="market",
                    confidence=0.7,
                    tags=["market", "clutter"],
                ),
            ]
        )

        ledger = retrieve_memory_with_ledger(recipe, bank, limit=1)
        selected = retrieve_memory(recipe, bank, limit=1)

        self.assertEqual([entry.entry_id for entry in selected], ledger.selected_memory_ids)
        self.assertEqual(ledger.selected_memory_ids, ["mem-obstacle"])
        self.assertGreater(ledger.candidates[0].score, ledger.candidates[1].score)
        self.assertIn("retrieval_backend=lexical_tag_overlap", ledger.claim_boundaries)


if __name__ == "__main__":
    unittest.main()
