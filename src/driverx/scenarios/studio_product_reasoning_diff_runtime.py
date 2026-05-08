"""OODrive Alpamayo reasoning diff command wrapper."""

from __future__ import annotations

from pathlib import Path

from driverx.pipeline.alpamayo_reasoning_diff import build_alpamayo_reasoning_diff
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths, oodrive_command


def run_studio_reasoning_diff(
    *,
    alpamayo_batch_path: Path,
    retrieval_ledger_paths: tuple[Path, ...] = (),
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-reasoning-diff",
) -> StudioCommandResult:
    report = build_alpamayo_reasoning_diff(
        alpamayo_batch_path,
        retrieval_ledger_paths=retrieval_ledger_paths,
        output_root=output_root,
        run_id=run_id,
    )
    artifacts = artifact_paths(report)
    return StudioCommandResult(
        command="oodrive reasoning-diff",
        run_id=run_id,
        status="passed" if int(report.get("case_count", 0)) > 0 else "blocked",
        artifacts=artifacts,
        next_commands=[
            oodrive_command(
                "evidence-panel --overlay-report artifacts/runs/task128-oodrive-live-product/demo-videos/"
                f"task131-score-gated-hero-v2/hero_demo_video.json --reasoning-diff {artifacts['json_path']}"
            )
        ],
        summary={
            "case_count": report.get("case_count"),
            "reasoning_changed_count": report.get("reasoning_changed_count"),
            "memory_case_count": report.get("memory_case_count"),
        },
        claim_boundaries=list(report.get("claim_boundaries", [])),
    )


__all__ = ["run_studio_reasoning_diff"]
