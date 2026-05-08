"""OODrive scenario ancestry cards command wrapper."""

from __future__ import annotations

from pathlib import Path

from driverx.pipeline.scenario_ancestry_cards import build_scenario_ancestry_cards
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths


def run_studio_ancestry_cards(
    db_path: Path,
    *,
    fail2drive_report_path: Path,
    retrieval_ledger_paths: tuple[Path, ...] = (),
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-scenario-ancestry-cards",
    limit: int = 8,
) -> StudioCommandResult:
    report = build_scenario_ancestry_cards(
        db_path=db_path,
        fail2drive_report_path=fail2drive_report_path,
        retrieval_ledger_paths=retrieval_ledger_paths,
        output_root=output_root,
        run_id=run_id,
        limit=limit,
    )
    return StudioCommandResult(
        command="oodrive ancestry-cards",
        run_id=run_id,
        status="passed" if int(report.get("card_count", 0)) >= 4 else "partial",
        artifacts=artifact_paths(report),
        next_commands=[],
        summary={"card_count": report.get("card_count")},
        claim_boundaries=list(report.get("claim_boundaries", [])),
    )


__all__ = ["run_studio_ancestry_cards"]
