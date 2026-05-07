"""Types for the Scenario Workbench evidence bundle."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


@dataclass(frozen=True)
class EvidenceRef:
    """A lightweight reference to an artifact without copying heavy files."""

    label: str
    path: str | None
    status: str
    summary: str

    def to_jsonable(self) -> JsonDict:
        return {
            "label": self.label,
            "path": self.path,
            "status": self.status,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class VideoEvidence:
    """Judge-visible video metadata for one scenario."""

    path: str | None
    export_status: str
    duration_s: float | None
    fps: float | None
    frame_count: int | None
    width: int | None
    height: int | None
    tracks_path: str | None
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> JsonDict:
        return {
            "path": self.path,
            "export_status": self.export_status,
            "duration_s": self.duration_s,
            "fps": self.fps,
            "frame_count": self.frame_count,
            "width": self.width,
            "height": self.height,
            "tracks_path": self.tracks_path,
            "claim_boundaries": list(self.claim_boundaries),
        }


@dataclass(frozen=True)
class ScenarioRunBundle:
    """One linked scenario lineage from generation through demo evidence."""

    bundle_id: str
    scenario_id: str | None
    behavior_id: str | None
    scenario_brief: JsonDict | None
    studio_candidate: JsonDict | None
    curation_record: JsonDict | None
    carla_video: VideoEvidence
    alpamayo_record: JsonDict | None
    risk_timeline_ref: EvidenceRef
    memory_ref: EvidenceRef
    reasoning_ref: EvidenceRef
    final_pack_ref: EvidenceRef
    product_loop: list[JsonDict]
    claim_boundaries: list[str]
    linkage_warnings: list[str]
    source_paths: dict[str, str | None]

    def to_jsonable(self) -> JsonDict:
        return {
            "bundle_id": self.bundle_id,
            "scenario_id": self.scenario_id,
            "behavior_id": self.behavior_id,
            "scenario_brief": self.scenario_brief,
            "studio_candidate": self.studio_candidate,
            "curation_record": self.curation_record,
            "carla_video": self.carla_video.to_jsonable(),
            "alpamayo_record": self.alpamayo_record,
            "risk_timeline_ref": self.risk_timeline_ref.to_jsonable(),
            "memory_ref": self.memory_ref.to_jsonable(),
            "reasoning_ref": self.reasoning_ref.to_jsonable(),
            "final_pack_ref": self.final_pack_ref.to_jsonable(),
            "product_loop": self.product_loop,
            "claim_boundaries": list(self.claim_boundaries),
            "linkage_warnings": list(self.linkage_warnings),
            "source_paths": dict(self.source_paths),
        }


def path_to_str(path: Path | None) -> str | None:
    return str(path) if path is not None else None
