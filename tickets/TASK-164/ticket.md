# TASK-164: Closed-Loop Integration Regression Score And Evidence Pack

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-157, TASK-158, TASK-161, TASK-162, TASK-163
- location: `src/driverx/evaluation`, `src/driverx/scenarios`, `autoresearch.*`, `qa/fixtures`, `tests`, `tickets/TASK-164`
- enter when: trace schema, runner, sync barrier, safety guardrails, and inference handoff are locally implemented.
- leave when: OODrive has a single regression metric and evidence pack that proves the Alpamayo/CARLA integration is not just runnable, but causally closed-loop, sensor-aligned, safety-guarded, cache-resumable, and claim-honest.
- blockers: none for fixture/fake regression; live Kasm score remains TASK-160.
- spawned follow-ups: final submission refresh after TASK-160 live score passes.
- complexity: M

### Summary

Turn hardening into a measurable gate. This ticket adds `closed_loop_integration_score` and a compact evidence pack so future changes cannot silently break sensor alignment, control safety, inference resumability, or claim boundaries.

### Scope

In scope:
- New score fixture and evaluator for integration readiness.
- CLI wrapper to score closed-loop integration artifacts.
- Autoresearch metric emission.
- Evidence pack linking trace, checkpoints, safety reports, inference results, and closed-loop score.

Out of scope:
- Live CARLA execution.
- Alpamayo latency optimization.
- Video polish beyond artifact links/summary.

### Gap Analysis

Current state:
- TASK-157 plans a `score-closed-loop` metric focused on trace claim honesty.
- TASK-161 through TASK-163 plan key reliability pieces, but they need one top-level regression gate.
- Existing autoresearch loops already work for hero videos, environment proof, generator runtime, and M4/M5 clarity.

Production expectation:
- A high-stakes simulator integration should have one command that answers: is this evidence actually closed-loop enough to promote?
- The score should fail if any required hardening layer is absent.
- Autoresearch should optimize the artifact contract, not lower thresholds.

Missing gaps:
- No integration-level score combining recurrence, sensor sync, safety, inference cache, and claim boundaries.
- No fixture that represents a fully hardened paused loop.
- No single evidence pack for a skeptical reviewer.

Recommendation:
- Add a mechanical score and fixture pack immediately after the hardening modules land.

### Plan

#### Change

Add:

```bash
PYTHONPATH=src python3 -m oodrive score-closed-loop-integration \
  --trace artifacts/runs/task158-paused-loop-fake/closed_loop_trace.json \
  --metric-only
```

Autoresearch should emit:

```text
METRIC closed_loop_integration_score=<number>
```

#### Why

Without one regression score, the integration can regress in a subtle way: frames still write, controls still apply, video still renders, but the proof stops being causal or safe.

#### Before -> After

- Before: closed-loop readiness is spread across multiple local checks and ticket prose.
- After: one score rejects missing sync provenance, unsafe controls, stale inference, weak recurrence, and overclaiming.

#### Touch

- `src/driverx/evaluation/closed_loop_integration_score.py` (new)
- `src/driverx/evaluation/closed_loop_control_score.py` (from TASK-157)
- `src/driverx/scenarios/studio_product_closed_loop_runtime.py` (from TASK-157)
- `src/driverx/scenarios/studio_product_cli.py`
- `qa/fixtures/closed_loop_integration_score/` (new)
- `tests/test_closed_loop_integration_score.py` (new)
- `tests/test_oodrive_cli.py`
- `autoresearch.md`
- `autoresearch.sh`
- `autoresearch.checks.sh`

#### Inspect

- `src/driverx/evaluation/hero_demo_score.py`
- `src/driverx/evaluation/submission_readiness_score.py`
- `src/driverx/evaluation/generator_runtime_score.py`
- `qa/fixtures/submission_readiness_score/`
- `autoresearch.jsonl`

#### Signature Delta

```python
src/driverx/evaluation/closed_loop_integration_score.py / load_closed_loop_integration_inputs(trace_path: Path): ClosedLoopIntegrationInputs
src/driverx/evaluation/closed_loop_integration_score.py / score_closed_loop_integration(inputs: ClosedLoopIntegrationInputs): ClosedLoopIntegrationScore
src/driverx/scenarios/studio_product_closed_loop_runtime.py / run_studio_score_closed_loop_integration(...): StudioCommandResult
```

#### Type Sketch

```python
ClosedLoopIntegrationScore = {
  "closed_loop_integration_score": float,
  "status": "passed" | "blocked",
  "subscores": {
    "recurrence": float,
    "sensor_sync": float,
    "control_safety": float,
    "inference_handoff": float,
    "claim_honesty": float,
    "artifact_completeness": float
  },
  "blockers": list[str],
  "evidence_paths": list[str]
}
```

#### Typed Flow Example

A hardened fake trace has 3 steps, aligned camera frames, safe chunks, cached inference results, and honest `paused_receding_horizon` labels. It scores above `85`. A weak trace with controls but missing sensor frame ids scores blocked below threshold.

#### Execution Steps

1. Define score inputs and subscores.
2. Add weak and target fixtures.
3. Register `oodrive score-closed-loop-integration`.
4. Write JSON/Markdown score reports.
5. Update autoresearch scripts to emit the new metric once fixtures exist.
6. Add tests for target pass, weak fail, overclaim fail, and missing artifact fail.
7. Link score output into TASK-160 live proof acceptance.

#### Recommendation

Make this the release gate before touching final submission claims. It gives us a 90th-percentile proof language: not just “it ran,” but “it ran with causal recurrence, synchronized observations, safe controls, and honest latency.”

#### Options Considered

- Fold everything into `score-closed-loop`: simple, but the trace scorer becomes overloaded.
- Keep only tests: good for code, weak for submission proof.
- Add integration score: best balance of engineering regression and judge-facing evidence.

#### Blast Radius

- Evaluation/CLI/autoresearch surfaces only.
- No runtime behavior changes.

#### Risks

- Metric can be gamed if fixtures are synthetic. Mitigation: require real artifact paths for live promotion and keep fake fixture labeled as local contract proof.
- Autoresearch scripts can become noisy. Mitigation: emit one focused metric and keep existing checks intact.

### Acceptance Criteria

- [ ] AC-1: Target fixture scores at or above `85`.
- [ ] AC-2: Weak fixture missing sensor sync or safety evidence scores blocked.
- [ ] AC-3: CLI emits `METRIC closed_loop_integration_score=<number>`.
- [ ] AC-4: Autoresearch checks include the integration score without weakening existing metrics.
- [ ] AC-5: TASK-160 live promotion requires both `score-closed-loop` and `score-closed-loop-integration`.

### Verification

```bash
PYTHONPATH=src python3 -m unittest tests.test_closed_loop_integration_score tests.test_closed_loop_control_score tests.test_oodrive_cli
./autoresearch.checks.sh
bash scripts/pre_push_check.sh
```

### Autonomy Readiness

- Local score uses fixtures and fake/cached artifacts only.
- Live artifact promotion remains blocked until TASK-160 supplies Kasm evidence.

### Evidence

- Planning source: user request to harden Alpamayo/CARLA integration.
- Inspected scoring patterns: `hero_demo_score.py`, `submission_readiness_score.py`, `generator_runtime_score.py`.
- Plan review: `tickets/TASK-161/artifacts/review/task161-164-hardening-plan-review.json`
- Implementation: added `src/driverx/evaluation/closed_loop_integration_score.py`, `oodrive score-closed-loop-integration`, autoresearch metric emission, and CLI modularization to keep the product CLI under the source-size gate.
- Metric: `./autoresearch.sh` emitted `METRIC closed_loop_integration_score=100.0000`.
- Proof: `./autoresearch.checks.sh` passed with `35 tests OK`; full `bash scripts/pre_push_check.sh` passed with `456 tests OK, 5 skipped`.
- Review: `tickets/TASK-161/artifacts/review/task157-164-impl-review.json`

### Blockers

- None for local score implementation.
