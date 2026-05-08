"""OODrive keyframe analysis runtime commands."""

from __future__ import annotations

from pathlib import Path

from driverx.pipeline.keyframe_analysis import build_keyframe_analysis
from driverx.scenarios.studio_product import StudioCommandResult


def run_studio_analyze_keyframes(
    *,
    visual_proof_path: Path,
    db_path: Path,
    run_manifest_path: Path,
    backend: str = "fake",
    keyframe_count: int = 8,
    output_root: Path | None = None,
    run_id: str = "oodrive-keyframe-analysis",
) -> StudioCommandResult:
    """Analyze CARLA keyframes using fake, blocked, or Alpamayo-local backend modes."""

    output = build_keyframe_analysis(
        visual_proof_path=visual_proof_path,
        db_path=db_path,
        run_manifest_path=run_manifest_path,
        backend=backend,
        keyframe_count=keyframe_count,
        output_root=output_root or Path("artifacts/runs"),
        run_id=run_id,
    )
    return StudioCommandResult(
        command="oodrive analyze-keyframes",
        run_id=Path(str(output["json_path"])).parent.name,
        status=str(output["status"]),
        artifacts={
            "keyframe_analysis_path": str(output["json_path"]),
            "keyframe_analysis_report_path": str(output["report_path"]),
            "commands_path": str(output["commands_path"]),
        },
        next_commands=[str(command) for command in list(output.get("next_commands", []))],
        summary={
            "backend": output["backend"],
            "same_lineage": output["same_lineage"],
            "keyframe_count": output["keyframe_count"],
            "reasoned_keyframe_count": output["reasoned_keyframe_count"],
            "blocked_keyframe_count": output["blocked_keyframe_count"],
            "model_evidence": output["model_evidence"],
        },
        claim_boundaries=[str(item) for item in list(output.get("claim_boundaries", []))],
        blockers=[str(item) for item in list(output.get("blockers", []))],
    )


__all__ = ["run_studio_analyze_keyframes"]
