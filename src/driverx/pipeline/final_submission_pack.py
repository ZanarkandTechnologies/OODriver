"""Final SoTA submission pack assembly for the last sprint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir


def run_final_submission_pack(
    *,
    output_root: Path,
    run_id: str,
    eval_matrix_path: Path | None = None,
    scenario_studio_path: Path | None = None,
    alpamayo_rag_batch_path: Path | None = None,
    fail2drive_extension_path: Path | None = None,
    hero_video_evidence_path: Path | None = None,
    scenario_browser_path: Path | None = None,
    blockers_path: Path | None = None,
) -> dict[str, Any]:
    run_dir = prepare_run_dir(output_root, run_id)
    return build_final_submission_pack(
        run_dir,
        eval_matrix_path=eval_matrix_path,
        scenario_studio_path=scenario_studio_path,
        alpamayo_rag_batch_path=alpamayo_rag_batch_path,
        fail2drive_extension_path=fail2drive_extension_path,
        hero_video_evidence_path=hero_video_evidence_path,
        scenario_browser_path=scenario_browser_path,
        blockers_path=blockers_path,
    )


def build_final_submission_pack(
    run_dir: Path,
    *,
    eval_matrix_path: Path | None = None,
    scenario_studio_path: Path | None = None,
    alpamayo_rag_batch_path: Path | None = None,
    fail2drive_extension_path: Path | None = None,
    hero_video_evidence_path: Path | None = None,
    scenario_browser_path: Path | None = None,
    blockers_path: Path | None = None,
) -> dict[str, Any]:
    eval_matrix = _load_json(eval_matrix_path)
    studio = _load_json(scenario_studio_path)
    alpamayo_batch = _load_json(alpamayo_rag_batch_path)
    fail2drive = _load_json(fail2drive_extension_path)
    hero_video = _load_json(hero_video_evidence_path)
    blockers = _parse_open_blockers(_read_text(blockers_path))
    artifact_map = _artifact_map(
        eval_matrix_path=eval_matrix_path,
        scenario_studio_path=scenario_studio_path,
        alpamayo_rag_batch_path=alpamayo_rag_batch_path,
        fail2drive_extension_path=fail2drive_extension_path,
        hero_video_evidence_path=hero_video_evidence_path,
        scenario_browser_path=scenario_browser_path,
        blockers_path=blockers_path,
    )
    evidence_rows = _evidence_rows(
        eval_matrix=eval_matrix,
        studio=studio,
        alpamayo_batch=alpamayo_batch,
        fail2drive=fail2drive,
        hero_video=hero_video,
        artifact_map=artifact_map,
    )
    payload = {
        "title": "0xDriver: Scenario Studio For Minimal-Shot Driving Evaluation",
        "thesis": (
            "0xDriver contributes a randomized OOD scenario-generation and evidence-management harness "
            "for testing frozen reasoning VLAs on weird but plausible driving cases without fine-tuning."
        ),
        "submission_status": _submission_status(evidence_rows),
        "scorecard": _scorecard(eval_matrix, studio, alpamayo_batch, fail2drive, hero_video),
        "evidence_rows": evidence_rows,
        "artifact_map": artifact_map,
        "video_script": _video_script(eval_matrix, studio, alpamayo_batch, fail2drive, hero_video),
        "two_page_writeup": _writeup(eval_matrix, studio, alpamayo_batch, fail2drive, hero_video, blockers),
        "model_and_data_declarations": _declarations(alpamayo_batch, fail2drive),
        "claim_boundaries": _claim_boundaries(studio, alpamayo_batch, fail2drive, hero_video),
        "open_blockers": blockers,
        "inputs": artifact_map,
    }
    return write_final_submission_pack(run_dir, payload)


def write_final_submission_pack(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "final_submission_pack_v7.json"
    report_path = run_dir / "final_submission_pack_v7.md"
    script_path = run_dir / "video_script_v7.md"
    writeup_path = run_dir / "writeup_2page_draft.md"
    artifact_map_path = run_dir / "artifact_map_v7.json"
    browser_path = run_dir / "scenario_browser_v7.html"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    artifact_map_path.write_text(json.dumps(payload["artifact_map"], indent=2), encoding="utf-8")
    report_path.write_text(_report_markdown(payload), encoding="utf-8")
    script_path.write_text(_video_script_markdown(payload), encoding="utf-8")
    writeup_path.write_text(_writeup_markdown(payload), encoding="utf-8")
    browser_path.write_text(_browser_html(payload), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
        "video_script_path": str(script_path),
        "writeup_path": str(writeup_path),
        "artifact_map_path": str(artifact_map_path),
        "browser_path": str(browser_path),
    }


def _scorecard(
    eval_matrix: dict[str, Any],
    studio: dict[str, Any],
    alpamayo_batch: dict[str, Any],
    fail2drive: dict[str, Any],
    hero_video: dict[str, Any],
) -> dict[str, Any]:
    return {
        "selected_cases": eval_matrix.get("case_count"),
        "hero_cases": eval_matrix.get("hero_count"),
        "scenario_studio_prompts": studio.get("prompt_count"),
        "scenario_studio_candidates": studio.get("candidate_count"),
        "alpamayo_rag_cases": alpamayo_batch.get("case_count"),
        "alpamayo_rag_passed": alpamayo_batch.get("passed_count"),
        "alpamayo_reasoning_changed": alpamayo_batch.get("reasoning_changed_count"),
        "alpamayo_mean_latency_ms": alpamayo_batch.get("mean_latency_ms"),
        "alpamayo_max_vram_peak_mb": alpamayo_batch.get("max_vram_peak_mb"),
        "fail2drive_extension_cases": fail2drive.get("generated_case_count"),
        "fail2drive_reference_count": fail2drive.get("reference_count"),
        "hero_video_duration_s": hero_video.get("duration_s"),
        "hero_video_path": _hero_video_path(hero_video),
    }


def _evidence_rows(
    *,
    eval_matrix: dict[str, Any],
    studio: dict[str, Any],
    alpamayo_batch: dict[str, Any],
    fail2drive: dict[str, Any],
    hero_video: dict[str, Any],
    artifact_map: dict[str, str | None],
) -> list[dict[str, Any]]:
    return [
        {
            "claim": "We can author randomized minimal-shot driving cases from short briefs.",
            "status": "proved" if studio.get("candidate_count", 0) else "blocked",
            "artifact": artifact_map.get("scenario_studio_path"),
            "why_it_matters": f"{studio.get('prompt_count', 0)} prompts generated {studio.get('candidate_count', 0)} candidate cases with curation rows.",
            "claim_boundary": "deterministic prompt compiler; live LLM/Meshy generation is not claimed.",
        },
        {
            "claim": "We have a judge-visible CARLA OOD video for the generated simulator path.",
            "status": "proved" if _hero_video_path(hero_video) else "partial",
            "artifact": _hero_video_path(hero_video) or artifact_map.get("hero_video_evidence_path"),
            "why_it_matters": f"Hero video duration is {hero_video.get('duration_s', 'unknown')} seconds.",
            "claim_boundary": "scripted simulator evidence; not an official Fail2Drive route score.",
        },
        {
            "claim": "Frozen Alpamayo can be evaluated with and without retrieved memory on OOD cases.",
            "status": "proved" if alpamayo_batch.get("passed_count", 0) >= 3 else "partial",
            "artifact": artifact_map.get("alpamayo_rag_batch_path"),
            "why_it_matters": (
                f"{alpamayo_batch.get('passed_count', 0)} passed comparisons; "
                f"{alpamayo_batch.get('reasoning_changed_count', 0)} changed reasoning."
            ),
            "claim_boundary": "open-loop trajectory-intent evaluation; not closed-loop VLA steering.",
        },
        {
            "claim": "DriverX generated cases extend Fail2Drive-style OOD families.",
            "status": "proved" if fail2drive.get("generated_case_count", 0) else "partial",
            "artifact": artifact_map.get("fail2drive_extension_path"),
            "why_it_matters": (
                f"{fail2drive.get('generated_case_count', 0)} generated cases linked to "
                f"{fail2drive.get('reference_count', 0)} references and "
                f"{fail2drive.get('memory_entry_count', 0)} memory entries."
            ),
            "claim_boundary": "reference layer only; official Fail2Drive score is false.",
        },
        {
            "claim": "The final submission scope is selected and auditable.",
            "status": "proved" if eval_matrix.get("case_count", 0) else "partial",
            "artifact": artifact_map.get("eval_matrix_path"),
            "why_it_matters": f"{eval_matrix.get('case_count', 0)} cases are role-classified for the submission.",
            "claim_boundary": "selection matrix is planning/evidence management, not runtime execution.",
        },
    ]


def _submission_status(rows: list[dict[str, Any]]) -> str:
    if any(row["status"] == "blocked" for row in rows):
        return "partial_with_blockers"
    if all(row["status"] == "proved" for row in rows):
        return "submission_ready"
    return "submission_ready_with_claim_boundaries"


def _artifact_map(**paths: Path | None) -> dict[str, str | None]:
    return {key: str(path) if path is not None else None for key, path in paths.items()}


def _video_script(
    eval_matrix: dict[str, Any],
    studio: dict[str, Any],
    alpamayo_batch: dict[str, Any],
    fail2drive: dict[str, Any],
    hero_video: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "time": "0:00-0:25",
            "beat": "Minimal-shot problem",
            "visual": "Title over CARLA hero video and scenario tags.",
            "narration": "The submission asks whether autonomy can handle new long-tail scenes without collecting a bespoke dataset for every corner case.",
        },
        {
            "time": "0:25-1:10",
            "beat": "Scenario Studio",
            "visual": "Show scenario_studio_gallery.md and generated candidates.",
            "narration": f"Scenario Studio turns {studio.get('prompt_count', 0)} human briefs into {studio.get('candidate_count', 0)} deterministic OOD candidates with assets, behaviors, memory queries, and curation gates.",
        },
        {
            "time": "1:10-1:50",
            "beat": "CARLA evidence",
            "visual": "Play hero video.",
            "narration": f"The hero CARLA run is {hero_video.get('duration_s', 'unknown')} seconds and demonstrates the generated OOD simulator path.",
        },
        {
            "time": "1:50-2:40",
            "beat": "Alpamayo plus memory",
            "visual": "Show Alpamayo batch table.",
            "narration": f"Frozen Alpamayo was evaluated on {alpamayo_batch.get('case_count', 0)} OOD cases with memory; {alpamayo_batch.get('reasoning_changed_count', 0)} cases changed reasoning and all remain explicitly open-loop.",
        },
        {
            "time": "2:40-3:20",
            "beat": "Fail2Drive extension",
            "visual": "Show extension matrix.",
            "narration": f"DriverX links {fail2drive.get('generated_case_count', 0)} generated cases to Fail2Drive-style families while avoiding an official-score claim.",
        },
        {
            "time": "3:20-4:00",
            "beat": "Submission claim",
            "visual": "Show evidence matrix and blockers.",
            "narration": f"The final matrix contains {eval_matrix.get('case_count', 0)} judge-facing cases; the contribution is the generator plus evidence flywheel, not a production AV stack.",
        },
    ]


def _writeup(
    eval_matrix: dict[str, Any],
    studio: dict[str, Any],
    alpamayo_batch: dict[str, Any],
    fail2drive: dict[str, Any],
    hero_video: dict[str, Any],
    blockers: list[str],
) -> dict[str, str]:
    return {
        "motivation": (
            "If autonomy depends on collecting examples of every weird road situation, it will always lag reality. "
            "0xDriver reframes minimal-shot driving as a stress-test and memory problem: generate plausible OOD cases, "
            "run frozen policies through them, and preserve failures as reusable context."
        ),
        "architecture": (
            "The system has a Scenario Studio compiler, deterministic environment and behavior generators, CARLA/Fail2Drive-compatible evidence paths, "
            "a failure-memory bank, and an Alpamayo open-loop evaluation harness. Scenario Studio emits the curation queue; CARLA produces video and tracks; "
            "Alpamayo is evaluated with and without retrieved memory; final reports keep claim boundaries explicit."
        ),
        "what_worked": (
            f"The final sprint generated {studio.get('candidate_count', 0)} OOD candidates from {studio.get('prompt_count', 0)} briefs, "
            f"selected {eval_matrix.get('case_count', 0)} judge-facing cases, linked {fail2drive.get('generated_case_count', 0)} cases to Fail2Drive references, "
            f"and summarized {alpamayo_batch.get('passed_count', 0)} Frozen Alpamayo+memory comparisons. "
            f"The hero video evidence is {hero_video.get('duration_s', 'unknown')} seconds."
        ),
        "what_did_not_work": (
            "The model evidence is open-loop and slow, not real-time closed-loop control. "
            "Full official Fail2Drive scoring remains a future runtime task. "
            f"Current open blockers: {blockers[0] if blockers else 'none that block the V7 evidence pack.'}"
        ),
        "where_prize_money_goes": (
            "The next prototype step is a persistent graphics-capable CARLA host plus GPU time for closed-loop VLA experiments, "
            "higher-fidelity generated assets, and enough repeated runs to convert partial candidates into accepted dataset rows."
        ),
    }


def _declarations(alpamayo_batch: dict[str, Any], fail2drive: dict[str, Any]) -> list[str]:
    return [
        "Base model: nvidia/Alpamayo-1.5-10B, used as a frozen non-commercial research model.",
        "No AV fine-tuning is performed for these generated scenarios.",
        f"Alpamayo batch status: {alpamayo_batch.get('status', 'not provided')}; open-loop only.",
        f"Fail2Drive reference sources: {fail2drive.get('reference_sources', [])}; official score claim is false.",
        "Model weights, datasets, videos, credentials, CARLA installs, and remote caches are excluded from git.",
    ]


def _claim_boundaries(
    studio: dict[str, Any],
    alpamayo_batch: dict[str, Any],
    fail2drive: dict[str, Any],
    hero_video: dict[str, Any],
) -> list[str]:
    boundaries = [
        "Scenario Studio is deterministic unless a future provider-backed generator is explicitly configured.",
        "Generated candidates marked accept_partial still need live CARLA/model evidence before becoming accepted dataset rows.",
        "Alpamayo evidence is open-loop trajectory-intent and reasoning evaluation, not closed-loop car control.",
        "Fail2Drive linkage is a benchmark reference layer, not an official leaderboard score.",
    ]
    boundaries.extend(str(item) for item in list(studio.get("claim_boundaries", [])))
    boundaries.extend(str(item) for item in list(alpamayo_batch.get("claim_boundaries", [])))
    boundaries.extend(str(item) for item in list(fail2drive.get("claim_boundaries", [])))
    if _hero_video_path(hero_video):
        boundaries.append("Hero video is generated simulator evidence and may be shown in the final demo.")
    return sorted(set(boundaries))


def _hero_video_path(hero_video: dict[str, Any]) -> str | None:
    path = hero_video.get("remote_video_path") or hero_video.get("video_path")
    return str(path) if path else None


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _read_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_open_blockers(text: str) -> list[str]:
    if not text:
        return []
    lines = text.splitlines()
    in_open = False
    blockers: list[str] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") and stripped.lstrip("#").strip().lower() == "open":
            in_open = True
            continue
        if in_open and stripped.startswith("#"):
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


def _report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['title']}",
        "",
        f"- Status: `{payload['submission_status']}`",
        "",
        "## Thesis",
        "",
        payload["thesis"],
        "",
        "## Scorecard",
        "",
    ]
    for key, value in dict(payload["scorecard"]).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Evidence Rows",
            "",
            "| claim | status | artifact | why it matters | boundary |",
            "|---|---|---|---|---|",
        ]
    )
    for row in payload["evidence_rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(row["claim"]),
                    _cell(row["status"]),
                    _cell(row["artifact"]),
                    _cell(row["why_it_matters"]),
                    _cell(row["claim_boundary"]),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Claim Boundaries", ""])
    lines.extend(f"- {item}" for item in payload["claim_boundaries"])
    lines.extend(["", "## Artifact Map", ""])
    for key, value in dict(payload["artifact_map"]).items():
        lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines) + "\n"


def _video_script_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Video Script V7", "", "| time | beat | visual | narration |", "|---|---|---|---|"]
    for beat in payload["video_script"]:
        lines.append(
            "| "
            + " | ".join([_cell(beat["time"]), _cell(beat["beat"]), _cell(beat["visual"]), _cell(beat["narration"])])
            + " |"
        )
    return "\n".join(lines) + "\n"


def _writeup_markdown(payload: dict[str, Any]) -> str:
    lines = ["# 0xDriver Two-Page Write-Up Draft", ""]
    for key, value in dict(payload["two_page_writeup"]).items():
        lines.extend([f"## {key.replace('_', ' ').title()}", "", str(value), ""])
    lines.extend(["## Model And Data Declarations", ""])
    lines.extend(f"- {item}" for item in payload["model_and_data_declarations"])
    return "\n".join(lines) + "\n"


def _browser_html(payload: dict[str, Any]) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{_escape(row['status'])}</td>"
        f"<td>{_escape(row['claim'])}</td>"
        f"<td>{_link(row.get('artifact'))}</td>"
        f"<td>{_escape(row['why_it_matters'])}</td>"
        f"<td>{_escape(row['claim_boundary'])}</td>"
        "</tr>"
        for row in payload["evidence_rows"]
    )
    score_items = "\n".join(
        f"<li><code>{_escape(key)}</code>: {_escape(value)}</li>"
        for key, value in dict(payload["scorecard"]).items()
    )
    artifacts = "\n".join(
        f"<li><code>{_escape(key)}</code>: {_link(value)}</li>"
        for key, value in dict(payload["artifact_map"]).items()
    )
    boundaries = "\n".join(f"<li>{_escape(item)}</li>" for item in payload["claim_boundaries"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape(payload['title'])}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; line-height: 1.45; color: #172026; background: #f8faf9; }}
    main {{ max-width: 1180px; margin: 0 auto; }}
    h1 {{ font-size: 34px; margin-bottom: 8px; }}
    h2 {{ margin-top: 32px; }}
    table {{ border-collapse: collapse; width: 100%; background: white; }}
    th, td {{ border: 1px solid #d8e0dd; padding: 10px 12px; vertical-align: top; }}
    th {{ background: #e8f0ed; text-align: left; }}
    code {{ background: #eef3f1; padding: 1px 4px; border-radius: 4px; }}
    .status {{ display: inline-block; padding: 4px 8px; background: #dff2e3; border-radius: 4px; }}
  </style>
</head>
<body>
<main>
  <h1>{_escape(payload['title'])}</h1>
  <p class="status">{_escape(payload['submission_status'])}</p>
  <p>{_escape(payload['thesis'])}</p>
  <h2>Scorecard</h2>
  <ul>{score_items}</ul>
  <h2>Evidence Rows</h2>
  <table>
    <thead><tr><th>Status</th><th>Claim</th><th>Artifact</th><th>Why It Matters</th><th>Boundary</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <h2>Artifact Map</h2>
  <ul>{artifacts}</ul>
  <h2>Claim Boundaries</h2>
  <ul>{boundaries}</ul>
</main>
</body>
</html>
"""


def _escape(value: Any) -> str:
    text = str(value if value is not None else "")
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _link(value: Any) -> str:
    text = str(value if value is not None else "")
    if not text:
        return ""
    escaped = _escape(text)
    return f'<a href="{escaped}">{escaped}</a>'


def _cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


__all__ = ["build_final_submission_pack", "run_final_submission_pack", "write_final_submission_pack"]
