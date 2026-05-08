# TASK-134: OODrive Product Loop Hardening

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-129, TASK-132
- location: `src/driverx/policies`, `src/driverx/scenarios`, `src/oodrive`, `tests`, `docs`
- enter when: the submission scorecard shows repeatability, manual-inference, or code-quality blockers below the 90-point target
- leave when: OODrive can run the product loop with a first-class `infer` step or a clean blocked artifact, and the product runtime is modular enough for future work to change one command without spelunking the whole CLI
- blockers: real Alpamayo execution still requires a configured GPU/model environment; local fake-backend proof is not blocked
- spawned follow-ups: close or archive TASK-129 as superseded after `oodrive infer` lands here
- complexity: L

### Summary

Turn the TASK-128 manual Alpamayo bridge into a product command and reduce the
code-quality risk around the OODrive runtime. This ticket is the "actually
works as a product" lane: the loop should be operator-simple, fail cleanly when
GPU dependencies are missing, and avoid adding more behavior into already large
runtime files.

### Scope

- In scope: `oodrive infer`, fake-backend tests, clean blocked artifacts for
  missing GPU/model dependencies, DB artifact writeback, next-command guidance,
  and a focused module split around OODrive command runtime/report code.
- Out of scope: SSH orchestration, HF token management, fresh closed-loop VLA
  control, and broad cleanup outside the product loop.

### Plan

#### Change

Make the canonical loop demonstrably product-owned:

```bash
oodrive generate -> oodrive place -> oodrive infer -> oodrive reason -> oodrive demo-video -> oodrive score-demo -> oodrive score-submission
```

`oodrive infer` should support:

```bash
PYTHONPATH=src python3 -m oodrive infer \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --run artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/run_manifest.json \
  --run-id task134-infer-proof
```

When Alpamayo is unavailable locally, it writes an explicit blocked artifact
instead of raising an opaque import/CUDA error.

#### Why

A 90th-percentile submission cannot rely on a hidden manual bridge for the
model step or a growing all-in-one runtime file for every product command.
Repeatability and code quality are part of the proof that OODrive is a harness,
not a one-off demo.

#### Before -> After

- Before: live Alpamayo inference is real but manual, and command logic is
  concentrated in large product runtime modules.
- After: inference is a product command with fake/local blocked/real modes, and
  new command behavior lives in focused modules with clear tests.

#### Touch

- `src/driverx/policies/alpamayo_local_inference.py`
- `src/driverx/policies/alpamayo_local_inference_cli.py`
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/scenarios/studio_product_runtime.py`
- `src/driverx/scenarios/studio_product_reports.py`
- `src/driverx/scenarios/studio_runtime/*` or an equivalent focused runtime
  package if the local code shape prefers another name
- `src/driverx/cli_extensions.py`
- `src/oodrive/__main__.py`
- `tests/test_alpamayo_local_inference.py`
- `tests/test_oodrive_cli.py`
- `tests/test_submission_readiness_score.py`
- nearest module `README.md` / `AGENTS.md` if a new runtime package is added

#### Inspect

- `tickets/TASK-129/ticket.md`
- `src/driverx/scenarios/studio_product_runtime.py`
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/policies`
- `scripts/run_remote_alpamayo_carla_inference.sh`
- `tickets/TASK-128/artifacts/qa/live-product-loop-qa.md`
- `docs/MEMORY.md`
- `docs/TROUBLES.md`

#### Signature Delta

```python
stage_alpamayo_package_for_local_inference(
    *,
    db_path: Path,
    run_manifest_path: Path,
    output_root: Path,
    run_id: str,
) -> AlpamayoInferencePackage

run_alpamayo_local_inference(
    package: AlpamayoInferencePackage,
    *,
    output_root: Path,
    backend: AlpamayoInferenceBackend,
    run_id: str,
) -> AlpamayoInferenceResult

run_studio_infer(
    db_path: Path,
    *,
    run_manifest_path: Path,
    package_path: Path | None,
    output_root: Path | None,
    run_id: str | None,
    fake_backend: bool = False,
) -> StudioCommandResult
```

#### Type Sketch

```python
AlpamayoInferencePackage = {
  "package_path": str,
  "frames": list[str],
  "scenario_id": str,
  "run_id": str,
  "source_run_manifest": str,
}

AlpamayoInferenceResult = {
  "status": "passed" | "blocked" | "failed",
  "prediction_path": str | None,
  "summary_path": str,
  "blockers": list[str],
  "next_command": str | None,
  "latency_ms": float | None,
  "vram_peak_mb": float | None,
}
```

#### Typed Flow Example

`oodrive infer --db ... --run ... --fake-backend`
-> stage package from CARLA frames
-> fake backend writes deterministic prediction
-> DB stores inference artifact
-> result prints exact `oodrive reason --prediction-json ...`
-> `score-submission` removes manual-bridge penalty.

#### Execution Steps

1. Merge the intent of TASK-129 into this hardening ticket without duplicating
   command semantics.
2. Add the smallest focused runtime module boundary needed before adding more
   inference logic.
3. Implement fake-backend inference first and prove DB writeback plus next
   command generation.
4. Implement local Alpamayo dependency detection and blocked-artifact output.
5. Wire `oodrive infer` into the product-facing CLI.
6. Update `score-submission` to award reproducibility credit for the fake/local
   proof and to keep a blocker for missing real GPU proof.
7. Run focused tests, `./autoresearch.sh`, guards, pre-push, and review.
8. Mark TASK-129 superseded or done with evidence once this ticket lands.

#### Recommendation

Do this third. It is higher ROI than fresh CARLA setup because it removes the
manual product gap and improves the code surface future tickets will touch.

#### Options Considered

- Implement TASK-129 alone: useful but too narrow for the user's code-quality
  concern.
- Do a broad refactor first: rejected because it risks churn without improving
  the submission.
- Product hardening around `infer`: selected because it improves uniqueness,
  repeatability, and code structure in one focused lane.

#### Blast Radius

- Product CLI gains one command.
- Runtime code moves toward focused modules; compatibility aliases must remain
  intact.
- Real GPU proof remains optional and honestly labeled unless available.

#### Risks

- Refactor scope can sprawl; keep it limited to command runtime/report seams
  needed for `infer` and readiness scoring.
- Fake backend must not be presented as real Alpamayo evidence.
- Local GPU dependency detection can be brittle; blocked artifacts must include
  exact missing imports/devices and suggested Kasm path.

### Gap Analysis

- Current proof is not operator-simple because the Alpamayo step still depends
  on manual remote/package choreography.
- Current code quality risk is visible in large product runtime files and a
  command surface that keeps accumulating responsibilities.
- The 90-point submission needs repeatability: a reviewer should be able to
  run the loop locally with fake inference and understand exactly what extra
  GPU setup is needed for real Alpamayo inference.

### Acceptance Criteria

- [ ] AC-1: `oodrive infer --help` exists and is documented as product-facing.
- [ ] AC-2: Fake-backend `oodrive infer` writes deterministic prediction,
  summary, DB artifact, and next `oodrive reason` command.
- [ ] AC-3: Missing Alpamayo/CUDA dependencies write a blocked artifact with
  concrete setup blockers and no stack trace.
- [ ] AC-4: Runtime/report code touched by this ticket is split into focused
  modules rather than growing the existing large file.
- [ ] AC-5: `oodrive score-submission` removes the manual-bridge blocker when
  the fake/local inference proof exists, while preserving the real-GPU blocker
  if no real Alpamayo run exists.
- [ ] AC-6: Claim boundaries remain honest and unchanged.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_local_inference tests.test_oodrive_cli tests.test_submission_readiness_score`
- `PYTHONPATH=src python3 -m oodrive infer --help`
- `PYTHONPATH=src python3 -m oodrive infer ... --fake-backend`
- `PYTHONPATH=src python3 -m oodrive score-submission ... --metric-only`
- `./autoresearch.sh`
- `./autoresearch.checks.sh`
- `bash scripts/pre_push_check.sh`
- Optional Kasm real Alpamayo proof if the configured GPU environment is live.
- Review result linked from this ticket before completion claim.

### Evidence

- Plan review:
  `tickets/TASK-132/artifacts/review/task132-134-planning-review.json`
- Partial prerequisite: TASK-133 moved submission scoring/export runtime into
  `src/driverx/scenarios/studio_product_submission_runtime.py` after the
  pre-push size gate caught `studio_product_runtime.py` crossing 1000 lines.
  The remaining TASK-134 scope is still `oodrive infer` and broader product
  loop hardening.

### Blockers

- Real Alpamayo execution requires a configured GPU/model environment; local
  fake-backend and blocked-artifact behavior are not blocked.
