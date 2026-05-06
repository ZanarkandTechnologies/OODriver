"""Judge-facing scenario browser and V6 submission pack builder."""

from __future__ import annotations

import html
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.scenarios import ScenarioCatalog, ScenarioCatalogRecord, load_scenario_catalog


@dataclass(frozen=True)
class SubmissionBrowserInputs:
    catalog_path: Path
    policy_evaluation_path: Path | None = None
    blockers_path: Path | None = None


@dataclass(frozen=True)
class SubmissionBrowserOutputs:
    browser_html: str
    dossier_md: str
    video_script_md: str
    summary_json: str
    hero_scenarios: list[str]
    failure_scenarios: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "browser_html": self.browser_html,
            "dossier_md": self.dossier_md,
            "video_script_md": self.video_script_md,
            "summary_json": self.summary_json,
            "hero_scenarios": self.hero_scenarios,
            "failure_scenarios": self.failure_scenarios,
        }


def build_submission_scenario_browser(
    inputs: SubmissionBrowserInputs,
    output_dir: Path,
) -> SubmissionBrowserOutputs:
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog = load_scenario_catalog(inputs.catalog_path)
    policy = _load_json(inputs.policy_evaluation_path)
    blockers = _load_blockers(inputs.blockers_path)
    hero_records = _hero_records(catalog)
    failure_records = _failure_records(catalog)
    policy_summary = _policy_summary(policy)
    browser_path = output_dir / "scenario_browser.html"
    dossier_path = output_dir / "submission_dossier_v6.md"
    script_path = output_dir / "video_script_v6.md"
    summary_path = output_dir / "submission_browser_summary.json"
    browser_path.write_text(
        _browser_html(catalog, policy, policy_summary, blockers, browser_path.parent),
        encoding="utf-8",
    )
    dossier_path.write_text(
        _dossier_markdown(catalog, policy_summary, blockers, hero_records, failure_records),
        encoding="utf-8",
    )
    script_path.write_text(
        _video_script_markdown(policy_summary, hero_records, failure_records),
        encoding="utf-8",
    )
    summary = {
        "scenario_count": len(catalog.records),
        "hero_scenarios": [record.scenario_id for record in hero_records],
        "failure_scenarios": [record.scenario_id for record in failure_records],
        "policy_evaluation_row_count": policy_summary["total"],
        "policy_status_counts": policy_summary["status_counts"],
        "policy_passed_count": policy_summary["passed"],
        "policy_planned_count": policy_summary["planned"],
        "policy_blocked_count": policy_summary["blocked"],
        "policy_decision_artifact_count": policy_summary["decision_artifact_count"],
        "catalog_path": str(inputs.catalog_path),
        "policy_evaluation_path": str(inputs.policy_evaluation_path) if inputs.policy_evaluation_path else None,
        "browser_html": str(browser_path),
        "dossier_md": str(dossier_path),
        "video_script_md": str(script_path),
        "summary_json": str(summary_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return SubmissionBrowserOutputs(
        browser_html=str(browser_path),
        dossier_md=str(dossier_path),
        video_script_md=str(script_path),
        summary_json=str(summary_path),
        hero_scenarios=[record.scenario_id for record in hero_records],
        failure_scenarios=[record.scenario_id for record in failure_records],
    )


def _hero_records(catalog: ScenarioCatalog) -> list[ScenarioCatalogRecord]:
    promoted_quality = [
        record
        for record in catalog.records
        if record.promotion.status == "hero"
        and record.quality.status == "passed"
        and record.quality.has_video
        and record.quality.road_aligned is True
    ]
    scored = sorted(
        promoted_quality,
        key=lambda record: (
            record.promotion.status == "hero",
            record.quality.has_video,
            record.quality.has_model_reasoning,
            record.quality.road_aligned is True,
            record.quality.has_conflict is True,
        ),
        reverse=True,
    )
    return scored[: min(3, len(scored))]


def _failure_records(catalog: ScenarioCatalog) -> list[ScenarioCatalogRecord]:
    promoted_failures = [
        record
        for record in catalog.records
        if record.promotion.status == "failure_case"
        and record.quality.status == "passed"
        and record.quality.has_video
        and record.quality.road_aligned is True
    ]
    return sorted(
        promoted_failures,
        key=lambda record: (
            record.quality.has_model_reasoning,
            record.quality.has_conflict is True,
            record.scenario_id,
        ),
        reverse=True,
    )[: min(3, len(promoted_failures))]


def _browser_html(
    catalog: ScenarioCatalog,
    policy: dict[str, Any],
    policy_summary: dict[str, Any],
    blockers: list[str],
    output_dir: Path,
) -> str:
    cards = "\n".join(_scenario_card(record, policy, output_dir) for record in catalog.records)
    blockers_html = "".join(f"<li>{html.escape(blocker)}</li>" for blocker in blockers[:12]) or "<li>none</li>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>0xDriver Scenario Browser</title>
  <style>
    body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #111; background: #f6f5f1; }}
    header {{ padding: 32px clamp(20px, 5vw, 72px); background: #101820; color: #fff; }}
    h1 {{ margin: 0 0 8px; font-size: 32px; letter-spacing: 0; }}
    p {{ line-height: 1.5; }}
    main {{ padding: 24px clamp(20px, 5vw, 72px) 48px; }}
    .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin: 20px 0; }}
    .stat {{ background: #fff; border: 1px solid #dedbd2; border-radius: 8px; padding: 14px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }}
    .card {{ background: #fff; border: 1px solid #dedbd2; border-radius: 8px; padding: 16px; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }}
    .chip {{ border: 1px solid #c7c2b8; border-radius: 999px; padding: 3px 8px; font-size: 12px; }}
    .ok {{ color: #106b3f; }}
    .warn {{ color: #9a5b00; }}
    a {{ color: #0058a3; }}
    code {{ font-size: 12px; }}
  </style>
</head>
<body>
  <header>
    <h1>0xDriver Scenario Browser</h1>
    <p>Randomized OOD scenario generation, quality gates, and minimal-shot VLA policy evidence for CARLA.</p>
  </header>
  <main>
    <section class="stats">
      <div class="stat"><strong>{len(catalog.records)}</strong><br />cataloged scenarios</div>
      <div class="stat"><strong>{sum(1 for r in catalog.records if r.quality.has_video)}</strong><br />with video evidence</div>
      <div class="stat"><strong>{sum(1 for r in catalog.records if r.quality.has_model_reasoning)}</strong><br />with VLA reasoning</div>
      <div class="stat"><strong>{policy_summary["passed"]}</strong><br />passed policy evals</div>
      <div class="stat"><strong>{policy_summary["planned"]}</strong><br />planned policy evals</div>
      <div class="stat"><strong>{policy_summary["blocked"]}</strong><br />blocked policy evals</div>
      <div class="stat"><strong>{policy_summary["decision_artifact_count"]}</strong><br />decision artifacts</div>
    </section>
    <section class="grid">{cards}</section>
    <section>
      <h2>Open Blockers</h2>
      <ul>{blockers_html}</ul>
    </section>
  </main>
</body>
</html>
"""


def _scenario_card(record: ScenarioCatalogRecord, policy: dict[str, Any], output_dir: Path) -> str:
    evaluations = [
        evaluation
        for evaluation in list(policy.get("evaluations", []))
        if evaluation.get("scenario_id") == record.scenario_id
    ]
    eval_html = "".join(
        f"<li>{html.escape(str(e.get('policy_mode')))}: <span class='{_status_class(str(e.get('status')))}'>{html.escape(str(e.get('status')))}</span></li>"
        for e in evaluations
    ) or "<li>not evaluated</li>"
    tags = "".join(
        f"<span class='chip'>{html.escape(tag)}</span>"
        for tag in [*record.environment_tags, *record.ood_tags][:10]
    )
    links = _artifact_links(record, output_dir)
    return f"""<article class="card">
  <h2>{html.escape(record.scenario_id)}</h2>
  <p><strong>Behavior:</strong> {html.escape(str(record.behavior_id or "unknown"))}</p>
  <p><strong>Quality:</strong> <span class="{_quality_class(record.quality.status)}">quality_status={html.escape(record.quality.status)}</span>, video={record.quality.has_video}, reasoning={record.quality.has_model_reasoning}, road_aligned={record.quality.road_aligned}</p>
  <p><strong>Promotion:</strong> <span class="{_promotion_class(record.promotion.status)}">promotion={html.escape(record.promotion.status)}</span>{_promotion_reason(record)}</p>
  <div class="chips">{tags}</div>
  <p><strong>Artifacts:</strong> {links}</p>
  <ul>{eval_html}</ul>
</article>"""


def _artifact_links(record: ScenarioCatalogRecord, output_dir: Path) -> str:
    pairs = [
        ("video", record.artifacts.video),
        ("tracks", record.artifacts.tracks),
        ("reasoning", record.artifacts.reasoning),
        ("package", record.artifacts.package),
        ("quality", record.artifacts.quality_report),
    ]
    links = [
        f"<a href='{html.escape(_artifact_href(path, output_dir))}'>{label}</a>"
        for label, path in pairs
        if path
    ]
    return ", ".join(links) if links else "none"


def _artifact_href(path: str, output_dir: Path) -> str:
    candidate = Path(path)
    if not candidate.is_absolute() and not candidate.exists():
        return path
    target = candidate.resolve()
    try:
        return Path(os.path.relpath(target, output_dir.resolve())).as_posix()
    except ValueError:
        return target.as_posix()


def _dossier_markdown(
    catalog: ScenarioCatalog,
    policy_summary: dict[str, Any],
    blockers: list[str],
    hero_records: list[ScenarioCatalogRecord],
    failure_records: list[ScenarioCatalogRecord],
) -> str:
    lines = [
        "# 0xDriver Submission Dossier V6",
        "",
        "## Thesis",
        "",
        "0xDriver is a CARLA OOD scenario forge for minimal-shot autonomy: generate weird-but-plausible road situations, quality-gate them, and measure how VLA-style policies reason about them without AV fine-tuning.",
        "",
        "## Current Evidence",
        "",
        f"- cataloged scenarios: `{len(catalog.records)}`",
        f"- scenarios with video: `{sum(1 for r in catalog.records if r.quality.has_video)}`",
        f"- scenarios with VLA reasoning: `{sum(1 for r in catalog.records if r.quality.has_model_reasoning)}`",
        f"- policy evaluations by status: passed `{policy_summary['passed']}`, planned `{policy_summary['planned']}`, blocked `{policy_summary['blocked']}`",
        f"- local decision artifacts attached: `{policy_summary['decision_artifact_count']}`",
        "",
        "## Hero Candidates",
        "",
    ]
    for record in hero_records:
        lines.append(
            f"- `{record.scenario_id}`: behavior `{record.behavior_id}`, "
            f"video `{record.quality.has_video}`, reasoning `{record.quality.has_model_reasoning}`"
        )
    if not hero_records:
        lines.append(
            "- No submission-grade hero is selected yet. A hero must be manually promoted and pass video plus road-alignment quality gates."
        )
    lines.extend(["", "## Failure Candidates", ""])
    for record in failure_records:
        lines.append(
            f"- `{record.scenario_id}`: behavior `{record.behavior_id}`, "
            f"video `{record.quality.has_video}`, reasoning `{record.quality.has_model_reasoning}`"
        )
    if not failure_records:
        lines.append("- No quality-passed failure case is selected yet.")
    lines.extend(
        [
            "",
            "## Claim Boundaries",
            "",
            "- This is a scenario-generation and open-loop VLA evaluation harness.",
            "- Closed-loop VLA driving remains future work unless a later run explicitly routes model output into CARLA control.",
            "- Custom GLB generation is represented by Meshy-ready prompts and stock CARLA proxies in this version.",
            "- RunPod CARLA rendering is unblocked for DriverX scripted OOD campaigns; stock Fail2Drive long-route scoring remains a separate runtime lane.",
            "",
            "## Open Blockers",
            "",
        ]
    )
    lines.extend(f"- {blocker}" for blocker in blockers[:20]) if blockers else lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _video_script_markdown(
    policy_summary: dict[str, Any],
    hero_records: list[ScenarioCatalogRecord],
    failure_records: list[ScenarioCatalogRecord],
) -> str:
    hero_line = (
        f"3. Show hero scenario `{hero_records[0].scenario_id}` with generated assets/behavior evidence."
        if hero_records
        else "3. State that no submission-grade hero is selected yet because strict road-aligned video proof is still blocked."
    )
    failure_line = (
        f"5. Show failure case `{failure_records[0].scenario_id}`, then show VLA policy status counts: passed `{policy_summary['passed']}`, planned `{policy_summary['planned']}`, blocked `{policy_summary['blocked']}`."
        if failure_records
        else f"5. Show VLA policy status counts honestly: passed `{policy_summary['passed']}`, planned `{policy_summary['planned']}`, blocked `{policy_summary['blocked']}`; no quality-passed failure case is selected yet."
    )
    close_line = (
        "6. Close with next step: attach Alpamayo reasoning to this hero scenario, route conservative trajectory replay through CARLA, and scale the OOD generator to more regional behaviors and generated meshes."
        if hero_records
        else "6. Close with next step: produce the first quality-passed RunPod CARLA hero video, then attach Alpamayo reasoning and generated meshes."
    )
    return "\n".join(
        [
            "# 0xDriver 1-5 Minute Video Script V6",
            "",
            "1. Start with the problem: rare environments break memorized autonomy.",
            "2. Show the generator: road-relative CARLA OOD recipes, environment packs, and behavior DSL variants.",
            hero_line,
            "4. Show quality gates: road alignment, conflict, duration, video, and artifact checks.",
            failure_line,
            close_line,
            "",
        ]
    )


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _policy_summary(policy: dict[str, Any]) -> dict[str, Any]:
    evaluations = [item for item in list(policy.get("evaluations", [])) if isinstance(item, dict)]
    status_counts = dict(policy.get("status_counts", {})) if isinstance(policy.get("status_counts"), dict) else {}
    if not status_counts:
        for evaluation in evaluations:
            status = str(evaluation.get("status") or "unknown")
            status_counts[status] = int(status_counts.get(status, 0) or 0) + 1
    total = int(policy.get("evaluation_count", len(evaluations)) or len(evaluations))
    decision_artifact_count = int(policy.get("decision_artifact_count", 0) or 0)
    if decision_artifact_count == 0:
        decision_artifact_count = sum(
            1
            for evaluation in evaluations
            if dict(evaluation.get("artifacts", {})).get("policy_decision")
        )
    return {
        "total": total,
        "status_counts": dict(sorted((str(key), int(value)) for key, value in status_counts.items())),
        "passed": int(status_counts.get("passed", 0) or 0),
        "planned": int(status_counts.get("planned", 0) or 0),
        "blocked": int(status_counts.get("blocked", 0) or 0),
        "decision_artifact_count": decision_artifact_count,
    }


def _load_blockers(path: Path | None) -> list[str]:
    if path is None or not path.exists():
        return []
    return _open_blocker_items(path.read_text(encoding="utf-8").splitlines())


def _open_blocker_items(lines: list[str]) -> list[str]:
    blockers: list[str] = []
    current: list[str] = []
    in_open_section = False
    for line in lines:
        if line.startswith("## "):
            if current and in_open_section:
                blockers.append(" ".join(current).strip())
            current = []
            in_open_section = line.strip().lower() == "## open"
            continue
        if not in_open_section:
            continue
        if line.startswith("- "):
            if current:
                blockers.append(" ".join(current).strip())
            current = [line.strip("- ").strip()]
        elif current and line.startswith("  "):
            current.append(line.strip())
    if current and in_open_section:
        blockers.append(" ".join(current).strip())
    return blockers


def _status_class(status: str) -> str:
    return "ok" if status == "passed" else "warn"


def _quality_class(status: str) -> str:
    return "ok" if status == "passed" else "warn"


def _promotion_class(status: str) -> str:
    return "ok" if status in {"hero", "failure_case"} else "warn"


def _promotion_reason(record: ScenarioCatalogRecord) -> str:
    if not record.promotion.reason:
        return ""
    return f", reason={html.escape(record.promotion.reason)}"


__all__ = [
    "SubmissionBrowserInputs",
    "SubmissionBrowserOutputs",
    "build_submission_scenario_browser",
]
