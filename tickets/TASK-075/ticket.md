# TASK-075: Memory Versus No-Memory Alpamayo OOD Experiment Report

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-014, TASK-074
- location: `src/driverx/pipeline`, `src/driverx/memory`, `src/driverx/policies`,
  tests, `tickets/TASK-075/artifacts`
- enter when: a generated CARLA OOD scene has at least one Alpamayo open-loop
  decision or a fixture decision
- leave when: one report compares Alpamayo baseline and memory-guided behavior
  on the same generated OOD scene with trajectory/reasoning/latency deltas
- blockers: live memory-guided inference needs RunPod; report builder can be
  completed with cached/fake decisions
- spawned follow-ups: TASK-077
- complexity: M

### Summary
Turn the minimal-shot claim into a measurable comparison: same generated OOD
scene, frozen Alpamayo, no retrieved memory versus compact retrieved safety
memory.

### Scope
- In scope: memory package augmentation, two-decision comparison, CoC snippet
  diff, trajectory delta, latency/VRAM delta, safety flags, report suitable for
  video/deck.
- Out of scope: official model score, fine-tuning, full closed-loop CARLA
  execution.

### Gap Analysis
- Current state: TASK-056 already compares Alpamayo with and without memory on
  an older Town10 capture; the new scenario forge needs the same proof on the
  generated OOD scene.
- Production expectation: minimal-shot submissions should show a mechanism for
  transferring lessons from few examples to new cases.
- Missing gaps: generated-scene linkage, reasoning snippets aligned to the
  final video, and batch-ready schema for multiple scenarios later.
- Recommendation: adapt the existing `alpamayo_ood_evaluation` path and add a
  scenario-linked report rather than building a new evaluator.

### Plan

#### Change
Extend `build-alpamayo-ood-comparison` or add a thin wrapper so generated CARLA
scene artifacts become the primary comparison inputs.

#### Why
The final submission should show not just that Alpamayo runs, but that retrieved
minimal-shot context changes its reasoning or trajectory on the OOD scene.

#### Before -> After
- Before: memory comparison exists but is not tied to the new long CARLA video.
- After: the same scenario/video has Alpamayo baseline and memory-guided
  reasoning/trajectory comparison.

#### Touch
- `src/driverx/pipeline/alpamayo_ood_evaluation.py`: add scenario/video fields
  if needed.
- `src/driverx/pipeline/alpamayo_ood_scene.py`: consume TASK-074 outputs if
  created.
- `src/driverx/memory/bank.py`: reuse retrieval snippets.
- `src/driverx/cli.py`.
- `tests/test_alpamayo_ood_evaluation.py`, `tests/test_alpamayo_ood_scene.py`.
- `README.md`, `docs/progress.md`.

#### Inspect
- `tickets/archive/TASK-056/artifacts/town10-memory-comparison/alpamayo_ood_comparison.json`
- `src/driverx/pipeline/alpamayo_ood_evaluation.py`
- `src/driverx/policies/runner.py`

#### Signature Delta
```python
src/driverx/pipeline/alpamayo_ood_evaluation.py / build_alpamayo_ood_evaluation(run_dir: Path, inputs: AlpamayoOodEvaluationInputs) -> dict[str, Any]
```

Add optional fields:
```python
AlpamayoOodEvaluationInputs = {
  "scenario_report_path": Path | None,
  "video_evidence_path": Path | None,
}
```

#### Type Sketch
```python
AlpamayoMemoryComparison = {
  "scenario_id": str,
  "video_evidence_path": str | None,
  "records": [
    {"mode": "alpamayo", "cot_snippet": str, "trajectory_summary": dict},
    {"mode": "alpamayo+memory", "cot_snippet": str, "trajectory_summary": dict},
  ],
  "memory_ids": list[str],
  "trajectory_delta": {"mean_l2_m": float, "final_l2_m": float},
  "reasoning_delta": dict[str, Any],
  "open_loop_policy_evaluation": True,
}
```

#### Typed Flow Example
`alpamayo_ood_scene_baseline.json`
-> `memory_augmented_alpamayo_carla_input_package.json`
-> `alpamayo_ood_scene_memory.json`
-> `alpamayo_ood_comparison.md`
-> TASK-077 submission pack consumes comparison path.

#### Execution Steps
1. Patch inputs/report fields to carry scenario and video evidence paths.
2. Ensure memory-augmented package generation preserves images and nav text.
3. Add tests for full comparison, missing memory decision, and scenario/video
   path inclusion.
4. Run live memory-guided inference only if RunPod is available; otherwise
   write generated package and blocker text.
5. Update submission docs with the new comparison path.

#### Recommendation
Use the existing comparison harness and make it scenario-linked. Avoid a new
experiment framework until one scenario has polished evidence.

#### Options Considered
- Single Alpamayo decision only: proves model runs but weak minimal-shot story.
- Batch of many fake comparisons: broad but less convincing.
- One real scenario-linked memory comparison: best first proof.

#### Blast Radius
- Alpamayo comparison report schema and submission pack inputs.
- No changes to model runtime or CARLA actor control.

#### Risks
- Memory context may not improve behavior; report should present deltas, not
  overclaim improvement.
- Live second inference can take minutes; blockers should allow continuation.

### Acceptance Criteria
- [ ] AC-1: Report links to generated scenario/video artifacts.
- [ ] AC-2: Report compares baseline and memory-guided Alpamayo records on the
  same source package.
- [ ] AC-3: Report includes memory ids, CoC snippets, trajectory delta,
  latency/VRAM delta, and open-loop labels.
- [ ] AC-4: Missing live memory decision produces a rerunnable command/blocker.

### Verification
- Focused:
  `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_ood_evaluation`
- Regression:
  `PYTHONPATH=src python3 -m unittest tests.test_submission_demo_pack`
- Full gate:
  `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- Can implement and test locally with fixture decisions.
- Live memory-guided inference needs RunPod; if unavailable, emit package and
  blocker and continue to TASK-077.

### Refs
- PRD US-003, FR-4, FR-5, FR-7, FR-8.
- TASK-056 prior comparison.

### Evidence
- Planning created 2026-05-06 18:16 +0800.
- Review: `docs/reviews/TASK-072-077-impl-plan-review.md`.

### Blockers
- Live two-run Alpamayo comparison needs reachable GPU runtime.
