"""OODrive generated scenario runtime product commands."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from driverx.core.artifacts import prepare_run_dir
from driverx.evaluation.generator_runtime_score import (
    load_generator_runtime_score_inputs,
    score_generator_runtime,
    write_generator_runtime_score,
)
from driverx.scenarios.generated_runtime import (
    GeneratorRuntimeBackend,
    build_generated_scenario_runtime_spec,
    run_generated_scenario_runtime,
)
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths, oodrive_command


def run_studio_generate_run(
    *,
    prompt: str,
    template_ids: tuple[str, ...] = (),
    behavior_ids: tuple[str, ...] = (),
    object_kinds: tuple[str, ...] = (),
    severity: int = 4,
    seed: int = 41,
    backend: str = "dry-run",
    config_path: Path = Path("configs/carla_ood_demo.local.sample.yaml"),
    output_root: Path | None = None,
    run_id: str = "oodrive-generated-runtime",
) -> StudioCommandResult:
    """Build and optionally execute a generated scenario runtime."""

    spec = build_generated_scenario_runtime_spec(
        prompt=prompt,
        template_ids=template_ids,
        behavior_ids=behavior_ids,
        object_kinds=object_kinds,
        severity=severity,
        seed=seed,
        config_path=config_path,
        output_root=output_root or Path("artifacts/runs"),
        run_id=run_id,
    )
    result = run_generated_scenario_runtime(
        spec,
        backend=cast(GeneratorRuntimeBackend, backend),
        config_path=config_path,
        output_root=Path(str(spec["run_dir"])),
        run_id=str(spec["run_id"]),
    )
    artifacts = artifact_paths(
        {
            "json_path": result["json_path"],
            "report_path": result["report_path"],
            "spec_path": spec["spec_path"],
            "spec_report_path": spec["spec_report_path"],
            "runtime_proof_path": result.get("runtime_proof", {}).get("json_path"),
            "tracks_path": result.get("runtime_proof", {}).get("tracks_path"),
        }
    )
    return StudioCommandResult(
        command="oodrive generate-run",
        run_id=str(result["run_id"]),
        status=str(result["status"]),
        artifacts=artifacts,
        next_commands=[
            oodrive_command(f"score-generator-runtime --runtime-manifest {result['json_path']} --metric-only")
        ],
        summary={
            "scenario_id": result.get("scenario_id"),
            "backend": result.get("backend"),
            "behavior_case_count": result.get("behavior_case_count"),
            "object_spawn_spec_count": result.get("object_spawn_spec_count"),
            "runtime_status": result.get("runtime_proof", {}).get("status"),
            "track_count": result.get("runtime_proof", {}).get("track_count"),
        },
        claim_boundaries=[str(item) for item in list(result.get("claim_boundaries", []))],
        blockers=[str(item) for item in list(result.get("blockers", []))],
    )


def run_studio_score_generator_runtime(
    *,
    runtime_manifest_path: Path,
    output_root: Path | None = None,
    run_id: str | None = None,
    metric_only: bool = False,
) -> StudioCommandResult:
    """Score a generated scenario runtime manifest."""

    inputs = load_generator_runtime_score_inputs(runtime_manifest_path)
    report = score_generator_runtime(inputs)
    score_id = run_id or f"{runtime_manifest_path.parent.name}-generator-runtime-score"
    run_dir = prepare_run_dir(output_root or (runtime_manifest_path.parent / "generator-runtime-scores"), score_id)
    artifacts = artifact_paths(write_generator_runtime_score(run_dir, report))
    if metric_only:
        print(f"METRIC generator_runtime_score={report.generator_runtime_score:.4f}")
        for key, value in report.components.items():
            print(f"METRIC {key}={value:.4f}")
    return StudioCommandResult(
        command="oodrive score-generator-runtime",
        run_id=run_dir.name,
        status=report.status,
        artifacts=artifacts,
        summary={
            "generator_runtime_score": report.generator_runtime_score,
            "threshold": report.threshold,
            "components": report.components,
            "recommendations": report.recommendations,
        },
        claim_boundaries=report.claim_boundaries,
        blockers=report.blockers,
    )


__all__ = ["run_studio_generate_run", "run_studio_score_generator_runtime"]
