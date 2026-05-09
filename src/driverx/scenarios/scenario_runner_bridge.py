"""CARLA ScenarioRunner package and run bridge for OODrive artifacts."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir

SCENARIO_RUNNER_PACKAGE_SCHEMA = "oodrive.scenario_runner_package.v1"


@dataclass(frozen=True)
class ScenarioRunnerPackage:
    status: str
    package_dir: str
    package_manifest_path: str
    entrypoint: str
    command: list[str]
    files: dict[str, str | None]
    coverage: dict[str, list[str]]
    blockers: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": SCENARIO_RUNNER_PACKAGE_SCHEMA,
            "status": self.status,
            "package_dir": self.package_dir,
            "package_manifest_path": self.package_manifest_path,
            "scenario_runner_entrypoint": self.entrypoint,
            "command": self.command,
            "files": self.files,
            "coverage": self.coverage,
            "blockers": self.blockers,
            "claim_boundaries": self.claim_boundaries,
        }


@dataclass(frozen=True)
class ScenarioRunnerBridgeRun:
    status: str
    package_manifest_path: str
    scenario_runner_root: str | None
    command: list[str]
    returncode: int | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    blockers: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": "oodrive.scenario_runner_run.v1",
            "status": self.status,
            "package_manifest_path": self.package_manifest_path,
            "scenario_runner_root": self.scenario_runner_root,
            "command": self.command,
            "returncode": self.returncode,
            "stdout_path": self.stdout_path,
            "stderr_path": self.stderr_path,
            "blockers": self.blockers,
            "claim_boundaries": self.claim_boundaries,
        }


def build_scenario_runner_package(
    *,
    scenario_graph_path: Path | None,
    osc2_path: Path | None,
    sidecar_path: Path | None,
    output_root: Path | None = None,
    run_id: str = "oodrive-scenario-runner-package",
) -> ScenarioRunnerPackage:
    """Write a ScenarioRunner package from OODrive graph or agent-authored OSC2."""

    run_dir = prepare_run_dir(output_root or Path("artifacts/runs"), run_id)
    package_dir = run_dir / "scenario_runner_package"
    package_dir.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    files: dict[str, str | None] = {"scenario_py": None, "osc2": None, "sidecar": None, "scenario_graph": None}
    coverage = {"native_fields": [], "sidecar_fields": [], "unsupported_fields": []}
    entrypoint = "python_class"
    if osc2_path is not None:
        if osc2_path.exists():
            copied = package_dir / osc2_path.name
            shutil.copyfile(osc2_path, copied)
            files["osc2"] = str(copied)
            entrypoint = "osc2"
            coverage["native_fields"].append("openscenario2")
        else:
            blockers.append(f"OpenSCENARIO 2.0 file not found: {osc2_path}")
    if scenario_graph_path is not None:
        if scenario_graph_path.exists():
            graph = json.loads(scenario_graph_path.read_text(encoding="utf-8"))
            graph_copy = package_dir / "scenario_graph.json"
            graph_copy.write_text(json.dumps(graph, indent=2), encoding="utf-8")
            files["scenario_graph"] = str(graph_copy)
            scenario_py = package_dir / "oodrive_generated_scenario.py"
            scenario_py.write_text(_scenario_py(graph), encoding="utf-8")
            files["scenario_py"] = str(scenario_py)
            coverage["native_fields"].extend(["actors", "static_objects", "actions"])
            coverage["sidecar_fields"].extend(["claim_boundaries", "asset provenance", "rag evidence"])
        else:
            blockers.append(f"Scenario graph not found: {scenario_graph_path}")
    if sidecar_path is not None:
        if sidecar_path.exists():
            copied_sidecar = package_dir / "oodrive_sidecar.json"
            shutil.copyfile(sidecar_path, copied_sidecar)
            files["sidecar"] = str(copied_sidecar)
            coverage["sidecar_fields"].append("agent sidecar")
        else:
            blockers.append(f"Sidecar not found: {sidecar_path}")
    if not files["osc2"] and not files["scenario_py"]:
        blockers.append("Provide --osc2 or --scenario-graph to build a ScenarioRunner package.")
    manifest_path = package_dir / "scenario_runner_package.json"
    command = _package_command(entrypoint, files)
    claims = [
        "scenario_runner_package=true",
        "scenario_runner_executed=false_until_scenario_runner_run_passes",
        "oodrive_sidecar_required=true",
    ]
    package = ScenarioRunnerPackage(
        status="passed" if not blockers else "blocked",
        package_dir=str(package_dir),
        package_manifest_path=str(manifest_path),
        entrypoint=entrypoint,
        command=command,
        files=files,
        coverage={key: _dedupe(value) for key, value in coverage.items()},
        blockers=blockers,
        claim_boundaries=claims,
    )
    manifest_path.write_text(json.dumps(package.to_jsonable(), indent=2), encoding="utf-8")
    (package_dir / "scenario_runner_command.sh").write_text(" ".join(command) + "\n", encoding="utf-8")
    return package


def run_scenario_runner_package(
    package_manifest_path: Path,
    *,
    scenario_runner_root: Path | None,
    output_root: Path | None = None,
    run_id: str = "oodrive-scenario-runner-run",
    timeout_s: float = 120.0,
) -> ScenarioRunnerBridgeRun:
    run_dir = prepare_run_dir(output_root or package_manifest_path.parent, run_id)
    package = json.loads(package_manifest_path.read_text(encoding="utf-8"))
    command = _package_command(str(package.get("scenario_runner_entrypoint")), dict(package.get("files", {})))
    claims = [
        "scenario_runner_package=true",
        "scenario_runner_executed=false_until_scenario_runner_passes",
    ]
    if scenario_runner_root is None or not scenario_runner_root.exists():
        return _write_bridge_run(
            run_dir,
            ScenarioRunnerBridgeRun(
                status="blocked",
                package_manifest_path=str(package_manifest_path),
                scenario_runner_root=str(scenario_runner_root) if scenario_runner_root else None,
                command=command,
                blockers=["ScenarioRunner root is missing; pass --scenario-runner-root with a valid checkout."],
                claim_boundaries=claims,
            ),
        )
    runner = scenario_runner_root / "scenario_runner.py"
    if not runner.exists():
        return _write_bridge_run(
            run_dir,
            ScenarioRunnerBridgeRun(
                status="blocked",
                package_manifest_path=str(package_manifest_path),
                scenario_runner_root=str(scenario_runner_root),
                command=command,
                blockers=[f"ScenarioRunner entrypoint not found: {runner}"],
                claim_boundaries=claims,
            ),
        )
    final_command = ["python3", str(runner), *command[2:]]
    stdout_path = run_dir / "scenario_runner_stdout.txt"
    stderr_path = run_dir / "scenario_runner_stderr.txt"
    try:
        completed = subprocess.run(final_command, cwd=scenario_runner_root, capture_output=True, text=True, timeout=timeout_s, check=False)
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        return _write_bridge_run(
            run_dir,
            ScenarioRunnerBridgeRun(
                status="passed" if completed.returncode == 0 else "blocked",
                package_manifest_path=str(package_manifest_path),
                scenario_runner_root=str(scenario_runner_root),
                command=final_command,
                returncode=completed.returncode,
                stdout_path=str(stdout_path),
                stderr_path=str(stderr_path),
                blockers=[] if completed.returncode == 0 else [f"ScenarioRunner exited with code {completed.returncode}."],
                claim_boundaries=[
                    "scenario_runner_package=true",
                    f"scenario_runner_executed={'true' if completed.returncode == 0 else 'false'}",
                ],
            ),
        )
    except subprocess.TimeoutExpired:
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(f"Timed out after {timeout_s:.1f}s.\n", encoding="utf-8")
        return _write_bridge_run(
            run_dir,
            ScenarioRunnerBridgeRun(
                status="blocked",
                package_manifest_path=str(package_manifest_path),
                scenario_runner_root=str(scenario_runner_root),
                command=final_command,
                stdout_path=str(stdout_path),
                stderr_path=str(stderr_path),
                blockers=[f"ScenarioRunner timed out after {timeout_s:.1f}s."],
                claim_boundaries=claims,
            ),
        )


def write_scenario_runner_package_report(package: ScenarioRunnerPackage) -> dict[str, Any]:
    package_dir = Path(package.package_dir)
    report_path = package_dir / "scenario_runner_package.md"
    payload = package.to_jsonable()
    report_path.write_text(_package_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": package.package_manifest_path, "report_path": str(report_path)}


def _write_bridge_run(run_dir: Path, result: ScenarioRunnerBridgeRun) -> ScenarioRunnerBridgeRun:
    json_path = run_dir / "scenario_runner_run.json"
    report_path = run_dir / "scenario_runner_run.md"
    payload = result.to_jsonable()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_run_markdown(payload), encoding="utf-8")
    return result


def _scenario_py(graph: dict[str, Any]) -> str:
    scenario_id = str(graph.get("scenario_id") or "oodrive_generated")
    return f'''"""Generated ScenarioRunner stub for {scenario_id}."""

try:
    from srunner.scenarios.basic_scenario import BasicScenario
except Exception:
    BasicScenario = object


class OODriveGeneratedScenario(BasicScenario):
    """Minimal generated ScenarioRunner class stub.

    OODrive sidecar metadata and richer behavior traces remain outside this
    file. This stub exists so ScenarioRunner package structure is explicit.
    """

    timeout = 60

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True):
        if BasicScenario is object:
            return
        super().__init__("{scenario_id}", ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)
'''


def _package_command(entrypoint: str, files: dict[str, str | None]) -> list[str]:
    if entrypoint == "osc2" and files.get("osc2"):
        return ["python3", "scenario_runner.py", "--openscenario2", str(files["osc2"])]
    if files.get("scenario_py"):
        return ["python3", "scenario_runner.py", "--scenario", "OODriveGeneratedScenario"]
    return ["python3", "scenario_runner.py"]


def _package_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ScenarioRunner Package",
            "",
            f"- status: `{payload.get('status')}`",
            f"- entrypoint: `{payload.get('scenario_runner_entrypoint')}`",
            f"- package: `{payload.get('package_dir')}`",
            "",
            "## Blockers",
            *([f"- {item}" for item in list(payload.get("blockers", []))] or ["- none"]),
        ]
    ) + "\n"


def _run_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ScenarioRunner Run",
            "",
            f"- status: `{payload.get('status')}`",
            f"- returncode: `{payload.get('returncode')}`",
            "",
            "## Blockers",
            *([f"- {item}" for item in list(payload.get("blockers", []))] or ["- none"]),
        ]
    ) + "\n"


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


__all__ = [
    "ScenarioRunnerBridgeRun",
    "ScenarioRunnerPackage",
    "build_scenario_runner_package",
    "run_scenario_runner_package",
    "write_scenario_runner_package_report",
]
