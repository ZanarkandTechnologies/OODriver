"""OODrive environment-to-reasoned-CARLA video runtime commands."""

from __future__ import annotations

from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.pipeline.environment_reasoned_carla_video import build_environment_reasoned_carla_video
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths


def run_studio_env_demo_video(
    *,
    environment_summary_path: Path,
    visual_proof_path: Path,
    keyframe_analysis_path: Path,
    output_root: Path | None = None,
    run_id: str = "environment-reasoned-carla-demo",
    target_duration_s: float = 120.0,
) -> StudioCommandResult:
    output = build_environment_reasoned_carla_video(
        environment_summary_path=environment_summary_path,
        visual_proof_path=visual_proof_path,
        keyframe_analysis_path=keyframe_analysis_path,
        output_root=output_root or Path("artifacts/runs"),
        run_id=run_id,
        target_duration_s=target_duration_s,
    )
    return StudioCommandResult(
        command="oodrive env-demo-video",
        run_id=Path(str(output["overlay_report_path"])).parent.name,
        status=str(output["status"]),
        artifacts=artifact_paths(output),
        next_commands=[str(command) for command in list(output.get("next_commands", []))],
        summary={
            "duration_s": output["duration_s"],
            "segment_count": len(list(output.get("timeline_segments", []))),
            "same_lineage": output["source_lineage"]["same_lineage"],
            "video_path": output["video_path"],
        },
        claim_boundaries=[str(item) for item in list(output.get("claim_boundaries", []))],
        blockers=[str(item) for item in list(output.get("blockers", []))],
    )


def run_studio_score_env_proof(
    *,
    environment_summary_path: Path,
    visual_proof_path: Path,
    keyframe_analysis_path: Path,
    overlay_report_path: Path | None = None,
    video_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str = "environment-reasoned-carla-score",
    metric_only: bool = False,
) -> StudioCommandResult:
    from driverx.evaluation.environment_reasoned_carla_score import (
        score_environment_reasoned_carla,
        write_environment_reasoned_carla_score,
    )

    report = score_environment_reasoned_carla(
        environment_summary_path=environment_summary_path,
        visual_proof_path=visual_proof_path,
        keyframe_analysis_path=keyframe_analysis_path,
        overlay_report_path=overlay_report_path,
        video_path=video_path,
    )
    run_dir = prepare_run_dir(output_root or Path("artifacts/runs"), run_id)
    output = write_environment_reasoned_carla_score(run_dir, report)
    if metric_only:
        print(f"METRIC environment_to_reasoned_carla_score={report.environment_to_reasoned_carla_score:.4f}")
        for key, value in report.components.items():
            print(f"METRIC {key}={value:.4f}")
    return StudioCommandResult(
        command="oodrive score-env-proof",
        run_id=run_dir.name,
        status=report.status,
        artifacts=artifact_paths(output),
        summary={
            "environment_to_reasoned_carla_score": report.environment_to_reasoned_carla_score,
            "threshold": report.threshold,
            "components": report.components,
        },
        claim_boundaries=report.claim_boundaries,
        blockers=report.blockers,
    )


__all__ = ["run_studio_env_demo_video", "run_studio_score_env_proof"]
