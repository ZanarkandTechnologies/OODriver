"""Build ancestry cards linking generated OODrive scenarios to reference seeds."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CLAIM_BOUNDARIES = [
    "scenario_generation_randomized=true",
    "fail2drive_reference_grounding=true",
    "official_fail2drive_score_claim=false",
    "source_citations=true",
]


def build_scenario_ancestry_cards(
    *,
    db_path: Path,
    fail2drive_report_path: Path,
    retrieval_ledger_paths: tuple[Path, ...] = (),
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-scenario-ancestry-cards",
    limit: int = 8,
) -> dict[str, Any]:
    db = _load_json(db_path)
    fail2drive = _load_json(fail2drive_report_path)
    ledgers = [_load_json(path) for path in retrieval_ledger_paths if path.exists()]
    extension_by_id = {
        str(record.get("generated_scenario_id")): record
        for record in _list(fail2drive.get("extension_records"))
        if isinstance(record, dict)
    }
    cards = []
    for candidate in _list(db.get("candidates"))[:limit]:
        if not isinstance(candidate, dict):
            continue
        recipe = candidate.get("compiled_recipe") if isinstance(candidate.get("compiled_recipe"), dict) else {}
        scenario_id = str(candidate.get("candidate_id") or recipe.get("recipe_id"))
        extension = extension_by_id.get(scenario_id) or _best_extension(extension_by_id, recipe)
        cards.append(_card(candidate, recipe, extension, ledgers))
    report = {
        "report_id": run_id,
        "db_path": str(db_path),
        "fail2drive_report_path": str(fail2drive_report_path),
        "retrieval_ledger_paths": [str(path) for path in retrieval_ledger_paths],
        "cards": cards,
        "card_count": len(cards),
        "claim_boundaries": CLAIM_BOUNDARIES,
    }
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "scenario_ancestry_cards.json"
    md_path = run_dir / "scenario_ancestry_cards.md"
    html_path = run_dir / "scenario_ancestry_cards.html"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    html_path.write_text(_html(report), encoding="utf-8")
    return {**report, "json_path": str(json_path), "report_path": str(md_path), "html_path": str(html_path)}


def _card(
    candidate: dict[str, Any],
    recipe: dict[str, Any],
    extension: dict[str, Any],
    ledgers: list[dict[str, Any]],
) -> dict[str, Any]:
    environment = recipe.get("environment") if isinstance(recipe.get("environment"), dict) else {}
    tags = _string_list(candidate.get("ood_tags")) or _string_list(environment.get("environment_tags"))
    selected_memories: list[str] = []
    for ledger in ledgers:
        selected_memories.extend(_string_list(ledger.get("selected_memory_ids")))
    return {
        "scenario_id": candidate.get("candidate_id") or recipe.get("recipe_id"),
        "parent_seed_id": recipe.get("parent_seed_id"),
        "mutation": recipe.get("mutation"),
        "environment_template_id": environment.get("environment_template_id"),
        "behavior_id": environment.get("behavior_id"),
        "ood_tags": tags[:8],
        "expected_failure_mode": recipe.get("expected_failure_mode"),
        "fail2drive_refs": extension.get("matched_reference_ids", []),
        "route_refs": extension.get("fail2drive_route_refs", []),
        "mutation_summary": extension.get("mutation_summary"),
        "memory_entry_ids": _string_list(extension.get("memory_entry_ids")) + selected_memories[:2],
        "citation_sources": [
            "scenario_studio_db",
            "fail2drive_extension_report",
            *("memory_retrieval_ledger" for _ in selected_memories[:1]),
        ],
    }


def _best_extension(extension_by_id: dict[str, dict[str, Any]], recipe: dict[str, Any]) -> dict[str, Any]:
    mutation = str(recipe.get("mutation", "")).replace("_", "-")
    parent = str(recipe.get("parent_seed_id", "")).lower()
    for record in extension_by_id.values():
        text = " ".join(str(value) for value in record.values()).lower()
        if mutation and mutation in text:
            return record
        if parent and parent in text:
            return record
    return next(iter(extension_by_id.values()), {})


def _markdown(report: dict[str, Any]) -> str:
    lines = ["# OODrive Scenario Ancestry Cards", "", f"- Cards: `{report['card_count']}`", ""]
    for card in report["cards"]:
        lines.extend(
            [
                f"## {card.get('scenario_id')}",
                "",
                f"- Parent seed: `{card.get('parent_seed_id')}`",
                f"- Mutation: `{card.get('mutation')}`",
                f"- Fail2Drive refs: `{', '.join(_string_list(card.get('fail2drive_refs'))) or 'none'}`",
                f"- Memory: `{', '.join(_string_list(card.get('memory_entry_ids'))) or 'none'}`",
                f"- Expected failure: {card.get('expected_failure_mode')}",
                "",
            ]
        )
    return "\n".join(lines)


def _html(report: dict[str, Any]) -> str:
    cards = "\n".join(
        "<article><h2>{}</h2><p><strong>Mutation:</strong> {}</p><p><strong>References:</strong> {}</p>"
        "<p><strong>Memory:</strong> {}</p><p>{}</p></article>".format(
            card.get("scenario_id"),
            card.get("mutation"),
            ", ".join(_string_list(card.get("fail2drive_refs"))) or "none",
            ", ".join(_string_list(card.get("memory_entry_ids"))) or "none",
            card.get("expected_failure_mode") or "",
        )
        for card in report["cards"]
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>OODrive Scenario Ancestry</title>"
        "<style>body{font-family:Arial,sans-serif;max-width:1100px;margin:32px auto;line-height:1.4}"
        "article{border:1px solid #ddd;border-radius:6px;padding:16px;margin:12px 0}</style>"
        "</head><body><h1>OODrive Scenario Ancestry Cards</h1>"
        f"<p>Cards: <strong>{report['card_count']}</strong></p>{cards}</body></html>"
    )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in _list(value)]


__all__ = ["build_scenario_ancestry_cards"]
