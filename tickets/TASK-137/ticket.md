# TASK-137: Alpamayo Keyframe Analysis For Generated CARLA Frames

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-136, TASK-134
- location: `src/driverx/policies`, `src/driverx/pipeline`, `src/driverx/scenarios`, `src/driverx/simulators`, `src/oodrive`, `tests`, `tickets/TASK-137`
- enter when: TASK-136 can produce same-lineage CARLA frames or a precise blocked visual proof manifest, but OODrive cannot yet attach frame-by-frame Alpamayo analysis to those exact frames
- leave when: `oodrive analyze-keyframes` produces a keyframe manifest/report with frame paths, source times, selected risk context, Alpamayo reasoning snippets or blocked/fake backend evidence, latency/compute fields, and honest claim labels
- blockers: real Alpamayo inference requires a configured GPU/model environment; fake and blocked local backends are implemented; substantial score movement still needs TASK-136 live CARLA frames
- spawned follow-ups: TASK-138
- complexity: L

### Summary

Turn sampled Alpamayo reasoning into a judge-auditable keyframe analysis product step. The target flow is:

```bash
oodrive render-env -> oodrive analyze-keyframes -> keyframe_analysis.json
```

Each keyframe entry must point to a concrete CARLA frame from TASK-136, include source timestamp/frame index, risk or nearest-object context, RAG/memory context when available, Alpamayo reasoning or a clean blocked/fake result, and measured or declared latency.

### Scope

- In scope: keyframe selection, Alpamayo package materialization, fake backend for local reproducibility, blocked artifact for missing GPU/model dependencies, real-backend wrapper hook when TASK-134 provides it, report/manifest output, DB/run artifact linkage, tests, and score integration.
- Out of scope: real-time closed-loop control, prompt injection through Kasm SSH, new model weights, model fine-tuning, and final video rendering.

### Plan

#### Change

Add a product command:

```bash
PYTHONPATH=src python3 -m oodrive analyze-keyframes \
  --visual-proof artifacts/runs/task136-env-c3-proof-v1/env_carla_proof_manifest.json \
  --db artifacts/runs/task136-env-c3-proof-v1/scenario_studio_db.json \
  --run artifacts/runs/task136-env-c3-proof-v1/runs/task136-env-c3-proof-v1/run_manifest.json \
  --backend fake \
  --keyframes 8 \
  --run-id task137-keyframe-analysis-v1
```

Backend modes:

- `fake`: deterministic local reasoning for repeatability tests, clearly labeled.
- `blocked`: explicit setup blockers when Alpamayo is unavailable.
- `alpamayo-local`: real local/GPU backend when TASK-134 `oodrive infer` lands or an equivalent package runner is available.

#### Why

The current hero video shows reasoning overlays, but the user's desired demo is stronger: generate a new environment, see it in CARLA, and then inspect what Alpamayo says at important frames. That requires frame-level provenance and readable analysis artifacts, not only a final overlay.

#### Before -> After

- Before: Alpamayo evidence exists as run-level policy evaluation attached to TASK-128 artifacts.
- After: OODrive can sample keyframes from a generated CARLA proof run and write per-frame reasoning evidence tied to exact image files.

#### Touch

- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/scenarios/studio_product_environment_runtime.py` or a new focused keyframe runtime module
- `src/driverx/policies/alpamayo_local_inference.py`
- `src/driverx/pipeline/alpamayo_ood_package.py`
- `src/driverx/perception/risk_timeline.py`
- `src/driverx/simulators/reasoning_timeline_overlay.py`
- `src/driverx/evaluation/submission_readiness_score.py`
- `tests/test_alpamayo_local_inference.py`
- `tests/test_keyframe_analysis.py` (new)
- `tests/test_oodrive_cli.py`
- `README.md`
- `docs/HISTORY.md`

#### Inspect

- `tickets/TASK-134/ticket.md`
- `tickets/TASK-136/ticket.md`
- `src/driverx/policies/alpamayo_local_inference.py`
- `src/driverx/pipeline/alpamayo_ood_package.py`
- `src/driverx/pipeline/alpamayo_ood_batch.py`
- `src/driverx/scenarios/studio_product_runtime.py`
- `src/driverx/simulators/reasoning_timeline_overlay.py`
- `tests/test_alpamayo_ood_package.py`
- `tests/test_reasoning_timeline_overlay.py`
- `docs/MEMORY.md`

#### Signature Delta

```python
select_carla_keyframes(
    *,
    visual_proof_path: Path,
    run_manifest_path: Path,
    risk_timeline_path: Path | None,
    limit: int,
) -> list[CarlaKeyframe]

build_keyframe_alpamayo_package(
    *,
    keyframes: list[CarlaKeyframe],
    db_path: Path,
    run_manifest_path: Path,
    output_root: Path,
    run_id: str,
) -> KeyframeAlpamayoPackage

run_keyframe_analysis_backend(
    package: KeyframeAlpamayoPackage,
    *,
    backend: Literal["fake", "blocked", "alpamayo-local"],
    output_root: Path,
    run_id: str,
) -> KeyframeAnalysisResult

run_studio_analyze_keyframes(
    *,
    visual_proof_path: Path,
    db_path: Path,
    run_manifest_path: Path,
    backend: str,
    keyframe_count: int,
    output_root: Path | None,
    run_id: str,
) -> StudioCommandResult
```

#### Type Sketch

```python
CarlaKeyframe = {
  "keyframe_id": str,
  "frame_index": int,
  "source_time_s": float,
  "image_path": str,
  "selection_reason": "risk_peak" | "first_visible_ood" | "uniform_sample",
  "risk": {"level": str, "nearest_actor": str | None, "distance_m": float | None},
}

KeyframeAnalysis = {
  "keyframe_id": str,
  "image_path": str,
  "source_time_s": float,
  "backend": "fake" | "blocked" | "alpamayo-local",
  "status": "passed" | "blocked" | "failed",
  "vla_reasoning": str | None,
  "action_intent": str | None,
  "memory_ids": list[str],
  "latency_ms": float | None,
  "vram_peak_mb": float | None,
  "blockers": list[str],
}

KeyframeAnalysisManifest = {
  "status": str,
  "visual_proof_path": str,
  "same_lineage": bool,
  "keyframe_count": int,
  "reasoned_keyframe_count": int,
  "blocked_keyframe_count": int,
  "analyses": list[KeyframeAnalysis],
  "claim_boundaries": [
    "sampled_open_loop_reasoning=true",
    "closed_loop_vla_control=false",
    "real_time_vla_control=false"
  ],
}
```

#### Typed Flow Example

`env_carla_proof_manifest.json` with `rgb_folder`
-> select 8 keyframes by risk peaks and uniform fallback
-> materialize an Alpamayo package with frame paths and prompt context
-> run `fake` locally or `alpamayo-local` on Kasm/GPU
-> write `keyframe_analysis.json` and `keyframe_analysis.md`
-> print next command for TASK-138 video assembly.

#### Execution Steps

1. Define `CarlaKeyframe` and keyframe selection around existing RGB frames and risk timeline data.
2. Add fake backend first so local tests and judge docs can run without GPU.
3. Add blocked backend that detects missing package/frame/model requirements and writes useful setup instructions.
4. Integrate real Alpamayo through the TASK-134 inference seam when available, without duplicating token or SSH handling.
5. Store all per-frame output in one manifest and a Markdown report.
6. Update DB/run artifact linkage so downstream `demo-video` can consume keyframe analysis directly.
7. Add tests for keyframe selection, fake backend determinism, blocked backend clarity, claim labels, and CLI help.
8. Update the nested autoresearch score to reward reasoned keyframes only when they point to same-run CARLA frames.

#### Recommendation

Build this after TASK-136 and alongside or after TASK-134. The fake backend makes the product loop reviewable locally; the real backend upgrades the submission when the Kasm/Alpamayo lane is ready.

#### Options Considered

- Reuse run-level `oodrive reason` only: rejected because it hides frame-level provenance and does not answer the user's keyframe ask.
- Make TASK-134 infer produce all keyframe analysis: rejected because TASK-134 is the generic product inference lane, while this ticket is about visual keyframe evidence.
- Add `oodrive analyze-keyframes`: selected because it creates a clean bridge between CARLA frames and sampled Alpamayo reasoning.

#### Blast Radius

- Adds one product command and a new analysis manifest shape.
- Downstream overlay/video code can optionally consume keyframe analysis.
- Does not change claim boundaries or imply closed-loop VLA control.

#### Risks

- Fake backend could be mistaken for real model evidence: every fake output must include `backend=fake` and `model_evidence=false`.
- Real Alpamayo latency is slow: record latency honestly and allow sparse keyframes instead of implying real-time operation.
- Keyframe selection can overfit to easy frames: require a mix of risk peaks and uniform temporal coverage.

### Gap Analysis

- Current evidence is run-level and video-overlay-level, not a reusable keyframe analysis artifact.
- A judge should be able to click from a reasoning snippet to the exact CARLA frame it describes.
- Production-grade model evaluation needs frame ids, source time, selected reason, prompt context, model output, latency, and backend status in one schema.

### Acceptance Criteria

- [x] AC-1: `oodrive analyze-keyframes --help` exists and documents backend modes.
- [ ] AC-2: Local fake backend writes deterministic `keyframe_analysis.json` with at least 5 keyframes from TASK-136 frame paths.
- [x] AC-3: Missing real Alpamayo dependencies produce a blocked artifact with concrete setup blockers and no stack trace.
- [ ] AC-4: Real backend path can consume the package produced from TASK-136 frames when configured.
- [x] AC-5: Every keyframe analysis includes frame index, source time, image path, selection reason, reasoning/action fields or blockers, and claim labels.
- [x] AC-6: Output preserves `sampled_open_loop_reasoning=true`, `closed_loop_vla_control=false`, and `real_time_vla_control=false`.

### Verification

- PASS: `PYTHONPATH=src python3 -m oodrive analyze-keyframes --help`
- PASS/BLOCKED AS EXPECTED: `PYTHONPATH=src python3 -m oodrive analyze-keyframes --visual-proof artifacts/runs/task136-env-c3-proof-v1/env_carla_proof_manifest.json --db artifacts/runs/task136-env-c3-proof-v1/scenario_studio_db.json --run artifacts/runs/task136-env-c3-proof-v1/runs/task136-env-c3-proof-v1/run_manifest.json --backend fake --keyframes 8 --run-id task137-keyframe-analysis-v1`
- PASS: `PYTHONPATH=src python3 -m unittest tests.test_keyframe_analysis tests.test_environment_to_carla_visual_proof tests.test_oodrive_cli` ran 15 tests.
- Optional Kasm/GPU real backend smoke when Alpamayo is configured.
- PASS: `tickets/TASK-136/autoresearch/autoresearch.sh` emitted latest `METRIC environment_to_reasoned_carla_score=45.0000`.
- PASS: `tickets/TASK-136/autoresearch/autoresearch.checks.sh` ran 33 tests.
- PASS: `bash scripts/pre_push_check.sh` ran 425 tests OK, 5 skipped.
- Review artifact linked from this ticket before completion claim.

### Autonomy Readiness

- Required compute: local Mac for fake/blocked analysis, Kasm/RunPod for real Alpamayo.
- Secrets: do not pass HF tokens through Kasm proxy SSH heredocs.
- Human gate: real token installation or external spend only.
- Safe fallback: fake and blocked outputs are acceptable for product-repeatability proof, but not for real model evidence claims.

### Evidence

- Plan review: `tickets/TASK-136/artifacts/review/task136-138-planning-review.json`
- Build QA: `tickets/TASK-136/artifacts/qa/task136-138-build-qa.md`
- Implementation review: `tickets/TASK-136/artifacts/review/task136-138-implementation-review.json`
- Autoresearch plan: `tickets/TASK-136/autoresearch/autoresearch.md`
- Blocked no-frame keyframe analysis:
  `artifacts/runs/task137-keyframe-analysis-v1/keyframe_analysis.json`

### Blockers

- Real Alpamayo inference remains blocked until the GPU/model environment is configured. Local fake/blocked proof is implemented, but TASK-136 live CARLA frames are needed for reasoned keyframes.
