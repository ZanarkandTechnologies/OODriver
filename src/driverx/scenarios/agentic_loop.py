"""Deterministic agentic OOD scenario generation loop."""

from __future__ import annotations

import html
import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.scenarios.catalog import ScenarioCatalogRecord, load_scenario_catalog
from driverx.scenarios.loader import load_scenario_seeds
from driverx.scenarios.studio import (
    DatasetCurationRecord,
    ScenarioBrief,
    ScenarioStudioCandidate,
    compile_scenario_prompt,
    expand_studio_plan,
    score_studio_candidate,
)


DEFAULT_SEED_THEMES = (
    "Malaysian monsoon roadwork with unsignaled motorcycle filtering",
    "night market double parking with pedestrians hidden by food carts",
    "flooded urban lane with debris and reflective barriers",
    "school-zone occlusion where a child emerges from behind a van",
    "dense informal traffic with wrong-way shoulder creep",
)

REGION_VARIANTS = ("Malaysian", "tropical urban", "informal market", "monsoon", "dense regional")
ENVIRONMENT_VARIANTS = ("wet roadwork", "night market", "flooded avenue", "school zone", "construction merge")
BEHAVIOR_VARIANTS = (
    "motorbike filters between cars without signal",
    "lorry brakes suddenly and blocks the lane",
    "wrong-way scooter creeps along the shoulder",
    "parked van hides a pedestrian crossing late",
    "taxi opens a door while a cyclist swerves",
)
OBJECT_VARIANTS = (
    "fallen cargo sack",
    "reflective flood barrier",
    "plastic food cart",
    "temporary construction cone maze",
    "low dark debris blending into water",
)
POLICY_PRESSURES = (
    "infer non-lane-disciplined motion and maintain lateral clearance",
    "separate irrelevant visual novelty from true collision risk",
    "yield under occlusion before the object is fully visible",
    "avoid assuming the next actor will signal or follow lane rules",
    "slow down enough to preserve a recovery path",
)


@dataclass(frozen=True)
class AgenticOodLoopConfig:
    count: int = 20
    random_seed: int = 17
    severity: int = 4
    count_per_brief: int = 1
    seed_themes: tuple[str, ...] = DEFAULT_SEED_THEMES
    seeds_path: Path = Path("tests/fixtures/fail2drive_like/seeds.json")
    catalog_path: Path | None = None
    output_root: Path = Path("artifacts/runs")
    run_id: str = "agentic-ood-generation-loop"
    min_accept_score: float = 0.55


@dataclass(frozen=True)
class OodNoveltyScore:
    candidate_id: str
    score: float
    pressure_score: float
    novelty_score: float
    novel_tags: list[str]
    duplicate_tags: list[str]
    reason: str

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "score": self.score,
            "pressure_score": self.pressure_score,
            "novelty_score": self.novelty_score,
            "novel_tags": self.novel_tags,
            "duplicate_tags": self.duplicate_tags,
            "reason": self.reason,
        }


def generate_ood_briefs(seed_themes: list[str] | tuple[str, ...], count: int, random_seed: int) -> list[ScenarioBrief]:
    rng = random.Random(random_seed)
    themes = list(seed_themes) or list(DEFAULT_SEED_THEMES)
    briefs: list[ScenarioBrief] = []
    for index in range(max(0, count)):
        theme = themes[index % len(themes)]
        region = rng.choice(REGION_VARIANTS)
        environment = rng.choice(ENVIRONMENT_VARIANTS)
        behavior = rng.choice(BEHAVIOR_VARIANTS)
        obj = rng.choice(OBJECT_VARIANTS)
        pressure = rng.choice(POLICY_PRESSURES)
        prompt = (
            f"{region} {environment}: {behavior} while a {obj} creates a confusing OOD hazard. "
            f"Seed theme: {theme}."
        )
        briefs.append(
            ScenarioBrief(
                brief_id=f"agent-brief-{random_seed:04d}-{index:03d}-{_slug(environment)}",
                prompt=prompt,
                author="agent",
                region=region.lower().replace(" ", "_"),
                requested_tags=_brief_tags(prompt),
                target_policy_pressure=pressure,
            )
        )
    return briefs


def score_ood_novelty(
    candidate: ScenarioStudioCandidate,
    prior: list[ScenarioCatalogRecord],
    accepted_signatures: set[tuple[str, str]],
) -> OodNoveltyScore:
    tags = sorted(
        set(
            candidate.compiled_recipe.memory_query
            + list(candidate.environment_recipe.tags)
            + list(candidate.behavior_plan.tags)
        )
    )
    prior_tags = set()
    for record in prior:
        prior_tags.update(record.environment_tags)
        prior_tags.update(record.ood_tags)
        prior_tags.add(record.behavior_id)
    signature = _signature(candidate)
    duplicate_tags = sorted((set(tags) & prior_tags) | (set(tags) if signature in accepted_signatures else set()))
    novel_tags = sorted(set(tags) - prior_tags)
    pressure_score = min(1.0, len(tags) / 8.0)
    novelty_score = min(1.0, len(novel_tags) / 6.0)
    score = round(0.55 * novelty_score + 0.35 * pressure_score + (0.10 if candidate.carla_run_ready else 0.0), 4)
    reason = (
        f"{len(novel_tags)} novel tag(s), {len(duplicate_tags)} duplicate tag(s), "
        f"pressure={pressure_score:.2f}."
    )
    return OodNoveltyScore(
        candidate_id=candidate.candidate_id,
        score=score,
        pressure_score=round(pressure_score, 4),
        novelty_score=round(novelty_score, 4),
        novel_tags=novel_tags,
        duplicate_tags=duplicate_tags,
        reason=reason,
    )


def run_agentic_ood_generation_loop(config: AgenticOodLoopConfig) -> dict[str, Any]:
    run_dir = prepare_run_dir(config.output_root, config.run_id)
    briefs = generate_ood_briefs(config.seed_themes, config.count, config.random_seed)
    seeds = load_scenario_seeds(config.seeds_path)
    prior = _load_prior(config.catalog_path)
    accepted_signatures: set[tuple[str, str]] = set()
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    scores: list[dict[str, Any]] = []
    plans: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    curation: list[dict[str, Any]] = []
    for index, brief in enumerate(briefs):
        plan = compile_scenario_prompt(brief.prompt, seed=config.random_seed + index)
        plans.append(plan.to_jsonable())
        expanded = expand_studio_plan(
            plan,
            count=config.count_per_brief,
            random_seed=config.random_seed + index * 101,
            seeds=seeds,
            severity=config.severity,
        )
        for candidate in expanded:
            studio_score = score_studio_candidate(candidate, prior)
            novelty = score_ood_novelty(candidate, prior, accepted_signatures)
            decision = _decision(candidate, studio_score, novelty, config.min_accept_score, accepted_signatures)
            row = _curation_row(candidate, studio_score, novelty, decision)
            scores.append(novelty.to_jsonable())
            candidates.append(candidate.to_jsonable())
            curation.append(row)
            if decision["accepted"]:
                accepted_signatures.add(_signature(candidate))
                accepted.append(row)
            else:
                rejected.append(row)
    payload = {
        "loop_id": run_dir.name,
        "status": "passed" if accepted else "partial",
        "brief_count": len(briefs),
        "plan_count": len(plans),
        "candidate_count": len(candidates),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "seed_themes": list(config.seed_themes),
        "briefs": [brief.to_jsonable() for brief in briefs],
        "plans": plans,
        "candidates": candidates,
        "novelty_scores": scores,
        "curation_queue": curation,
        "accepted_candidate_ids": [row["candidate_id"] for row in accepted],
        "rejected_candidate_ids": [row["candidate_id"] for row in rejected],
        "next_runtime_targets": _next_runtime_targets(accepted),
        "claim_boundaries": [
            "deterministic_agentic_generation=true",
            "live_llm_generation=false",
            "mesh_asset_generation=false",
            "carla_execution=false",
            "dataset_curation_queue=true",
        ],
    }
    return write_agentic_ood_generation_loop(run_dir, payload)


def write_agentic_ood_generation_loop(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    json_path = run_dir / "agentic_ood_generation_loop.json"
    queue_path = run_dir / "dataset_curation_queue.md"
    gallery_path = run_dir / "scenario_brief_gallery.html"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    queue_path.write_text(_queue_markdown(payload), encoding="utf-8")
    gallery_path.write_text(_gallery_html(payload), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "queue_path": str(queue_path),
        "gallery_path": str(gallery_path),
    }


def _decision(
    candidate: ScenarioStudioCandidate,
    studio_score: DatasetCurationRecord,
    novelty: OodNoveltyScore,
    min_accept_score: float,
    accepted_signatures: set[tuple[str, str]],
) -> dict[str, Any]:
    signature = _signature(candidate)
    if not candidate.carla_run_ready:
        return {"accepted": False, "status": "reject_invalid", "reason": "candidate did not compile for CARLA"}
    if signature in accepted_signatures:
        return {"accepted": False, "status": "reject_duplicate", "reason": "same environment/behavior already accepted"}
    combined = round((studio_score.score + novelty.score) / 2.0, 4)
    if combined < min_accept_score:
        return {"accepted": False, "status": "reject_weak", "reason": f"combined score {combined} below {min_accept_score}"}
    return {"accepted": True, "status": "accept_partial", "reason": f"combined score {combined} passes curation gate"}


def _curation_row(
    candidate: ScenarioStudioCandidate,
    studio_score: DatasetCurationRecord,
    novelty: OodNoveltyScore,
    decision: dict[str, Any],
) -> dict[str, Any]:
    return {
        "candidate_id": candidate.candidate_id,
        "accepted": bool(decision["accepted"]),
        "curation_status": decision["status"],
        "reason": decision["reason"],
        "studio_score": studio_score.score,
        "novelty_score": novelty.score,
        "pressure_score": novelty.pressure_score,
        "novel_tags": novelty.novel_tags,
        "duplicate_tags": novelty.duplicate_tags,
        "environment_template_id": candidate.compiled_recipe.environment.get("environment_template_id"),
        "behavior_id": candidate.behavior_plan.behavior_id,
        "next_action": (
            "run high-fidelity CARLA capture and Alpamayo/RAG open-loop evaluation"
            if decision["accepted"]
            else "revise prompt or mutate a different behavior/environment pair"
        ),
    }


def _next_runtime_targets(accepted: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "candidate_id": row["candidate_id"],
            "why": f"{row['reason']}; run CARLA for {row['behavior_id']} in {row['environment_template_id']}",
        }
        for row in accepted[:8]
    ]


def _queue_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Agentic OOD Dataset Queue: {payload['loop_id']}",
        "",
        f"- Accepted: `{payload['accepted_count']}`",
        f"- Rejected: `{payload['rejected_count']}`",
        "",
        "| Candidate | Decision | Novelty | Pressure | Next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["curation_queue"]:
        lines.append(
            f"| `{row['candidate_id']}` | {row['curation_status']} | {row['novelty_score']} | {row['pressure_score']} | {row['next_action']} |"
        )
    return "\n".join(lines) + "\n"


def _gallery_html(payload: dict[str, Any]) -> str:
    cards = []
    curation_by_id = {row["candidate_id"]: row for row in payload["curation_queue"]}
    for candidate in payload["candidates"]:
        row = curation_by_id.get(candidate["candidate_id"], {})
        recipe = candidate.get("compiled_recipe", {})
        tags = ", ".join(recipe.get("memory_query", [])[:8])
        cards.append(
            f"""
<article>
  <h2>{html.escape(candidate["candidate_id"])}</h2>
  <p><strong>{html.escape(str(row.get("curation_status", "")))}</strong> - {html.escape(str(row.get("reason", "")))}</p>
  <p>Environment: <code>{html.escape(str(row.get("environment_template_id", "")))}</code></p>
  <p>Behavior: <code>{html.escape(str(row.get("behavior_id", "")))}</code></p>
  <p>Tags: {html.escape(tags)}</p>
</article>"""
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Agentic OOD Scenario Gallery</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 28px; background: #f8fafc; color: #111827; }}
    main {{ max-width: 1120px; margin: 0 auto; }}
    article {{ background: white; border: 1px solid #d9dee7; border-radius: 6px; padding: 14px 16px; margin: 12px 0; }}
    h1 {{ font-size: 28px; }}
    h2 {{ font-size: 17px; margin: 0 0 8px; }}
    code {{ background: #eef2f7; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body><main>
<h1>Agentic OOD Scenario Gallery</h1>
<p>Deterministic agent loop generated {payload['candidate_count']} candidate(s), accepting {payload['accepted_count']} for the next CARLA run queue.</p>
{''.join(cards)}
</main></body></html>
"""


def _brief_tags(prompt: str) -> list[str]:
    lowered = prompt.lower()
    tags = []
    for token in (
        "malaysian",
        "monsoon",
        "motorbike",
        "motorcycle",
        "roadwork",
        "flood",
        "market",
        "pedestrian",
        "occlusion",
        "wrong-way",
        "debris",
        "construction",
    ):
        if token in lowered:
            tags.append(token.replace("-", "_"))
    return sorted(set(tags))


def _signature(candidate: ScenarioStudioCandidate) -> tuple[str, str]:
    environment = str(candidate.compiled_recipe.environment.get("environment_template_id", ""))
    return environment, candidate.behavior_plan.behavior_id


def _load_prior(path: Path | None) -> list[ScenarioCatalogRecord]:
    if path is None or not path.exists():
        return []
    return load_scenario_catalog(path).records


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:40] or "scenario"
