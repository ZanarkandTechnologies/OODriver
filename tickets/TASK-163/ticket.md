# TASK-163: Robust Alpamayo Inference Handoff And Cache Contract

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-159, TASK-161
- location: `src/driverx/policies`, `src/driverx/remote`, `scripts`, `tests`, `tickets/TASK-163`
- enter when: `oodrive infer` exists or is being implemented for fake/cached/remote Alpamayo checkpoint inference.
- leave when: Alpamayo inference handoff is resumable, timeout-aware, cache-keyed by checkpoint content, safe for Kasm proxy constraints, and produces precise blocked/failed/passed result artifacts per checkpoint.
- blockers: real remote mode still requires Kasm/HF auth installed through a safe channel.
- spawned follow-ups: none
- complexity: M

### Summary

Make Alpamayo inference usable inside a long-running closed-loop run. The current model lane is slow and remote, so the integration needs a strong handoff contract: content-addressed packages, cached predictions, timeout and retry semantics, structured blocker reports, and no secret-bearing SSH heredocs.

### Scope

In scope:
- Cache key for Alpamayo packages.
- Per-checkpoint inference result with latency, mode, status, prediction path, and blocker detail.
- Timeout/retry handling for remote commands.
- Resume behavior when a prediction already exists.
- Safe Kasm handoff docs/command construction that never embeds secrets.

Out of scope:
- Optimizing Alpamayo latency.
- Persistent model server.
- Installing HF credentials.

### Gap Analysis

Current state:
- TASK-159 plans `oodrive infer` but the remote lane can still become an ad hoc shell boundary.
- `scripts/run_remote_alpamayo_carla_inference.sh` exists for older remote inference flows.
- `docs/MEMORY.md` MEM-0027 forbids sending secrets through Kasm proxy SSH heredocs.

Production expectation:
- Closed-loop runtime can pause for inference without corrupting state.
- If Alpamayo is slow or unavailable, the trace records a precise blocked state.
- Re-running the same checkpoint should reuse cached prediction artifacts.
- Remote commands should be auditable and secret-safe.

Missing gaps:
- No checkpoint content hash/cache contract.
- No retry/timeout schema shared by runner and CLI.
- No artifact-level distinction between blocked remote config and model failure.
- No remote handoff manifest that can be copied independently of secrets.

Recommendation:
- Harden the bridge as a manifest/cached-result protocol before TASK-160 live proof.

### Plan

#### Change

Add a resumable inference request/result contract:

```bash
PYTHONPATH=src python3 -m oodrive infer \
  --package artifacts/runs/task158/step_000/alpamayo_carla_input_package.json \
  --mode remote-kasm \
  --timeout-s 180 \
  --cache-root artifacts/cache/alpamayo \
  --run-id task163-step-000
```

#### Why

The closed-loop runner cannot be robust if the model call is a brittle one-off. It needs to know whether it should wait, resume, retry, use cache, or stop and preserve honest claims.

#### Before -> After

- Before: inference is a manual/batch-shaped step with weak closed-loop runtime semantics.
- After: each checkpoint writes `alpamayo_inference_result.json` with `status`, `cache_key`, `latency_ms`, `prediction_json_path`, `remote_manifest_path`, and `blockers`.

#### Touch

- `src/driverx/policies/alpamayo_inference_bridge.py` (from TASK-159)
- `src/driverx/remote/alpamayo_handoff.py` (new)
- `src/driverx/scenarios/studio_product_infer_runtime.py` (from TASK-159)
- `src/driverx/simulators/carla_closed_loop_runner.py` (from TASK-158)
- `scripts/run_remote_alpamayo_carla_inference.sh` (inspect/update only if needed)
- `tests/test_alpamayo_inference_bridge.py`
- `tests/test_alpamayo_handoff.py` (new)

#### Inspect

- `src/driverx/policies/alpamayo_live.py`
- `src/driverx/policies/alpamayo_materializer.py`
- `src/driverx/pipeline/alpamayo_ood_batch.py`
- `src/driverx/remote/README.md`
- `docs/MEMORY.md` MEM-0019, MEM-0027, MEM-0028

#### Signature Delta

```python
src/driverx/remote/alpamayo_handoff.py / build_alpamayo_handoff_manifest(package_path: Path, output_root: Path): AlpamayoHandoffManifest
src/driverx/remote/alpamayo_handoff.py / package_cache_key(package_path: Path): str
src/driverx/policies/alpamayo_inference_bridge.py / run_alpamayo_inference_bridge(..., timeout_s: float, cache_root: Path | None, retries: int): AlpamayoInferenceResult
src/driverx/policies/alpamayo_inference_bridge.py / load_or_block_cached_prediction(cache_key: str, cache_root: Path): AlpamayoInferenceResult
```

#### Type Sketch

```python
AlpamayoInferenceRequest = {
  "package_path": str,
  "package_sha256": str,
  "cache_key": str,
  "mode": "fake" | "cached-json" | "remote-kasm",
  "timeout_s": float,
  "retries": int,
  "remote_output_root": str | None
}

AlpamayoInferenceResult = {
  "status": "passed" | "blocked" | "failed" | "cached",
  "cache_key": str,
  "prediction_json_path": str | None,
  "latency_ms": float | None,
  "vram_peak_mb": float | None,
  "reasoning_snippet": str | None,
  "blockers": list[str],
  "safe_for_kasm_proxy": bool
}
```

#### Typed Flow Example

Closed-loop step 1 writes a synced package. `oodrive infer` computes `cache_key=sha256(package+mode)`, finds no local cached prediction, writes a remote handoff manifest, and returns `blocked` if Kasm credentials are absent. A later run with the prediction copied back resolves the same cache key as `cached`.

#### Execution Steps

1. Implement package hashing and handoff manifest writing.
2. Add fake and cached modes that populate the same result schema as remote mode.
3. Add timeout/retry fields and blocked-vs-failed distinction.
4. Add cache lookup and cache write after successful prediction.
5. Add Kasm-safe command rendering with no secrets in generated command text.
6. Wire closed-loop runner to resume from inference results instead of shelling directly.
7. Test missing package, cached hit, cached miss, remote blocked, timeout failure, and result schema stability.

#### Recommendation

Use cache-first remote inference. Alpamayo latency is high enough that resumability matters more than elegance.

#### Options Considered

- Direct in-process Alpamayo import: too risky for memory/runtime isolation.
- Persistent server: desirable later, but too much new infrastructure.
- File-manifest bridge: reliable, inspectable, and compatible with Kasm constraints.

#### Blast Radius

- Inference CLI/runtime and closed-loop runner adapter.
- No model weights or secrets enter git.

#### Risks

- Cache could reuse a prediction for the wrong package. Mitigation: cache key includes package bytes and mode metadata.
- Remote failures could be mistaken for model failures. Mitigation: use `blocked` for missing config/credentials and `failed` for executed model errors.

### Acceptance Criteria

- [ ] AC-1: Same package + same mode resolves to the same cache key.
- [ ] AC-2: Cached predictions can resume a closed-loop step without remote execution.
- [ ] AC-3: Remote Kasm mode writes a handoff manifest and never emits token-bearing commands.
- [ ] AC-4: Timeout, blocked, failed, cached, and passed states are distinguishable in JSON and Markdown.
- [ ] AC-5: Closed-loop runner records inference result paths per step.

### Verification

```bash
PYTHONPATH=src python3 -m unittest tests.test_alpamayo_handoff tests.test_alpamayo_inference_bridge tests.test_carla_closed_loop_runner tests.test_oodrive_cli
bash scripts/pre_push_check.sh
```

### Autonomy Readiness

- Local tests use fake/cached modes.
- Remote mode must stop with blocker text if Kasm/HF auth is unavailable.
- Do not send secrets through Kasm proxy SSH streams.

### Evidence

- Planning source: user request to harden Alpamayo/CARLA integration.
- Inspected seams: `studio_product_cli.py`, `alpamayo_live.py`, `scripts/run_remote_alpamayo_carla_inference.sh`, `docs/MEMORY.md`.
- Plan review: `tickets/TASK-161/artifacts/review/task161-164-hardening-plan-review.json`
- Implementation: added `src/driverx/remote/alpamayo_handoff.py`, package cache keys, Kasm-safe handoff manifests, fake/cached/remote inference result states, and cache reuse.
- Proof: `tests.test_alpamayo_handoff` passed; fake and remote smoke commands produced passed/blocked artifacts as expected.
- Review: `tickets/TASK-161/artifacts/review/task157-164-impl-review.json`

### Blockers

- Remote live inference requires Kasm/HF auth and GPU availability.
