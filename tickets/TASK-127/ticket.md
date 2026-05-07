# TASK-127: OODrive Place-And-Reason Product Loop

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-126
- location: `src/driverx/scenarios`, `src/oodrive`, `tests`, `docs`
- enter when: placement plans exist but the product lacks direct `place` and `reason` commands
- leave when: `oodrive place` can dry-run or live-run the CARLA OOD demo and `oodrive reason` attaches Alpamayo reasoning/cached prediction evidence to the run
- blockers: live CARLA and live Alpamayo remain environment-dependent; local tests use dry-run and cached prediction
- spawned follow-ups: TASK-128 live closed-loop/replay hardening if needed
- complexity: M

### Summary

Expose the runtime half of the product loop. A generated placement plan should
be runnable through CARLA when available, and the resulting run should have a
single reasoning command that packages CARLA evidence for Alpamayo and attaches
model reasoning when a prediction JSON is available.

### Scope

- In scope: `oodrive place`, `oodrive reason`, dry-run manifest, live CARLA
  execution wrapper, Alpamayo package creation from CARLA demo artifacts when
  possible, cached reasoning evaluation, replay bundle handoff.
- Out of scope: Alpamayo real-time steering and true closed-loop control claims.

### Plan

#### Change

Add product commands:

```bash
oodrive place --db artifacts/runs/demo/scenario_studio_db.json --live
oodrive reason --db artifacts/runs/demo/scenario_studio_db.json \
  --prediction-json alpamayo_live_prediction.json
```

`place` records either a live CARLA OOD demo result or a dry-run placement
manifest. `reason` attaches Alpamayo reasoning/cached trajectory evidence and
builds the replay bundle used by final demo tooling.

#### Why

The submission user story is not complete until the generated scenario flows
into simulator evidence and model reasoning. The CLI must make this path obvious
and mechanically testable.

#### Before -> After

- Before: users manually stitch together `run-carla-ood-demo`,
  `build-alpamayo-ood-package`, `evaluate`, and `replay`.
- After: users run `oodrive place` and `oodrive reason`, with DB artifacts
  tracking the path.

#### Touch

- `src/driverx/scenarios/studio_runtime.py`
- `src/driverx/scenarios/studio_product.py`
- `src/driverx/scenarios/studio_product_cli.py`
- `tests/test_oodrive_cli.py`
- `README.md`, `docs/HISTORY.md`

#### Signature Delta

```python
run_studio_place(
    db_path: Path,
    *,
    scenario_id: str | None,
    placement_path: Path | None,
    config_path: Path,
    output_root: Path | None,
    run_id: str | None,
    live: bool,
) -> StudioCommandResult

run_studio_reason(
    db_path: Path,
    *,
    run_manifest_path: Path | None,
    prediction_json: Path | None,
    output_root: Path | None,
    run_id: str | None,
    memory: str,
) -> StudioCommandResult
```

#### Type Sketch

```python
PlaceResult = {
  "run_manifest": str,
  "placement_plan": str,
  "carla_ood_demo": str | None,
  "objects_placed": bool,
  "live": bool,
}

ReasonResult = {
  "evaluation": str,
  "bundle": str | None,
  "alpamayo_package": str | None,
  "policy_decision": str | None,
  "sampled_open_loop_reasoning": bool,
}
```

#### Typed Flow Example

Placement plan with two static generated objects
-> `oodrive place --live`
-> `carla_ood_demo.json` with RGB/tracks when CARLA is reachable, or precise
CARLA blocker when not
-> `oodrive reason --prediction-json ...`
-> `policy_evaluation.json` with CoC snippet
-> replay bundle/export surfaces.

#### Execution Steps

1. Add reusable placement reconstruction helpers shared by dry-run and live
   execution.
2. Implement `run_studio_place` and `run_studio_reason`.
3. Wire parser commands and product next-command chain.
4. Add dry-run and cached-prediction tests.
5. Update docs and evidence.

### Acceptance Criteria

- [x] AC-1: `oodrive place` writes a run manifest from a generated placement.
- [x] AC-2: `oodrive place --live` calls the existing CARLA OOD demo runner and
  records clean blockers if CARLA is unavailable.
- [x] AC-3: `oodrive reason --prediction-json ...` writes an evaluation with
  Alpamayo reasoning text and replay bundle.
- [x] AC-4: Claims distinguish dry-run, live scripted CARLA, open-loop
  Alpamayo reasoning, and no real-time VLA control.

### Verification

- Focused unit tests for dry-run place and cached reason.
- CLI smoke through generate -> place -> reason.
- `bash scripts/pre_push_check.sh`.

### Evidence

- QA report: `tickets/TASK-127/artifacts/qa/place-reason-qa.md`.
- Review: `docs/reviews/TASK-126-127-oodrive-product-loop-review.md`.
- Dry-run manifest:
  `artifacts/runs/oodrive-generate-place-smoke-v2/runs/oodrive-smoke-v2-dry-place/run_manifest.json`.
- Cached Alpamayo reasoning:
  `artifacts/runs/oodrive-generate-place-smoke-v2/reasoning/evaluations/oodrive-smoke-v2-reason-evaluation/policy_evaluation.json`.
- Replay bundle:
  `artifacts/runs/oodrive-generate-place-smoke-v2/reasoning/bundles/oodrive-smoke-v2-reason-bundle/scenario_run_bundle.json`.
- Live CARLA blocked manifest:
  `artifacts/runs/oodrive-generate-place-smoke-v2/runs/oodrive-smoke-v2-live-place/run_manifest.json`.
- Full gate: `bash scripts/pre_push_check.sh`.

### Blockers

- Live Docker path timed out against `host.docker.internal:2000` in this pass.
  The command reached the CARLA OOD demo runner and wrote a clean blocked run
  manifest; rerun once CARLA is reachable from Docker or from the graphics pod.
