# TASK-092: Behavior Scenario DSL And Solvability Validator

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-089
- location: `src/driverx/behaviors`, `src/driverx/scenarios`, `tests`, docs, `tickets/TASK-092/artifacts`
- enter when: existing behavior traces are useful but under-specified and not validated for lane-relative starts, conflicts, visibility, or solvability
- leave when: behaviors are generated from a small DSL, validated against road-frame constraints, and reported with conflict/solvability metrics
- blockers: none
- spawned follow-ups: TASK-093 campaign quality gates consume behavior validation
- complexity: M

### Summary

Turn the regional driving examples into a configurable behavior generator rather
than a fixed list of traces. We still keep deterministic outputs, but the
operator can vary aggressiveness, start lane, reaction timing, and actor type.

### Scope

- In scope: behavior DSL, parameterized behavior families, validation metrics,
  scenario-local coordinate constraints, and report generation.
- Out of scope: CARLA Traffic Manager integration, learned driver policies, or
  multi-agent planning.

### Gap Analysis

- Current state: eight hand-written behavior traces exist, including
  motorcycle filtering and unsignaled U-turn, but they are not validated for
  conflict timing or road-frame legality.
- Production expectation: scenario generation should create many variants of
  "Malaysian-style no-signal merge", "sudden brake", "lane-splitting
  motorbike", and "wrong-way shoulder creep" while guaranteeing that the
  setup is physically meaningful enough to test a policy.
- Missing gaps: parameter schema, deterministic sampling, metrics such as
  time-to-conflict/min-distance/visibility window, and failure-mode labels.
- Recommendation: add a small declarative DSL instead of hard-coding more trace
  arrays.

### Plan

#### Change

Add behavior templates and a compiler from behavior parameters to
`BehaviorPlan`, plus a validator that checks road-local starts, conflict
windows, speeds, accelerations, and solvability.

#### Why

Minimal-shot testing needs scenario diversity. Parameterized behaviors let us
generate 10/100 variants without hand-authoring every trace.

#### Before -> After

- Before: `motorcycle_filtering` is one trace.
- After: `motorcycle_filtering` is a behavior family with variations over
  lateral gap, speed, conflict timing, and aggressiveness.

#### Touch

- `src/driverx/behaviors/dsl.py`: new template and parameter compiler.
- `src/driverx/behaviors/validators.py`: behavior quality metrics.
- `src/driverx/behaviors/library.py`: migrate existing behaviors into DSL
  templates while preserving IDs.
- `src/driverx/scenarios/generator.py`: select behavior parameters from
  mutation policy.
- `src/driverx/behaviors/reports.py`: behavior suite report.
- `tests/test_behavior_dsl.py`, `tests/test_behaviors.py`.

#### Inspect

- `src/driverx/behaviors/types.py`
- `src/driverx/behaviors/library.py`
- `src/driverx/pipeline/local_ood_sim.py`
- `src/driverx/pipeline/scripted_ood_campaign.py`

#### Signature Delta

```python
compile_behavior_template(template: BehaviorTemplate, params: BehaviorParameters) -> BehaviorPlan
validate_behavior_plan(plan: BehaviorPlan, constraints: BehaviorConstraints) -> BehaviorValidationReport
generate_behavior_variants(template_id: str, count: int, random_seed: int, severity: int) -> list[BehaviorPlan]
```

#### Type Sketch

```python
BehaviorValidationReport = {
  "behavior_id": str,
  "starts_in_allowed_zone": bool,
  "max_speed_mps": float,
  "max_accel_mps2": float | None,
  "min_ego_distance_m": float | None,
  "time_to_conflict_s": float | None,
  "visibility_window_s": float | None,
  "solvable": bool,
  "warnings": list[str],
}
```

#### Typed Flow Example

`template=motorcycle_filtering + severity=4 + seed=11`
-> behavior params
-> compiled road-local trace
-> validation metrics
-> catalog quality fields
-> campaign runner.

#### Execution Steps

1. Define behavior template schema and compiler.
2. Port existing eight behavior IDs through templates or adapters.
3. Add parameterized variants for motorbike lane splitting, sudden brake,
   no-signal cut-in, wrong-way shoulder creep, double-parked door swerve, and
   unsignaled U-turn.
4. Add validation reports and tests.
5. Feed validation metrics into scenario reports.

#### Recommendation

Implement this in parallel after TASK-089 fake tests, but only promote videos
after TASK-093 quality gates consume the validator.

#### Options Considered

- Add more fixed traces: quick but scales poorly.
- Integrate CARLA Traffic Manager behaviors now: higher fidelity but harder to
  control deterministically.
- Build a simple DSL and validator: best current path for lots of repeatable
  OOD cases.

#### Blast Radius

- Moderate: behavior library internals change, but public `load_behavior_plan`
  should remain compatible.

#### Risks

- Over-validating can reject interesting edge cases. Keep severity labels and
  warnings separate from hard failures.

### Acceptance Criteria

- [x] AC-1: Existing behavior IDs still load and produce comparable traces.
- [x] AC-2: At least six behavior families can generate deterministic variants.
- [x] AC-3: Validation report includes starts-in-zone, min distance, conflict
  timing, and solvability fields.
- [x] AC-4: Invalid/off-road/impossible starts fail validation before live CARLA
  execution.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_behavior_dsl tests.test_behaviors`
- `PYTHONPATH=src python3 -m driverx report-behaviors --run-id task92-behavior-dsl`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Fully local and independent of CARLA/GPU.

### Evidence

- Planned 2026-05-06 to make regional driving behavior generation a real
  simulator contribution.
- Plan review: `docs/reviews/TASK-089-095-impl-plan-review.md`.
- Implemented behavior DSL templates, deterministic variant generation, and
  solvability/conflict validation in `src/driverx/behaviors`.
- Focused tests passed:
  `PYTHONPATH=src python3 -m unittest tests.test_behavior_dsl tests.test_behaviors tests.test_cli`.
- Generated behavior DSL evidence:
  `tickets/TASK-092/artifacts/behavior-dsl-v2/behavior_report.md` and
  `tickets/TASK-092/artifacts/behavior-dsl-v2/validation/behavior_validation.md`.

### Blockers

- None.
