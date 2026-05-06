# TASK-074: Alpamayo Reasoning Capture For CARLA OOD Scenes

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-052, TASK-059, TASK-072
- location: `src/driverx/simulators`, `src/driverx/policies`,
  `src/driverx/pipeline`, `scripts/`, tests, `tickets/TASK-074/artifacts`
- enter when: TASK-072 can produce a CARLA OOD scene capture package or saved
  frames, and RunPod Alpamayo cache is available
- leave when: Alpamayo runs open-loop on a DriverX CARLA OOD scene and records
  reasoning/CoC, trajectory, latency, VRAM, and claim boundaries
- blockers: live GPU inference needs the RunPod Alpamayo lane; implementation
  and fake prediction tests can proceed without GPU
- spawned follow-ups: TASK-075, TASK-077
- complexity: L

### Summary
Connect the generated CARLA OOD demo to Alpamayo as an open-loop reasoning VLA
probe. The output should be a compact reasoning artifact that can be shown in
the submission video and compared against memory-augmented context.

### Scope
- In scope: capture/package selection from TASK-072, optional use of existing
  `capture-alpamayo-carla-input`, remote inference script reuse, CoC/reasoning
  summary extraction, trajectory conversion, evidence report.
- Out of scope: real-time steering, model fine-tuning, changing Alpamayo
  weights, or closed-loop claims.

### Gap Analysis
- Current state: Alpamayo live inference works on CARLA packages and PhysicalAI
  samples, but not yet on the newly generated DriverX scripted OOD scenes.
- Production expectation: the submission should show how the latest reasoning
  model interprets the generated edge case.
- Missing gaps: scenario-linked package metadata, reasoning panel extraction,
  direct linkage from CARLA video frames to Alpamayo decision, and latency/VRAM
  surfaced in the same report.
- Recommendation: keep Alpamayo open-loop and scenario-linked; do not block on
  real-time control.

### Plan

#### Change
Add `run-alpamayo-ood-scene` or extend the existing live Alpamayo path to take a
TASK-072 package/report, run remote inference when configured, and write
`alpamayo_ood_scene_decision.json/md`.

#### Why
The submission thesis needs model reasoning evidence, not only simulator
motion. Alpamayo's explicit CoC output is the best available proof surface.

#### Before -> After
- Before: Alpamayo evidence is real but tied to older captures/comparisons.
- After: a generated CARLA OOD scene has its own Alpamayo reasoning and
  trajectory intent artifact.

#### Touch
- `src/driverx/policies/alpamayo_live.py`: preserve scenario/video metadata.
- `src/driverx/pipeline/alpamayo_ood_scene.py`: new report builder if needed.
- `src/driverx/simulators/carla_alpamayo_capture.py`: ensure capture packages
  can reference TASK-072 scenario/video artifacts.
- `scripts/run_remote_alpamayo_carla_inference.sh`: reuse; only patch if output
  metadata needs hardening.
- `src/driverx/cli.py`, `src/driverx/pipeline/__init__.py`.
- `tests/test_alpamayo_ood_scene.py`, `tests/test_alpamayo_live.py`.
- `README.md`, `docs/progress.md`, `blockers.md`.

#### Inspect
- `src/driverx/policies/alpamayo_live.py`
- `src/driverx/policies/alpamayo_materializer.py`
- `src/driverx/pipeline/alpamayo_ood_evaluation.py`
- `tickets/TASK-059/artifacts/physicalai-shape-probe-summary/alpamayo_shape_probe_report.md`
- `tickets/archive/TASK-056/artifacts/town10-memory-comparison/alpamayo_ood_comparison.md`

#### Signature Delta
```python
src/driverx/pipeline/alpamayo_ood_scene.py / build_alpamayo_ood_scene_report(run_dir: Path, inputs: AlpamayoOodSceneInputs) -> dict[str, Any]
src/driverx/policies/alpamayo_live.py / run_alpamayo_live_package(..., scenario_context: dict[str, Any] | None = None) -> dict[str, Any]
```

#### Type Sketch
```python
AlpamayoOodSceneInputs = {
  "package_path": Path,
  "prediction_path": Path | None,
  "policy_decision_path": Path | None,
  "video_evidence_path": Path | None,
  "scenario_report_path": Path | None,
}

AlpamayoOodSceneEvidence = {
  "open_loop_policy_evaluation": True,
  "closed_loop_control": False,
  "scenario_id": str,
  "cot_snippet": str | None,
  "trajectory_points_xy": list[list[float]],
  "latency_ms": float | None,
  "vram_peak_mb": float | None,
  "model_id": "nvidia/Alpamayo-1.5-10B",
  "video_evidence_path": str | None,
}
```

#### Typed Flow Example
`TASK-072 carla_ood_demo.json`
-> `capture-alpamayo-carla-input --route-name driverx_ood_demo`
-> `alpamayo_carla_input_package.json`
-> remote `alpamayo_live_prediction.json`
-> `alpamayo_policy_decision.json`
-> `alpamayo_ood_scene.md` with CoC snippet and trajectory.

#### Execution Steps
1. Add scenario/video context fields to package/report handling.
2. Implement report builder that can use either a real prediction/decision or a
   fake fixture prediction for tests.
3. Add CLI command or extend existing CLI with `--scenario-report` and
   `--video-evidence`.
4. Run fake prediction tests locally.
5. If RunPod is reachable, run one live inference; if not, write the exact SSH
   or GPU blocker and keep the fixture evidence.

#### Recommendation
Run Alpamayo on selected frames from the generated CARLA scene as open-loop
reasoning evidence. Do not attempt to drive CARLA live with Alpamayo in this
ticket.

#### Options Considered
- Full closed-loop Alpamayo: not credible with current 100s-class eager
  inference latency.
- VQA-only screenshot question answering: easier but weaker because Alpamayo can
  emit trajectory intent.
- Open-loop reasoning + trajectory intent: strongest feasible proof.

#### Blast Radius
- Alpamayo policy artifacts and submission reports.
- No live CARLA control changes.

#### Risks
- RunPod port/cache may change; blockers should name SSH target and local paths.
- CoC text may be long; reports should store raw JSON but show short snippets.
- Open-loop evidence must not be described as closed-loop autonomy.

### Acceptance Criteria
- [ ] AC-1: A generated CARLA OOD scene package can be associated with an
  Alpamayo decision artifact.
- [ ] AC-2: Report includes CoC/reasoning snippet, trajectory summary,
  latency/VRAM when available, and open-loop labels.
- [ ] AC-3: Tests pass with fake prediction data and no CUDA.
- [ ] AC-4: Live GPU failure modes are classified as setup blockers, not
  silent missing evidence.

### Verification
- Focused:
  `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_ood_scene tests.test_alpamayo_live`
- Regression:
  `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_ood_evaluation tests.test_alpamayo_materializer`
- Optional live proof:
  `ALPAMAYO_ATTN_IMPLEMENTATION=eager bash scripts/run_remote_alpamayo_carla_inference.sh ...`
- Full gate:
  `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- Local implementation can proceed without GPU.
- Live proof needs RunPod SSH and HF/model cache; if blocked, record in
  `blockers.md` and continue to TASK-075 using fixture/fake decisions.

### Refs
- PRD FR-6, FR-7, FR-8, FR-9.
- `MEM-0019`.

### Evidence
- Planning created 2026-05-06 18:16 +0800.
- Review: `docs/reviews/TASK-072-077-impl-plan-review.md`.
- Implementation review: `docs/reviews/TASK-072-077-implementation-review.md`.
- Build: `src/driverx/pipeline/alpamayo_ood_scene.py`,
  `src/driverx/pipeline/alpamayo_ood_scene_cli.py`, and
  `tests/test_alpamayo_ood_scene.py`.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_ood_scene`.
- Scenario-linked setup report:
  `tickets/TASK-074/artifacts/generated-scene-open-loop-blocker-v2/alpamayo_ood_scene.md`.

### Blockers
- Live proof depends on a successful generated-scene CARLA capture package and
  a supplied Alpamayo policy decision. Current report is intentionally a setup
  blocker because the TASK-072 live CARLA run did not capture frames.
