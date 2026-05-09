"""ASAM OpenSCENARIO 2.0 validation and ScenarioRunner handoff helpers."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir

OSC2_SCHEMA_VERSION = "oodrive.openscenario2.v1"


@dataclass(frozen=True)
class OpenScenario2Validation:
    status: str
    osc_path: str
    sidecar_path: str | None = None
    coverage_ratio: float = 0.0
    supported_features: list[str] = field(default_factory=list)
    unsupported_features: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": OSC2_SCHEMA_VERSION,
            "status": self.status,
            "osc_path": self.osc_path,
            "sidecar_path": self.sidecar_path,
            "coverage_ratio": self.coverage_ratio,
            "supported_features": self.supported_features,
            "unsupported_features": self.unsupported_features,
            "blockers": self.blockers,
            "claim_boundaries": self.claim_boundaries,
        }


@dataclass(frozen=True)
class OpenScenario2RunResult:
    status: str
    osc_path: str
    scenario_runner_root: str | None
    command: list[str]
    returncode: int | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    blockers: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": OSC2_SCHEMA_VERSION,
            "status": self.status,
            "osc_path": self.osc_path,
            "scenario_runner_root": self.scenario_runner_root,
            "command": self.command,
            "returncode": self.returncode,
            "stdout_path": self.stdout_path,
            "stderr_path": self.stderr_path,
            "blockers": self.blockers,
            "claim_boundaries": self.claim_boundaries,
        }


def validate_openscenario2(osc_path: Path, *, sidecar_path: Path | None = None) -> OpenScenario2Validation:
    """Validate an agent-authored `.osc` file enough for OODrive handoff."""

    blockers: list[str] = []
    supported: list[str] = []
    unsupported: list[str] = []
    if not osc_path.exists():
        blockers.append(f"OpenSCENARIO 2.0 file not found: {osc_path}")
        text = ""
    else:
        text = osc_path.read_text(encoding="utf-8", errors="replace")
    if osc_path.suffix != ".osc":
        blockers.append("OpenSCENARIO 2.0 files must use the .osc suffix.")
    markers = {
        "scenario": "scenario declaration",
        "actor": "actor declaration",
        "do": "action block",
        "serial": "serial composition",
        "parallel": "parallel composition",
        "speed": "speed modifier",
        "position": "position modifier",
        "lane": "lane modifier",
        "change_lane": "change lane modifier",
    }
    lowered = text.lower()
    for token, label in markers.items():
        if token in lowered:
            supported.append(label)
    if "scenario declaration" not in supported:
        blockers.append("Missing `scenario` declaration.")
    if "action block" not in supported:
        blockers.append("Missing `do` action block.")
    if "mesh" in lowered or "rag" in lowered or "alpamayo" in lowered:
        unsupported.append("non-standard OODrive evidence/provenance should live in sidecar")
    sidecar_payload = _load_optional_sidecar(sidecar_path, blockers)
    if sidecar_path is not None and sidecar_payload is not None:
        supported.append("oodrive sidecar")
    required_weight = 4.0
    coverage_ratio = round(min(len(supported) / max(required_weight, float(len(markers))), 1.0), 4)
    claims = [
        "asam_openscenario2_file=true",
        f"asam_openscenario2_validated={'true' if not blockers else 'false'}",
        "asam_openscenario2_executable=false_until_run_osc2_passes",
        "agent_authored_scenario=true",
    ]
    return OpenScenario2Validation(
        status="passed" if not blockers else "blocked",
        osc_path=str(osc_path),
        sidecar_path=str(sidecar_path) if sidecar_path else None,
        coverage_ratio=coverage_ratio,
        supported_features=_dedupe(supported),
        unsupported_features=_dedupe(unsupported),
        blockers=blockers,
        claim_boundaries=claims,
    )


def write_openscenario2_validation(run_dir: Path, validation: OpenScenario2Validation) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = validation.to_jsonable()
    json_path = run_dir / "osc2_validation.json"
    report_path = run_dir / "osc2_validation.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_validation_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def run_openscenario2(
    osc_path: Path,
    *,
    scenario_runner_root: Path | None,
    output_dir: Path,
    timeout_s: float = 120.0,
) -> OpenScenario2RunResult:
    """Run an `.osc` file through CARLA ScenarioRunner when installed."""

    command = _scenario_runner_command(osc_path, scenario_runner_root, output_dir)
    claims = [
        "asam_openscenario2_file=true",
        "asam_openscenario2_executable=false_until_scenario_runner_passes",
        "agent_authored_scenario=true",
    ]
    if scenario_runner_root is None or not scenario_runner_root.exists():
        return OpenScenario2RunResult(
            status="blocked",
            osc_path=str(osc_path),
            scenario_runner_root=str(scenario_runner_root) if scenario_runner_root else None,
            command=command,
            blockers=["ScenarioRunner root is missing; pass --scenario-runner-root with a valid checkout."],
            claim_boundaries=claims,
        )
    runner = scenario_runner_root / "scenario_runner.py"
    if not runner.exists():
        return OpenScenario2RunResult(
            status="blocked",
            osc_path=str(osc_path),
            scenario_runner_root=str(scenario_runner_root),
            command=command,
            blockers=[f"ScenarioRunner entrypoint not found: {runner}"],
            claim_boundaries=claims,
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = output_dir / "scenario_runner_stdout.txt"
    stderr_path = output_dir / "scenario_runner_stderr.txt"
    try:
        completed = subprocess.run(command, cwd=scenario_runner_root, capture_output=True, text=True, timeout=timeout_s, check=False)
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        status = "passed" if completed.returncode == 0 else "blocked"
        return OpenScenario2RunResult(
            status=status,
            osc_path=str(osc_path),
            scenario_runner_root=str(scenario_runner_root),
            command=command,
            returncode=completed.returncode,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            blockers=[] if completed.returncode == 0 else [f"ScenarioRunner exited with code {completed.returncode}."],
            claim_boundaries=[
                "asam_openscenario2_file=true",
                f"asam_openscenario2_executable={'true' if completed.returncode == 0 else 'false'}",
                "agent_authored_scenario=true",
            ],
        )
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(exc.stdout or "", encoding="utf-8")
        stderr_path.write_text(exc.stderr or "", encoding="utf-8")
        return OpenScenario2RunResult(
            status="blocked",
            osc_path=str(osc_path),
            scenario_runner_root=str(scenario_runner_root),
            command=command,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            blockers=[f"ScenarioRunner timed out after {timeout_s:.1f}s."],
            claim_boundaries=claims,
        )


def write_openscenario2_run(run_dir: Path, result: OpenScenario2RunResult) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = result.to_jsonable()
    json_path = run_dir / "osc2_run_result.json"
    report_path = run_dir / "osc2_run_result.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_run_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def prepare_osc2_run_dir(output_root: Path | None, run_id: str) -> Path:
    return prepare_run_dir(output_root or Path("artifacts/runs"), run_id)


def _scenario_runner_command(osc_path: Path, scenario_runner_root: Path | None, output_dir: Path) -> list[str]:
    runner = (scenario_runner_root / "scenario_runner.py") if scenario_runner_root else Path("scenario_runner.py")
    return ["python3", str(runner), "--openscenario2", str(osc_path), "--outputDir", str(output_dir)]


def _load_optional_sidecar(path: Path | None, blockers: list[str]) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        blockers.append(f"Sidecar file not found: {path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        blockers.append(f"Sidecar is not valid JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        blockers.append("Sidecar JSON must be an object.")
        return None
    return payload


def _validation_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OpenSCENARIO 2.0 Validation",
        "",
        f"- status: `{payload.get('status')}`",
        f"- osc: `{payload.get('osc_path')}`",
        f"- coverage_ratio: `{payload.get('coverage_ratio')}`",
        "",
        "## Supported",
        *[f"- {item}" for item in list(payload.get("supported_features", []))],
        "",
        "## Blockers",
        *([f"- {item}" for item in list(payload.get("blockers", []))] or ["- none"]),
    ]
    return "\n".join(lines) + "\n"


def _run_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OpenSCENARIO 2.0 Run Result",
        "",
        f"- status: `{payload.get('status')}`",
        f"- osc: `{payload.get('osc_path')}`",
        f"- returncode: `{payload.get('returncode')}`",
        "",
        "## Blockers",
        *([f"- {item}" for item in list(payload.get("blockers", []))] or ["- none"]),
    ]
    return "\n".join(lines) + "\n"


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


__all__ = [
    "OpenScenario2RunResult",
    "OpenScenario2Validation",
    "prepare_osc2_run_dir",
    "run_openscenario2",
    "validate_openscenario2",
    "write_openscenario2_run",
    "write_openscenario2_validation",
]
