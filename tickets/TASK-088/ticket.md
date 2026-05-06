# TASK-088: Stock Fail2Drive Full-Score Runtime Handoff

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-060, TASK-071
- location: `scripts/`, `src/driverx/simulators`, `src/driverx/pipeline`, docs, `tickets/TASK-088/artifacts`
- enter when: the submission wants benchmark-pure stock Fail2Drive scoring beyond scripted CARLA proof
- leave when: the repo has a graphics-host checklist, sync/run script, and exact handoff bundle for one full Town13 score attempt
- blockers: needs a graphics-capable Linux CARLA host; current RTX 6000 Ada RunPod lane is enough for Alpamayo but not proven for CARLA graphics/Vulkan
- spawned follow-ups: full route score execution ticket when host is available
- complexity: M

### Summary

Keep the benchmark-purity track alive without letting it block the scripted
submission. This ticket packages the exact host requirements, route command,
artifacts, and diagnostics needed to run full stock Fail2Drive scoring on a
graphics-capable Linux CARLA host.

### Scope

- In scope: host suitability checklist, remote sync/run plan, CARLA graphics
  diagnostics, route command pack, expected outputs, and blocker classifier.
- Out of scope: renting a new host, spending money, rebuilding SimLingo, or
  claiming score evidence before the route finishes.

### Gap Analysis

- Current state: local Mac/Kegworks route starts and emits early video but is
  too slow for full score; H100 SimLingo path blocked on Vulkan/graphics.
- Production expectation: stock Fail2Drive scoring needs a Linux host where
  CARLA can render/tick and the Python evaluator can run long enough to finish.
- Missing gaps: reproducible host checklist, one-command remote attempt, and
  compact diagnostics that separate missing GPU graphics from Python/model
  issues.
- Recommendation: produce the handoff bundle now; execute only when an
  appropriate graphics host is available.

### Plan

#### Change

Add a `plan-full-fail2drive-score-host` or equivalent script/report that
validates host capabilities, emits the exact Docker/native route run command,
and explains how to pull back compact score/video/log evidence.

#### Why

This prevents us from repeatedly losing time to ad hoc runtime setup while the
main submission progresses.

#### Before -> After

- Before: stock Fail2Drive full score is a known blocker with scattered
  diagnostics.
- After: there is one auditable handoff bundle telling the operator which host
  is acceptable and exactly what command/evidence to run.

#### Touch

- `scripts/sync_remote_gpu.sh`: reuse; no change expected unless current args
  cannot support a graphics host.
- `scripts/run_remote_fail2drive_score.sh`: new optional wrapper if useful.
- `src/driverx/simulators/fail2drive_host_plan.py`: host checklist and command
  plan.
- `src/driverx/simulators/fail2drive_host_plan_cli.py`: CLI registration.
- `src/driverx/pipeline/route_evidence.py`: ensure compact pullback paths are
  documented.
- `tests/test_fail2drive_host_plan.py`.
- `README.md`, `blockers.md`, `docs/progress.md`.

#### Inspect

- `tickets/TASK-060/artifacts/town13-long-score-attempt-001-evidence/run_evidence.md`
- `tickets/archive/TASK-020/artifacts/task20-remote/carla_runtime_diagnostics.md`
- `scripts/run_fail2drive_client_docker.sh`
- `scripts/sync_remote_gpu.sh`
- `docs/MEMORY.md` `MEM-0012`, `MEM-0017`, `MEM-0020`

#### Signature Delta

```python
src/driverx/simulators/fail2drive_host_plan.py / build_fail2drive_host_plan(config: Fail2DriveHostPlanConfig) -> Fail2DriveHostPlan
src/driverx/simulators/fail2drive_host_plan.py / classify_graphics_host_diagnostics(payload: dict[str, Any]) -> HostSuitability
src/driverx/simulators/fail2drive_host_plan.py / write_fail2drive_host_plan(run_dir: Path, plan: Fail2DriveHostPlan) -> dict[str, Any]
```

#### Type Sketch

```python
Fail2DriveHostPlan = {
  "target_route": "Generalization_PedestriansOnRoad_1088",
  "required": ["NVIDIA GPU", "working Vulkan/OpenGL CARLA render", "CARLA 0.9.16 or matching Fail2Drive setup", "Docker/native Python client"],
  "recommended_gpus": ["RTX A6000", "RTX 3090", "L40S", "A40"],
  "not_sufficient_alone": ["CUDA visible without graphics ICD"],
  "commands": list[str],
  "expected_outputs": list[str],
  "pullback_policy": {"include": ["json", "md", "logs"], "exclude": ["weights", "videos unless explicitly requested"]},
}
```

#### Typed Flow Example

`host ssh target + route config`
-> `plan-full-fail2drive-score-host`
-> `host_suitability_plan.md`
-> operator rents/points host
-> future execution ticket runs one score attempt and ingests route evidence.

#### Execution Steps

1. Consolidate current blockers and diagnostics into one host suitability model.
2. Add CLI/report builder with no external side effects.
3. Add tests for suitable host, CUDA-only-but-no-graphics host, and missing
   CARLA outputs.
4. Update blockers with exact host request language.
5. Defer actual spend/execution to a future ticket once host details exist.

#### Recommendation

Do not spend more time forcing full Fail2Drive score on the Mac or the current
headless inference pod. Keep it as a prepared handoff while the submission uses
scripted CARLA evidence.

#### Options Considered

- Keep rerunning locally: low odds; already observed route cadence stalls.
- Rebuild CARLA/SimLingo stacks: too large for current submission path.
- Prepare host handoff: best; preserves benchmark path without blocking.

#### Blast Radius

- Planning/reporting scripts only.
- No simulator execution unless a future ticket runs the plan.

#### Risks

- Host recommendations can drift by provider; keep them capability-based
  rather than provider-specific.
- Operator may confuse Alpamayo inference GPU with CARLA graphics host; report
  must state that RTX 6000 Ada is enough for Alpamayo but not proven for CARLA
  graphics.

### Acceptance Criteria

- [x] AC-1: Host plan command writes JSON/Markdown with requirements, commands, expected outputs, and pullback policy.
- [x] AC-2: Classifier distinguishes CUDA-only inference suitability from CARLA graphics suitability.
- [x] AC-3: Blockers/docs state exactly what host is needed and why the current path is blocked.
- [x] AC-4: No external spend, deploy, or remote execution happens in this ticket.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_host_plan`
- `PYTHONPATH=src python3 -m driverx plan-full-fail2drive-score-host --run-id task88-host-plan`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Fully local.
- Human gate remains: provide or approve a graphics-capable Linux CARLA host
  before actual full-score execution.

### Evidence

- Planned 2026-05-06 from TASK-060/TASK-071 blockers.
- Plan review: `docs/reviews/TASK-083-088-impl-plan-review.md`.
- Implementation review: `docs/reviews/TASK-083-088-implementation-review.md`.
- QA report: `tickets/TASK-087/artifacts/qa/TASK-083-088-qa-report.md`.
- Implemented 2026-05-06. Evidence:
  `tickets/TASK-088/artifacts/task88-host-plan/fail2drive_host_plan.md`.

### Blockers

- Actual route execution waits on a graphics-capable Linux CARLA host.
