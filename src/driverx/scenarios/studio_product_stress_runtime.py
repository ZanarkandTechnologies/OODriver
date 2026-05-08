"""OODrive bad-path stress demo runtime command."""

from __future__ import annotations

from pathlib import Path

from driverx.pipeline.bad_path_stress_demo import DEFAULT_CASE_IDS, build_bad_path_stress_demo
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths


def run_studio_stress_demo(
    *,
    output_root: Path | None = None,
    run_id: str = "oodrive-bad-path-stress-demo",
    case_ids: tuple[str, ...] = DEFAULT_CASE_IDS,
    target_duration_s: float = 60.0,
    fps: int = 8,
) -> StudioCommandResult:
    """Build the bad-path stress demo pack."""

    output = build_bad_path_stress_demo(
        output_root=output_root or Path("artifacts/runs"),
        run_id=run_id,
        case_ids=case_ids,
        target_duration_s=target_duration_s,
        fps=fps,
    )
    return StudioCommandResult(
        command="oodrive stress-demo",
        run_id=str(output["run_id"]),
        status=str(output["status"]),
        artifacts=artifact_paths(output),
        summary={
            "case_count": output["case_count"],
            "bad_path_stress_score": output["bad_path_stress_score"],
            "video_status": output.get("video_render", {}).get("status"),
            "video_path": output.get("video_path"),
        },
        claim_boundaries=[str(item) for item in list(output.get("claim_boundaries", []))],
        blockers=[str(item) for item in list(output.get("blockers", []))],
    )


__all__ = ["run_studio_stress_demo"]
