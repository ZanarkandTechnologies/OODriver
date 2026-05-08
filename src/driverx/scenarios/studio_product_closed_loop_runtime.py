"""OODrive closed-loop Alpamayo/CARLA product command wrappers."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from driverx.core.artifacts import prepare_run_dir
from driverx.evaluation.closed_loop_control_score import (
    score_closed_loop_control,
    write_closed_loop_control_score,
)
from driverx.evaluation.closed_loop_integration_score import (
    score_closed_loop_integration,
    write_closed_loop_integration_score,
)
from driverx.evaluation.closed_loop_video_score import (
    score_closed_loop_video,
    write_closed_loop_video_score,
)
from driverx.pipeline.closed_loop_video import ClosedLoopVideoInputs, build_closed_loop_video
from driverx.policies.alpamayo_inference_bridge import (
    InferenceMode,
    run_alpamayo_inference_bridge,
    write_alpamayo_inference_result,
)
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths, oodrive_command
from driverx.simulators.carla_closed_loop_runner import (
    ClosedLoopBackend,
    ClosedLoopPolicy,
    PausedClosedLoopConfig,
    run_paused_closed_loop,
)


def run_studio_closed_loop_run(
    *,
    db_path: Path | None = None,
    scenario_id: str | None = None,
    backend: str = "fake-carla",
    policy: str = "fake-trajectory",
    output_root: Path | None = None,
    run_id: str = "oodrive-closed-loop-run",
    steps: int = 3,
    control_ticks_per_step: int = 4,
    host: str = "127.0.0.1",
    port: int = 2000,
    timeout_s: float = 45.0,
    town: str | None = None,
    map_name: str | None = None,
    load_map: bool = False,
    weather_preset: str | None = None,
    camera_width: int = 640,
    camera_height: int = 360,
    camera_fov: float = 90.0,
    cache_root: Path | None = None,
    remote_output_root: str | None = None,
    alpamayo_python: Path | None = None,
    alpamayo_command: str | None = None,
) -> StudioCommandResult:
    run_dir = prepare_run_dir(output_root or Path("artifacts/runs"), run_id)
    trace = run_paused_closed_loop(
        PausedClosedLoopConfig(
            backend=cast(ClosedLoopBackend, backend),
            policy=cast(ClosedLoopPolicy, policy),
            steps=steps,
            control_ticks_per_step=control_ticks_per_step,
            run_id=run_dir.name,
            scenario_id=scenario_id or "fake-static-blocker",
            host=host,
            port=port,
            timeout_s=timeout_s,
            town=town,
            map_name=map_name,
            load_map=load_map,
            weather_preset=weather_preset,
            camera_width=camera_width,
            camera_height=camera_height,
            camera_fov=camera_fov,
            cache_root=cache_root,
            remote_output_root=remote_output_root,
            alpamayo_python=alpamayo_python,
            alpamayo_command=alpamayo_command,
        ),
        run_dir,
    )
    artifacts = artifact_paths({"trace_path": trace["json_path"], "report_path": trace["report_path"]})
    if db_path is not None:
        artifacts["db_path"] = str(db_path)
    return StudioCommandResult(
        command="oodrive closed-loop-run",
        run_id=run_dir.name,
        status="passed" if not trace.get("blockers") else "blocked",
        artifacts=artifacts,
        next_commands=[
            oodrive_command(f"score-closed-loop --trace {trace['json_path']} --metric-only"),
            oodrive_command(f"score-closed-loop-integration --trace {trace['json_path']} --metric-only"),
            oodrive_command(f"closed-loop-video --trace {trace['json_path']} --run-id {run_dir.name}-video"),
        ],
        summary={
            "mode": trace.get("mode"),
            "backend": trace.get("backend"),
            "policy": trace.get("policy"),
            "step_count": len(list(trace.get("steps", []))),
            "control_applied_count": trace.get("control_applied_count"),
        },
        claim_boundaries=[str(item) for item in list(trace.get("claim_boundaries", []))],
        blockers=[str(item) for item in list(trace.get("blockers", []))],
    )


def run_studio_score_closed_loop(
    *,
    trace_path: Path,
    output_root: Path | None = None,
    run_id: str | None = None,
    metric_only: bool = False,
) -> StudioCommandResult:
    report = score_closed_loop_control(trace_path)
    score_id = run_id or f"{trace_path.parent.name}-closed-loop-score"
    run_dir = prepare_run_dir(output_root or (trace_path.parent / "closed-loop-scores"), score_id)
    artifacts = artifact_paths(write_closed_loop_control_score(run_dir, report))
    if metric_only:
        print(f"METRIC closed_loop_score={report.closed_loop_score:.4f}")
        for key, value in report.components.items():
            print(f"METRIC {key}={value:.4f}")
    return StudioCommandResult(
        command="oodrive score-closed-loop",
        run_id=run_dir.name,
        status=report.status,
        artifacts=artifacts,
        summary={"closed_loop_score": report.closed_loop_score, "threshold": report.threshold, "components": report.components},
        claim_boundaries=report.claim_boundaries,
        blockers=report.blockers,
    )


def run_studio_infer(
    *,
    package_path: Path,
    mode: str,
    output_root: Path | None = None,
    run_id: str = "oodrive-infer",
    prediction_json: Path | None = None,
    cache_root: Path | None = None,
    remote_output_root: str | None = None,
    alpamayo_python: Path | None = None,
    alpamayo_command: str | None = None,
    timeout_s: float = 180.0,
    retries: int = 0,
) -> StudioCommandResult:
    run_dir = prepare_run_dir(output_root or Path("artifacts/runs"), run_id)
    result = run_alpamayo_inference_bridge(
        package_path=package_path,
        mode=cast(InferenceMode, mode),
        output_root=run_dir.parent,
        run_id=run_dir.name,
        prediction_json=prediction_json,
        cache_root=cache_root,
        remote_output_root=remote_output_root,
        alpamayo_python=alpamayo_python,
        alpamayo_command=alpamayo_command,
        timeout_s=timeout_s,
        retries=retries,
    )
    artifacts = artifact_paths(write_alpamayo_inference_result(run_dir, result))
    return StudioCommandResult(
        command="oodrive infer",
        run_id=run_dir.name,
        status=result.status,
        artifacts=artifacts,
        summary={
            "mode": result.mode,
            "cache_key": result.cache_key,
            "latency_ms": result.latency_ms,
            "prediction_json_path": result.prediction_json_path,
        },
        claim_boundaries=result.claim_boundaries,
        blockers=result.blockers,
    )


def run_studio_score_closed_loop_integration(
    *,
    trace_path: Path,
    output_root: Path | None = None,
    run_id: str | None = None,
    metric_only: bool = False,
) -> StudioCommandResult:
    report = score_closed_loop_integration(trace_path)
    score_id = run_id or f"{trace_path.parent.name}-closed-loop-integration-score"
    run_dir = prepare_run_dir(output_root or (trace_path.parent / "closed-loop-integration-scores"), score_id)
    artifacts = artifact_paths(write_closed_loop_integration_score(run_dir, report))
    if metric_only:
        print(f"METRIC closed_loop_integration_score={report.closed_loop_integration_score:.4f}")
        for key, value in report.subscores.items():
            print(f"METRIC {key}={value:.4f}")
    return StudioCommandResult(
        command="oodrive score-closed-loop-integration",
        run_id=run_dir.name,
        status=report.status,
        artifacts=artifacts,
        summary={
            "closed_loop_integration_score": report.closed_loop_integration_score,
            "threshold": report.threshold,
            "subscores": report.subscores,
        },
        claim_boundaries=[],
        blockers=report.blockers,
    )


def run_studio_closed_loop_video(
    *,
    trace_path: Path,
    rgb_folder: Path | None = None,
    source_video: Path | None = None,
    scenario_pack: Path | None = None,
    output_video: Path | None = None,
    output_root: Path | None = None,
    run_id: str = "closed-loop-video",
    fps: int = 24,
    duration_s: float = 0.0,
) -> StudioCommandResult:
    result = build_closed_loop_video(
        ClosedLoopVideoInputs(
            trace_path=trace_path,
            rgb_folder=rgb_folder,
            source_video=source_video,
            scenario_pack=scenario_pack,
            output_video=output_video,
            output_root=output_root,
            run_id=run_id,
            fps=fps,
            duration_s=duration_s,
        )
    )
    artifacts = artifact_paths(
        {
            "video_path": result.video_path,
            "manifest_path": result.manifest_path,
            "sample_frame_paths": list(result.sample_frame_paths),
        }
    )
    next_commands = []
    if result.video_path:
        next_commands.append(
            oodrive_command(
                f"score-closed-loop-video --trace {trace_path} --manifest {result.manifest_path} --video {result.video_path} --metric-only"
            )
        )
    return StudioCommandResult(
        command="oodrive closed-loop-video",
        run_id=run_id,
        status=result.status,
        artifacts=artifacts,
        next_commands=next_commands,
        summary={
            "frame_count": result.frame_count,
            "duration_s": result.duration_s,
            "sample_frame_count": len(result.sample_frame_paths),
        },
        claim_boundaries=list(result.claim_boundaries),
        blockers=list(result.blockers),
    )


def run_studio_score_closed_loop_video(
    *,
    trace_path: Path,
    manifest_path: Path | None = None,
    video_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
    metric_only: bool = False,
) -> StudioCommandResult:
    report = score_closed_loop_video(trace_path=trace_path, manifest_path=manifest_path, video_path=video_path)
    score_id = run_id or f"{trace_path.parent.name}-closed-loop-video-score"
    run_dir = prepare_run_dir(output_root or (trace_path.parent / "closed-loop-video-scores"), score_id)
    artifacts = artifact_paths(write_closed_loop_video_score(run_dir, report))
    if metric_only:
        print(f"METRIC closed_loop_video_score={report.closed_loop_video_score:.4f}")
        for key, value in report.components.items():
            print(f"METRIC {key}={value:.4f}")
    return StudioCommandResult(
        command="oodrive score-closed-loop-video",
        run_id=run_dir.name,
        status=report.status,
        artifacts=artifacts,
        summary={
            "closed_loop_video_score": report.closed_loop_video_score,
            "threshold": report.threshold,
            "components": report.components,
        },
        claim_boundaries=[],
        blockers=report.blockers,
    )


__all__ = [
    "run_studio_closed_loop_video",
    "run_studio_closed_loop_run",
    "run_studio_infer",
    "run_studio_score_closed_loop",
    "run_studio_score_closed_loop_integration",
    "run_studio_score_closed_loop_video",
]
