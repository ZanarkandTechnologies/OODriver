# TASK-159: Productized Alpamayo Inference Bridge For Closed Loop

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-129, TASK-157, TASK-158
- location: `src/driverx/policies`, `src/driverx/scenarios/studio_product_cli.py`, `scripts`, `tests`, `tickets/TASK-159`
- enter when: the paused runner can request a trajectory per checkpoint, but Alpamayo inference is still manual/remote-script shaped.
- leave when: OODrive exposes an inference adapter usable by the closed-loop runner, with local fake, cached JSON, and remote Kasm command modes, plus latency/VRAM/blocker reporting per checkpoint.
- blockers: real remote Alpamayo requires Kasm/HF auth; local tests use fake/cached modes.
- spawned follow-ups: TASK-160
- complexity: L

### Summary

Productize the Alpamayo step enough for the closed-loop runner. This supersedes the useful parts of TASK-129 for the deadline path: one adapter interface that accepts an Alpamayo package and returns prediction JSON, latency, VRAM, reasoning, and blockers.

### Gap Analysis

- Current state: `scripts/run_remote_alpamayo_carla_inference.sh` and TASK-104 batch records can invoke/reuse remote Alpamayo, but `oodrive` does not expose a simple inference command for step-by-step closed-loop use.
- Production expectation: the controller calls a policy inference adapter with timeout, environment, output path, and structured failure records.
- Missing gaps: no `oodrive infer`, no per-checkpoint remote/cached/fake adapter, no timeout semantics, no model mode labels.
- Recommendation: implement the adapter before live Kasm runs; do not optimize latency yet.

### Plan

#### Change

Add:

```bash
PYTHONPATH=src python3 -m oodrive infer \
  --package artifacts/runs/task158/step_000/alpamayo_package.json \
  --mode cached-json \
  --prediction-json tickets/archive/TASK-100/artifacts/hero-alpamayo-live/alpamayo_live_prediction.json \
  --run-id task159-infer-smoke
```

Remote mode:

```bash
PYTHONPATH=src python3 -m oodrive infer \
  --package <alpamayo_package.json> \
  --mode remote-kasm \
  --remote-output-root /workspace/driverx_remote_artifacts/closed-loop \
  --run-id <step-id>
```

#### Why

The runner should not shell out to fragile ad hoc scripts directly. It needs a structured result with prediction path, latency, VRAM, model mode, and blockers.

#### Before -> After

- Before: Alpamayo inference is batch/manual and external to `oodrive`.
- After: `oodrive infer` returns a standardized prediction artifact the closed-loop runner can consume.

#### Touch

- `src/driverx/policies/alpamayo_inference_bridge.py` (new)
- `src/driverx/scenarios/studio_product_infer_runtime.py` (new)
- `src/driverx/scenarios/studio_product_cli.py`
- `scripts/run_remote_alpamayo_carla_inference.sh` (inspect, avoid token heredocs)
- `tests/test_alpamayo_inference_bridge.py` (new)
- `tests/test_oodrive_cli.py`

#### Inspect

- `src/driverx/pipeline/alpamayo_ood_batch.py`
- `src/driverx/policies/alpamayo_materializer.py`
- `src/driverx/policies/alpamayo_live.py`
- `scripts/run_remote_alpamayo_carla_inference.sh`
- `docs/MEMORY.md` MEM-0027, MEM-0038

#### Signature Delta

```python
run_alpamayo_inference_bridge(package_path: Path, mode: Literal["fake", "cached-json", "remote-kasm"], output_root: Path, run_id: str, prediction_json: Path | None = None) -> dict[str, Any]
run_studio_infer(...) -> StudioCommandResult
```

#### Type Sketch

```python
AlpamayoInferenceResult = {
  "status": "passed" | "blocked" | "failed",
  "mode": "fake" | "cached-json" | "remote-kasm",
  "package_path": str,
  "prediction_json_path": str | None,
  "latency_ms": float | None,
  "vram_peak_mb": float | None,
  "reasoning_snippet": str | None,
  "trajectory_shape": list[int] | None,
  "blockers": list[str],
  "claim_boundaries": list[str],
}
```

#### Typed Flow Example

`ClosedLoopObservation.alpamayo_package_path`
-> `run_alpamayo_inference_bridge(mode="cached-json")`
-> `AlpamayoInferenceResult(prediction_json_path=...)`
-> `build_alpamayo_live_decision`
-> `trajectory_to_control_trace`
-> closed-loop step control chunk.

#### Execution Steps

1. Implement fake and cached-json inference modes locally.
2. Wrap the existing remote script in a structured command builder that never sends secrets through Kasm proxy heredocs.
3. Add timeout/blocker fields per checkpoint.
4. Register `oodrive infer`.
5. Add tests for cached/fake outputs, missing package, missing prediction, and remote blocked config.
6. Update TASK-158 runner to call the bridge through an adapter hook.

#### Recommendation

Ship fake/cached modes first, then run remote Kasm manually through the same CLI. Latency optimization is a later ticket.

#### Options Considered

- Directly import Alpamayo model in-process: too risky and memory-heavy for the runner.
- Persistent model server: best long-term but not first deadline slice.
- Structured CLI bridge: fastest credible bridge.

#### Blast Radius

- Additive policy/CLI command.
- No secrets committed or transmitted.

#### Risks

- Remote proxy echoes commands. Mitigation: no tokens in command streams; follow MEM-0027.
- Latency too high for real-time. Mitigation: claim `real_time_vla_control=false`.

### Acceptance Criteria

- [ ] AC-1: `oodrive infer` writes prediction result JSON/Markdown in fake and cached-json modes.
- [ ] AC-2: Inference result includes latency, trajectory shape, reasoning snippet, and claim boundaries when available.
- [ ] AC-3: Remote mode produces precise blockers without secrets.
- [ ] AC-4: Closed-loop runner can consume the inference bridge through a local fake/cached adapter.

### Verification

```bash
PYTHONPATH=src python3 -m unittest tests.test_alpamayo_inference_bridge tests.test_alpamayo_live tests.test_oodrive_cli
bash scripts/pre_push_check.sh
```

### Blockers

- Remote live inference requires Kasm/HF auth and GPU availability.

### Implementation Evidence

- Added `src/driverx/policies/alpamayo_inference_bridge.py` and `oodrive infer`.
- Fake mode writes prediction/result artifacts; cached-json mode copies prediction artifacts; remote-kasm mode writes a safe blocked handoff manifest.
- Smoke confirmed fake inference passed and remote-kasm blocked with no claim upgrade.
- `tests.test_alpamayo_handoff` passed; full `bash scripts/pre_push_check.sh` passed with `456 tests OK, 5 skipped`.
- Review: `tickets/TASK-161/artifacts/review/task157-164-impl-review.json`

### Plan Review

- `tickets/TASK-157/artifacts/review/task157-160-closed-loop-plan-review.json`
