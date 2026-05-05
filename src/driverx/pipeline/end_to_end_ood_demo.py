"""One-command local OOD scenario, policy, control, and simulator demo."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.behaviors import default_behavior_plans, simulate_behavior
from driverx.behaviors.types import BehaviorTrace
from driverx.core.artifacts import prepare_run_dir
from driverx.core.config import read_config_mapping
from driverx.core.types import FrameBundle
from driverx.datasets.fixtures import load_fixture_frame
from driverx.memory import build_memory_bank, retrieve_memory, write_memory_bank
from driverx.policies import PolicyContext, PolicyDecision, select_policy_adapter
from driverx.policies.trajectory_control import ControlTrace, trajectory_to_control_trace
from driverx.scenarios import (
    MutationPolicy,
    ScenarioRecipe,
    ScenarioResult,
    generate_scenario_recipes,
    load_scenario_results,
    load_scenario_seeds,
    write_scenario_suite,
)
from driverx.simulators.local_ood_sim import run_local_ood_sim, write_local_ood_sim_result


@dataclass(frozen=True)
class EndToEndOodDemoConfig:
    scenario_config_path: Path = Path("configs/scenario_forge.sample.yaml")
    output_root: Path = Path("artifacts/runs")
    run_id: str = "local-ood-demo"
    fixture: str = "construction_merge"
    behavior_id: str = "motorcycle_filtering"
    mutation: str = "regional_driving_behavior"
    random_seed: int = 7
    memory_results_path: Path = Path("tests/fixtures/fail2drive_like/results.json")
    memory_limit: int = 3


def run_end_to_end_ood_demo(config: EndToEndOodDemoConfig) -> dict[str, Any]:
    run_dir = prepare_run_dir(config.output_root, config.run_id)
    recipe = _generate_one_recipe(config, run_dir / "scenario")
    behavior = _load_behavior(config.behavior_id)
    frame = _frame_for_recipe(config.fixture, recipe, behavior)
    bank = build_memory_bank(
        [
            *load_scenario_results(config.memory_results_path),
            _behavior_memory_result(recipe, behavior),
        ]
    )
    memory_summary = write_memory_bank(run_dir / "memory", bank)
    memories = retrieve_memory(recipe, bank, config.memory_limit)
    decisions = [
        ("policy", _decide(policy="mock", frame=frame, recipe=recipe, memories=[])),
        ("policy+memory", _decide(policy="mock", frame=frame, recipe=recipe, memories=memories)),
        ("hybrid", _decide(policy="hybrid", frame=frame, recipe=recipe, memories=[])),
    ]
    control_traces = [
        (label, _control_trace(label, decision))
        for label, decision in decisions
    ]
    _write_behavior(run_dir / "behavior", behavior)
    _write_decisions(run_dir / "policy", decisions)
    _write_controls(run_dir / "controls", control_traces)
    reaction_matrix = _write_reaction_matrix(run_dir / "policy", decisions)
    sim_result = run_local_ood_sim(
        recipe=recipe,
        behavior=behavior,
        decisions=decisions,
        control_traces=control_traces,
        output_dir=run_dir / "local-sim",
    )
    sim_summary = write_local_ood_sim_result(run_dir / "local-sim", sim_result)
    payload = {
        "demo_id": run_dir.name,
        "status": "ready",
        "claim_boundaries": {
            "local_2d_simulator": True,
            "closed_loop_carla": False,
            "live_vla": False,
            "minimal_shot_memory_eval": True,
        },
        "recipe": recipe.to_jsonable(),
        "behavior": behavior.to_jsonable(),
        "retrieved_memory_ids": [memory.entry_id for memory in memories],
        "policy_decisions": {
            label: decision.to_jsonable()
            for label, decision in decisions
        },
        "control_traces": {
            label: trace.to_jsonable()
            for label, trace in control_traces
        },
        "local_sim": sim_result.to_jsonable(),
        "artifact_map": {
            "scenario_summary": str(run_dir / "scenario" / "scenario_suite_summary.json"),
            "memory_bank": str(memory_summary["json_path"]),
            "behavior_trace": str(run_dir / "behavior" / "behavior_trace.json"),
            "policy_decisions": str(run_dir / "policy" / "policy_decisions.json"),
            "reaction_matrix": str(reaction_matrix["json_path"]),
            "control_traces": str(run_dir / "controls" / "control_traces.json"),
            "local_sim_json": str(sim_summary["json_path"]),
            "local_sim_report": str(sim_summary["report_path"]),
            "local_sim_svg": sim_summary["svg_path"],
            "local_sim_html": sim_summary["html_path"],
        },
    }
    return write_end_to_end_ood_demo(run_dir, payload)


def write_end_to_end_ood_demo(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    json_path = run_dir / "end_to_end_demo.json"
    report_path = run_dir / "end_to_end_demo.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _generate_one_recipe(config: EndToEndOodDemoConfig, run_dir: Path) -> ScenarioRecipe:
    raw = read_config_mapping(config.scenario_config_path)
    scenario = dict(raw.get("scenario", {})) if isinstance(raw.get("scenario"), dict) else {}
    seeds_path = Path(str(scenario.get("seeds_path", "tests/fixtures/fail2drive_like/seeds.json")))
    seeds = load_scenario_seeds(seeds_path)
    recipes = generate_scenario_recipes(
        seeds,
        MutationPolicy(mutations=(config.mutation,)),
        count=1,
        random_seed=config.random_seed,
    )
    write_scenario_suite(run_dir, seeds, recipes)
    return recipes[0]


def _load_behavior(behavior_id: str) -> BehaviorTrace:
    plans = {plan.behavior_id: plan for plan in default_behavior_plans()}
    if behavior_id not in plans:
        raise ValueError(f"Unknown behavior id: {behavior_id}")
    return simulate_behavior(plans[behavior_id])


def _frame_for_recipe(
    fixture: str,
    recipe: ScenarioRecipe,
    behavior: BehaviorTrace,
) -> FrameBundle:
    base = load_fixture_frame(fixture)
    metadata = {
        **base.metadata,
        "scenario": f"{base.metadata.get('scenario', fixture)}::{recipe.mutation}",
        "hazards": [
            *[str(item) for item in base.metadata.get("hazards", [])],
            recipe.expected_failure_mode,
            behavior.plan.expected_pressure,
        ],
        "recipe_id": recipe.recipe_id,
        "behavior_id": behavior.plan.behavior_id,
    }
    return FrameBundle(
        frame_name=f"{base.frame_name}::{recipe.recipe_id}",
        front_images=base.front_images,
        ego_history_xy=base.ego_history_xy,
        future_xy=base.future_xy,
        metadata=metadata,
    )


def _behavior_memory_result(
    recipe: ScenarioRecipe,
    behavior: BehaviorTrace,
) -> ScenarioResult:
    return ScenarioResult(
        scenario_id=f"fixture_prior::{behavior.plan.behavior_id}",
        policy="fixture_prior_policy",
        success=False,
        driving_score=48.0,
        route_completion=78.0,
        infractions={"behavior_pressure": [behavior.plan.expected_pressure]},
        failure_summary=(
            f"Prior policy drove too assertively during {behavior.plan.behavior_id}; "
            f"{behavior.plan.expected_pressure}"
        ),
        latency_ms={"policy_inference": 95.0},
        tags=[*behavior.plan.tags, recipe.mutation, *recipe.memory_query],
    )


def _decide(
    *,
    policy: str,
    frame: FrameBundle,
    recipe: ScenarioRecipe,
    memories: list[Any],
) -> PolicyDecision:
    adapter = select_policy_adapter(policy, memory_aware=bool(memories))
    return adapter.decide(PolicyContext(frame=frame, recipe=recipe, memories=memories))


def _control_trace(label: str, decision: PolicyDecision) -> ControlTrace:
    if decision.action.trajectory is None:
        raise ValueError(f"Policy decision has no trajectory: {label}")
    return trajectory_to_control_trace(
        decision.action.trajectory,
        source_policy_id=f"{decision.policy_id}:{label}",
    )


def _write_behavior(run_dir: Path, behavior: BehaviorTrace) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "behavior_trace.json").write_text(
        json.dumps(behavior.to_jsonable(), indent=2),
        encoding="utf-8",
    )


def _write_decisions(run_dir: Path, decisions: list[tuple[str, PolicyDecision]]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "policy_decisions.json").write_text(
        json.dumps({label: decision.to_jsonable() for label, decision in decisions}, indent=2),
        encoding="utf-8",
    )


def _write_controls(run_dir: Path, traces: list[tuple[str, ControlTrace]]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "control_traces.json").write_text(
        json.dumps({label: trace.to_jsonable() for label, trace in traces}, indent=2),
        encoding="utf-8",
    )


def _write_reaction_matrix(
    run_dir: Path,
    decisions: list[tuple[str, PolicyDecision]],
) -> dict[str, str]:
    rows = []
    for label, decision in decisions:
        control = decision.action.control
        rows.append(
            {
                "mode": label,
                "policy_id": decision.policy_id,
                "adapter_kind": decision.adapter_kind,
                "setup_status": "ready" if decision.setup_blocker is None else "blocked",
                "latency_ms": decision.latency_ms,
                "target_behavior": decision.intent.target_behavior,
                "target_speed_mps": control.get("target_speed_mps"),
                "yield": control.get("yield"),
                "memory_guided": control.get("memory_guided"),
                "retrieved_memory_ids": decision.retrieved_memory_ids,
                "safety_score_proxy": _safety_score_proxy(decision),
                "setup_blocker": decision.setup_blocker,
            }
        )
    json_path = run_dir / "policy_reaction_matrix.json"
    report_path = run_dir / "policy_reaction_matrix.md"
    payload = {"rows": rows}
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_reaction_matrix_markdown(rows), encoding="utf-8")
    return {"json_path": str(json_path), "report_path": str(report_path)}


def _safety_score_proxy(decision: PolicyDecision) -> float:
    target_speed = float(decision.action.control.get("target_speed_mps", 0.0))
    yield_bonus = 15.0 if decision.action.control.get("yield") else 0.0
    memory_bonus = 8.0 if decision.action.control.get("memory_guided") else 0.0
    uncertainty_penalty = decision.intent.uncertainty * 20.0
    speed_penalty = max(0.0, target_speed - 4.0) * 3.0
    return round(max(0.0, min(100.0, 70.0 + yield_bonus + memory_bonus - uncertainty_penalty - speed_penalty)), 4)


def _reaction_matrix_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Policy Reaction Matrix",
        "",
        "| Mode | Policy | Status | Target speed | Yield | Memory ids | Safety proxy |",
        "| --- | --- | --- | ---: | --- | --- | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['mode']}` | `{row['policy_id']}` | `{row['setup_status']}` | "
            f"`{row['target_speed_mps']}` | `{row['yield']}` | "
            f"`{', '.join(row['retrieved_memory_ids'])}` | `{row['safety_score_proxy']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _markdown(payload: dict[str, Any]) -> str:
    artifact_map = dict(payload["artifact_map"])
    local_sim = dict(payload["local_sim"])
    lines = [
        "# End-To-End Local OOD Demo",
        "",
        f"- demo_id: `{payload['demo_id']}`",
        f"- status: `{payload['status']}`",
        f"- recipe_id: `{payload['recipe']['recipe_id']}`",
        f"- mutation: `{payload['recipe']['mutation']}`",
        f"- behavior_id: `{payload['behavior']['plan']['behavior_id']}`",
        f"- retrieved_memory_ids: `{', '.join(payload['retrieved_memory_ids'])}`",
        f"- local_simulator: `{payload['claim_boundaries']['local_2d_simulator']}`",
        f"- closed_loop_carla: `{payload['claim_boundaries']['closed_loop_carla']}`",
        f"- live_vla: `{payload['claim_boundaries']['live_vla']}`",
        "",
        "## What Ran",
        "",
        "1. Generated one deterministic OOD recipe from Fail2Drive-like seeds.",
        "2. Simulated one erratic regional behavior trace.",
        "3. Retrieved compact prior failure memory for the recipe.",
        "4. Ran the mock policy once without memory and once with memory.",
        "5. Converted both trajectories into bounded cached-replay controls.",
        "6. Rendered a local top-down simulator artifact.",
        "",
        "## Policy Reaction",
        "",
    ]
    for label, decision in dict(payload["policy_decisions"]).items():
        action = dict(decision["action"])
        control = dict(action["control"])
        lines.extend(
            [
                f"### {label}",
                "",
                f"- target_behavior: `{decision['intent']['target_behavior']}`",
                f"- speed_profile: `{decision['intent']['speed_profile']}`",
                f"- target_speed_mps: `{control.get('target_speed_mps')}`",
                f"- yield: `{control.get('yield')}`",
                f"- memory_guided: `{control.get('memory_guided')}`",
                f"- latency_ms: `{decision['latency_ms']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Local Simulator Summary",
            "",
            f"- worst_risk_level: `{local_sim['worst_risk_level']}`",
            f"- min_distance_m: `{local_sim['min_distance_m']}`",
        f"- svg: `{artifact_map['local_sim_svg']}`",
        f"- html: `{artifact_map['local_sim_html']}`",
        f"- reaction_matrix: `{artifact_map['reaction_matrix']}`",
        "",
            "## Claim Boundary",
            "",
            "This artifact proves the DriverX OOD generation, memory, policy, trajectory, and local simulation loop. It is not a live CARLA route score and not real-time closed-loop VLA driving.",
            "",
        ]
    )
    return "\n".join(lines)


__all__ = [
    "EndToEndOodDemoConfig",
    "run_end_to_end_ood_demo",
    "write_end_to_end_ood_demo",
]
