"""OODrive product-level scenario database orchestration."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from driverx.core.artifacts import timestamp_run_id
from driverx.scenarios.policy_evaluation import (
    PolicyEvaluationRecord,
    write_policy_evaluation,
)
from driverx.scenarios.queue import (
    QueueBuildOptions,
    build_scenario_dataset_queue,
    write_scenario_dataset_queue,
)
from driverx.scenarios.run_manifest import ScenarioRunManifest, write_run_manifest
from driverx.scenarios.studio import ScenarioStudioConfig, generate_studio_batch
from driverx.scenarios.studio_db import (
    OODRIVE_PRODUCT_NAME,
    append_brief,
    append_bundle,
    append_command,
    append_evaluation,
    append_export,
    append_run,
    load_studio_db,
    new_studio_db,
    replace_db,
    studio_db_path,
    write_studio_db,
)
from driverx.scenarios.studio_product_helpers import (
    artifact_paths,
    candidate_for_run,
    cot_from_prediction,
    latency_from_prediction,
    load_or_latest_evaluation,
    load_or_latest_run,
    load_prediction,
    memory_ids_for_candidate,
    mock_actions_for_record,
    oodrive_command,
    queue_next_commands,
    select_queue_record,
    trajectory_summary_from_prediction,
    update_queue_record,
)
from driverx.scenarios.studio_product_reports import (
    build_bundle_payload,
    build_export_payload,
    write_bundle,
    write_export_pack,
)


@dataclass(frozen=True)
class StudioCommandResult:
    command: str
    run_id: str
    status: str
    artifacts: dict[str, str] = field(default_factory=dict)
    next_commands: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    claim_boundaries: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "product": OODRIVE_PRODUCT_NAME,
            "command": self.command,
            "run_id": self.run_id,
            "status": self.status,
            "artifacts": self.artifacts,
            "next_commands": self.next_commands,
            "summary": self.summary,
            "claim_boundaries": self.claim_boundaries,
            "blockers": self.blockers,
        }


def run_studio_init(output_root: Path, run_id: str, *, force: bool = False) -> StudioCommandResult:
    path = studio_db_path(output_root, run_id)
    if path.exists() and not force:
        db = load_studio_db(path)
        status = "passed"
        summary = {"created": False, "brief_count": len(db.briefs), "candidate_count": len(db.candidates)}
    else:
        db = new_studio_db(run_id)
        write_studio_db(path, db)
        status = "passed"
        summary = {"created": True, "brief_count": 0, "candidate_count": 0}
    db = append_command(
        load_studio_db(path),
        command="oodrive init",
        status=status,
        artifacts={"db_path": str(path), "report_path": str(path.with_suffix(".md"))},
        summary=summary,
    )
    artifacts = artifact_paths(write_studio_db(path, db))
    return StudioCommandResult(
        command="oodrive init",
        run_id=db.run_id,
        status=status,
        artifacts=artifacts,
        next_commands=[oodrive_command(f"ingest-brief --db {path} --prompt '<brief>'")],
        summary=summary,
        claim_boundaries=db.claim_boundaries,
    )


def run_studio_ingest_brief(
    db_path: Path,
    *,
    prompt: str,
    author: str = "human",
    requested_tags: Iterable[str] = (),
    region: str | None = None,
    target_policy_pressure: str | None = None,
) -> StudioCommandResult:
    db = load_studio_db(db_path)
    clean_prompt = prompt.strip()
    if not clean_prompt:
        raise ValueError("Brief prompt is required.")
    brief = {
        "brief_id": f"brief-{len(db.briefs) + 1:04d}",
        "prompt": clean_prompt,
        "author": author,
        "region": region,
        "requested_tags": sorted({tag for tag in requested_tags if tag}),
        "target_policy_pressure": target_policy_pressure,
    }
    db = append_brief(db, brief)
    db = append_command(
        db,
        command="oodrive ingest-brief",
        status="passed",
        artifacts={"db_path": str(db_path)},
        summary={"brief_id": brief["brief_id"], "prompt": clean_prompt},
    )
    artifacts = artifact_paths(write_studio_db(db_path, db))
    return StudioCommandResult(
        command="oodrive ingest-brief",
        run_id=db.run_id,
        status="passed",
        artifacts=artifacts,
        next_commands=[oodrive_command(f"compile --db {db_path} --count 6 --seed 7")],
        summary={"brief": brief, "brief_count": len(db.briefs)},
        claim_boundaries=db.claim_boundaries,
    )


def generate_ai_scenario_briefs(
    prompt: str,
    *,
    count: int = 4,
    provider: str = "codex-template",
    seed: int = 7,
    starting_index: int = 0,
) -> list[dict[str, Any]]:
    """Generate deterministic AI-style scenario briefs from one source prompt."""

    clean_prompt = prompt.strip()
    if not clean_prompt:
        raise ValueError("AI scenario prompt is required.")
    if count < 1:
        raise ValueError("AI scenario generation count must be at least 1.")

    variants = _scenario_variant_templates(clean_prompt)
    briefs: list[dict[str, Any]] = []
    for offset in range(count):
        variant = variants[(seed + offset) % len(variants)]
        generated_prompt = _combine_prompt(clean_prompt, variant)
        tags = _infer_ai_tags(generated_prompt)
        region = _infer_ai_region(generated_prompt)
        brief_number = starting_index + offset + 1
        briefs.append(
            {
                "brief_id": f"brief-{brief_number:04d}",
                "prompt": generated_prompt,
                "author": "provider",
                "provider": provider,
                "source_prompt": clean_prompt,
                "region": region,
                "requested_tags": tags,
                "target_policy_pressure": _infer_policy_pressure(tags),
                "generation_notes": [
                    "generated_by=oodrive_ai_generate",
                    f"provider={provider}",
                    f"seed={seed}",
                    f"variant_index={offset}",
                ],
            }
        )
    return briefs


def run_studio_ai_generate(
    *,
    prompts: Iterable[str],
    db_path: Path | None = None,
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-ai",
    count: int = 4,
    provider: str = "codex-template",
    seed: int = 7,
    force: bool = False,
    compile_candidates: bool = False,
    queue_candidates: bool = False,
    severity: int = 4,
    accept: str = "top:3",
) -> StudioCommandResult:
    prompt_list = [prompt.strip() for prompt in prompts if prompt.strip()]
    if not prompt_list:
        raise ValueError("At least one --prompt is required for ai-generate.")
    if queue_candidates and not compile_candidates:
        raise ValueError("Pass --compile when using --queue so queued candidates exist.")
    if db_path is None:
        init_result = run_studio_init(output_root, run_id, force=force)
        db_path = Path(init_result.artifacts["db_path"])
    elif not db_path.exists():
        raise FileNotFoundError(f"OODrive studio DB not found: {db_path}")

    db = load_studio_db(db_path)
    generated: list[dict[str, Any]] = []
    next_index = len(db.briefs)
    for prompt_index, source_prompt in enumerate(prompt_list):
        briefs = generate_ai_scenario_briefs(
            source_prompt,
            count=count,
            provider=provider,
            seed=seed + prompt_index,
            starting_index=next_index,
        )
        next_index += len(briefs)
        generated.extend(briefs)
        for brief in briefs:
            db = append_brief(db, brief)
    db = replace_db(
        db,
        claim_boundaries=_with_replaced_boundary(
            db.claim_boundaries,
            prefix="scenario_generation_ai_provider=",
            replacement=f"scenario_generation_ai_provider={provider}",
        ),
    )
    db = append_command(
        db,
        command="oodrive ai-generate",
        status="passed",
        artifacts={"db_path": str(db_path)},
        summary={
            "provider": provider,
            "source_prompt_count": len(prompt_list),
            "generated_count": len(generated),
        },
    )
    artifacts = artifact_paths(write_studio_db(db_path, db))
    next_commands = [oodrive_command(f"compile --db {db_path} --count {max(1, len(generated))} --severity {severity} --seed {seed}")]
    compiled = False
    queued = False
    candidate_count = len(db.candidates)
    queue_count = len(db.queue)

    if compile_candidates:
        compile_result = run_studio_compile(
            db_path,
            count=max(1, len(generated)),
            severity=severity,
            seed=seed,
        )
        artifacts = {**artifacts, **compile_result.artifacts}
        candidate_count = int(compile_result.summary.get("candidate_count", 0))
        compiled = True
        next_commands = [oodrive_command(f"queue --db {db_path} --accept {accept}")]

    if queue_candidates:
        queue_result = run_studio_queue(db_path, accept=accept)
        artifacts = {**artifacts, **queue_result.artifacts}
        queue_count = int(queue_result.summary.get("queue_count", 0))
        queued = True
        next_commands = queue_result.next_commands

    db = load_studio_db(db_path)
    return StudioCommandResult(
        command="oodrive ai-generate",
        run_id=db.run_id,
        status="passed",
        artifacts=artifacts,
        next_commands=next_commands,
        summary={
            "provider": provider,
            "source_prompt_count": len(prompt_list),
            "generated_count": len(generated),
            "compiled": compiled,
            "queued": queued,
            "candidate_count": candidate_count,
            "queue_count": queue_count,
            "generated_brief_ids": [str(brief.get("brief_id")) for brief in generated],
        },
        claim_boundaries=sorted(
            set(
                [
                    *db.claim_boundaries,
                    f"ai_generation_provider={provider}",
                    "network_llm_call=false",
                    "scenario_generation_ai_assisted=true",
                    "closed_loop_carla_execution=false_until_run_manifest_proves_it",
                ]
            )
        ),
    )


def run_studio_compile(
    db_path: Path,
    *,
    count: int = 6,
    severity: int = 3,
    seed: int = 7,
    seeds_path: Path = Path("tests/fixtures/fail2drive_like/seeds.json"),
    catalog_path: Path | None = None,
) -> StudioCommandResult:
    db = load_studio_db(db_path)
    prompts = [str(brief.get("prompt", "")).strip() for brief in db.briefs if str(brief.get("prompt", "")).strip()]
    if not prompts:
        raise ValueError("Studio DB has no briefs. Run oodrive ingest-brief first.")
    count_per_prompt = max(1, math.ceil(max(1, count) / len(prompts)))
    batch = generate_studio_batch(
        ScenarioStudioConfig(
            prompts=tuple(prompts),
            seeds_path=seeds_path,
            catalog_path=catalog_path,
            output_root=db_path.parent,
            run_id="compile",
            count_per_prompt=count_per_prompt,
            severity=max(1, min(5, severity)),
            random_seed=seed,
        )
    )
    limited_candidates = list(batch.get("candidates", []))[: max(1, count)]
    limited_ids = {str(candidate.get("candidate_id", "")) for candidate in limited_candidates}
    limited_curation = [
        row
        for row in list(batch.get("curation", []))
        if str(row.get("candidate_id", "")) in limited_ids
    ]
    plan_ids = {str(candidate.get("plan_id", "")) for candidate in limited_candidates}
    limited_plans = [
        row
        for row in list(batch.get("plans", []))
        if str(row.get("plan_id", "")) in plan_ids
    ] or list(batch.get("plans", []))
    db = replace_db(
        db,
        plans=limited_plans,
        candidates=limited_candidates,
        curation=limited_curation,
        artifacts={
            **db.artifacts,
            "scenario_studio_batch": str(batch.get("json_path", "")),
            "scenario_studio_gallery": str(batch.get("gallery_path", "")),
            "scenario_studio_recipes": str(batch.get("recipes_path", "")),
        },
    )
    db = append_command(
        db,
        command="oodrive compile",
        status="passed",
        artifacts={
            "db_path": str(db_path),
            "scenario_studio_batch": str(batch.get("json_path", "")),
            "scenario_studio_gallery": str(batch.get("gallery_path", "")),
            "scenario_studio_recipes": str(batch.get("recipes_path", "")),
        },
        summary={
            "prompt_count": len(prompts),
            "candidate_count": len(limited_candidates),
            "accepted_candidate_ids": [
                str(row.get("candidate_id", ""))
                for row in limited_curation
                if str(row.get("curation_status", row.get("status", ""))) in {"accept", "accept_partial"}
            ],
        },
    )
    artifacts = artifact_paths(write_studio_db(db_path, db))
    return StudioCommandResult(
        command="oodrive compile",
        run_id=db.run_id,
        status="passed",
        artifacts={**artifacts, "scenario_studio_batch": str(batch.get("json_path", ""))},
        next_commands=[oodrive_command(f"queue --db {db_path} --accept top:3")],
        summary={
            "prompt_count": len(prompts),
            "candidate_count": len(limited_candidates),
            "curation_count": len(limited_curation),
        },
        claim_boundaries=db.claim_boundaries,
    )


def run_studio_queue(
    db_path: Path,
    *,
    accept: str = "top:3",
    policy_targets: Iterable[str] = ("mock", "carla-autopilot", "alpamayo-trajectory"),
) -> StudioCommandResult:
    db = load_studio_db(db_path)
    queue = build_scenario_dataset_queue(
        db,
        db_path=db_path,
        options=QueueBuildOptions(accept=accept, policy_targets=tuple(policy_targets)),
    )
    queue_payload = write_scenario_dataset_queue(db_path.parent, queue)
    queue_artifacts = artifact_paths(queue_payload)
    db = replace_db(
        db,
        queue=list(queue.records),
        artifacts={**db.artifacts, **queue_artifacts},
    )
    db = append_command(
        db,
        command="oodrive queue",
        status="passed",
        artifacts=queue_artifacts,
        summary={"queue_count": len(queue.records), "accept": accept},
    )
    artifacts = artifact_paths(write_studio_db(db_path, db))
    return StudioCommandResult(
        command="oodrive queue",
        run_id=db.run_id,
        status="passed",
        artifacts={**artifacts, **queue_artifacts},
        next_commands=queue_next_commands(db_path, list(queue.records)),
        summary={"queue_count": len(queue.records), "records": list(queue.records)},
        claim_boundaries=db.claim_boundaries,
    )


def run_studio_run(
    db_path: Path,
    *,
    scenario_id: str | None = None,
    policy: str = "mock",
    config_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
) -> StudioCommandResult:
    db = load_studio_db(db_path)
    record = select_queue_record(db, scenario_id)
    scenario_id = str(record.get("scenario_id", scenario_id or "unknown-scenario"))
    candidate_id = str(record.get("candidate_id", scenario_id))
    run_id = run_id or f"{scenario_id}-{policy}-{timestamp_run_id('run')}"
    run_dir = (output_root or (db_path.parent / "runs")) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    status = "complete"
    runtime = "local"
    artifacts: dict[str, str | None] = {}
    actions = mock_actions_for_record(record) if policy == "mock" else []
    timings = {"load_ms": 1.0, "policy_ms": 2.0, "write_ms": 1.0}
    claim_boundaries = [
        f"product_name={OODRIVE_PRODUCT_NAME}",
        "closed_loop_carla_execution=false",
        "real_time_vla_control=false",
        "mock_policy=true" if policy == "mock" else "mock_policy=false",
    ]
    if policy == "carla-autopilot":
        runtime = "carla-smoke"
        claim_boundaries = [
            f"product_name={OODRIVE_PRODUCT_NAME}",
            "closed_loop_carla_execution=false_until_video_tracks_manifest_exists",
            "real_time_vla_control=false",
            "carla_autopilot_requested=true",
        ]
        if config_path is None:
            status = "blocked"
            blockers.append("No CARLA config supplied. Pass --config configs/carla_local.sample.yaml or a live host config.")
        else:
            from driverx.simulators.carla import load_carla_run_config, smoke_carla_server

            try:
                cfg = load_carla_run_config(config_path)
                smoke = smoke_carla_server(cfg.host, cfg.port, cfg.timeout_s)
                artifacts["carla_config"] = str(config_path)
                artifacts["carla_smoke"] = json.dumps(smoke.to_jsonable(), sort_keys=True)
                if smoke.reachable:
                    status = "partial"
                    blockers.append(
                        "CARLA TCP port is reachable; OODrive CLI V1 records a manifest but does not yet invoke full route execution."
                    )
                    claim_boundaries[1] = "closed_loop_carla_execution=partial_smoke_only"
                else:
                    status = "blocked"
                    blockers.append(f"CARLA TCP smoke failed at {cfg.host}:{cfg.port}: {smoke.error}")
            except (FileNotFoundError, OSError, ValueError) as exc:
                status = "blocked"
                blockers.append(f"CARLA config/smoke failed: {exc}")
    elif policy == "alpamayo-trajectory":
        runtime = "offline-evaluation-required"
        status = "blocked"
        blockers.append("Use oodrive evaluate with an Alpamayo prediction JSON; run does not execute model inference.")
        claim_boundaries = [
            f"product_name={OODRIVE_PRODUCT_NAME}",
            "closed_loop_carla_execution=false",
            "alpamayo_open_loop_evaluation=false_until_prediction_attached",
            "real_time_vla_control=false",
        ]
    trace_path = run_dir / "action_trace.json"
    trace_path.write_text(json.dumps({"scenario_id": scenario_id, "policy": policy, "actions": actions}, indent=2), encoding="utf-8")
    artifacts["action_trace"] = str(trace_path)
    manifest = ScenarioRunManifest(
        run_id=run_id,
        scenario_id=scenario_id,
        candidate_id=candidate_id,
        policy=policy,
        runtime=runtime,
        status=status,
        artifacts=artifacts,
        timings_ms=timings,
        actions=actions,
        claim_boundaries=claim_boundaries,
        blockers=blockers,
    )
    manifest_payload = write_run_manifest(run_dir, manifest)
    manifest_artifacts = artifact_paths(manifest_payload)
    db = update_queue_record(db, candidate_id, "complete" if status == "complete" else status)
    db = append_run(db, {**manifest.to_jsonable(), **manifest_artifacts})
    db = append_command(
        db,
        command="oodrive run",
        status=status if status != "complete" else "passed",
        artifacts=manifest_artifacts,
        summary={"scenario_id": scenario_id, "policy": policy, "status": status},
    )
    db_artifacts = artifact_paths(write_studio_db(db_path, db))
    return StudioCommandResult(
        command="oodrive run",
        run_id=db.run_id,
        status=status if status != "complete" else "passed",
        artifacts={**db_artifacts, **manifest_artifacts},
        next_commands=[
            oodrive_command(
                f"evaluate --db {db_path} --run {manifest_artifacts['json_path']} --policy alpamayo-trajectory"
            )
        ],
        summary=manifest.to_jsonable(),
        claim_boundaries=claim_boundaries,
        blockers=blockers,
    )


def run_studio_evaluate(
    db_path: Path,
    *,
    run_manifest_path: Path | None = None,
    policy: str = "alpamayo-trajectory",
    memory: str = "auto",
    prediction_json: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
) -> StudioCommandResult:
    db = load_studio_db(db_path)
    run_payload = load_or_latest_run(db, run_manifest_path)
    scenario_id = str(run_payload.get("scenario_id", "unknown-scenario"))
    run_id = run_id or f"{scenario_id}-{policy}-eval"
    run_dir = (output_root or (db_path.parent / "evaluations")) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    prediction = load_prediction(prediction_json, blockers)
    candidate = candidate_for_run(db, run_payload)
    memory_ids = memory_ids_for_candidate(candidate) if memory == "auto" else []
    cot = cot_from_prediction(prediction)
    latency = latency_from_prediction(prediction)
    trajectory_summary = trajectory_summary_from_prediction(prediction)
    if prediction_json is None:
        blockers.append("No Alpamayo prediction JSON supplied; recorded evaluation as blocked/cached-missing.")
    record = PolicyEvaluationRecord(
        evaluation_id=run_id,
        scenario_id=scenario_id,
        policy=policy,
        reasoning_mode="cached_open_loop" if prediction else "blocked_missing_prediction",
        memory_mode="retrieved" if memory_ids else "none",
        cot_summary=cot,
        trajectory_summary=trajectory_summary,
        control_trace_path=None,
        latency_ms=latency,
        memory_ids=memory_ids,
        claim_boundaries=[
            f"product_name={OODRIVE_PRODUCT_NAME}",
            "sampled_open_loop_reasoning=true" if prediction else "sampled_open_loop_reasoning=false",
            "closed_loop_carla_execution=false",
            "real_time_vla_control=false",
            "memory_augmented_prompt_context=true" if memory_ids else "memory_augmented_prompt_context=false",
        ],
        blockers=blockers,
    )
    evaluation_payload = write_policy_evaluation(run_dir, record)
    evaluation_artifacts = artifact_paths(evaluation_payload)
    db = append_evaluation(db, {**record.to_jsonable(), **evaluation_artifacts})
    db = append_command(
        db,
        command="oodrive evaluate",
        status="blocked" if blockers and not prediction else "passed",
        artifacts=evaluation_artifacts,
        summary={"scenario_id": scenario_id, "policy": policy, "memory_ids": memory_ids},
    )
    db_artifacts = artifact_paths(write_studio_db(db_path, db))
    return StudioCommandResult(
        command="oodrive evaluate",
        run_id=db.run_id,
        status="blocked" if blockers and not prediction else "passed",
        artifacts={**db_artifacts, **evaluation_artifacts},
        next_commands=[
            oodrive_command(f"replay --db {db_path} --evaluation {evaluation_artifacts['json_path']}")
        ],
        summary=record.to_jsonable(),
        claim_boundaries=record.claim_boundaries,
        blockers=blockers,
    )


def run_studio_replay(
    db_path: Path,
    *,
    run_manifest_path: Path | None = None,
    evaluation_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
) -> StudioCommandResult:
    db = load_studio_db(db_path)
    run_payload = load_or_latest_run(db, run_manifest_path)
    eval_payload = load_or_latest_evaluation(db, evaluation_path)
    scenario_id = str(run_payload.get("scenario_id", eval_payload.get("scenario_id", "scenario")))
    bundle_id = run_id or f"{scenario_id}-bundle"
    run_dir = (output_root or (db_path.parent / "bundles")) / bundle_id
    run_dir.mkdir(parents=True, exist_ok=True)
    candidate = candidate_for_run(db, run_payload)
    bundle = build_bundle_payload(db, run_payload, eval_payload, candidate, bundle_id)
    artifacts = write_bundle(run_dir, bundle)
    db = append_bundle(db, {**bundle, **artifacts})
    db = append_command(
        db,
        command="oodrive replay",
        status="passed",
        artifacts=artifacts,
        summary={"scenario_id": scenario_id, "bundle_id": bundle_id},
    )
    db_artifacts = artifact_paths(write_studio_db(db_path, db))
    return StudioCommandResult(
        command="oodrive replay",
        run_id=db.run_id,
        status="passed",
        artifacts={**db_artifacts, **artifacts},
        next_commands=[oodrive_command(f"export --db {db_path}")],
        summary=bundle,
        claim_boundaries=list(bundle["claim_boundaries"]),
    )


def run_studio_export(
    db_path: Path,
    *,
    output_root: Path | None = None,
    run_id: str | None = None,
) -> StudioCommandResult:
    db = load_studio_db(db_path)
    export_id = run_id or f"{db.run_id}-export"
    run_dir = (output_root or (db_path.parent / "exports")) / export_id
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = build_export_payload(db, db_path, export_id)
    artifacts = write_export_pack(run_dir, payload)
    db = append_export(db, {**payload, **artifacts})
    db = append_command(
        db,
        command="oodrive export",
        status="passed",
        artifacts=artifacts,
        summary={"scenario_count": payload["scenario_count"], "pack_id": export_id},
    )
    db_artifacts = artifact_paths(write_studio_db(db_path, db))
    return StudioCommandResult(
        command="oodrive export",
        run_id=db.run_id,
        status="passed",
        artifacts={**db_artifacts, **artifacts},
        next_commands=[],
        summary=payload,
        claim_boundaries=list(payload["claim_boundaries"]),
    )


def run_studio_quickstart(
    output_root: Path,
    run_id: str,
    *,
    prompts: Iterable[str],
    count: int = 3,
    severity: int = 3,
    seed: int = 7,
    policy: str = "mock",
    force: bool = True,
) -> StudioCommandResult:
    prompt_list = [prompt.strip() for prompt in prompts if prompt.strip()]
    if not prompt_list:
        raise ValueError("At least one --prompt is required for quickstart.")
    init = run_studio_init(output_root, run_id, force=force)
    db_path = Path(init.artifacts["db_path"])
    for prompt in prompt_list:
        run_studio_ingest_brief(db_path, prompt=prompt, author="codex")
    compile_result = run_studio_compile(db_path, count=count, severity=severity, seed=seed)
    queue_result = run_studio_queue(db_path, accept=f"top:{min(3, max(1, count))}")
    run_result = run_studio_run(db_path, policy=policy, run_id=f"{run_id}-{policy}-run")
    evaluate_result = run_studio_evaluate(db_path, run_manifest_path=Path(run_result.artifacts["json_path"]))
    replay_result = run_studio_replay(
        db_path,
        run_manifest_path=Path(run_result.artifacts["json_path"]),
        evaluation_path=Path(evaluate_result.artifacts["json_path"]),
    )
    export_result = run_studio_export(db_path)
    blockers = run_result.blockers + evaluate_result.blockers
    return StudioCommandResult(
        command="oodrive quickstart",
        run_id=run_id,
        status="partial" if blockers else ("passed" if run_result.status == "passed" else "partial"),
        artifacts={
            "db_path": str(db_path),
            "compile_batch": compile_result.artifacts.get("scenario_studio_batch", ""),
            "queue_path": queue_result.artifacts.get("json_path", ""),
            "run_manifest": run_result.artifacts.get("json_path", ""),
            "evaluation": evaluate_result.artifacts.get("json_path", ""),
            "bundle": replay_result.artifacts.get("json_path", ""),
            "export": export_result.artifacts.get("json_path", ""),
        },
        next_commands=[],
        summary={
            "brief_count": len(prompt_list),
            "candidate_count": compile_result.summary.get("candidate_count", 0),
            "queue_count": queue_result.summary.get("queue_count", 0),
            "run_status": run_result.status,
            "evaluation_status": evaluate_result.status,
            "export_pack_id": export_result.summary.get("pack_id"),
        },
        claim_boundaries=sorted(
            set(
                init.claim_boundaries
                + compile_result.claim_boundaries
                + run_result.claim_boundaries
                + evaluate_result.claim_boundaries
                + export_result.claim_boundaries
            )
        ),
        blockers=blockers,
    )


def _scenario_variant_templates(source_prompt: str) -> list[dict[str, str]]:
    lowered = source_prompt.lower()
    base_templates = [
        {
            "stressor": "sudden unsignaled lead-vehicle braking",
            "environment": "wet reflective road surface with glare",
            "actor": "motorcycle filtering through a narrowing lane",
            "failure": "late braking or unsafe lateral dodge",
        },
        {
            "stressor": "roadwork cones and loose debris narrowing the lane",
            "environment": "night-market roadside occlusion",
            "actor": "wrong-way scooter creeping on the shoulder",
            "failure": "over-commitment to the blocked lane",
        },
        {
            "stressor": "double-parked vehicle door opening into traffic",
            "environment": "dense mixed traffic with low lane discipline",
            "actor": "delivery rider cutting across the ego path",
            "failure": "failure to preserve a crawl-speed escape margin",
        },
        {
            "stressor": "bus or lorry occluding a pedestrian crossing",
            "environment": "rain-smeared camera view and headlight bloom",
            "actor": "pedestrian emerging from behind a roadside vendor",
            "failure": "insufficient yield before the occlusion clears",
        },
        {
            "stressor": "erratic merge without signal",
            "environment": "construction detour with temporary lane markings",
            "actor": "motorbike carrying oversized cargo wobbling near ego",
            "failure": "trajectory prediction ignores non-standard rider motion",
        },
    ]
    if "desert" in lowered or "dust" in lowered:
        base_templates.append(
            {
                "stressor": "dust plume hiding a stopped utility vehicle",
                "environment": "low-contrast desert construction detour",
                "actor": "work truck reversing across the route",
                "failure": "visibility-induced over-speeding",
            }
        )
    if "flood" in lowered or "water" in lowered:
        base_templates.append(
            {
                "stressor": "standing water hiding lane boundaries",
                "environment": "flooded urban underpass",
                "actor": "small motorcycle splashing through the shoulder",
                "failure": "misreading drivable surface and lane geometry",
            }
        )
    return base_templates


def _combine_prompt(source_prompt: str, variant: dict[str, str]) -> str:
    return (
        f"{source_prompt.strip()} | Stress test: {variant['stressor']}; "
        f"environment: {variant['environment']}; actor: {variant['actor']}; "
        f"expected failure: {variant['failure']}."
    )


def _infer_ai_region(prompt: str) -> str | None:
    lowered = prompt.lower()
    if any(word in lowered for word in ("malaysia", "malaysian", "kl", "kuala lumpur")):
        return "malaysia"
    if any(word in lowered for word in ("desert", "rural", "off-road")):
        return "rural"
    if any(word in lowered for word in ("construction", "roadwork", "detour")):
        return "construction_zone"
    return None


def _infer_ai_tags(prompt: str) -> list[str]:
    lowered = prompt.lower()
    keyword_tags = {
        "motorcycle_filtering": ("motorcycle", "motorbike", "scooter", "rider"),
        "unsignaled_brake": ("brake", "braking", "unsignaled", "without signal"),
        "roadwork_lane_narrowing": ("roadwork", "construction", "cone", "debris", "detour"),
        "wet_glare": ("wet", "rain", "reflective", "glare", "headlight"),
        "occlusion": ("occlusion", "occluding", "vendor", "blocked view", "behind"),
        "wrong_way_actor": ("wrong-way", "wrong way", "opposite direction"),
        "dense_mixed_traffic": ("dense", "mixed traffic", "night market", "double-parked"),
        "regional_context": ("malaysia", "malaysian", "kl", "kuala lumpur"),
        "low_lane_discipline": ("low lane discipline", "without signal", "cutting", "erratic"),
        "visual_noise": ("dust", "smear", "low-contrast", "headlight bloom"),
    }
    tags = [
        tag
        for tag, keywords in keyword_tags.items()
        if any(keyword in lowered for keyword in keywords)
    ]
    if not tags:
        tags.append("generated_ood_case")
    return sorted(set(tags))


def _infer_policy_pressure(tags: list[str]) -> str:
    if "occlusion" in tags and "unsignaled_brake" in tags:
        return "reason about hidden actors while preserving braking margin"
    if "motorcycle_filtering" in tags:
        return "maintain lateral clearance for non-lane-following vulnerable road users"
    if "roadwork_lane_narrowing" in tags:
        return "select a cautious path through temporary lane geometry"
    return "generalize from first principles under unfamiliar road context"


def _with_replaced_boundary(boundaries: list[str], *, prefix: str, replacement: str) -> list[str]:
    kept = [boundary for boundary in boundaries if not boundary.startswith(prefix)]
    return sorted(set([*kept, replacement]))


__all__ = [
    "StudioCommandResult",
    "generate_ai_scenario_briefs",
    "run_studio_ai_generate",
    "run_studio_compile",
    "run_studio_evaluate",
    "run_studio_export",
    "run_studio_ingest_brief",
    "run_studio_init",
    "run_studio_queue",
    "run_studio_quickstart",
    "run_studio_replay",
    "run_studio_run",
]
