# TASK-120: Flagship OODrive Scenario Contract

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-114, TASK-115, TASK-116, TASK-117, TASK-118, TASK-119
- location: `src/driverx/scenarios`, `configs`, `tickets/TASK-120/artifacts`
- enter when: current OODrive CLI exists but the next GPU/CARLA work still lacks one crisp flagship scenario target
- leave when: one submission-grade Malaysian wet roadwork scenario contract can be generated locally with run commands, quality gates, actor choreography, memory queries, and claim boundaries
- blockers: none for local scenario contract; live CARLA/Alpamayo proof moves to TASK-121 through TASK-124
- spawned follow-ups: TASK-121, TASK-122, TASK-123, TASK-124
- complexity: S

### Summary

Create the concrete scenario we will spend the remaining dev time making great:
**Malaysian wet night roadwork chaos**. The artifact must be more specific than
a prompt. It should define the map/runtime target, environment, OOD actors,
behavior pressures, memory/RAG intent, quality gates, and the exact commands to
run when the H100 Kasm VM arrives.

### Scope

- In scope: one deterministic scenario contract, a CLI to write the contract,
  config defaults, Markdown report, command plan, unit tests, README/ticket
  evidence.
- Out of scope: live CARLA execution, live Alpamayo inference, final video
  rendering, official Fail2Drive scoring.

### Plan

#### Change

Add a flagship scenario pack builder that writes JSON and Markdown artifacts
under `artifacts/runs/<run_id>/`.

#### Why

The remaining work should optimize one realistic, legible, complex OOD example
instead of generating more shallow scenarios.

#### Before -> After

- Before: OODrive can generate/queue many scenarios, but the next live runtime
  target is diffuse.
- After: one named scenario contract drives CARLA capture, Alpamayo frame
  inference, trajectory replay, and final video/dossier tickets.

#### Touch

- `src/driverx/scenarios/flagship.py`
- `src/driverx/scenarios/flagship_cli.py`
- `src/driverx/cli_extensions.py`
- `src/driverx/scenarios/__init__.py`
- `configs/oodrive_flagship_malaysia.yaml`
- `tests/test_oodrive_flagship.py`
- `README.md`
- `docs/HISTORY.md`

#### Inspect

- `src/driverx/scenarios/studio_product.py`
- `src/driverx/pipeline/scripted_ood_campaign.py`
- `src/driverx/simulators/carla_ood_demo.py`
- `docs/prd.md`
- `docs/specs/scenario-generator-cli-v1.md`
- `docs/MEMORY.md`

#### Signature Delta

```python
load_flagship_config(path: Path) -> FlagshipScenarioConfig
build_flagship_scenario(config: FlagshipScenarioConfig) -> FlagshipScenarioPack
write_flagship_scenario(run_dir: Path, pack: FlagshipScenarioPack) -> dict[str, Any]
```

CLI:

```bash
PYTHONPATH=src python3 -m driverx build-flagship-oodrive-scenario \
  --config configs/oodrive_flagship_malaysia.yaml \
  --output-root artifacts/runs \
  --run-id flagship-malaysia
```

#### Type Sketch

```python
FlagshipScenarioPack = {
  "scenario_id": str,
  "title": str,
  "prompt": str,
  "map_name": str,
  "environment": dict,
  "actors": list[dict],
  "behavior_sequence": list[str],
  "memory_queries": list[str],
  "quality_targets": dict,
  "runtime_commands": list[str],
  "claim_boundaries": list[str],
}
```

#### Typed Flow Example

`configs/oodrive_flagship_malaysia.yaml`
-> `FlagshipScenarioConfig(scenario_id="flagship-malaysia-wet-roadwork")`
-> `FlagshipScenarioPack(... behavior_sequence=["sudden_brake", "motorcycle_filtering", "double_parked_door_swerve", "wrong_way_shoulder_creep"])`
-> `flagship_scenario.json` and `flagship_scenario.md`
-> TASK-121 uses the command plan to capture CARLA checkpoints.

#### Execution Steps

1. Add typed config/pack dataclasses and deterministic builder.
2. Add CLI registration and config sample.
3. Add tests for complexity, command plan, quality targets, and claim
   boundaries.
4. Write docs and evidence.
5. Run focused tests and full pre-push gate.
6. Review and commit.

#### Recommendation

Implement this now before the H100 VM arrives.

#### Options Considered

- Generate many new scenarios now: good breadth, weaker demo depth.
- Jump straight to VM capture: tempting, but would re-enter setup without one
  crisp target.
- Recommended: freeze one excellent flagship scenario contract first.

#### Blast Radius

Low. Adds a new local CLI and artifacts without changing existing runtime
commands.

#### Risks

- The pack could overclaim closed-loop capability. Mitigate with explicit claim
  boundaries and VM follow-up tickets.
- Scenario could be too fantastical. Mitigate with plausible Malaysian urban
  driving elements and quality gates.

### Acceptance Criteria

- [ ] AC-1: CLI writes `flagship_scenario.json` and `flagship_scenario.md`.
- [ ] AC-2: Pack includes at least four interacting OOD pressures: roadwork
  narrowing, unsignaled brake, motorcycle filtering, roadside occlusion.
- [ ] AC-3: Pack includes CARLA, Alpamayo checkpoint, replay, and final overlay
  command plan entries.
- [ ] AC-4: Pack labels no live closed-loop Alpamayo proof until TASK-123.

### Agent Contract
- Open: `src/driverx/scenarios/flagship.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_oodrive_flagship`
- Stabilize: keep all generation deterministic from config values
- Inspect: JSON/Markdown artifacts under `artifacts/runs/flagship-malaysia`
- Key screens/states: none
- QA cookbook: run CLI smoke and inspect claim boundaries
- Taste refs: demo should read like a paper case study, not a toy prompt
- Expected artifacts: `flagship_scenario.json`, `flagship_scenario.md`, review
- Delegate with: TASK-120 ticket and OODrive CLI spec

### Evidence Checklist
- [x] CLI smoke captured
- [x] Unit tests captured
- [x] Pre-push captured
- [x] Review linked

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_oodrive_flagship`
- `PYTHONPATH=src python3 -m driverx build-flagship-oodrive-scenario --config configs/oodrive_flagship_malaysia.yaml --run-id flagship-malaysia`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Inputs: no secrets, no GPU, no CARLA required.
- Compute: local Python only.
- Human gates: none.
- Follow-up gates: TASK-121+ require the H100 Kasm VM and CARLA availability.

### Evidence

- CLI: `PYTHONPATH=src python3 -m driverx build-flagship-oodrive-scenario --config configs/oodrive_flagship_malaysia.yaml --output-root artifacts/runs --run-id flagship-malaysia-smoke`.
- Smoke artifacts:
  `artifacts/runs/flagship-malaysia-smoke/flagship_scenario.json` and
  `artifacts/runs/flagship-malaysia-smoke/flagship_scenario.md`.
- QA report:
  `tickets/TASK-120/artifacts/qa/flagship-scenario-qa.md`.
- Review:
  `docs/reviews/TASK-120-flagship-scenario-review.md`.
- Tests:
  `PYTHONPATH=src python3 -m unittest tests.test_oodrive_flagship`.
- Full gate: `bash scripts/pre_push_check.sh` passed with `395` tests and `3`
  skipped.

### Blockers

- None.
