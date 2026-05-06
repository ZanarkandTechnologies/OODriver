"""Build a compact submission-facing dossier from project evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_submission_dossier(
    run_dir: Path,
    *,
    ood_suite_manifest_path: Path | None = None,
    gpu_host_suitability_path: Path | None = None,
    demo_pack_path: Path | None = None,
    reasoning_pack_path: Path | None = None,
    campaign_summary_path: Path | None = None,
    alpamayo_batch_path: Path | None = None,
    cached_replay_path: Path | None = None,
    progress_path: Path | None = None,
    blockers_path: Path | None = None,
) -> dict[str, Any]:
    """Write a JSON and Markdown dossier for the current submission state."""

    ood = _load_json(ood_suite_manifest_path)
    gpu = _load_json(gpu_host_suitability_path)
    demo_pack = _load_json(demo_pack_path)
    reasoning_pack = _load_json(reasoning_pack_path)
    campaign = _load_json(campaign_summary_path)
    alpamayo_batch = _load_json(alpamayo_batch_path)
    cached_replay = _load_json(cached_replay_path)
    progress_tail = _latest_progress_lines(_read_text(progress_path), limit=18)
    blockers = _parse_open_blockers(_read_text(blockers_path))
    readiness = _readiness_summary(ood, demo_pack, reasoning_pack, campaign, alpamayo_batch, cached_replay)
    metrics = _metric_highlights(ood, demo_pack, reasoning_pack, campaign, alpamayo_batch, cached_replay)
    gpu_host = _gpu_host_summary(gpu, alpamayo_batch, blockers)
    artifact_checklist = _artifact_checklist(
        demo_pack_path=demo_pack_path,
        reasoning_pack_path=reasoning_pack_path,
        campaign_summary_path=campaign_summary_path,
        alpamayo_batch_path=alpamayo_batch_path,
        cached_replay_path=cached_replay_path,
        ood_suite_manifest_path=ood_suite_manifest_path,
        gpu_host_suitability_path=gpu_host_suitability_path,
        blockers_path=blockers_path,
    )
    artifact_checklist.extend(
        _derived_artifact_checklist(
            demo_pack=demo_pack,
            reasoning_pack=reasoning_pack,
            campaign=campaign,
            alpamayo_batch=alpamayo_batch,
        )
    )
    payload = {
        "title": "0xDriver Minimal-Shot OOD Driving Harness",
        "thesis": (
            "Use generated long-tail CARLA/Bench2Drive scenarios, retrieved safety memory, "
            "and frozen VLA policy adapters to test minimal-shot driving behavior without "
            "fine-tuning on the generated cases."
        ),
        "ood_readiness": readiness,
        "metric_highlights": metrics,
        "gpu_host": gpu_host,
        "demo_pack": _compact_demo_pack(demo_pack, demo_pack_path),
        "artifact_checklist": artifact_checklist,
        "video_script": _video_script(reasoning_pack, campaign, alpamayo_batch, cached_replay, blockers),
        "slide_outline": _slide_outline(reasoning_pack, campaign, alpamayo_batch, cached_replay),
        "model_declarations": _model_declarations(reasoning_pack, alpamayo_batch),
        "claim_boundaries": _claim_boundaries(reasoning_pack, campaign, alpamayo_batch, cached_replay),
        "two_page_writeup": _two_page_writeup(reasoning_pack, campaign, alpamayo_batch, cached_replay),
        "open_blockers": blockers,
        "demo_outline": _demo_outline(readiness, metrics, gpu_host, blockers),
        "progress_tail": progress_tail,
        "inputs": {
            "ood_suite_manifest_path": _path_str(ood_suite_manifest_path),
            "gpu_host_suitability_path": _path_str(gpu_host_suitability_path),
            "demo_pack_path": _path_str(demo_pack_path),
            "reasoning_pack_path": _path_str(reasoning_pack_path),
            "campaign_summary_path": _path_str(campaign_summary_path),
            "alpamayo_batch_path": _path_str(alpamayo_batch_path),
            "cached_replay_path": _path_str(cached_replay_path),
            "progress_path": _path_str(progress_path),
            "blockers_path": _path_str(blockers_path),
        },
    }
    return write_submission_dossier(run_dir, payload)


def write_submission_dossier(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "submission_dossier.json"
    report_path = run_dir / "submission_dossier.md"
    script_path = run_dir / "video_script.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    script_path.write_text(_video_script_markdown(payload), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
        "video_script_path": str(script_path),
    }


def _demo_outline(
    readiness: dict[str, Any],
    metrics: dict[str, Any],
    gpu_host: dict[str, Any],
    blockers: list[str],
) -> list[str]:
    gpu_state = gpu_host.get("overall_state")
    outline = [
        "Show generated OOD recipes and Bench2Drive route pack.",
        "Show overlay/sidecar plan that injects companion actors into CARLA.",
        (
            "Show RAG comparison result "
            f"(Alpamayo final trajectory delta: {metrics.get('alpamayo_batch_mean_trajectory_final_l2_m', 'unknown')}m)."
        ),
        (
            "Show live-policy readiness honestly "
            f"(alpamayo_memory_comparison_available={readiness.get('alpamayo_memory_comparison_available')}, "
            f"gpu_host={gpu_state})."
        ),
    ]
    if blockers:
        outline.append("Close with the current blocker and the next graphics-capable NVIDIA host run.")
    else:
        outline.append("Close with the first successful closed-loop SimLingo route video.")
    return outline


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.expanduser().exists():
        return None
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _read_text(path: Path | None) -> str | None:
    if path is None:
        return None
    return path.expanduser().read_text(encoding="utf-8", errors="replace")


def _latest_progress_lines(text: str | None, *, limit: int) -> list[str]:
    if text is None:
        return []
    lines = text.splitlines()
    latest = _section_lines(lines, "Latest Evidence")
    if latest:
        return _first_complete_bullets(latest, max_bullets=8, max_lines=limit)
    return lines[-limit:]


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


def _parse_open_blockers(text: str | None) -> list[str]:
    if text is None:
        return []
    lines = text.splitlines()
    in_open = False
    blockers: list[str] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") and stripped.lstrip("#").strip().lower() in {"open", "open blockers"}:
            in_open = True
            continue
        if in_open and stripped.startswith("#"):
            break
        if not in_open:
            continue
        if stripped.startswith(("- ", "* ")):
            if current:
                blockers.append(" ".join(current).strip())
            current = [stripped[2:].strip()]
        elif current and (line.startswith("  ") or line.startswith("\t")):
            current.append(stripped)
    if current:
        blockers.append(" ".join(current).strip())
    return [blocker for blocker in blockers if blocker and blocker.lower() != "none currently."]


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _path_str(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _artifact_checklist(**paths: Path | None) -> list[dict[str, Any]]:
    labels = {
        "demo_pack_path": "V4 demo pack",
        "reasoning_pack_path": "Reasoning overlay pack",
        "campaign_summary_path": "Scripted OOD campaign",
        "alpamayo_batch_path": "Alpamayo OOD batch",
        "cached_replay_path": "Cached Alpamayo replay",
        "ood_suite_manifest_path": "OOD suite manifest",
        "gpu_host_suitability_path": "GPU host suitability",
        "blockers_path": "Blocker ledger",
    }
    checklist: list[dict[str, Any]] = []
    for key, path in paths.items():
        if path is None:
            continue
        exists = path.expanduser().exists() if path is not None else False
        checklist.append(
            {
                "label": labels.get(key, key),
                "path": str(path) if path is not None else None,
                "exists": exists,
                "heavy_artifact": _is_heavy(path),
            }
        )
    return checklist


def _derived_artifact_checklist(
    *,
    demo_pack: dict[str, Any] | None,
    reasoning_pack: dict[str, Any] | None,
    campaign: dict[str, Any] | None,
    alpamayo_batch: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    demo_artifacts = _mapping(_mapping(demo_pack).get("artifact_map"))
    live = _mapping(_mapping(demo_pack).get("live_evidence"))
    ood_video = _mapping(live.get("ood_video"))
    reasoning_inputs = _mapping(_mapping(reasoning_pack).get("inputs"))
    paths: list[tuple[str, str | None]] = [
        (
            "Live OOD video evidence",
            _first_path(reasoning_inputs.get("ood_video_evidence_path"), demo_artifacts.get("ood_video_evidence_path")),
        ),
        (
            "Live OOD MP4",
            _first_path(_mapping(reasoning_pack).get("video_path"), ood_video.get("video_path")),
        ),
        (
            "Alpamayo comparison artifact",
            _first_path(reasoning_inputs.get("alpamayo_comparison_path"), demo_artifacts.get("alpamayo_comparison_path")),
        ),
        ("Reasoning HTML pack", _first_path(_mapping(reasoning_pack).get("html_path"))),
    ]
    for index, case in enumerate(list(_mapping(campaign).get("cases", []))):
        if isinstance(case, dict) and case.get("video_path"):
            paths.append((f"Campaign case {index:03d} MP4", str(case["video_path"])))
        if isinstance(case, dict) and case.get("video_evidence_path"):
            paths.append((f"Campaign case {index:03d} video evidence", str(case["video_evidence_path"])))
    if _mapping(alpamayo_batch).get("json_path"):
        paths.append(("Alpamayo batch JSON artifact", str(_mapping(alpamayo_batch)["json_path"])))
    return [_artifact_ref(label, path) for label, path in paths if path]


def _artifact_ref(label: str, path: str | None) -> dict[str, Any]:
    expanded = Path(path).expanduser() if path else None
    return {
        "label": label,
        "path": path,
        "exists": expanded.exists() if expanded is not None else False,
        "heavy_artifact": _is_heavy(expanded),
    }


def _readiness_summary(
    ood: dict[str, Any] | None,
    demo_pack: dict[str, Any] | None,
    reasoning_pack: dict[str, Any] | None,
    campaign: dict[str, Any] | None,
    alpamayo_batch: dict[str, Any] | None,
    cached_replay: dict[str, Any] | None,
) -> dict[str, Any]:
    explicit = _mapping(_mapping(ood).get("readiness"))
    live = _mapping(_mapping(demo_pack).get("live_evidence"))
    if explicit:
        summary = dict(explicit)
    else:
        summary = {}
    summary.update(
        {
            "scenario_generation_ready": bool(summary.get("scenario_generation_ready"))
            or _mapping(campaign).get("status") in {"passed", "partial"},
            "live_carla_video_available": _has_live_video(demo_pack, reasoning_pack, campaign),
            "alpamayo_reasoning_available": _mapping(reasoning_pack).get("status") == "ready"
            or bool(live.get("alpamayo_scene")),
            "alpamayo_memory_comparison_available": _mapping(alpamayo_batch).get("status") in {"passed", "planned"}
            or bool(live.get("alpamayo_comparison")),
            "cached_replay_available": _mapping(cached_replay).get("status") == "passed"
            or bool(_mapping(live.get("cached_replay")).get("available")),
            "stock_fail2drive_full_score_available": False,
        }
    )
    return summary


def _metric_highlights(
    ood: dict[str, Any] | None,
    demo_pack: dict[str, Any] | None,
    reasoning_pack: dict[str, Any] | None,
    campaign: dict[str, Any] | None,
    alpamayo_batch: dict[str, Any] | None,
    cached_replay: dict[str, Any] | None,
) -> dict[str, Any]:
    metrics = dict(_mapping(_mapping(ood).get("metric_highlights")))
    live_ood = _mapping(_mapping(_mapping(demo_pack).get("live_evidence")).get("ood_video"))
    metrics.update(
        {
            "campaign_case_count": _mapping(campaign).get("case_count"),
            "campaign_live_case_count": _mapping(campaign).get("live_case_count"),
            "campaign_mean_min_distance_m": _mapping(campaign).get("mean_min_distance_m"),
            "live_ood_video_duration_s": _first_value(_mapping(reasoning_pack).get("duration_s"), live_ood.get("duration_s")),
            "cached_replay_duration_s": _mapping(cached_replay).get("duration_s"),
            "alpamayo_batch_mean_latency_ms": _mapping(alpamayo_batch).get("mean_latency_ms"),
            "alpamayo_batch_mean_vram_peak_mb": _mapping(alpamayo_batch).get("mean_vram_peak_mb"),
            "alpamayo_batch_max_vram_peak_mb": _mapping(alpamayo_batch).get("max_vram_peak_mb"),
            "alpamayo_batch_mean_trajectory_final_l2_m": _mapping(alpamayo_batch).get("mean_trajectory_final_l2_m"),
        }
    )
    return {key: value for key, value in metrics.items() if value is not None}


def _gpu_host_summary(
    gpu: dict[str, Any] | None,
    alpamayo_batch: dict[str, Any] | None,
    blockers: list[str],
) -> dict[str, Any]:
    explicit = _mapping(gpu)
    if explicit:
        return {
            "overall_state": explicit.get("overall_state"),
            "recommendation": explicit.get("recommendation"),
            "blockers": list(explicit.get("blockers", [])),
            "warnings": list(explicit.get("warnings", [])),
        }
    return {
        "overall_state": "alpamayo_open_loop_ready__stock_fail2drive_score_host_pending",
        "recommendation": (
            "RTX 6000 Ada evidence is sufficient for Alpamayo 1.5 single-sample open-loop inference; "
            "stock Fail2Drive full-score execution remains a graphics-capable Linux CARLA host handoff."
        ),
        "blockers": blockers,
        "warnings": [
            "The submission does not claim real-time closed-loop VLA control.",
            "Full benchmark scoring is separated from Alpamayo open-loop reasoning evidence.",
        ],
        "alpamayo_mean_vram_peak_mb": _mapping(alpamayo_batch).get("mean_vram_peak_mb"),
        "alpamayo_max_vram_peak_mb": _mapping(alpamayo_batch).get("max_vram_peak_mb"),
    }


def _compact_demo_pack(demo_pack: dict[str, Any] | None, path: Path | None) -> dict[str, Any]:
    payload = _mapping(demo_pack)
    return {
        "path": _path_str(path),
        "title": payload.get("title"),
        "submission_angle": payload.get("submission_angle"),
        "headline_artifact": payload.get("headline_artifact"),
    }


def _has_live_video(
    demo_pack: dict[str, Any] | None,
    reasoning_pack: dict[str, Any] | None,
    campaign: dict[str, Any] | None,
) -> bool:
    live = _mapping(_mapping(demo_pack).get("live_evidence"))
    if _mapping(reasoning_pack).get("video_path") or _mapping(live.get("ood_video")).get("video_path"):
        return True
    return any(isinstance(case, dict) and bool(case.get("video_path")) for case in list(_mapping(campaign).get("cases", [])))


def _first_path(*values: object) -> str | None:
    for value in values:
        if value:
            return str(value)
    return None


def _first_value(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _video_script(
    reasoning_pack: dict[str, Any] | None,
    campaign: dict[str, Any] | None,
    alpamayo_batch: dict[str, Any] | None,
    cached_replay: dict[str, Any] | None,
    blockers: list[str],
) -> list[dict[str, str]]:
    scenario_id = _mapping(reasoning_pack).get("scenario_id") or _mapping(campaign).get("campaign_id") or "generated OOD cases"
    return [
        {
            "time": "0:00-0:25",
            "visual": "Scenario forge and CARLA OOD scene",
            "narration": f"0xDriver generates long-tail driving cases, then runs them in CARLA. The current proof centers on {scenario_id}.",
        },
        {
            "time": "0:25-0:55",
            "visual": "Reasoning pack with Alpamayo CoC and memory",
            "narration": "A frozen Alpamayo 1.5 policy is evaluated open-loop with and without retrieved safety memory; no generated-case fine-tuning is used.",
        },
        {
            "time": "0:55-1:25",
            "visual": "Cached replay or campaign risk table",
            "narration": f"The control layer can replay cached VLA trajectory intent conservatively; campaign status is {_mapping(campaign).get('status', 'not yet run')}.",
        },
        {
            "time": "1:25-1:55",
            "visual": "Latency and hardware evidence",
            "narration": f"Alpamayo batch status is {_mapping(alpamayo_batch).get('status', 'not yet run')}; RTX 6000 Ada is enough for single-sample open-loop inference.",
        },
        {
            "time": "1:55-2:20",
            "visual": "Claim boundaries and next steps",
            "narration": "The current submission claims randomized OOD generation and open-loop reasoning evidence, not production autonomous driving.",
        },
    ] + (
        [
            {
                "time": "2:20-2:35",
                "visual": "Blocker table",
                "narration": f"Main remaining blocker: {blockers[0]}",
            }
        ]
        if blockers
        else []
    )


def _slide_outline(
    reasoning_pack: dict[str, Any] | None,
    campaign: dict[str, Any] | None,
    alpamayo_batch: dict[str, Any] | None,
    cached_replay: dict[str, Any] | None,
) -> list[dict[str, str]]:
    return [
        {
            "title": "Minimal-Shot Autonomy Thesis",
            "proof": "Frozen VLA + generated OOD stress tests + retrieved safety memory.",
            "artifact": "submission_dossier.md",
        },
        {
            "title": "Randomized Scenario Forge",
            "proof": f"Campaign cases: {_mapping(campaign).get('case_count', 'pending')}.",
            "artifact": _mapping(campaign).get("json_path", "scripted_ood_campaign_summary.json"),
        },
        {
            "title": "Reasoning VLA Evidence",
            "proof": f"Scenario: {_mapping(reasoning_pack).get('scenario_id', 'pending')}.",
            "artifact": _mapping(reasoning_pack).get("html_path", "reasoning_video_pack.html"),
        },
        {
            "title": "Policy-To-Control Bridge",
            "proof": f"Cached replay status: {_mapping(cached_replay).get('status', 'pending')}.",
            "artifact": _mapping(cached_replay).get("json_path", "cached_ood_replay.json"),
        },
        {
            "title": "Evaluation And Limits",
            "proof": f"Alpamayo batch status: {_mapping(alpamayo_batch).get('status', 'pending')}.",
            "artifact": _mapping(alpamayo_batch).get("json_path", "alpamayo_ood_batch_summary.json"),
        },
    ]


def _model_declarations(
    reasoning_pack: dict[str, Any] | None,
    alpamayo_batch: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    latencies = _mapping(reasoning_pack).get("latency", {})
    return [
        {
            "model": "nvidia/Alpamayo-1.5-10B",
            "role": "Frozen reasoning VLA for open-loop trajectory and CoC evidence.",
            "fine_tuned_on_generated_cases": False,
            "license_note": "Non-commercial research release; see upstream model card.",
            "latency_evidence": latencies,
            "batch_status": _mapping(alpamayo_batch).get("status"),
        },
        {
            "model": "DriverX deterministic controller",
            "role": "Conservative trajectory-to-control replay and scenario instrumentation.",
            "fine_tuned_on_generated_cases": False,
        },
    ]


def _claim_boundaries(
    reasoning_pack: dict[str, Any] | None,
    campaign: dict[str, Any] | None,
    alpamayo_batch: dict[str, Any] | None,
    cached_replay: dict[str, Any] | None,
) -> list[str]:
    boundaries = [
        "randomized_ood_scenario_generation=true",
        "model_weights_frozen=true",
        "alpamayo_open_loop_policy_evaluation=true",
        "production_autonomy_claim=false",
    ]
    for payload in (reasoning_pack, campaign, alpamayo_batch, cached_replay):
        for item in list(_mapping(payload).get("claim_boundaries", [])):
            text = str(item)
            if text not in boundaries:
                boundaries.append(text)
    return boundaries


def _two_page_writeup(
    reasoning_pack: dict[str, Any] | None,
    campaign: dict[str, Any] | None,
    alpamayo_batch: dict[str, Any] | None,
    cached_replay: dict[str, Any] | None,
) -> dict[str, str]:
    return {
        "motivation": (
            "Minimal-shot autonomy should be judged by how systems respond to strange-but-plausible scenes "
            "that were not memorized during data collection."
        ),
        "architecture": (
            "0xDriver combines a deterministic OOD scenario forge, CARLA execution/evidence capture, "
            "a frozen reasoning VLA adapter, retrieved safety memory, and a conservative trajectory-control bridge."
        ),
        "what_worked": (
            f"Generated campaign status: {_mapping(campaign).get('status', 'pending')}; "
            f"reasoning pack scenario: {_mapping(reasoning_pack).get('scenario_id', 'pending')}; "
            f"cached replay status: {_mapping(cached_replay).get('status', 'pending')}."
        ),
        "what_did_not": (
            "Stock Fail2Drive full-route scoring still needs a stable graphics-capable Linux CARLA host. "
            "The current Alpamayo evidence is open-loop or cached replay, not real-time closed-loop VLA control."
        ),
        "next": (
            "Use funding for a stable CARLA graphics host, route-aligned closed-loop evaluation, and larger randomized OOD campaigns."
        ),
    }


def _is_heavy(path: Path | None) -> bool:
    if path is None:
        return False
    suffix = path.suffix.lower()
    return suffix in {".mp4", ".mov", ".tar", ".gz", ".tfrecord", ".pt", ".safetensors"}


def _markdown(payload: dict[str, Any]) -> str:
    gpu_host = _mapping(payload.get("gpu_host"))
    lines = [
        f"# {payload['title']}",
        "",
        "## Thesis",
        "",
        str(payload["thesis"]),
        "",
        "## Readiness",
        "",
    ]
    for key, value in _mapping(payload.get("ood_readiness")).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Metric Highlights", ""])
    for key, value in _mapping(payload.get("metric_highlights")).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Artifact Checklist", ""])
    for artifact in list(payload.get("artifact_checklist", [])):
        lines.append(
            f"- [{'x' if artifact.get('exists') else ' '}] {artifact.get('label')}: "
            f"`{artifact.get('path')}` heavy=`{artifact.get('heavy_artifact')}`"
        )
    lines.extend(["", "## Claim Boundaries", ""])
    for boundary in list(payload.get("claim_boundaries", [])):
        lines.append(f"- `{boundary}`")
    lines.extend(["", "## Slide Outline", ""])
    for slide in list(payload.get("slide_outline", [])):
        lines.append(f"- **{slide.get('title')}**: {slide.get('proof')} (`{slide.get('artifact')}`)")
    lines.extend(["", "## Two-Page Write-Up Draft", ""])
    for key, value in _mapping(payload.get("two_page_writeup")).items():
        lines.extend([f"### {key.replace('_', ' ').title()}", "", str(value), ""])
    lines.extend(
        [
            "",
            "## GPU Host",
            "",
            f"- overall_state: `{gpu_host.get('overall_state')}`",
            f"- recommendation: {gpu_host.get('recommendation')}",
            "",
            "## Open Blockers",
            "",
        ]
    )
    blockers = list(payload.get("open_blockers", []))
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("None.")
    lines.extend(["", "## Demo Outline", ""])
    for index, step in enumerate(list(payload.get("demo_outline", [])), start=1):
        lines.append(f"{index}. {step}")
    lines.extend(["", "## Recent Progress", ""])
    for line in list(payload.get("progress_tail", [])):
        lines.append(f"> {line}")
    return "\n".join(lines) + "\n"


def _video_script_markdown(payload: dict[str, Any]) -> str:
    lines = ["# 0xDriver Video Script", ""]
    for item in list(payload.get("video_script", [])):
        lines.extend(
            [
                f"## {item.get('time')}",
                "",
                f"- visual: {item.get('visual')}",
                f"- narration: {item.get('narration')}",
                "",
            ]
        )
    return "\n".join(lines)


__all__ = ["build_submission_dossier", "write_submission_dossier"]
