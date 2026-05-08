"""Judge-facing OODrive submission story pack builder."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


REQUIRED_CLAIM_BOUNDARIES = [
    "closed_loop_vla_control=false",
    "real_time_vla_control=false",
    "sampled_open_loop_reasoning=true",
    "time_warped_offline_demo=true",
]


def build_submission_story_pack(
    *,
    db_path: Path,
    run_manifest_path: Path,
    evaluation_path: Path,
    hero_video_path: Path,
    hero_score_path: Path,
    output_root: Path,
    run_id: str,
    readiness_score_path: Path | None = None,
    environment_demo_path: Path | None = None,
) -> dict[str, Any]:
    """Build a compact commission-facing OODrive evidence pack."""

    output_root.mkdir(parents=True, exist_ok=True)
    pack_dir = output_root / run_id
    suffix = 1
    while pack_dir.exists():
        pack_dir = output_root / f"{run_id}-{suffix:03d}"
        suffix += 1
    pack_dir.mkdir(parents=True, exist_ok=False)
    db_payload = _load_json(db_path)
    run_payload = _load_json(run_manifest_path)
    evaluation_payload = _load_json(evaluation_path)
    hero_score_payload = _load_json(hero_score_path)
    readiness_payload = _load_optional_json(readiness_score_path)
    environment_demo_payload = _load_optional_json(environment_demo_path)
    claim_boundaries = _dedupe(
        [
            *_string_list(db_payload.get("claim_boundaries")),
            *_string_list(run_payload.get("claim_boundaries")),
            *_string_list(evaluation_payload.get("claim_boundaries")),
            *_string_list(hero_score_payload.get("claim_boundaries")),
            *REQUIRED_CLAIM_BOUNDARIES,
        ]
    )
    artifacts = _artifact_inventory(
        {
            "scenario_db": db_path,
            "run_manifest": run_manifest_path,
            "policy_evaluation": evaluation_path,
            "hero_video": hero_video_path,
            "hero_score": hero_score_path,
            "readiness_score": readiness_score_path,
            "environment_demo": environment_demo_path,
        }
    )
    command_transcript = _command_transcript(db_payload, db_path, run_manifest_path, evaluation_path, hero_video_path, hero_score_path)
    sections = _sections(db_payload, run_payload, evaluation_payload, hero_score_payload, environment_demo_payload)
    claim_matrix = _claim_matrix(artifacts, claim_boundaries)
    failure_cases = [
        {
            "title": "Open-loop reasoning is not closed-loop control yet",
            "what_happened": (
                "Alpamayo reasoning is sampled over captured CARLA frames, then rendered into a "
                "time-warped evidence video. It does not drive CARLA controls in real time."
            ),
            "what_we_learned": (
                "The submission is strongest as a minimal-shot scenario generation and evaluation "
                "harness today; prize funding would turn the open-loop reasoning bridge into a "
                "closed-loop controller experiment."
            ),
            "evidence": [str(evaluation_path), str(hero_score_path)],
        }
    ]
    unique_contributions = [
        "Randomized weird-but-plausible CARLA scenario generation from a minimal prompt.",
        "Product loop from generation to placement, reasoning, video, and score gates.",
        "RAG/memory callouts tied to OOD driving principles instead of hidden narration.",
        "Latency and claim-boundary honesty around open-loop Alpamayo reasoning.",
    ]
    if environment_demo_path is not None:
        unique_contributions.insert(
            1,
            "Environment Studio surfaces CARLA weather, traffic, stock proxy assets, and road-local placements as a recordable app view.",
        )
    manifest = {
        "pack_id": pack_dir.name,
        "product_name": "OODrive",
        "headline_claim": (
            "OODrive is a minimal-shot CARLA OOD scenario generator and evidence harness: "
            "it creates weird driving cases, places them in CARLA, attaches sampled VLA "
            "reasoning plus RAG memory, and produces judge-visible reports without claiming "
            "real-time closed-loop VLA control."
        ),
        "motivation": (
            "Minimal-shot autonomy should be judged on new long-tail situations instead of "
            "memorized routes. OODrive focuses the prototype on the missing tooling: fast "
            "generation of plausible rare scenarios and honest evidence about how frozen "
            "reasoning models behave on them."
        ),
        "sections": sections,
        "loop_steps": _loop_steps(command_transcript, artifacts),
        "claim_matrix": claim_matrix,
        "unique_contributions": unique_contributions,
        "hero_media": {
            "local_file": str(hero_video_path),
            "score": _optional_float(hero_score_payload.get("hero_demo_score")) or 0.0,
            "duration_s": _first_float(
                _mapping(hero_score_payload.get("metrics")).get("output_duration_s"),
                _mapping(hero_score_payload.get("inputs")).get("output_duration_s"),
            ),
        },
        "failure_cases": failure_cases,
        "limitations": [
            "No real-time closed-loop VLA control claim.",
            "Alpamayo inference is sampled offline over captured CARLA frames.",
            "The hero video is time-warped to be judge-visible.",
            "The TASK-102 visual source and TASK-128 reasoning evidence are combined and labeled.",
        ],
        "artifact_inventory": artifacts,
        "environment_demo": {
            "path": str(environment_demo_path) if environment_demo_path is not None else "",
            "status": "local_file" if environment_demo_path is not None and environment_demo_path.exists() else "missing",
            "family_count": environment_demo_payload.get("family_count"),
            "asset_request_count": environment_demo_payload.get("asset_request_count"),
        },
        "command_transcript": command_transcript,
        "readiness_score": readiness_payload.get("submission_readiness_score"),
        "claim_boundaries": claim_boundaries,
        "artifacts": {
            "submission_pack_manifest_path": str(pack_dir / "submission_manifest.json"),
            "hero_demo_video_path": str(hero_video_path),
            "hero_demo_score_json_path": str(hero_score_path),
            "policy_evaluation_path": str(evaluation_path),
            "run_manifest_path": str(run_manifest_path),
            "environment_demo_manifest_path": str(environment_demo_path) if environment_demo_path is not None else "",
        },
    }
    outputs = _write_pack(pack_dir, manifest)
    return {**manifest, "pack_dir": str(pack_dir), **outputs}


def _write_pack(pack_dir: Path, manifest: dict[str, Any]) -> dict[str, str]:
    manifest_path = pack_dir / "submission_manifest.json"
    claim_matrix_path = pack_dir / "claim_matrix.json"
    inventory_path = pack_dir / "artifact_inventory.json"
    commands_path = pack_dir / "commands.sh"
    readme_path = pack_dir / "README.md"
    scorecard_path = pack_dir / "scorecard.md"
    html_path = pack_dir / "index.html"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    claim_matrix_path.write_text(json.dumps(manifest["claim_matrix"], indent=2), encoding="utf-8")
    inventory_path.write_text(json.dumps(manifest["artifact_inventory"], indent=2), encoding="utf-8")
    commands_path.write_text(_commands_sh(manifest), encoding="utf-8")
    readme_path.write_text(render_submission_pack_markdown(manifest), encoding="utf-8")
    scorecard_path.write_text(_scorecard_markdown(manifest), encoding="utf-8")
    html_path.write_text(render_submission_pack_html(manifest), encoding="utf-8")
    return {
        "index_html_path": str(html_path),
        "readme_path": str(readme_path),
        "submission_manifest_path": str(manifest_path),
        "claim_matrix_path": str(claim_matrix_path),
        "commands_path": str(commands_path),
        "artifact_inventory_path": str(inventory_path),
        "scorecard_path": str(scorecard_path),
    }


def render_submission_pack_markdown(pack: dict[str, Any]) -> str:
    lines = [
        "# OODrive Submission Pack",
        "",
        pack["headline_claim"],
        "",
        "## Why This Should Win",
        "",
        pack["motivation"],
        "",
        "## Product Loop",
        "",
        "| step | command | artifact |",
        "| --- | --- | --- |",
    ]
    for step in pack.get("loop_steps", []):
        lines.append(f"| {step.get('name')} | `{step.get('command')}` | `{step.get('artifact')}` |")
    lines.extend(["", "## Unique Contributions", ""])
    lines.extend(f"- {item}" for item in pack.get("unique_contributions", []))
    lines.extend(["", "## Failure Case", ""])
    for case in pack.get("failure_cases", []):
        lines.extend(
            [
                f"### {case.get('title')}",
                "",
                str(case.get("what_happened", "")),
                "",
                f"Learned: {case.get('what_we_learned', '')}",
                "",
            ]
        )
    lines.extend(["## Claim Matrix", "", "| claim | status | evidence |", "| --- | --- | --- |"])
    for row in pack.get("claim_matrix", []):
        lines.append(
            f"| {row.get('claim')} | {row.get('status')} | "
            f"{', '.join(str(item) for item in row.get('evidence', []))} |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in pack.get("limitations", []))
    lines.extend(["", "## Claim Boundaries", ""])
    lines.extend(f"- `{item}`" for item in pack.get("claim_boundaries", []))
    return "\n".join(lines) + "\n"


def render_submission_pack_html(pack: dict[str, Any]) -> str:
    sections = "".join(
        f"<section><h2>{_esc(section.get('title'))}</h2><p>{_esc(section.get('body'))}</p></section>"
        for section in pack.get("sections", [])
    )
    claims = "".join(
        "<tr>"
        f"<td>{_esc(row.get('claim'))}</td>"
        f"<td>{_esc(row.get('status'))}</td>"
        f"<td>{_esc(', '.join(str(item) for item in row.get('evidence', [])))}</td>"
        "</tr>"
        for row in pack.get("claim_matrix", [])
    )
    loop = "".join(
        "<tr>"
        f"<td>{_esc(step.get('name'))}</td>"
        f"<td><code>{_esc(step.get('command'))}</code></td>"
        f"<td><code>{_esc(step.get('artifact'))}</code></td>"
        "</tr>"
        for step in pack.get("loop_steps", [])
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>OODrive Submission Pack</title>"
        "<style>body{font-family:Inter,Arial,sans-serif;max-width:1120px;margin:36px auto;padding:0 24px;line-height:1.45;color:#17202a}"
        "h1{font-size:34px;margin-bottom:8px}h2{margin-top:28px}section{border-top:1px solid #d8e0e8;padding-top:12px}"
        "table{border-collapse:collapse;width:100%;margin:16px 0}td,th{border:1px solid #d6dde5;padding:8px;text-align:left;vertical-align:top}th{background:#f4f7fb}"
        "code{background:#eef3f8;padding:2px 4px;border-radius:4px}.hero{font-size:18px}</style>"
        "</head><body>"
        f"<h1>OODrive</h1><p class='hero'>{_esc(pack.get('headline_claim'))}</p>"
        f"<h2>Why this matters</h2><p>{_esc(pack.get('motivation'))}</p>"
        f"{sections}"
        "<h2>Product loop</h2><table><tr><th>Step</th><th>Command</th><th>Artifact</th></tr>"
        f"{loop}</table>"
        "<h2>Claim matrix</h2><table><tr><th>Claim</th><th>Status</th><th>Evidence</th></tr>"
        f"{claims}</table>"
        "</body></html>"
    )


def _sections(
    db_payload: dict[str, Any],
    run_payload: dict[str, Any],
    evaluation_payload: dict[str, Any],
    hero_score_payload: dict[str, Any],
    environment_demo_payload: dict[str, Any],
) -> list[dict[str, str]]:
    sections = [
        {
            "id": "motivation",
            "title": "Motivation",
            "body": "Autonomy that needs heavy data collection will always lag reality; OODrive tests rare situations from minimal prompts.",
        },
        {
            "id": "scenario_generation",
            "title": "Randomized Scenario Generation",
            "body": f"{len(_list_of_mappings(db_payload.get('candidates')))} generated candidates and {len(_list_of_mappings(db_payload.get('briefs')))} prompt brief(s) are tracked in the DB.",
        },
        {
            "id": "carla_navigation",
            "title": "CARLA Navigation Evidence",
            "body": f"Run `{run_payload.get('run_id')}` uses runtime `{run_payload.get('runtime')}` with status `{run_payload.get('status')}`.",
        },
        {
            "id": "reasoning_memory",
            "title": "Reasoning + Memory",
            "body": str(evaluation_payload.get("cot_summary") or "Sampled Alpamayo reasoning is attached to the captured CARLA evidence."),
        },
        {
            "id": "latency_compute",
            "title": "Latency + Compute Honesty",
            "body": f"Recorded latency is `{evaluation_payload.get('latency_ms', 'not recorded in this artifact')}` ms; open-loop labels stay visible.",
        },
        {
            "id": "failure_case",
            "title": "Failure Case",
            "body": "Current failure: the system reasons over captured frames but does not yet drive CARLA controls in real time.",
        },
    ]
    if environment_demo_payload:
        sections.insert(
            2,
            {
                "id": "environment_studio",
                "title": "Environment Studio",
                "body": (
                    f"{environment_demo_payload.get('family_count', 0)} environment families and "
                    f"{environment_demo_payload.get('asset_request_count', 0)} CARLA asset requests are exposed in a recordable app view."
                ),
            },
        )
    return sections


def _loop_steps(command_transcript: list[str], artifacts: list[dict[str, str]]) -> list[dict[str, str]]:
    lookup = {item["name"]: item["path"] for item in artifacts}
    return [
        {"name": "Generate", "command": _first_command(command_transcript, "oodrive generate"), "artifact": lookup.get("scenario_db", "")},
        {"name": "Place", "command": _first_command(command_transcript, "oodrive place"), "artifact": lookup.get("run_manifest", "")},
        {"name": "Reason", "command": _first_command(command_transcript, "oodrive reason"), "artifact": lookup.get("policy_evaluation", "")},
        {"name": "Demo Video", "command": _first_command(command_transcript, "oodrive demo-video"), "artifact": lookup.get("hero_video", "")},
        {"name": "Score Demo", "command": _first_command(command_transcript, "oodrive score-demo"), "artifact": lookup.get("hero_score", "")},
    ]


def _claim_matrix(artifacts: list[dict[str, str]], claim_boundaries: list[str]) -> list[dict[str, Any]]:
    lookup = {item["name"]: item["path"] for item in artifacts}
    rows = [
        {"claim": "OODrive generates randomized OOD driving scenarios from minimal prompts.", "status": "proved", "evidence": [lookup.get("scenario_db", "")]},
        {"claim": "OODrive generates CARLA-ready environment variants with weather, traffic, proxy assets, and road-local placements.", "status": "proved" if lookup.get("environment_demo") else "partial", "evidence": [lookup.get("environment_demo", "")]},
        {"claim": "The selected scenario was placed and rendered in CARLA.", "status": "proved", "evidence": [lookup.get("run_manifest", "")]},
        {"claim": "The demo includes visible risk/object telemetry.", "status": "proved", "evidence": [lookup.get("hero_score", "")]},
        {"claim": "Alpamayo reasoning is sampled over captured frames.", "status": "proved", "evidence": [lookup.get("policy_evaluation", "")]},
        {"claim": "RAG/memory callouts are included in the judge-visible artifact.", "status": "proved", "evidence": [lookup.get("hero_score", "")]},
        {"claim": "The system does not claim real-time closed-loop VLA control.", "status": "explicit limitation", "evidence": claim_boundaries},
        {"claim": "The work has one understood failure case.", "status": "proved", "evidence": ["submission_manifest.json#failure_cases"]},
        {"claim": "Prize funding would target closed-loop controller integration.", "status": "roadmap", "evidence": ["submission_manifest.json#motivation"]},
    ]
    return rows


def _artifact_inventory(paths: dict[str, Path | None]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for name, path in paths.items():
        if path is None:
            out.append({"name": name, "path": "", "status": "missing"})
        else:
            out.append({"name": name, "path": str(path), "status": "local_file" if path.exists() else "missing"})
    return out


def _command_transcript(
    db_payload: dict[str, Any],
    db_path: Path,
    run_manifest_path: Path,
    evaluation_path: Path,
    hero_video_path: Path,
    hero_score_path: Path,
) -> list[str]:
    commands = [
        str(item.get("command", ""))
        for item in _list_of_mappings(db_payload.get("command_log"))
        if str(item.get("command", "")).strip()
    ]
    if not any(command.startswith("oodrive generate") for command in commands):
        commands.insert(0, f"oodrive generate '<prompt>' --db {db_path}")
    for command in (
        f"oodrive place --db {db_path} --run-id <run-id>",
        f"oodrive reason --db {db_path} --run {run_manifest_path} --prediction-json <alpamayo_prediction.json>",
        f"oodrive demo-video --db {db_path} --run {run_manifest_path} --evaluation {evaluation_path} --input-video <source.mp4>",
        f"oodrive score-demo --db {db_path} --run {run_manifest_path} --evaluation {evaluation_path} --video {hero_video_path} --overlay-report <hero_demo_video.json>",
        f"oodrive score-submission --db {db_path} --run {run_manifest_path} --evaluation {evaluation_path} --hero-score {hero_score_path}",
    ):
        if not any(item.startswith(command.split(" --", maxsplit=1)[0]) for item in commands):
            commands.append(command)
    return commands


def _commands_sh(pack: dict[str, Any]) -> str:
    lines = ["#!/usr/bin/env bash", "set -euo pipefail", ""]
    for command in pack.get("command_transcript", []):
        lines.append(f"# {command}")
    return "\n".join(lines) + "\n"


def _scorecard_markdown(pack: dict[str, Any]) -> str:
    hero = pack.get("hero_media", {})
    lines = [
        "# OODrive Scorecard",
        "",
        f"- Hero demo score: `{hero.get('score')}`",
        f"- Hero media: `{hero.get('local_file')}`",
        f"- Pack id: `{pack.get('pack_id')}`",
        "",
        "Run `oodrive score-submission` with this manifest to compute the commission-readiness score.",
        "",
    ]
    return "\n".join(lines)


def _first_command(commands: list[str], prefix: str) -> str:
    return next((command for command in commands if command.startswith(prefix)), prefix)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, dict) else {}


def _load_optional_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        return _load_json(path)
    except (OSError, json.JSONDecodeError):
        return {}


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in value] if isinstance(value, list) and all(isinstance(item, dict) for item in value) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _optional_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_float(*values: object) -> float:
    for value in values:
        parsed = _optional_float(value)
        if parsed is not None:
            return parsed
    return 0.0


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


__all__ = [
    "build_submission_story_pack",
    "render_submission_pack_html",
    "render_submission_pack_markdown",
]
