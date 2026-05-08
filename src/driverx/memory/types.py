"""Types for retrieval memory built from scenario failures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MemoryEntry:
    entry_id: str
    situation: str
    observed_failure: str
    principle: str
    recommended_behavior: str
    source_scenario: str
    confidence: float
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("MemoryEntry confidence must be between 0 and 1.")
        for value in (
            self.entry_id,
            self.situation,
            self.observed_failure,
            self.principle,
            self.recommended_behavior,
            self.source_scenario,
        ):
            if not value:
                raise ValueError("MemoryEntry text fields must be non-empty.")

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "situation": self.situation,
            "observed_failure": self.observed_failure,
            "principle": self.principle,
            "recommended_behavior": self.recommended_behavior,
            "source_scenario": self.source_scenario,
            "confidence": self.confidence,
            "tags": self.tags,
        }


@dataclass(frozen=True)
class MemoryBank:
    entries: list[MemoryEntry]

    def to_jsonable(self) -> dict[str, Any]:
        return {"entries": [entry.to_jsonable() for entry in self.entries]}


@dataclass(frozen=True)
class MemoryRetrievalCandidate:
    entry: MemoryEntry
    query_tokens: list[str]
    matched_tokens: list[str]
    overlap_count: int
    score: float
    selected: bool
    rank: int

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry.entry_id,
            "source_scenario": self.entry.source_scenario,
            "situation": self.entry.situation,
            "principle": self.entry.principle,
            "recommended_behavior": self.entry.recommended_behavior,
            "confidence": self.entry.confidence,
            "tags": self.entry.tags,
            "query_tokens": self.query_tokens,
            "matched_tokens": self.matched_tokens,
            "overlap_count": self.overlap_count,
            "score": round(self.score, 4),
            "selected": self.selected,
            "rank": self.rank,
        }


@dataclass(frozen=True)
class MemoryRetrievalLedger:
    query_id: str
    query_tokens: list[str]
    backend: str
    candidates: list[MemoryRetrievalCandidate]
    selected_memory_ids: list[str]
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "query_tokens": self.query_tokens,
            "retrieval_backend": self.backend,
            "candidates": [candidate.to_jsonable() for candidate in self.candidates],
            "selected_memory_ids": self.selected_memory_ids,
            "claim_boundaries": self.claim_boundaries,
        }
