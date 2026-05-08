"""OODrive decongested reasoning panel command wrapper."""

from __future__ import annotations

from pathlib import Path

from driverx.pipeline.reasoning_evidence_panel import build_reasoning_evidence_panel
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths, oodrive_command


def run_studio_evidence_panel(
    *,
    overlay_report_path: Path,
    reasoning_diff_path: Path,
    retrieval_ledger_paths: tuple[Path, ...] = (),
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-reasoning-evidence-panel",
) -> StudioCommandResult:
    report = build_reasoning_evidence_panel(
        overlay_report_path=overlay_report_path,
        reasoning_diff_path=reasoning_diff_path,
        retrieval_ledger_paths=retrieval_ledger_paths,
        output_root=output_root,
        run_id=run_id,
    )
    artifacts = artifact_paths(report)
    return StudioCommandResult(
        command="oodrive evidence-panel",
        run_id=run_id,
        status="passed" if len(report.get("chapters", [])) >= 4 else "partial",
        artifacts=artifacts,
        next_commands=[
            oodrive_command(
                "ancestry-cards --db artifacts/runs/task141-realistic-ood-generation-v1/scenario_studio_db.json "
                "--fail2drive-report tickets/TASK-105/artifacts/fail2drive-extension-report/"
                "fail2drive_extension_report.json"
            )
        ],
        summary={
            "chapter_count": len(report.get("chapters", [])),
            "max_hud_rows": report.get("max_hud_rows"),
            "citation_count": report.get("citation_count"),
        },
        claim_boundaries=list(report.get("claim_boundaries", [])),
    )


__all__ = ["run_studio_evidence_panel"]
