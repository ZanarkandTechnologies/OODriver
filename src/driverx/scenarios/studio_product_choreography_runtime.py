"""OODrive product runtime for scenario choreography."""

from __future__ import annotations

from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.evaluation.scenario_choreography_score import (
    load_scenario_choreography_score_inputs,
    score_scenario_choreography,
    write_scenario_choreography_score,
)
from driverx.scenarios.choreography import build_choreography_plan
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths, oodrive_command


def run_studio_choreograph(
    *,
    prompt: str,
    case_ids: tuple[str, ...] = (),
    behavior_ids: tuple[str, ...] = (),
    object_kinds: tuple[str, ...] = (),
    template_ids: tuple[str, ...] = ("construction_lane_closure",),
    seed: int = 41,
    severity: int = 4,
    output_root: Path | None = None,
    run_id: str = "oodrive-choreography",
) -> StudioCommandResult:
    """Build a timed actor/object choreography manifest."""

    manifest = build_choreography_plan(
        prompt,
        case_ids=case_ids,
        behavior_ids=behavior_ids,
        object_kinds=object_kinds,
        template_ids=template_ids,
        seed=seed,
        severity=severity,
        output_root=output_root or Path("artifacts/runs"),
        run_id=run_id,
    )
    return StudioCommandResult(
        command="oodrive choreograph",
        run_id=str(manifest["run_id"]),
        status=str(manifest["status"]),
        artifacts=artifact_paths(
            {
                "choreography_manifest_path": manifest["json_path"],
                "choreography_report_path": manifest["report_path"],
                "tracks_path": manifest["proof"]["tracks_path"],
            }
        ),
        next_commands=[str(item) for item in list(manifest.get("next_commands", []))],
        summary={
            "case_count": manifest["case_count"],
            "actor_count": len(list(manifest.get("actors", []))),
            "object_count": len(list(manifest.get("objects", []))),
            "trigger_count": len(list(manifest.get("triggers", []))),
            "entity_track_count": manifest["proof"]["entity_track_count"],
            "expected_responses": manifest["expected_responses"],
        },
        claim_boundaries=[str(item) for item in list(manifest.get("claim_boundaries", []))],
        blockers=[],
    )


def run_studio_score_choreography(
    *,
    choreography_manifest_path: Path,
    output_root: Path | None = None,
    run_id: str | None = None,
) -> StudioCommandResult:
    """Score a scenario choreography manifest."""

    inputs = load_scenario_choreography_score_inputs(choreography_manifest_path)
    report = score_scenario_choreography(inputs)
    score_id = run_id or f"{choreography_manifest_path.parent.name}-choreography-score"
    run_dir = prepare_run_dir(output_root or (choreography_manifest_path.parent / "choreography-scores"), score_id)
    artifacts = artifact_paths(write_scenario_choreography_score(run_dir, report))
    return StudioCommandResult(
        command="oodrive score-choreography",
        run_id=run_dir.name,
        status=report.status,
        artifacts=artifacts,
        next_commands=[oodrive_command(f"choreograph-video --choreography-manifest {choreography_manifest_path} --backend carla-live")],
        summary={
            "scenario_choreography_score": report.scenario_choreography_score,
            "threshold": report.threshold,
            "components": report.components,
            "recommendations": report.recommendations,
        },
        claim_boundaries=report.claim_boundaries,
        blockers=report.blockers,
    )


__all__ = ["run_studio_choreograph", "run_studio_score_choreography"]
