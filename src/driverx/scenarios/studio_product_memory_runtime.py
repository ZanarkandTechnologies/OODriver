"""OODrive memory retrieval evidence commands."""

from __future__ import annotations

from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.memory import MemoryBank, MemoryEntry, retrieve_memory_with_ledger, write_memory_retrieval_ledger
from driverx.policies.runner import memory_entries_from_json, sample_memory_entries
from driverx.scenarios.studio_db import load_studio_db
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths, oodrive_command
from driverx.scenarios.types import ScenarioRecipe


def run_studio_memory_ledger(
    db_path: Path,
    *,
    scenario_id: str | None = None,
    memory_bank_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str = "oodrive-memory-ledger",
    limit: int = 6,
) -> StudioCommandResult:
    db = load_studio_db(db_path)
    candidate = _select_candidate(db.candidates, scenario_id)
    recipe_payload = candidate.get("compiled_recipe")
    if not isinstance(recipe_payload, dict):
        raise ValueError("Selected candidate does not include a compiled_recipe.")
    recipe = ScenarioRecipe.from_jsonable(recipe_payload)
    bank = MemoryBank(entries=memory_entries_from_json(memory_bank_path) if memory_bank_path else _default_ledger_entries())
    ledger = retrieve_memory_with_ledger(recipe, bank, limit)
    run_dir = prepare_run_dir(output_root or Path("artifacts/runs"), run_id)
    artifacts = artifact_paths(write_memory_retrieval_ledger(run_dir, ledger))
    return StudioCommandResult(
        command="oodrive memory-ledger",
        run_id=run_id,
        status="passed" if ledger.selected_memory_ids else "partial",
        artifacts=artifacts,
        next_commands=[
            oodrive_command(
                "reasoning-diff --alpamayo-batch tickets/TASK-104/artifacts/alpamayo-rag-batch-v1/"
                f"alpamayo_ood_batch_summary.json --retrieval-ledger {artifacts['json_path']}"
            )
        ],
        summary={
            "scenario_id": recipe.recipe_id,
            "candidate_id": candidate.get("candidate_id"),
            "retrieval_backend": ledger.backend,
            "candidate_count": len(ledger.candidates),
            "selected_memory_ids": ledger.selected_memory_ids,
        },
        claim_boundaries=ledger.claim_boundaries,
    )


def _select_candidate(candidates: list[dict[str, object]], scenario_id: str | None) -> dict[str, object]:
    if not candidates:
        raise ValueError("Studio DB has no candidates.")
    if scenario_id is None:
        return dict(candidates[0])
    for candidate in candidates:
        values = {
            str(candidate.get("candidate_id", "")),
            str(candidate.get("scenario_id", "")),
        }
        recipe = candidate.get("compiled_recipe")
        if isinstance(recipe, dict):
            values.add(str(recipe.get("recipe_id", "")))
        if scenario_id in values:
            return dict(candidate)
    raise ValueError(f"Scenario id not found in candidates: {scenario_id}")


__all__ = ["run_studio_memory_ledger"]


def _default_ledger_entries() -> list[MemoryEntry]:
    return [
        *sample_memory_entries(),
        MemoryEntry(
            entry_id="mem-sample-occupied-lane-obstacle",
            situation="static object occupies the ego lane in wet low-visibility driving",
            observed_failure="Policy treated a route blocker like background clutter and committed too late.",
            principle="Unknown objects on the drivable route should be treated as occupied space.",
            recommended_behavior="Slow early, stop before the object, and resume only when a free lane-level bypass is visible.",
            source_scenario="fixture_blocked_lane_obstacle",
            confidence=0.86,
            tags=["blocked", "lane", "obstacle", "occupied", "wet"],
        ),
        MemoryEntry(
            entry_id="mem-sample-roadside-occlusion",
            situation="roadside market clutter hides an actor that can enter the route",
            observed_failure="Policy over-trusted the visible lane and missed an occluded crossing threat.",
            principle="Occluded occupied space should reduce commitment speed until the hidden area is visible.",
            recommended_behavior="Creep with low speed, keep lane discipline, and preserve stopping margin near occluders.",
            source_scenario="fixture_roadside_market_occlusion",
            confidence=0.8,
            tags=["occlusion", "roadside", "market", "regional", "creep"],
        ),
    ]
