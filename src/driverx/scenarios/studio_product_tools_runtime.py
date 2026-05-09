"""OODrive tool-manifest and artifact-index product wrappers."""

from __future__ import annotations

from pathlib import Path

from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths
from driverx.tools.artifact_index import build_and_write_artifact_index
from driverx.tools.oodrive_manifest import build_and_write_tools_manifest


def run_studio_tools_manifest(
    *,
    output_root: Path | None = None,
    run_id: str = "oodrive-tools-manifest",
    include_experimental: bool = True,
) -> StudioCommandResult:
    payload = build_and_write_tools_manifest(output_root, run_id, include_experimental=include_experimental)
    return StudioCommandResult(
        command="oodrive tools-manifest",
        run_id=Path(str(payload["json_path"])).parent.name,
        status="passed",
        artifacts=artifact_paths(payload),
        summary={"tool_count": len(list(payload.get("tools", [])))},
        claim_boundaries=[str(item) for item in list(payload.get("claim_boundaries", []))],
    )


def run_studio_artifacts_list(
    *,
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-artifacts-index",
    limit: int = 50,
) -> StudioCommandResult:
    payload = build_and_write_artifact_index(output_root, run_id, limit=limit)
    return StudioCommandResult(
        command="oodrive artifacts-list",
        run_id=Path(str(payload["json_path"])).parent.name,
        status="passed",
        artifacts=artifact_paths(payload),
        summary={"artifact_count": payload.get("artifact_count", 0), "output_root": str(output_root)},
        claim_boundaries=["artifact_index_only=true"],
    )


__all__ = ["run_studio_artifacts_list", "run_studio_tools_manifest"]
