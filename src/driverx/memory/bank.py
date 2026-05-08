"""Build and retrieve compact safety memory."""

from __future__ import annotations

import json
import re
from pathlib import Path

from driverx.memory.types import MemoryBank, MemoryEntry, MemoryRetrievalCandidate, MemoryRetrievalLedger
from driverx.scenarios.types import ScenarioRecipe, ScenarioResult


def _tokens(values: list[str]) -> set[str]:
    text = " ".join(values).lower()
    return {token for token in re.split(r"[^a-z0-9]+", text) if token}


def _recommended_behavior(tags: set[str], summary: str) -> str:
    lower_summary = summary.lower()
    if {"animal", "animals"} & tags:
        return "Slow early, treat the object as occupied space, and proceed only after the path is clear."
    if "occlusion" in tags or "hidden" in lower_summary:
        return "Creep forward with low speed and preserve stopping margin until the hidden area is visible."
    if "blocked" in lower_summary or "blockage" in tags:
        return "Stop before blocked space, then take only a clearly free local bypass."
    if "motorcycle" in lower_summary or "regional" in tags:
        return "Expect lateral filtering and keep extra side clearance before committing."
    return "Prefer a conservative speed profile and verify route relevance before reacting to novelty."


def _principle(tags: set[str], summary: str) -> str:
    if {"animal", "animals", "obstacle"} & tags:
        return "Unknown objects on the drivable route should be treated as occupied space."
    if "occlusion" in tags or "hidden" in summary.lower():
        return "Occluded cross-traffic risk should reduce commitment speed until visibility improves."
    if "visual" in tags or "distractor" in tags:
        return "Novel visual artifacts matter only when they change occupied space or route constraints."
    return "When the scene distribution shifts, preserve controllability before optimizing progress."


def build_memory_bank(results: list[ScenarioResult]) -> MemoryBank:
    entries: list[MemoryEntry] = []
    for result in results:
        if result.success:
            continue
        summary = result.failure_summary or "Policy failed the scenario."
        tags = _tokens([result.scenario_id, summary, *result.tags])
        entry_id = f"mem-{len(entries):04d}-{re.sub(r'[^a-z0-9]+', '-', result.scenario_id.lower()).strip('-')}"
        entries.append(
            MemoryEntry(
                entry_id=entry_id,
                situation=f"{result.scenario_id} with tags {', '.join(sorted(tags))}",
                observed_failure=summary,
                principle=_principle(tags, summary),
                recommended_behavior=_recommended_behavior(tags, summary),
                source_scenario=result.scenario_id,
                confidence=0.72 if result.driving_score is None else max(0.1, min(0.95, 1.0 - result.driving_score / 100.0)),
                tags=sorted(tags),
            )
        )
    return MemoryBank(entries=entries)


def retrieve_memory(
    recipe: ScenarioRecipe,
    bank: MemoryBank,
    limit: int,
) -> list[MemoryEntry]:
    return [candidate.entry for candidate in retrieve_memory_with_ledger(recipe, bank, limit).candidates if candidate.selected]


def retrieve_memory_with_ledger(
    recipe: ScenarioRecipe,
    bank: MemoryBank,
    limit: int,
    *,
    backend: str = "lexical_tag_overlap",
) -> MemoryRetrievalLedger:
    if limit <= 0:
        return MemoryRetrievalLedger(
            query_id=recipe.recipe_id,
            query_tokens=[],
            backend=backend,
            candidates=[],
            selected_memory_ids=[],
            claim_boundaries=_retrieval_claim_boundaries(backend),
        )
    query = _tokens(
        [
            recipe.recipe_id,
            recipe.parent_seed_id,
            recipe.mutation,
            recipe.expected_failure_mode,
            *recipe.memory_query,
        ]
    )
    scored: list[tuple[float, int, float, str, MemoryEntry, list[str]]] = []
    for entry in bank.entries:
        matched = sorted(query.intersection(set(entry.tags)))
        overlap = len(matched)
        score = overlap + entry.confidence
        scored.append((score, overlap, entry.confidence, entry.entry_id, entry, matched))
    scored.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3]))
    selected_ids = {
        entry.entry_id
        for _score, overlap, _confidence, _entry_id, entry, _matched in scored[:limit]
        if overlap > 0
    }
    candidates = [
        MemoryRetrievalCandidate(
            entry=entry,
            query_tokens=sorted(query),
            matched_tokens=matched,
            overlap_count=overlap,
            score=score,
            selected=entry.entry_id in selected_ids,
            rank=index + 1,
        )
        for index, (score, overlap, _confidence, _entry_id, entry, matched) in enumerate(scored)
    ]
    return MemoryRetrievalLedger(
        query_id=recipe.recipe_id,
        query_tokens=sorted(query),
        backend=backend,
        candidates=candidates,
        selected_memory_ids=[candidate.entry.entry_id for candidate in candidates if candidate.selected],
        claim_boundaries=_retrieval_claim_boundaries(backend),
    )


def write_memory_bank(run_dir: Path, bank: MemoryBank) -> dict[str, str | int]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "memory_bank.json"
    md_path = run_dir / "memory_bank.md"
    json_path.write_text(json.dumps(bank.to_jsonable(), indent=2), encoding="utf-8")
    lines = ["# Memory Bank", "", f"- Entries: `{len(bank.entries)}`", ""]
    for entry in bank.entries:
        lines.extend(
            [
                f"## {entry.entry_id}",
                "",
                f"- Situation: {entry.situation}",
                f"- Observed failure: {entry.observed_failure}",
                f"- Principle: {entry.principle}",
                f"- Recommended behavior: {entry.recommended_behavior}",
                f"- Source scenario: `{entry.source_scenario}`",
                "",
            ]
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "num_entries": len(bank.entries),
        "json_path": str(json_path),
        "report_path": str(md_path),
    }


def write_memory_retrieval_ledger(run_dir: Path, ledger: MemoryRetrievalLedger) -> dict[str, str | int]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "retrieval_ledger.json"
    md_path = run_dir / "retrieval_ledger.md"
    json_path.write_text(json.dumps(ledger.to_jsonable(), indent=2), encoding="utf-8")
    lines = [
        "# Memory Retrieval Ledger",
        "",
        f"- Query: `{ledger.query_id}`",
        f"- Backend: `{ledger.backend}`",
        f"- Selected memories: `{', '.join(ledger.selected_memory_ids) or 'none'}`",
        "",
        "## Candidates",
        "",
    ]
    for candidate in ledger.candidates:
        mark = "selected" if candidate.selected else "candidate"
        lines.extend(
            [
                f"### {candidate.rank}. {candidate.entry.entry_id} ({mark})",
                "",
                f"- Score: `{candidate.score:.4f}`",
                f"- Matched tokens: `{', '.join(candidate.matched_tokens) or 'none'}`",
                f"- Source scenario: `{candidate.entry.source_scenario}`",
                f"- Principle: {candidate.entry.principle}",
                f"- Recommended behavior: {candidate.entry.recommended_behavior}",
                "",
            ]
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "candidate_count": len(ledger.candidates),
        "selected_count": len(ledger.selected_memory_ids),
        "json_path": str(json_path),
        "report_path": str(md_path),
    }


def _retrieval_claim_boundaries(backend: str) -> list[str]:
    return [
        f"retrieval_backend={backend}",
        "semantic_vector_rag=false",
        "embedding_rag=false",
        "memory_retrieval_ledger=true",
        "source_citations=true",
    ]
