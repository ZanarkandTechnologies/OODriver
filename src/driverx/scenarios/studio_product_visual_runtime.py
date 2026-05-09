"""OODrive visual-fidelity scoring runtime wrappers."""

from __future__ import annotations

from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.evaluation.visual_fidelity_score import score_visual_fidelity, write_visual_fidelity_score
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths


def run_studio_score_visual_fidelity(
    *,
    media_manifest_path: Path,
    output_root: Path | None = None,
    run_id: str = "oodrive-visual-fidelity-score",
    threshold: float = 90.0,
    metric_only: bool = False,
) -> StudioCommandResult:
    report = score_visual_fidelity(media_manifest_path, threshold=threshold)
    run_dir = prepare_run_dir(output_root or Path("artifacts/runs"), run_id)
    artifacts = artifact_paths(write_visual_fidelity_score(run_dir, report))
    if metric_only:
        print(f"METRIC visual_fidelity_score={report.visual_fidelity_score:.4f}")
        for key, value in report.components.items():
            print(f"METRIC {key}={value:.4f}")
    return StudioCommandResult(
        command="oodrive score-visual-fidelity",
        run_id=run_dir.name,
        status=report.status,
        artifacts=artifacts,
        summary={
            "visual_fidelity_score": report.visual_fidelity_score,
            "threshold": report.threshold,
            "components": report.components,
            "recommendations": report.recommendations,
        },
        claim_boundaries=report.claim_boundaries,
        blockers=report.blockers,
    )


__all__ = ["run_studio_score_visual_fidelity"]
