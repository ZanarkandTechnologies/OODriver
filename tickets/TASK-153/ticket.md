# TASK-153: Live CARLA Scenario Installer And Runner

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-151, TASK-152
- location: `src/driverx/simulators`, `src/driverx/scenarios`, `src/driverx/assets`, `src/oodrive`, `tests`, `scripts`, `tickets/TASK-153`
- enter when: OODrive can compile a scenario graph and resolve generated/custom asset blueprints, but cannot yet run the whole pack as a live CARLA scenario with evidence-grade video/tracks.
- leave when: `oodrive run-scenario` installs/probes assets, spawns objects and behavior actors in CARLA, records RGB/tracks/action traces/video, cleans up actors, and writes a run manifest with honest custom-asset and policy-control claims.
- blockers: live proof requires Kasm CARLA; local fake backend must remain deterministic.
- spawned follow-ups: TASK-154 visualizes runs; TASK-155 exports accepted runs; TASK-139 can plug in time-warped VLA policy mode.
- complexity: L

### Summary

This is the "prompt and the scenario actually appears in CARLA" ticket. It consumes the scenario pack, asset registry, and scenario graph, then produces live CARLA evidence with custom asset resolution when installed and stock-proxy fallback when not.

### Scope

- In scope: product runner command, fake/live backends, asset install/probe integration, scenario graph executor, behavior actor application, frame/tracks/action recording, MP4 assembly hook, cleanup, scoring hooks, and tests.
- Out of scope: remote provider asset generation, Unreal packaging internals, real-time VLA serving, official leaderboard scoring, and public video hosting.

### Gap Analysis

- Current state: TASK-141 can run generated objects/one behavior in live CARLA through a focused demo path.
- Production expectation: a scenario pack becomes a full simulator run with installed/probed assets, behavior graph execution, deterministic evidence, cleanup, and promotion gates.
- Missing gaps: no general graph runner, no asset registry resolver in live spawn, no scenario-pack input command, no repeated-run/batch mode, and no custom-asset claim gate.
- Recommended boundary: implement one robust run command with fake and live modes before adding workbench/batch UI.

### Plan

#### Change

Add:

```bash
PYTHONPATH=src python3 -m oodrive run-scenario \
  --scenario-graph artifacts/runs/task152-scenario-graph/scenario_graph.json \
  --scenario-pack artifacts/runs/prod-pack/scenario_pack.json \
  --asset-registry artifacts/runs/task151-import-plan/carla_asset_registry.json \
  --backend carla-live \
  --config configs/carla_ood_demo.runpod.high_fidelity.yaml \
  --run-id task153-live-generated-scenario
```

#### Why

The product promise is not complete until the generated scenario is visible in CARLA, not merely compiled into a JSON plan.

#### Before -> After

- Before: live CARLA proof is a specialized generated-runtime demo.
- After: a general scenario graph runner drives live or fake CARLA from a production pack.

#### Touch

- `src/driverx/simulators/carla_scenario_runner.py` (new)
- `src/driverx/simulators/carla_ood_demo.py`
- `src/driverx/assets/carla_registry.py`
- `src/driverx/scenarios/scenario_graph.py`
- `src/driverx/scenarios/studio_product_runner_runtime.py` (new)
- `src/driverx/scenarios/studio_product_cli.py`
- `src/oodrive/cli.py`
- `src/driverx/evaluation/scenario_run_score.py` (new or extend TASK-156)
- `tests/test_carla_scenario_runner.py` (new)
- `tests/test_oodrive_cli.py`
- `docs/HISTORY.md`

#### Inspect

- `src/driverx/simulators/carla_ood_demo.py`
- `src/driverx/scenarios/generated_runtime.py`
- `src/driverx/simulators/carla_policy_replay.py`
- `src/driverx/assets/carla_mapping.py`
- `tickets/TASK-139/ticket.md`
- `tickets/TASK-141/ticket.md`
- `docs/MEMORY.md` MEM-0023, MEM-0025, MEM-0032, MEM-0042
- `docs/TROUBLES.md`

#### Signature Delta

```python
run_carla_scenario_graph(
    graph: dict[str, Any],
    *,
    pack: dict[str, Any],
    asset_registry: dict[str, Any] | None,
    config: CarlaOodDemoConfig,
    run_dir: Path,
    backend: Literal["fake-carla", "carla-live"],
    carla_module: object | None = None,
) -> CarlaScenarioRunResult

run_studio_run_scenario(...) -> StudioCommandResult
```

#### Type Sketch

```python
CarlaScenarioRunResult = {
  "status": "passed" | "partial" | "blocked" | "failed",
  "backend": "fake-carla" | "carla-live",
  "spawned_static_count": int,
  "spawned_dynamic_count": int,
  "custom_asset_spawn_count": int,
  "stock_proxy_spawn_count": int,
  "rgb_folder": str | None,
  "tracks_path": str | None,
  "action_trace_path": str | None,
  "video_path": str | None,
  "claim_boundaries": list[str],
  "blockers": list[str],
}
```

#### Typed Flow Example

A scenario graph object with `blueprint_ref=driverx.generated.asset_roadside_vendor` is resolved by registry. If installed, `custom_asset_spawn_count += 1`; otherwise it falls back to `static.prop.foodcart` and records `custom_asset_spawn_count=0`, `stock_proxy_spawn_count=1`.

#### Execution Steps

1. Build a fake backend first using existing fake-CARLA track semantics.
2. Extract reusable spawn/record/cleanup helpers from `carla_ood_demo.py` without breaking TASK-141.
3. Implement graph actor spawning and behavior timeline stepping.
4. Integrate asset registry resolution and claim-boundary accounting.
5. Record RGB frames, tracks, action trace, spawned/destroyed actor ids, and run manifest.
6. Add MP4 assembly hook that uses existing frame/video utilities when available.
7. Add local tests for fake/live-blocked paths and a Kasm cookbook for live proof.

#### Recommendation

Unify around scenario graph execution while keeping TASK-141's specific demo path as a compatibility/evidence fixture. The new runner should be the production path.

#### Options Considered

- Extend `carla_ood_demo.py` directly: faster but risks another bespoke demo.
- Use ScenarioRunner directly now: attractive, but custom assets and OODrive graph fields need sidecar execution.
- Build OODrive runner from graph: recommended because it matches current code and can export standards separately.

#### Blast Radius

High in simulator integration. Protect old demos with tests and keep CARLA imports inside live edges.

#### Risks

- Kasm CARLA setup can block; fake backend and precise live blockers must still pass locally.
- Video can look bad even when run succeeds; promotion requires TASK-156 scoring and MEM-0023 gates.

### Acceptance Criteria

- [x] AC-1: `oodrive run-scenario --backend fake-carla` writes run manifest, tracks, action trace, and claim boundaries.
- [x] AC-2: `--backend carla-live` either produces RGB/tracks/spawn proof/video on Kasm or a precise setup blocker locally.
- [x] AC-3: Custom installed assets and stock fallback proxies are counted separately.
- [x] AC-4: Actor cleanup evidence is recorded.
- [x] AC-5: Existing TASK-141 generated-runtime tests still pass.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_carla_scenario_runner tests.test_generated_carla_runtime tests.test_oodrive_cli`
- `PYTHONPATH=src python3 -m oodrive run-scenario --scenario-graph <graph> --scenario-pack <pack> --backend fake-carla --run-id task153-fake`
- Kasm proof command with `--backend carla-live`, attached RGB/tracks/video, and score report.

### Autonomy Readiness

- Inputs: scenario pack, graph, optional asset registry, CARLA config.
- Compute: local for fake; Kasm GPU/desktop for live.
- External services: none unless assets were generated earlier.
- Stop gates: do not mutate shared CARLA installs; do not claim custom asset success unless registry/probe and live spawn agree.

### Refs

- CARLA actor blueprint model: https://carla.readthedocs.io/en/latest/core_actors/
- ScenarioRunner OpenSCENARIO support: https://scenario-runner.readthedocs.io/en/latest/openscenario_support/

### Evidence

- Planning review: `tickets/TASK-149/artifacts/review/production-generator-plan-review.json`
- Fake-CARLA proof: `artifacts/runs/task153-production-fake-proof/scenario_run_manifest.json`
- Pulled live CARLA run manifest: `artifacts/runs/task153-live-prompt-to-carla-pulled/artifacts/runs/task153-live-prompt-to-carla-pack/task153-live-prompt-to-carla-assets/task153-live-prompt-to-carla-run/scenario_run_manifest.json`
- Pulled live CARLA frame: `artifacts/runs/task153-live-prompt-to-carla-pulled/artifacts/runs/task153-live-prompt-to-carla-pack/task153-live-prompt-to-carla-assets/task153-live-prompt-to-carla-run/live-generated-runtime/live_cases/behavior-00-motorcycle-filtering/rgb/frame_000240.png`
- Prompt-image QA: `tickets/TASK-153/artifacts/qa/prompt-to-carla-image-qa.md`

### Blockers

- Prompt-image QA is partial: live CARLA is proved, but exact wet/Malaysian/roadwork visual fidelity is not.
