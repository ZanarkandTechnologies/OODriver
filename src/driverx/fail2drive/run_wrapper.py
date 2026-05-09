"""OODrive wrapper around Fail2Drive route evaluator planning and evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.fail2drive.catalog import load_fail2drive_catalog
from driverx.fail2drive.route_validation import validate_fail2drive_route, write_fail2drive_route_validation
from driverx.pipeline.route_evidence import RouteEvidenceInputs, build_route_evidence
from driverx.simulators.carla import CarlaRunConfig
from driverx.simulators.fail2drive_route_runner import Fail2DriveRouteRunConfig, run_fail2drive_route, write_fail2drive_route_run
from driverx.simulators.fail2drive_video import Fail2DriveVideoSmokeConfig, plan_fail2drive_video_smoke, write_fail2drive_video_smoke_plan


@dataclass(frozen=True)
class Fail2DriveRouteRunRequest:
    route_path: Path
    fail2drive_root: Path
    output_root: Path
    run_id: str
    agent_kind: str = "pdm-lite"
    agent_path: Path | None = None
    agent_config: Path | None = None
    host: str = "127.0.0.1"
    port: int = 2000
    track: str = "MAP"
    live: bool = False
    timeout_s: float = 120.0
    skip_validate: bool = False


def run_fail2drive_route_workflow(request: Fail2DriveRouteRunRequest) -> dict[str, Any]:
    run_dir = prepare_run_dir(request.output_root, request.run_id)
    root = request.fail2drive_root.expanduser().resolve()
    route_path = _resolve_under(root, request.route_path).resolve()
    agent_path = _resolve_agent(root, request.agent_kind, request.agent_path)
    validation_summary = None
    if not request.skip_validate:
        catalog = load_fail2drive_catalog(root)
        validation = validate_fail2drive_route(route_path, catalog)
        validation_summary = write_fail2drive_route_validation(run_dir, validation)
    config = Fail2DriveVideoSmokeConfig.from_carla_config(
        CarlaRunConfig(
            host=request.host,
            port=request.port,
            timeout_s=request.timeout_s,
            carla_root=None,
            fail2drive_root=root,
            route_path=route_path,
            agent_path=agent_path,
            output_dir=run_dir / "fail2drive_outputs",
            track=request.track,
        ),
        agent_config=request.agent_config,
        timeout_s=request.timeout_s,
        live_visu=True,
        method_name="OODriveFail2Drive",
    )
    plan = plan_fail2drive_video_smoke(config)
    plan_summary = write_fail2drive_video_smoke_plan(run_dir, plan)
    route_run_summary = None
    if request.live:
        route_run = run_fail2drive_route(
            Fail2DriveRouteRunConfig(
                plan_path=Path(plan_summary["json_path"]),
                run_dir=run_dir,
                timeout_s=request.timeout_s,
                dry_run=False,
            )
        )
        route_run_summary = write_fail2drive_route_run(run_dir, route_run)
    evidence = build_route_evidence(
        run_dir,
        RouteEvidenceInputs(
            plan_path=Path(plan_summary["json_path"]),
            route_run_path=Path(route_run_summary["json_path"]) if route_run_summary else None,
        ),
    )
    status = "blocked" if plan.live_blockers or (validation_summary and not validation_summary.get("ok")) else "planned"
    if request.live and route_run_summary and route_run_summary.get("status") == "passed":
        status = "passed"
    payload = {
        "schema_version": "oodrive.fail2drive_route_run_workflow.v1",
        "status": status,
        "route_path": str(route_path),
        "agent_path": str(agent_path),
        "agent_kind": request.agent_kind,
        "plan": plan_summary,
        "validation": validation_summary,
        "route_run": route_run_summary,
        "evidence": evidence,
        "blockers": _dedupe([*plan.live_blockers, *_evidence_blockers(evidence)]),
        "claim_boundaries": [
            "fail2drive_evaluator_is_upstream=true",
            f"live_carla_execution={str(request.live).lower()}",
            "closed_loop_vla_control=false_unless_agent_outputs_drive_controls",
        ],
    }
    json_path = run_dir / "fail2drive_route_run_workflow.json"
    report_path = run_dir / "fail2drive_route_run_workflow.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path), "run_dir": str(run_dir)}


def _resolve_under(root: Path, path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_absolute():
        return expanded
    if expanded.exists():
        return expanded
    return root / expanded


def _resolve_agent(root: Path, agent_kind: str, explicit: Path | None) -> Path:
    if explicit is not None:
        return _resolve_under(root, explicit)
    if agent_kind == "human":
        return root / "leaderboard" / "leaderboard" / "autoagents" / "human_agent_keyboard.py"
    if agent_kind == "transfuser":
        return root / "team_code" / "sensor_agent.py"
    return root / "team_code" / "visu_agent.py"


def _evidence_blockers(evidence: dict[str, Any]) -> list[str]:
    blockers = evidence.get("blockers")
    return [str(item) for item in blockers] if isinstance(blockers, list) else []


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Fail2Drive Route Run Workflow",
        "",
        f"- status: {payload.get('status')}",
        f"- route: `{payload.get('route_path')}`",
        f"- agent: `{payload.get('agent_path')}`",
        "",
    ]
    for blocker in payload.get("blockers", []):
        lines.append(f"- blocker: {blocker}")
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["Fail2DriveRouteRunRequest", "run_fail2drive_route_workflow"]
