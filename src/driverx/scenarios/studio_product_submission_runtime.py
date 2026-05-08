"""OODrive submission scoring and pack export runtime commands."""

from __future__ import annotations

from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.scenarios.studio_db import (
    append_command,
    load_studio_db,
    replace_db,
    write_studio_db,
)
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths, load_or_latest_run, oodrive_command


def run_studio_score_submission(
    db_path: Path | None = None,
    *,
    run_manifest_path: Path | None = None,
    evaluation_path: Path | None = None,
    hero_score_path: Path | None = None,
    overlay_report_path: Path | None = None,
    pack_manifest_path: Path | None = None,
    checks_report_path: Path | None = None,
    score_input_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
    metric_only: bool = False,
) -> StudioCommandResult:
    """Score OODrive's commission-readiness across evidence surfaces."""

    from driverx.evaluation.submission_readiness_score import (
        load_submission_readiness_inputs,
        score_submission_readiness,
        write_submission_readiness_score,
    )

    if db_path is None and score_input_path is None:
        raise ValueError("Pass either --db or --score-input.")
    db = load_studio_db(db_path) if db_path is not None and db_path.exists() else None
    run_payload = load_or_latest_run(db, run_manifest_path) if db is not None and score_input_path is None else {}
    resolved_run_manifest_path = run_manifest_path or _json_path_from_payload(run_payload)
    score_id = run_id or (
        f"{score_input_path.stem}-readiness"
        if score_input_path is not None
        else f"{run_payload.get('scenario_id', 'submission')}-readiness"
    )
    run_dir = prepare_run_dir(
        output_root or ((db_path.parent / "submission-scores") if db_path else Path("artifacts/runs")),
        score_id,
    )
    inputs = load_submission_readiness_inputs(
        db_path=db_path,
        run_manifest_path=resolved_run_manifest_path,
        evaluation_path=evaluation_path,
        hero_score_path=hero_score_path,
        overlay_report_path=overlay_report_path,
        pack_manifest_path=pack_manifest_path,
        checks_report_path=checks_report_path,
        score_input_path=score_input_path,
    )
    report = score_submission_readiness(inputs)
    artifacts = artifact_paths(write_submission_readiness_score(run_dir, report))
    if metric_only:
        print(f"METRIC submission_readiness_score={report.submission_readiness_score:.4f}")
        for key in (
            "hero_demo_score",
            "challenge_adherence",
            "minimal_shot_simulation_environment",
            "judge_comprehension_pack",
            "operator_reproducibility",
            "code_quality",
        ):
            value = report.metrics.get(key) if key == "hero_demo_score" else report.components.get(key)
            if isinstance(value, (float, int)):
                print(f"METRIC {key}={float(value):.4f}")
    if db is not None and db_path is not None:
        db = replace_db(
            db,
            artifacts={**db.artifacts, **artifacts},
            claim_boundaries=sorted(
                set(
                    [
                        *db.claim_boundaries,
                        "sota_commission_readiness_score_required_for_promotion=true",
                        "submission_readiness_score_is_internal_not_official_driving_score=true",
                    ]
                )
            ),
        )
        db = append_command(
            db,
            command="oodrive score-submission",
            status=report.status,
            artifacts=artifacts,
            summary={
                "submission_readiness_score": report.submission_readiness_score,
                "threshold": report.threshold,
                "blocker_count": len(report.blockers),
                "component_count": len(report.components),
            },
        )
        artifacts = {**artifact_paths(write_studio_db(db_path, db)), **artifacts}
        claim_boundaries = db.claim_boundaries
        command_run_id = db.run_id
    else:
        claim_boundaries = report.claim_boundaries
        command_run_id = score_id
    next_commands = []
    if report.status != "passed" and db_path is not None:
        next_commands.append(oodrive_command(f"export --db {db_path}"))
    return StudioCommandResult(
        command="oodrive score-submission",
        run_id=command_run_id,
        status=report.status,
        artifacts=artifacts,
        next_commands=next_commands,
        summary={
            "submission_readiness_score": report.submission_readiness_score,
            "threshold": report.threshold,
            "components": report.components,
            "recommendations": report.recommendations,
        },
        claim_boundaries=claim_boundaries,
        blockers=report.blockers,
    )


def run_studio_export_submission(
    db_path: Path,
    *,
    run_manifest_path: Path,
    evaluation_path: Path,
    hero_video_path: Path,
    hero_score_path: Path,
    readiness_score_path: Path | None = None,
    environment_demo_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
) -> StudioCommandResult:
    """Build a judge-facing SoTA Commission submission pack."""

    from driverx.pipeline.submission_story_pack import build_submission_story_pack

    db = load_studio_db(db_path)
    pack_id = run_id or f"{db.run_id}-submission-pack"
    pack = build_submission_story_pack(
        db_path=db_path,
        run_manifest_path=run_manifest_path,
        evaluation_path=evaluation_path,
        hero_video_path=hero_video_path,
        hero_score_path=hero_score_path,
        readiness_score_path=readiness_score_path,
        environment_demo_path=environment_demo_path,
        output_root=output_root or (db_path.parent / "submission-packs"),
        run_id=pack_id,
    )
    artifacts = {
        "submission_pack_index_path": str(pack["index_html_path"]),
        "submission_pack_readme_path": str(pack["readme_path"]),
        "submission_pack_manifest_path": str(pack["submission_manifest_path"]),
        "submission_pack_claim_matrix_path": str(pack["claim_matrix_path"]),
        "submission_pack_commands_path": str(pack["commands_path"]),
        "submission_pack_artifact_inventory_path": str(pack["artifact_inventory_path"]),
        "submission_pack_scorecard_path": str(pack["scorecard_path"]),
    }
    if environment_demo_path is not None:
        artifacts["environment_demo_manifest_path"] = str(environment_demo_path)
    db = replace_db(
        db,
        artifacts={**db.artifacts, **artifacts},
        claim_boundaries=sorted(
            set(
                [
                    *db.claim_boundaries,
                    "sota_commission_submission_pack=true",
                    "closed_loop_vla_control=false",
                    "real_time_vla_control=false",
                    "sampled_open_loop_reasoning=true",
                    "time_warped_offline_demo=true",
                ]
            )
        ),
    )
    db = append_command(
        db,
        command="oodrive export-submission",
        status="passed",
        artifacts=artifacts,
        summary={
            "pack_id": pack["pack_id"],
            "claim_matrix_rows": len(pack["claim_matrix"]),
            "section_count": len(pack["sections"]),
            "failure_case_count": len(pack["failure_cases"]),
        },
    )
    db_artifacts = artifact_paths(write_studio_db(db_path, db))
    score_command = oodrive_command(
        f"score-submission --db {db_path} --run {run_manifest_path} --evaluation {evaluation_path} "
        f"--hero-score {hero_score_path} --pack-manifest {pack['submission_manifest_path']}"
    )
    return StudioCommandResult(
        command="oodrive export-submission",
        run_id=db.run_id,
        status="passed",
        artifacts={**db_artifacts, **artifacts},
        next_commands=[score_command],
        summary={
            "pack_id": pack["pack_id"],
            "index_html_path": pack["index_html_path"],
            "submission_manifest_path": pack["submission_manifest_path"],
            "claim_matrix_rows": len(pack["claim_matrix"]),
            "section_count": len(pack["sections"]),
            "failure_case_count": len(pack["failure_cases"]),
        },
        claim_boundaries=db.claim_boundaries,
    )


def _json_path_from_payload(payload: dict[str, object]) -> Path | None:
    value = payload.get("json_path")
    return Path(value) if isinstance(value, str) and value else None


__all__ = ["run_studio_export_submission", "run_studio_score_submission"]
