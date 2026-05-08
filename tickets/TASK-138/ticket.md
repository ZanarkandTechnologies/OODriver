# TASK-138: Scored Environment-To-Reasoned-CARLA Video

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-136, TASK-137
- location: `src/driverx/pipeline`, `src/driverx/evaluation`, `src/driverx/simulators`, `src/driverx/scenarios`, `src/oodrive`, `tests`, `tickets/TASK-138`
- enter when: OODrive can generate an environment, render same-lineage CARLA visual proof, and attach keyframe Alpamayo analysis, but judges still need one 1-5 minute video that explains the whole loop
- leave when: `oodrive env-demo-video` or the selected equivalent command builds a 1-5 minute MP4/story pack with CLI generation, CARLA preview/video, frame-linked keyframe analysis, RAG/risk callouts, claim boundaries, and `environment_to_reasoned_carla_score >= 90`
- blockers: local story/scoring commands and same-lineage still-frame MP4 assembly are implemented; final MP4 remains blocked by missing TASK-136 live CARLA preview/RGB frames and reasoned keyframes
- spawned follow-ups: final submission video stitching/publishing only after this score passes
- complexity: L

### Summary

Assemble the user-requested flow into one judge-visible video artifact:

```bash
oodrive generate-envs
oodrive render-env
oodrive analyze-keyframes
oodrive env-demo-video
oodrive score-env-proof
```

The video should show the generated environment command, the CARLA preview/image and motion evidence, and frame-by-frame Alpamayo analysis panels with source frame numbers, timestamps, risk, RAG/memory, action intent, and claim labels.

### Scope

- In scope: video/story pack builder, overlay/report schema, product CLI commands, environment proof scorer, root or nested autoresearch metric integration, tests, README/submission pack references after pass, and review/QA evidence.
- Out of scope: public hosting, real-time VLA claims, new CARLA runtime setup beyond using TASK-136 artifacts, and changing scorer thresholds to inflate quality.

### Plan

#### Change

Add final assembly and scoring commands:

```bash
PYTHONPATH=src python3 -m oodrive env-demo-video \
  --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json \
  --visual-proof artifacts/runs/task136-env-c3-proof-v1/env_carla_proof_manifest.json \
  --keyframe-analysis artifacts/runs/task137-keyframe-analysis-v1/keyframe_analysis.json \
  --run-id task138-env-reasoned-carla-v1

PYTHONPATH=src python3 -m oodrive score-env-proof \
  --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json \
  --visual-proof artifacts/runs/task136-env-c3-proof-v1/env_carla_proof_manifest.json \
  --keyframe-analysis artifacts/runs/task137-keyframe-analysis-v1/keyframe_analysis.json \
  --video artifacts/runs/task138-env-reasoned-carla-v1/environment_reasoned_carla_demo.mp4 \
  --overlay-report artifacts/runs/task138-env-reasoned-carla-v1/environment_reasoned_carla_demo.json \
  --metric-only
```

#### Why

The strongest submission story is not another raw simulator clip. It is a visible product loop: generate weird environment, render it in CARLA, ask Alpamayo to reason over keyframes, then show judge-visible evidence and limitations in one concise video.

#### Before -> After

- Before: environment generation, CARLA evidence, and reasoning overlays exist as separate proof surfaces.
- After: a single scored artifact ties all three together and can be dropped into the final 1-5 minute SoTA Commission submission.

#### Touch

- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/scenarios/studio_product_environment_runtime.py` or new focused `studio_product_env_video_runtime.py`
- `src/driverx/pipeline/environment_reasoned_carla_video.py` (new)
- `src/driverx/evaluation/environment_reasoned_carla_score.py` (new)
- `src/driverx/simulators/reasoning_timeline_overlay.py`
- `src/driverx/pipeline/submission_story_pack.py`
- `src/driverx/evaluation/submission_readiness_score.py`
- `tests/test_environment_reasoned_carla_video.py` (new)
- `tests/test_environment_reasoned_carla_score.py` (new)
- `tests/test_oodrive_cli.py`
- `README.md`
- `docs/HISTORY.md`
- `tickets/TASK-136/autoresearch/*`

#### Inspect

- `src/driverx/pipeline/environment_demo_pack.py`
- `src/driverx/evaluation/environment_demo_score.py`
- `src/driverx/simulators/reasoning_timeline_overlay.py`
- `src/driverx/evaluation/hero_demo_score.py`
- `src/driverx/evaluation/submission_readiness_score.py`
- `src/driverx/pipeline/submission_story_pack.py`
- `tests/test_environment_demo_pack.py`
- `tests/test_hero_demo_score.py`
- `tickets/TASK-131/ticket.md`
- `tickets/TASK-135/ticket.md`

#### Signature Delta

```python
build_environment_reasoned_carla_video(
    *,
    environment_summary_path: Path,
    visual_proof_path: Path,
    keyframe_analysis_path: Path,
    output_root: Path,
    run_id: str,
    target_duration_s: float = 120.0,
) -> EnvironmentReasonedCarlaVideo

load_environment_reasoned_carla_score_inputs(
    *,
    environment_summary_path: Path,
    visual_proof_path: Path,
    keyframe_analysis_path: Path,
    video_path: Path | None,
    overlay_report_path: Path | None,
    score_input_path: Path | None = None,
) -> EnvironmentReasonedCarlaScoreInputs

score_environment_reasoned_carla(
    inputs: EnvironmentReasonedCarlaScoreInputs,
) -> EnvironmentReasonedCarlaScoreReport

run_studio_env_demo_video(...) -> StudioCommandResult
run_studio_score_env_proof(...) -> StudioCommandResult
```

#### Type Sketch

```python
EnvironmentReasonedCarlaVideo = {
  "status": "passed" | "blocked" | "failed",
  "video_path": str | None,
  "overlay_report_path": str,
  "duration_s": float,
  "source_lineage": {
    "environment_summary_path": str,
    "visual_proof_path": str,
    "keyframe_analysis_path": str,
    "same_lineage": bool,
  },
  "timeline_segments": list[{
    "start_s": float,
    "end_s": float,
    "kind": "cli_generation" | "carla_preview" | "keyframe_reasoning" | "claim_boundary",
    "frame_index": int | None,
    "source_time_s": float | None,
    "text": str,
  }],
  "claim_boundaries": list[str],
}

EnvironmentReasonedCarlaScoreReport = {
  "environment_to_reasoned_carla_score": float,
  "status": "passed" | "blocked",
  "threshold": 90.0,
  "components": {
    "cli_generation": float,
    "same_run_carla_visual": float,
    "keyframe_reasoning": float,
    "video_readiness": float,
    "reproducibility": float,
  },
  "blockers": list[str],
  "recommendations": list[str],
}
```

#### Typed Flow Example

`environment_suite_summary.json`
-> `env_carla_proof_manifest.json` with `preview_image_path` and optional source MP4/RGB frames
-> `keyframe_analysis.json` with at least 5 frame-linked analyses
-> `env-demo-video` builds a 1-5 minute MP4 and overlay JSON
-> `score-env-proof` emits `METRIC environment_to_reasoned_carla_score=<score>`
-> `score-submission` can reference this as the environment-generation proof.

#### Execution Steps

1. Define a strict same-lineage score input loader before building new video polish.
2. Implement the scorer with fixtures for weak, blocked, and target states.
3. Add video pack builder that can assemble from a live source MP4 when present or from preview/keyframe stills when only frame folders exist.
4. Reuse `reasoning_timeline_overlay.py` for frame/time/keyframe panels instead of creating a separate overlay renderer unless the existing renderer cannot express static intro segments.
5. Add product CLI commands `env-demo-video` and `score-env-proof`.
6. Update the TASK-136 autoresearch script to use the real scorer once it exists.
7. Update submission pack/readiness surfaces only after `environment_to_reasoned_carla_score >= 90`.
8. Run visual/media QA: sample frame exists, text fits, duration is 60-300s, MP4 opens, and claim labels are visible.
9. Run focused tests, autoresearch verify/checks, pre-push, and final review.

#### Recommendation

Build this third. Do not start with video assembly before TASK-136/TASK-137 prove same-lineage data; otherwise the artifact risks becoming another impressive but disconnected reel.

#### Options Considered

- Reuse TASK-131 hero video directly: rejected because it does not prove the newly generated environment lineage.
- Build only a slide deck: acceptable fallback for submission, but weaker than a runnable product-generated MP4.
- Build scored same-lineage video: selected because it most directly satisfies the user's desired demo and the challenge brief.

#### Blast Radius

- Adds additive video/scoring commands.
- Submission pack/readiness references change only after a passing scored artifact exists.
- Existing hero demo and environment demo scores remain valid.
- No changes to model or CARLA runtime claims.

#### Risks

- If live CARLA is unavailable, a still-frame video can satisfy local product proof but should not be promoted as navigation evidence.
- If real Alpamayo is blocked, fake/blocked analysis can prove product shape but not model reasoning; the score must reflect that distinction.
- Video polish can hide provenance. The overlay report must expose every source artifact and same-lineage check.

### Gap Analysis

- The current submission can score well, but the user's desired "generate -> CARLA image -> Alpamayo keyframe video" workflow is not a single reproducible artifact yet.
- Judges need to understand that OODrive is a simulation environment generator and evaluation harness, not just a video editing wrapper.
- A production-grade proof video should be inspectable by manifest, not only visually persuasive.

### Acceptance Criteria

- [x] AC-1: `oodrive env-demo-video --help` and `oodrive score-env-proof --help` exist.
- [x] AC-2: A video/story pack is generated from TASK-136 and TASK-137 artifacts with source lineage recorded in JSON.
- [ ] AC-3: MP4 duration is between 60s and 300s for the final challenge video path, or a shorter local QA clip is explicitly marked as QA-only.
- [ ] AC-4: Video/report shows CLI generation, CARLA preview or motion evidence, at least 5 keyframe analyses, frame/time labels, risk/RAG/action panels, and claim labels.
- [x] AC-5: `score-env-proof --metric-only` emits `METRIC environment_to_reasoned_carla_score=<number>` and target artifacts score `>=90`.
- [ ] AC-6: Submission pack/readiness references the artifact only after the score passes.

### Verification

- PASS: `PYTHONPATH=src python3 -m oodrive env-demo-video --help`
- PASS: `PYTHONPATH=src python3 -m oodrive score-env-proof --help`
- PASS/BLOCKED AS EXPECTED: `PYTHONPATH=src python3 -m oodrive env-demo-video --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json --visual-proof artifacts/runs/task136-env-c3-proof-v1/env_carla_proof_manifest.json --keyframe-analysis artifacts/runs/task137-keyframe-analysis-v1/keyframe_analysis.json --run-id task138-env-reasoned-carla-v1`
- PASS/BLOCKED AS EXPECTED: `PYTHONPATH=src python3 -m oodrive score-env-proof --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json --visual-proof artifacts/runs/task136-env-c3-proof-v1/env_carla_proof_manifest.json --keyframe-analysis artifacts/runs/task137-keyframe-analysis-v1/keyframe_analysis.json --overlay-report artifacts/runs/task138-env-reasoned-carla-v1/environment_reasoned_carla_demo.json --run-id task138-env-reasoned-carla-score-v1 --metric-only`
- PASS: `tickets/TASK-136/autoresearch/autoresearch.sh` emitted latest `METRIC environment_to_reasoned_carla_score=45.0000`.
- PASS: `tickets/TASK-136/autoresearch/autoresearch.checks.sh` ran 33 tests.
- PASS: `PYTHONPATH=src python3 -m unittest tests.test_environment_reasoned_carla tests.test_keyframe_analysis tests.test_environment_to_carla_visual_proof tests.test_environment_demo_pack tests.test_environment_demo_score tests.test_oodrive_cli` ran 24 tests.
- PASS: MP4 renderer unit test assembled a 12s `environment_reasoned_carla_demo.mp4` from preview/keyframe stills when images are available.
- PASS: `./autoresearch.sh` emitted `submission_readiness_score=96.3500` and `hero_demo_score=100.0000`.
- PASS: `./autoresearch.checks.sh` ran 22 tests.
- PASS: `bash scripts/pre_push_check.sh` ran 425 tests OK, 5 skipped.
- Visual/video QA with sample frames or MP4 shown to the user.
- Review artifact linked from this ticket before completion claim.

### Autonomy Readiness

- Required compute: local Mac can assemble/scoring from existing frames; Kasm/RunPod needed for fresh live CARLA; GPU needed for real Alpamayo.
- Secrets: none in local video assembly; do not transmit HF tokens through proxy SSH.
- Human gate: public upload/publish only.
- Safe fallback: local scored artifact can remain ignored; final submission promotion requires local or public media visibility.

### Evidence

- Plan review: `tickets/TASK-136/artifacts/review/task136-138-planning-review.json`
- Build QA: `tickets/TASK-136/artifacts/qa/task136-138-build-qa.md`
- Implementation review: `tickets/TASK-136/artifacts/review/task136-138-implementation-review.json`
- Autoresearch plan: `tickets/TASK-136/autoresearch/autoresearch.md`
- Blocked story/overlay pack:
  `artifacts/runs/task138-env-reasoned-carla-v1/environment_reasoned_carla_demo.json`
- Score report:
  `artifacts/runs/task138-env-reasoned-carla-score-v1/environment_reasoned_carla_score.json`

### Blockers

- Final MP4 promotion blocks on live TASK-136 CARLA preview/RGB frames and reasoned keyframes. The MP4 renderer itself is implemented and unit-tested with still images; the current local artifact has no live source frames to render. Real model evidence also blocks on configured Alpamayo runtime, but fake/blocked product proof is locally testable.
