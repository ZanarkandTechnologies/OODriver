"""Map DriverX generated OOD cases back to Fail2Drive reference families."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Sequence

from driverx.core.artifacts import prepare_run_dir
from driverx.memory.bank import build_memory_bank
from driverx.memory.types import MemoryBank, MemoryEntry
from driverx.scenarios import ScenarioCatalogRecord, load_scenario_catalog
from driverx.scenarios.loader import load_scenario_results, load_scenario_seeds
from driverx.scenarios.types import ScenarioSeed

ExtensionClaim = Literal["generated_extension", "fixture_reference", "unlinked_generated_case"]


@dataclass(frozen=True)
class GeneratedCaseRef:
    scenario_id: str
    source_path: str
    source_kind: str
    family: str
    behavior_id: str | None
    tags: list[str]
    route_refs: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "source_path": self.source_path,
            "source_kind": self.source_kind,
            "family": self.family,
            "behavior_id": self.behavior_id,
            "tags": self.tags,
            "route_refs": self.route_refs,
        }


@dataclass(frozen=True)
class Fail2DriveReference:
    ref_id: str
    split: str
    scenario_class: str
    route_id: str | None
    route_path: str | None
    tags: list[str]
    failure_summary: str | None = None
    source: str = "fixture"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "ref_id": self.ref_id,
            "split": self.split,
            "scenario_class": self.scenario_class,
            "route_id": self.route_id,
            "route_path": self.route_path,
            "tags": self.tags,
            "failure_summary": self.failure_summary,
            "source": self.source,
        }


@dataclass(frozen=True)
class Fail2DriveExtensionRecord:
    generated_scenario_id: str
    driverx_behavior_id: str | None
    fail2drive_seed_family: str | None
    fail2drive_route_refs: list[str]
    matched_reference_ids: list[str]
    mutation_summary: str
    memory_entry_ids: list[str]
    claim: ExtensionClaim
    official_score_claim: str
    match_score: float

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "generated_scenario_id": self.generated_scenario_id,
            "driverx_behavior_id": self.driverx_behavior_id,
            "fail2drive_seed_family": self.fail2drive_seed_family,
            "fail2drive_route_refs": self.fail2drive_route_refs,
            "matched_reference_ids": self.matched_reference_ids,
            "mutation_summary": self.mutation_summary,
            "memory_entry_ids": self.memory_entry_ids,
            "claim": self.claim,
            "official_score_claim": self.official_score_claim,
            "match_score": self.match_score,
        }


@dataclass(frozen=True)
class Fail2DriveExtensionReportConfig:
    generated_source_paths: tuple[Path, ...]
    output_root: Path = Path("artifacts/runs")
    run_id: str = "fail2drive-extension-report"
    fail2drive_root: Path | None = None
    memory_bank_path: Path | None = None
    fixture_seeds_path: Path = Path("tests/fixtures/fail2drive_like/seeds.json")
    fixture_results_path: Path = Path("tests/fixtures/fail2drive_like/results.json")


def run_fail2drive_extension_report(config: Fail2DriveExtensionReportConfig) -> dict[str, Any]:
    run_dir = prepare_run_dir(config.output_root, config.run_id)
    return build_fail2drive_extension_report(
        generated_source_paths=config.generated_source_paths,
        output_dir=run_dir,
        fail2drive_root=config.fail2drive_root,
        memory_bank_path=config.memory_bank_path,
        fixture_seeds_path=config.fixture_seeds_path,
        fixture_results_path=config.fixture_results_path,
    )


def build_fail2drive_extension_report(
    *,
    generated_source_paths: Sequence[Path],
    output_dir: Path,
    fail2drive_root: Path | None = None,
    memory_bank_path: Path | None = None,
    fixture_seeds_path: Path = Path("tests/fixtures/fail2drive_like/seeds.json"),
    fixture_results_path: Path = Path("tests/fixtures/fail2drive_like/results.json"),
) -> dict[str, Any]:
    if not generated_source_paths:
        raise ValueError("At least one generated source path is required.")
    generated_cases = _load_generated_cases(generated_source_paths)
    references = _load_references(
        fail2drive_root=fail2drive_root,
        fixture_seeds_path=fixture_seeds_path,
        fixture_results_path=fixture_results_path,
    )
    memory_bank = _load_memory_bank(memory_bank_path, fixture_results_path)
    records = [
        _extension_record(case, references, memory_bank)
        for case in generated_cases
    ]
    payload = {
        "report_id": output_dir.name,
        "generated_case_count": len(generated_cases),
        "reference_count": len(references),
        "memory_entry_count": len(memory_bank.entries),
        "claim_counts": _count_by(records, "claim"),
        "reference_sources": sorted({reference.source for reference in references}),
        "generated_sources": [str(path) for path in generated_source_paths],
        "fail2drive_root": str(fail2drive_root) if fail2drive_root else None,
        "generated_cases": [case.to_jsonable() for case in generated_cases],
        "fail2drive_references": [reference.to_jsonable() for reference in references],
        "extension_records": [record.to_jsonable() for record in records],
        "claim_boundaries": [
            "fail2drive_reference_layer=true",
            "generated_cases_are_driverx_extensions=true",
            "official_fail2drive_score_claim=false",
            "live_fail2drive_execution=false",
        ],
    }
    return write_fail2drive_extension_report(output_dir, payload)


def write_fail2drive_extension_report(output_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "fail2drive_extension_report.json"
    report_path = output_dir / "fail2drive_extension_report.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _load_generated_cases(paths: Sequence[Path]) -> list[GeneratedCaseRef]:
    cases: dict[str, GeneratedCaseRef] = {}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for case in _cases_from_payload(payload, path):
            current = cases.get(case.scenario_id)
            if current is None or _case_strength(case) > _case_strength(current):
                cases[case.scenario_id] = case
            elif current is not None:
                cases[case.scenario_id] = _merge_generated_case(current, case)
    return sorted(cases.values(), key=lambda item: item.scenario_id)


def _cases_from_payload(payload: dict[str, Any], path: Path) -> list[GeneratedCaseRef]:
    if isinstance(payload.get("records"), list):
        return [_case_from_catalog_record(ScenarioCatalogRecord.from_jsonable(dict(record)), path) for record in payload["records"]]
    if isinstance(payload.get("cases"), list):
        return [_case_from_matrix_case(dict(case), path) for case in payload["cases"]]
    if isinstance(payload.get("candidates"), list):
        return [_case_from_studio_candidate(dict(candidate), path) for candidate in payload["candidates"]]
    if "record_count" in payload:
        catalog = load_scenario_catalog(path)
        return [_case_from_catalog_record(record, path) for record in catalog.records]
    raise ValueError(f"Unsupported generated source payload: {path}")


def _case_from_catalog_record(record: ScenarioCatalogRecord, path: Path) -> GeneratedCaseRef:
    return GeneratedCaseRef(
        scenario_id=record.scenario_id,
        source_path=str(path),
        source_kind="scenario_catalog",
        family=record.family,
        behavior_id=record.behavior_id,
        tags=sorted(set([record.family, *record.environment_tags, *record.ood_tags])),
        route_refs=record.source_artifacts,
    )


def _case_from_matrix_case(case: dict[str, Any], path: Path) -> GeneratedCaseRef:
    return GeneratedCaseRef(
        scenario_id=str(case["scenario_id"]),
        source_path=str(path),
        source_kind="submission_eval_matrix",
        family=str(case.get("scenario_family", "unknown")),
        behavior_id=_optional_str(case.get("behavior_id")),
        tags=sorted(set(_strings(case.get("environment_tags", [])) + _strings(case.get("ood_tags", [])) + [str(case.get("scenario_family", "unknown"))])),
        route_refs=_strings(case.get("blockers", [])),
    )


def _case_from_studio_candidate(candidate: dict[str, Any], path: Path) -> GeneratedCaseRef:
    recipe = dict(candidate.get("compiled_recipe", {}))
    environment = dict(candidate.get("environment_recipe", {}))
    behavior = dict(candidate.get("behavior_plan", {}))
    recipe_environment = dict(recipe.get("environment", {}))
    environment_tags = _strings(environment.get("tags", []))
    behavior_tags = _strings(behavior.get("tags", []))
    recipe_tags = _strings(recipe_environment.get("ood_tags", [])) + _strings(recipe_environment.get("asset_tags", []))
    memory_query = _strings(recipe.get("memory_query", []))
    route_path = _optional_str(recipe.get("route_path"))
    return GeneratedCaseRef(
        scenario_id=str(candidate["candidate_id"]),
        source_path=str(path),
        source_kind="scenario_studio",
        family=str(environment.get("family", recipe_environment.get("environment_family", "generated"))),
        behavior_id=_optional_str(behavior.get("behavior_id") or recipe_environment.get("behavior_id")),
        tags=sorted(set([*environment_tags, *behavior_tags, *recipe_tags, *memory_query])),
        route_refs=[route_path] if route_path else [],
    )


def _case_strength(case: GeneratedCaseRef) -> int:
    return len(case.tags) + len(case.route_refs) + (2 if case.behavior_id else 0)


def _merge_generated_case(left: GeneratedCaseRef, right: GeneratedCaseRef) -> GeneratedCaseRef:
    return GeneratedCaseRef(
        scenario_id=left.scenario_id,
        source_path=left.source_path,
        source_kind=left.source_kind,
        family=left.family if left.family != "unknown" else right.family,
        behavior_id=left.behavior_id or right.behavior_id,
        tags=sorted(set(left.tags) | set(right.tags)),
        route_refs=sorted(set(left.route_refs) | set(right.route_refs)),
    )


def _load_references(
    *,
    fail2drive_root: Path | None,
    fixture_seeds_path: Path,
    fixture_results_path: Path,
) -> list[Fail2DriveReference]:
    references: dict[str, Fail2DriveReference] = {}
    if fixture_seeds_path.exists():
        for seed in load_scenario_seeds(fixture_seeds_path):
            references[seed.seed_id] = _reference_from_seed(seed, source="fixture_seed")
    if fixture_results_path.exists():
        for result in load_scenario_results(fixture_results_path):
            if result.success:
                continue
            ref_id = result.scenario_id
            references[ref_id] = Fail2DriveReference(
                ref_id=ref_id,
                split="Generalization" if "Generalization" in ref_id else "Result",
                scenario_class=_class_from_identifier(ref_id),
                route_id=_route_id_from_identifier(ref_id),
                route_path=None,
                tags=sorted(set(_tokens([ref_id, result.failure_summary or "", *result.tags]))),
                failure_summary=result.failure_summary,
                source="fixture_result",
            )
    if fail2drive_root is not None and fail2drive_root.exists():
        for xml_path in _iter_fail2drive_xmls(fail2drive_root):
            seed = _seed_from_route_xml(xml_path)
            if seed is not None:
                references.setdefault(seed.seed_id, _reference_from_seed(seed, source="external_route"))
    return sorted(references.values(), key=lambda item: item.ref_id)


def _reference_from_seed(seed: ScenarioSeed, *, source: str) -> Fail2DriveReference:
    return Fail2DriveReference(
        ref_id=seed.seed_id,
        split=seed.split,
        scenario_class=seed.scenario_class,
        route_id=seed.route_id,
        route_path=str(seed.route_path) if seed.route_path else None,
        tags=sorted(set([seed.scenario_class, *seed.ood_tags, *_tokens([seed.seed_id, seed.scenario_class])])),
        source=source,
    )


def _iter_fail2drive_xmls(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for rel in ("leaderboard/data", "leaderboard/data/bench2drive", "data", "routes", "fail2drive_split"):
        base = root / rel
        if base.exists():
            candidates.extend(sorted(base.rglob("*.xml"))[:1000])
    if not candidates:
        candidates = sorted(root.glob("**/*.xml"))[:1000]
    return candidates


def _seed_from_route_xml(path: Path) -> ScenarioSeed | None:
    from driverx.scenarios.loader import load_scenario_seeds

    try:
        return load_scenario_seeds(path)[0]
    except (FileNotFoundError, ValueError, IndexError):
        return None


def _load_memory_bank(path: Path | None, fixture_results_path: Path) -> MemoryBank:
    if path is not None and path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries = [MemoryEntry(**dict(entry)) for entry in list(payload.get("entries", []))]
        return MemoryBank(entries=entries)
    if fixture_results_path.exists():
        return build_memory_bank(load_scenario_results(fixture_results_path))
    return MemoryBank(entries=[])


def _extension_record(
    case: GeneratedCaseRef,
    references: list[Fail2DriveReference],
    memory_bank: MemoryBank,
) -> Fail2DriveExtensionRecord:
    matches = _rank_references(case, references)
    matched_refs = [reference for score, reference in matches if score > 0][:3]
    memory_ids = _matching_memory_ids(case, memory_bank, limit=3)
    claim: ExtensionClaim
    if matched_refs:
        claim = "fixture_reference" if case.source_kind == "scenario_catalog" and case.family.lower() in {"animals", "pedestriansonroad", "customobstacles"} else "generated_extension"
    else:
        claim = "unlinked_generated_case"
    top_family = matched_refs[0].scenario_class if matched_refs else None
    route_refs = sorted({ref.route_path or ref.ref_id for ref in matched_refs})
    return Fail2DriveExtensionRecord(
        generated_scenario_id=case.scenario_id,
        driverx_behavior_id=case.behavior_id,
        fail2drive_seed_family=top_family,
        fail2drive_route_refs=route_refs,
        matched_reference_ids=[ref.ref_id for ref in matched_refs],
        mutation_summary=_mutation_summary(case, matched_refs),
        memory_entry_ids=memory_ids,
        claim=claim,
        official_score_claim="reference_only_no_official_fail2drive_score",
        match_score=round(matches[0][0], 4) if matches else 0.0,
    )


def _rank_references(case: GeneratedCaseRef, references: list[Fail2DriveReference]) -> list[tuple[float, Fail2DriveReference]]:
    case_tokens = _tokens([case.scenario_id, case.family, case.behavior_id or "", *case.tags])
    ranked: list[tuple[float, Fail2DriveReference]] = []
    for reference in references:
        ref_tokens = _tokens([reference.ref_id, reference.scenario_class, *reference.tags])
        overlap = len(case_tokens & ref_tokens)
        semantic = _semantic_bonus(case_tokens, reference.scenario_class)
        route_bonus = 1.5 if any(reference.ref_id in ref or str(reference.route_id or "") in ref for ref in case.route_refs) else 0.0
        score = float(overlap) + semantic + route_bonus
        ranked.append((score, reference))
    ranked.sort(key=lambda item: (-item[0], item[1].ref_id))
    return ranked


def _semantic_bonus(tokens: set[str], scenario_class: str) -> float:
    normalized = scenario_class.lower()
    if normalized == "animals" and tokens & {"animal", "animals", "unknown", "obstacle", "occupied", "visual", "noise"}:
        return 2.0
    if normalized == "pedestriansonroad" and tokens & {"pedestrian", "crossing", "school", "occlusion", "hidden", "creep"}:
        return 2.0
    if normalized == "customobstacles" and tokens & {"custom", "obstacle", "debris", "visual", "artifact", "low", "flood"}:
        return 2.0
    return 0.0


def _matching_memory_ids(case: GeneratedCaseRef, memory_bank: MemoryBank, *, limit: int) -> list[str]:
    case_tokens = _tokens([case.scenario_id, case.family, case.behavior_id or "", *case.tags])
    scored: list[tuple[int, float, str]] = []
    for entry in memory_bank.entries:
        overlap = len(case_tokens & _tokens([entry.entry_id, entry.situation, entry.observed_failure, *entry.tags]))
        if overlap:
            scored.append((overlap, entry.confidence, entry.entry_id))
    scored.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return [entry_id for _overlap, _confidence, entry_id in scored[:limit]]


def _mutation_summary(case: GeneratedCaseRef, references: list[Fail2DriveReference]) -> str:
    behavior = case.behavior_id or "unspecified behavior"
    if not references:
        return f"DriverX generated `{case.family}` with `{behavior}` but no close Fail2Drive fixture reference was found."
    family = references[0].scenario_class
    tags = ", ".join(case.tags[:6])
    return f"DriverX extends Fail2Drive `{family}` references with `{behavior}` under tags: {tags}."


def _count_by(records: list[Fail2DriveExtensionRecord], attr: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        key = str(getattr(record, attr))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _class_from_identifier(value: str) -> str:
    match = re.search(r"(?:Base|Generalization)_([A-Za-z]+)_", value)
    return match.group(1) if match else value


def _route_id_from_identifier(value: str) -> str | None:
    match = re.search(r"_(\d{4})(?:$|_)", value)
    return match.group(1) if match else None


def _tokens(values: Sequence[str]) -> set[str]:
    text = " ".join(str(value) for value in values if value).lower()
    return {token for token in re.split(r"[^a-z0-9]+", text) if token}


def _strings(values: Any) -> list[str]:
    if isinstance(values, list):
        return [str(value) for value in values if str(value)]
    if isinstance(values, tuple):
        return [str(value) for value in values if str(value)]
    if values is None:
        return []
    return [str(values)] if str(values) else []


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Fail2Drive Extension Report",
        "",
        f"- Generated cases: `{payload['generated_case_count']}`",
        f"- Fail2Drive references: `{payload['reference_count']}`",
        f"- Memory entries: `{payload['memory_entry_count']}`",
        f"- Claim counts: `{payload['claim_counts']}`",
        "",
        "## Claim Boundaries",
        "",
    ]
    for boundary in payload["claim_boundaries"]:
        lines.append(f"- `{boundary}`")
    lines.extend(
        [
            "",
            "## Extension Matrix",
            "",
            "| generated case | claim | behavior | Fail2Drive family | references | memory | summary |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for record in payload["extension_records"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(record["generated_scenario_id"]),
                    _cell(record["claim"]),
                    _cell(record["driverx_behavior_id"]),
                    _cell(record["fail2drive_seed_family"]),
                    _cell(", ".join(record["matched_reference_ids"])),
                    _cell(", ".join(record["memory_entry_ids"])),
                    _cell(record["mutation_summary"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This report is a reference and extension layer. It connects DriverX-generated OOD cases to Fail2Drive-style families and failure memories, but it does not claim an official Fail2Drive leaderboard score.",
            "",
        ]
    )
    return "\n".join(lines)


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


__all__ = [
    "Fail2DriveExtensionRecord",
    "Fail2DriveExtensionReportConfig",
    "Fail2DriveReference",
    "GeneratedCaseRef",
    "build_fail2drive_extension_report",
    "run_fail2drive_extension_report",
    "write_fail2drive_extension_report",
]
