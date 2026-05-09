"""Run generated vault Fail2Drive routes and capture RGB/video evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from driverx.pipeline.route_evidence import RouteEvidenceInputs, build_route_evidence
from driverx.simulators.carla import CarlaRunConfig
from driverx.simulators.fail2drive_route_runner import (
    Fail2DriveRouteRunConfig,
    run_fail2drive_route,
    write_fail2drive_route_run,
)
from driverx.simulators.fail2drive_video import (
    Fail2DriveVideoSmokeConfig,
    plan_fail2drive_video_smoke,
    write_fail2drive_video_smoke_plan,
)


def main() -> None:
    repo = Path("/workspace/0xDriver")
    manifest_path = repo / "artifacts" / "runs" / "vault-f2d-scenarios" / "vault_f2d_scenarios_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected = set(sys.argv[1:] or [case["id"] for case in manifest["cases"]])
    summaries = []
    for case in manifest["cases"]:
        if case["id"] not in selected:
            continue
        summaries.append(_run_case(repo, case))
    output_path = repo / "artifacts" / "runs" / "vault-f2d-scenarios" / "vault_f2d_render_summary.json"
    output_path.write_text(json.dumps({"cases": summaries}, indent=2), encoding="utf-8")
    print(json.dumps({"summary_path": str(output_path), "cases": summaries}, indent=2))


def _run_case(repo: Path, case: dict[str, str]) -> dict[str, object]:
    run_dir = repo / "artifacts" / "runs" / f"vault-render-{case['id']}"
    run_dir.mkdir(parents=True, exist_ok=True)
    root = Path("/workspace/fail2drive")
    route = Path(case["route_path"])
    agent = repo / "artifacts" / "agents" / "driverx_viz_basic_agent.py"
    config = Fail2DriveVideoSmokeConfig.from_carla_config(
        CarlaRunConfig(
            host="127.0.0.1",
            port=2000,
            timeout_s=180,
            carla_root=Path("/workspace/carla/CARLA_0.9.16"),
            fail2drive_root=root,
            route_path=route,
            agent_path=agent,
            output_dir=run_dir / "fail2drive_outputs",
            track="MAP",
        ),
        timeout_s=180,
        live_visu=True,
        method_name=f"OODriveVault_{case['id']}",
    )
    plan = plan_fail2drive_video_smoke(config)
    plan_summary = write_fail2drive_video_smoke_plan(run_dir, plan)
    result = run_fail2drive_route(
        Fail2DriveRouteRunConfig(
            plan_path=Path(plan_summary["json_path"]),
            run_dir=run_dir,
            timeout_s=180,
            dry_run=False,
            min_video_frames=90,
            video_fps=15,
            video_timeout_s=140,
            stop_after_video=True,
            ffmpeg_path="ffmpeg",
        )
    )
    run_summary = write_fail2drive_route_run(run_dir, result)
    evidence = build_route_evidence(
        run_dir,
        RouteEvidenceInputs(
            plan_path=Path(plan_summary["json_path"]),
            route_run_path=Path(run_summary["json_path"]),
        ),
    )
    rgb_folder = Path(plan_summary["expected_outputs"]["rgb_folder"])
    snapshots = sorted(str(path) for path in rgb_folder.glob("*.jpg"))[:6]
    return {
        "id": case["id"],
        "scenario_type": case["scenario_type"],
        "run_dir": str(run_dir),
        "plan_path": plan_summary["json_path"],
        "run_path": run_summary["json_path"],
        "evidence_path": evidence["json_path"],
        "status": run_summary["status"],
        "blockers": run_summary.get("route_blockers", []),
        "video_path": plan_summary["expected_outputs"].get("video"),
        "rgb_folder": str(rgb_folder),
        "snapshots": snapshots,
    }


if __name__ == "__main__":
    main()
