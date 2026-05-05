"""Build the submission demo pack from generated OOD evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driverx.pipeline.submission_demo_pack_live import live_evidence, preferred_blocker


def build_submission_demo_pack(
    run_dir: Path,
    *,
    generated_suite_path: Path | None = None,
    policy_matrix_path: Path | None = None,
    alpamayo_probe_path: Path | None = None,
    route_evidence_path: Path | None = None,
    alpamayo_comparison_path: Path | None = None,
    cached_replay_path: Path | None = None,
    blockers_path: Path | None = None,
    progress_path: Path | None = None,
) -> dict[str, Any]:
    suite = _load_json(generated_suite_path)
    policy_matrix = _load_json(policy_matrix_path)
    alpamayo_probe = _load_json(alpamayo_probe_path)
    route_evidence = _load_json(route_evidence_path)
    alpamayo_comparison = _load_json(alpamayo_comparison_path)
    cached_replay = _load_json(cached_replay_path)
    blockers = _parse_open_blockers(_read_text(blockers_path))
    progress_tail = _latest_lines(_read_text(progress_path), limit=12)
    payload = {
        "title": "0xDriver Minimal-Shot OOD Driving Harness",
        "submission_angle": (
            "A randomized CARLA/Fail2Drive scenario forge plus retrieval-guided "
            "policy harness for testing frozen driving policies on weird but "
            "plausible long-tail situations without fine-tuning on those cases."
        ),
        "storyboard": _storyboard(
            suite,
            policy_matrix,
            alpamayo_probe,
            route_evidence,
            alpamayo_comparison,
            cached_replay,
            blockers,
        ),
        "failure_case": _failure_case(suite, route_evidence, blockers),
        "artifact_map": _artifact_map(
            suite,
            policy_matrix_path=policy_matrix_path,
            alpamayo_probe_path=alpamayo_probe_path,
            route_evidence_path=route_evidence_path,
            alpamayo_comparison_path=alpamayo_comparison_path,
            cached_replay_path=cached_replay_path,
            blockers_path=blockers_path,
        ),
        "model_declarations": _model_declarations(policy_matrix, alpamayo_probe, alpamayo_comparison),
        "data_declarations": _data_declarations(suite, route_evidence),
        "claim_boundaries": _claim_boundaries(alpamayo_comparison, cached_replay),
        "live_evidence": live_evidence(route_evidence, alpamayo_comparison, cached_replay),
        "writeup_draft": _writeup_draft(
            suite,
            policy_matrix,
            alpamayo_probe,
            route_evidence,
            alpamayo_comparison,
            cached_replay,
            blockers,
        ),
        "progress_tail": progress_tail,
        "inputs": {
            "generated_suite_path": _path_str(generated_suite_path),
            "policy_matrix_path": _path_str(policy_matrix_path),
            "alpamayo_probe_path": _path_str(alpamayo_probe_path),
            "route_evidence_path": _path_str(route_evidence_path),
            "alpamayo_comparison_path": _path_str(alpamayo_comparison_path),
            "cached_replay_path": _path_str(cached_replay_path),
            "blockers_path": _path_str(blockers_path),
            "progress_path": _path_str(progress_path),
        },
    }
    return write_submission_demo_pack(run_dir, payload)


def write_submission_demo_pack(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "submission_demo_pack.json"
    report_path = run_dir / "submission_demo_pack.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _storyboard(
    suite: dict[str, Any],
    policy_matrix: dict[str, Any],
    alpamayo_probe: dict[str, Any],
    route_evidence: dict[str, Any],
    alpamayo_comparison: dict[str, Any],
    cached_replay: dict[str, Any],
    blockers: list[str],
) -> list[dict[str, str]]:
    readiness = _mapping(suite.get("readiness"))
    ready_count = _mapping(policy_matrix).get("ready_count", "unknown")
    alpamayo_status = _mapping(alpamayo_probe).get("status", "not provided")
    route_video = _mapping(route_evidence.get("video"))
    trajectory_delta = _mapping(alpamayo_comparison.get("trajectory_delta"))
    replay_command_count = cached_replay.get("command_count", "unknown")
    replay_mode = cached_replay.get("closed_loop_control", "not provided")
    blocker_line = preferred_blocker(blockers)
    return [
        {
            "time": "0:00-0:20",
            "beat": "Problem",
            "visual": "Title over generated CARLA/Bench2Drive route and OOD tags.",
            "narration": "Minimal-shot autonomy should be judged on new long-tail scenes, not only memorized routes.",
        },
        {
            "time": "0:20-0:55",
            "beat": "Scenario Forge",
            "visual": "Show generated recipe ids, mutations, route pack, and overlay plan paths.",
            "narration": f"The harness generated {readiness.get('recipe_count', suite.get('num_recipes', 'unknown'))} scenario recipe(s) with deterministic mutations and reusable route artifacts.",
        },
        {
            "time": "0:55-1:30",
            "beat": "Policy Harness",
            "visual": "Show policy runtime matrix and mock/memory/hybrid readiness rows.",
            "narration": f"Local policies and Fail2Drive dry-run adapters are ready while heavier VLA rows remain setup-gated; ready rows: {ready_count}.",
        },
        {
            "time": "1:30-2:10",
            "beat": "Route Video Evidence",
            "visual": "Play the Town10 CARLA route video and show the route evidence report.",
            "narration": f"The local route proof produced video={route_video.get('exists', False)} while keeping missing route-score/entity-track limitations explicit.",
        },
        {
            "time": "2:10-2:45",
            "beat": "Alpamayo Memory Test",
            "visual": "Show Alpamayo no-memory vs memory CoC snippets and trajectory delta.",
            "narration": f"Alpamayo is now a live open-loop policy probe: status {alpamayo_status}, memory changed trajectory final L2 by {trajectory_delta.get('final_l2_m', 'unknown')}m, and cached replay produced {replay_command_count} bounded commands labeled {replay_mode}.",
        },
        {
            "time": "2:45-3:20",
            "beat": "Next Run",
            "visual": "Show blockers.md and the exact next live command.",
            "narration": blocker_line,
        },
    ]


def _failure_case(
    suite: dict[str, Any],
    route_evidence: dict[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    if route_evidence:
        metrics = _mapping(route_evidence.get("metrics"))
        if metrics.get("driving_score") is None or metrics.get("route_completion") is None:
            return {
                "scenario_id": route_evidence.get("route_id"),
                "route_path": _mapping(route_evidence.get("plan")).get("command"),
                "status": route_evidence.get("status"),
                "summary": "Live route video exists, but the bounded smoke run has no completed route score or route completion.",
                "why_it_matters": (
                    "This is the honest remaining gap between visible CARLA evidence and a full "
                    "closed-loop policy evaluation."
                ),
                "artifact": route_evidence.get("json_path") or "provided route evidence path",
                "blockers": list(route_evidence.get("blockers", []))
                if isinstance(route_evidence.get("blockers"), list)
                else [],
            }
    records = list(suite.get("recipe_records", [])) if isinstance(suite.get("recipe_records"), list) else []
    for record in records:
        if isinstance(record, dict) and record.get("blockers"):
            record_blockers = [str(item) for item in list(record.get("blockers", []))]
            return {
                "scenario_id": record.get("recipe_id"),
                "route_path": record.get("route_path"),
                "status": record.get("route_evidence_status"),
                "summary": record_blockers[0],
                "why_it_matters": (
                    "This is the current evidence bottleneck between generated OOD recipes "
                    "and judge-facing route video: the route command/video artifact must be "
                    "produced before claiming live behavior."
                ),
                "artifact": record.get("route_evidence_path"),
                "blockers": record_blockers,
            }
    return {
        "scenario_id": None,
        "route_path": None,
        "status": "blocked" if blockers else "unknown",
        "summary": blockers[0] if blockers else "No failure case was present in the provided artifacts.",
        "why_it_matters": "The submission must include at least one understood failure case.",
        "artifact": None,
        "blockers": blockers[:3],
    }


def _artifact_map(
    suite: dict[str, Any],
    *,
    policy_matrix_path: Path | None,
    alpamayo_probe_path: Path | None,
    route_evidence_path: Path | None,
    alpamayo_comparison_path: Path | None,
    cached_replay_path: Path | None,
    blockers_path: Path | None,
) -> dict[str, Any]:
    recipe_artifacts = []
    for record in list(suite.get("recipe_records", [])) if isinstance(suite.get("recipe_records"), list) else []:
        if isinstance(record, dict):
            recipe_artifacts.append(
                {
                    "recipe_id": record.get("recipe_id"),
                    "route_path": record.get("route_path"),
                    "video_smoke_plan_path": record.get("video_smoke_plan_path"),
                    "route_evidence_path": record.get("route_evidence_path"),
                }
            )
    return {
        "scenario_summary_path": suite.get("scenario_summary_path"),
        "route_pack_path": suite.get("route_pack_path"),
        "overlay_plan_path": suite.get("overlay_plan_path"),
        "overlay_evidence_path": suite.get("overlay_evidence_path"),
        "policy_matrix_path": _path_str(policy_matrix_path),
        "alpamayo_probe_path": _path_str(alpamayo_probe_path),
        "route_evidence_path": _path_str(route_evidence_path),
        "alpamayo_comparison_path": _path_str(alpamayo_comparison_path),
        "cached_replay_path": _path_str(cached_replay_path),
        "blockers_path": _path_str(blockers_path),
        "recipe_artifacts": recipe_artifacts,
    }


def _model_declarations(
    policy_matrix: dict[str, Any],
    alpamayo_probe: dict[str, Any],
    alpamayo_comparison: dict[str, Any],
) -> list[dict[str, Any]]:
    declarations: list[dict[str, Any]] = []
    rows = list(policy_matrix.get("rows", [])) if isinstance(policy_matrix.get("rows"), list) else []
    for row in rows:
        if isinstance(row, dict):
            declarations.append(
                {
                    "name": row.get("policy"),
                    "runtime_kind": row.get("runtime_kind"),
                    "state": row.get("ready_state"),
                    "base_model_or_policy": _base_policy_label(row),
                    "uses_public_model_pretraining": row.get("policy") in {"simlingo", "alpamayo"},
                    "blocker": row.get("blocker"),
                }
            )
    if alpamayo_probe:
        declarations.append(
            {
                "name": "alpamayo-probe",
                "runtime_kind": "offline_model_probe",
                "state": alpamayo_probe.get("status"),
                "base_model_or_policy": alpamayo_probe.get("model_id"),
                "uses_public_model_pretraining": True,
                "blocker": "; ".join(str(item) for item in list(alpamayo_probe.get("blockers", []))),
            }
        )
    if alpamayo_comparison:
        records = [
            record
            for record in list(alpamayo_comparison.get("records", []))
            if isinstance(record, dict)
        ]
        declarations.append(
            {
                "name": "alpamayo-live-ood-comparison",
                "runtime_kind": "open_loop_vla_policy_evaluation",
                "state": "live_memory_comparison_ready",
                "base_model_or_policy": "nvidia/Alpamayo-1.5-10B",
                "uses_public_model_pretraining": True,
                "blocker": None,
                "open_loop_policy_evaluation": alpamayo_comparison.get("open_loop_policy_evaluation"),
                "closed_loop_control": alpamayo_comparison.get("closed_loop_control"),
                "latency_ms": [record.get("latency_ms") for record in records],
                "vram_peak_mb": [record.get("vram_peak_mb") for record in records],
            }
        )
    return declarations


def _data_declarations(suite: dict[str, Any], route_evidence: dict[str, Any]) -> list[str]:
    declarations = [
        "Fail2Drive-style route/scenario seeds are used as scenario references; external checkout is not vendored.",
        "Generated OOD recipes, route packs, overlay plans, evidence reports, and blocker ledgers are small local artifacts.",
        "Waymo E2E remains a supporting open-loop track; no dataset shards are committed.",
        "Model weights, generated videos, CARLA installs, and credentials are excluded from git.",
    ]
    if suite.get("route_pack_path"):
        declarations.append(f"Current route pack evidence: {suite.get('route_pack_path')}")
    video = _mapping(route_evidence.get("video"))
    if video.get("exists"):
        declarations.append(
            f"Current local route video evidence: {video.get('path')} "
            f"({video.get('duration_s')}s, {video.get('size_bytes')} bytes)"
        )
    return declarations


def _claim_boundaries(
    alpamayo_comparison: dict[str, Any],
    cached_replay: dict[str, Any],
) -> list[str]:
    boundaries = [
        "Generated CARLA/Fail2Drive OOD scenarios and route artifacts are real repo outputs.",
        "Alpamayo comparisons are open-loop trajectory-intent evaluations unless a route controller consumes them.",
    ]
    if alpamayo_comparison:
        boundaries.append(
            f"Alpamayo comparison closed_loop_control={alpamayo_comparison.get('closed_loop_control')}."
        )
    if cached_replay:
        boundaries.append(
            "Cached replay converts a saved policy decision into bounded controls, "
            f"but dry_run={cached_replay.get('dry_run')} and it is not real-time VLA steering."
        )
    boundaries.append("Model weights, CARLA installs, videos, and credentials are not committed.")
    return boundaries


def _writeup_draft(
    suite: dict[str, Any],
    policy_matrix: dict[str, Any],
    alpamayo_probe: dict[str, Any],
    route_evidence: dict[str, Any],
    alpamayo_comparison: dict[str, Any],
    cached_replay: dict[str, Any],
    blockers: list[str],
) -> dict[str, str]:
    failure = _failure_case(suite, route_evidence, blockers)
    ready_rows = _mapping(policy_matrix).get("ready_count", "unknown")
    trajectory_delta = _mapping(alpamayo_comparison.get("trajectory_delta"))
    return {
        "motivation": (
            "Autonomy systems fail when they only work on distributions they have already seen. "
            "0xDriver treats minimal-shot driving as an evaluation and orchestration problem: "
            "generate plausible out-of-distribution pressure cases, run frozen policies through "
            "the same artifact contract, and preserve the failures as retrieval memory."
        ),
        "architecture": (
            "The current implementation builds deterministic scenario recipes, exports route-compatible "
            "CARLA/Bench2Drive artifacts, plans companion overlay actors, bundles route evidence, and "
            "tracks policy readiness. A retrieval layer can guide local policy decisions today, while "
            "SimLingo and Alpamayo remain swappable live-policy adapters."
        ),
        "what_worked": (
            f"The local harness is reproducible: generated suite status is `{suite.get('status')}`, "
            f"policy runtime ready rows are `{ready_rows}`, and the Alpamayo probe status is "
            f"`{alpamayo_probe.get('status', 'not provided')}`. The live Alpamayo memory comparison "
            f"changed trajectory final L2 by `{trajectory_delta.get('final_l2_m', 'unknown')}` metres "
            f"while staying explicitly open-loop. Cached replay produced "
            f"`{cached_replay.get('command_count', 'unknown')}` bounded control command(s) from a saved "
            "policy decision without claiming real-time VLA control."
        ),
        "what_did_not_work": (
            f"The current named failure is `{failure.get('summary')}`. This blocks a polished live route "
            "video but gives a precise next step instead of an ambiguous model-quality claim."
        ),
        "next_funding_step": (
            "Use the prize budget for a graphics-capable NVIDIA CARLA host, a confirmed reasoning-VLA "
            "checkpoint/runtime, and enough GPU hours to run generated OOD suites closed-loop with video, "
            "latency, infractions, and failure-memory comparisons."
        ),
    }


def _base_policy_label(row: dict[str, Any]) -> str:
    policy = str(row.get("policy", ""))
    if policy.startswith("fail2drive"):
        return "Fail2Drive stock CARLA policy/agent path"
    if policy == "simlingo":
        return "SimLingo / CARLA VLA checkpoint, setup-gated"
    if policy == "alpamayo":
        return "Alpamayo reasoning VLA, setup-gated"
    return "DriverX local deterministic or mock policy"


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _read_text(path: Path | None) -> str | None:
    if path is None:
        return None
    return path.expanduser().read_text(encoding="utf-8", errors="replace")


def _parse_open_blockers(text: str | None) -> list[str]:
    if text is None:
        return []
    lines = text.splitlines()
    in_open = False
    current: list[str] = []
    blockers: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.lower() == "## open":
            in_open = True
            continue
        if in_open and stripped.startswith("## "):
            break
        if not in_open:
            continue
        if stripped.startswith("- "):
            if current:
                blockers.append(" ".join(current).strip())
            current = [stripped[2:].strip()]
        elif current and (line.startswith("  ") or line.startswith("\t")):
            current.append(stripped)
    if current:
        blockers.append(" ".join(current).strip())
    return blockers


def _latest_lines(text: str | None, *, limit: int) -> list[str]:
    if text is None:
        return []
    lines = text.splitlines()
    latest = _section_lines(lines, "Latest Evidence")
    if latest:
        return _first_complete_bullets(latest, max_bullets=6, max_lines=limit)
    return [line for line in lines if line.strip()][-limit:]


def _first_complete_bullets(lines: list[str], *, max_bullets: int, max_lines: int) -> list[str]:
    bullets: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("- "):
            if current:
                bullets.append(current)
            current = [line]
        elif current and (line.startswith("  ") or line.startswith("\t")):
            current.append(line)
    if current:
        bullets.append(current)
    output: list[str] = []
    for bullet in bullets[:max_bullets]:
        if len(output) + len(bullet) > max_lines:
            break
        output.extend(bullet)
    return output


def _section_lines(lines: list[str], heading: str) -> list[str]:
    target = f"## {heading}".lower()
    in_section = False
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.lower() == target:
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if in_section and stripped:
            output.append(line)
    return output


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _path_str(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['title']}",
        "",
        "## Submission Angle",
        "",
        str(payload["submission_angle"]),
        "",
        "## 1-5 Minute Demo Outline",
        "",
        "| time | beat | visual | narration |",
        "|---|---|---|---|",
    ]
    for beat in list(payload.get("storyboard", [])):
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(beat.get("time")),
                    _cell(beat.get("beat")),
                    _cell(beat.get("visual")),
                    _cell(beat.get("narration")),
                ]
            )
            + " |"
        )
    failure = _mapping(payload.get("failure_case"))
    lines.extend(
        [
            "",
            "## Understood Failure Case",
            "",
            f"- scenario_id: `{failure.get('scenario_id')}`",
            f"- status: `{failure.get('status')}`",
            f"- route_path: `{failure.get('route_path')}`",
            f"- summary: {failure.get('summary')}",
            f"- artifact: `{failure.get('artifact')}`",
            "",
            "## Artifact Map",
            "",
        ]
    )
    for key, value in _mapping(payload.get("artifact_map")).items():
        if key == "recipe_artifacts":
            continue
        lines.append(f"- `{key}`: `{value}`")
    recipe_artifacts = list(_mapping(payload.get("artifact_map")).get("recipe_artifacts", []))
    if recipe_artifacts:
        lines.extend(["", "### Recipe Artifacts", ""])
        for artifact in recipe_artifacts:
            if isinstance(artifact, dict):
                lines.append(f"- `{artifact.get('recipe_id')}` -> `{artifact.get('route_evidence_path')}`")
    live = _mapping(payload.get("live_evidence"))
    if live:
        route = _mapping(live.get("route"))
        comparison = _mapping(live.get("alpamayo_comparison"))
        replay = _mapping(live.get("cached_replay"))
        lines.extend(
            [
                "",
                "## Live Evidence",
                "",
                f"- route_status: `{route.get('status')}`",
                f"- route_video: `{_mapping(route.get('video')).get('path')}`",
                f"- alpamayo_open_loop: `{comparison.get('open_loop_policy_evaluation')}`",
                f"- trajectory_delta: `{comparison.get('trajectory_delta')}`",
                f"- cached_replay: `{replay}`",
            ]
        )
    lines.extend(["", "## Claim Boundaries", ""])
    lines.extend(f"- {item}" for item in list(payload.get("claim_boundaries", [])))
    lines.extend(["", "## Model Declarations", ""])
    for declaration in list(payload.get("model_declarations", [])):
        if isinstance(declaration, dict):
            lines.append(
                f"- `{declaration.get('name')}`: {declaration.get('base_model_or_policy')} "
                f"({declaration.get('state')})"
            )
    lines.extend(["", "## Data And Asset Declarations", ""])
    lines.extend(f"- {item}" for item in list(payload.get("data_declarations", [])))
    lines.extend(["", "## Short Write-Up Draft", ""])
    for key, value in _mapping(payload.get("writeup_draft")).items():
        lines.extend([f"### {key.replace('_', ' ').title()}", "", str(value), ""])
    return "\n".join(lines)


def _cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|")


__all__ = ["build_submission_demo_pack", "write_submission_demo_pack"]
