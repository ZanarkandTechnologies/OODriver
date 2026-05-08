# TASK-131: Score-Gated Hero Demo From Live Evidence

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-128, TASK-130
- location: `artifacts/runs/task128-oodrive-live-product`, `artifacts/exported`, `tickets/TASK-131/artifacts`, `docs/HISTORY.md`
- enter when: TASK-130 provides the hero-demo score contract and TASK-128 provides live OODrive CARLA + Alpamayo evidence, but the current video is too slow and does not visibly show the product loop
- leave when: a local judge-visible OODrive hero MP4 with frame/time, risk, RAG, reasoning, and honest claim-boundary overlays scores at least `72` through `oodrive score-demo`
- blockers: none
- spawned follow-ups: TASK-129 remains optional after this artifact passes
- complexity: M

### Summary

Turn the existing OODrive live CARLA + Alpamayo proof into a score-gated
submission hero artifact. This ticket is artifact-first: recover or reconstruct
the TASK-128 DB/run/evaluation JSON locally, render a time-warped reasoning/RAG
demo video from the best available CARLA source MP4, and iterate the artifact
until `hero_demo_score >= 72`.

### Scope

- In scope: TASK-128 evidence intake, local demo-video rendering, score-demo
  verification, artifact evidence, history writeback, and final demo reference
  updates after a passing score exists.
- Out of scope: fresh GPU setup unless evidence intake fails, real-time
  closed-loop Alpamayo control, threshold relaxation, and TASK-129 `oodrive
  infer`.

### Plan

#### Change

Produce a score-gated hero demo artifact from TASK-128 product evidence and the
best visible CARLA source clip.

#### Why

The current live proof is technically real but not judge-visible enough. The
next submission move is to make the OODrive contribution obvious in-frame:
generated scenario context, CARLA motion, risk/object telemetry, retrieved
memory, sampled Alpamayo reasoning, and explicit no-real-time-control labels.

#### Before -> After

- Before: TASK-128 has a live product-loop MP4, but it is visually weak and
  scores below the hero-demo promotion threshold.
- After: TASK-131 has a local MP4 and score report that pass the mechanical
  hero-demo gate without changing the claim boundary.

#### Touch

- `tickets/TASK-131/ticket.md`
- `tickets/TASK-131/artifacts/*`
- `docs/HISTORY.md`
- ignored local artifacts under `artifacts/runs/task128-oodrive-live-product/`
- source only if live artifact scoring exposes a real extraction bug

#### Inspect

- `tickets/TASK-128/artifacts/qa/live-product-loop-qa.md`
- `tickets/TASK-130/ticket.md`
- `src/driverx/evaluation/hero_demo_score.py`
- `src/driverx/simulators/reasoning_timeline_overlay.py`
- `src/driverx/scenarios/studio_product_runtime.py`
- `artifacts/exported/task102_high_fidelity_hero_v6_full.mp4`
- `artifacts/exported/task128_oodrive_live_product.mp4`

#### Signature Delta

Prefer no source API delta. If scoring a live artifact reveals a legitimate
extraction bug, keep changes to the existing seams:

```python
load_demo_score_inputs(..., overlay_report_path: Path | None) -> HeroDemoScoreInputs
build_reasoning_overlay_events(..., limit: int = 10) -> list[ReasoningOverlayEvent]
run_studio_demo_video(..., speed_factor: float = 4.0) -> StudioCommandResult
```

#### Type Sketch

```python
HeroArtifactSet = {
  "db_path": str,
  "run_manifest_path": str,
  "carla_report_path": str,
  "policy_evaluation_path": str,
  "policy_decision_path": str,
  "source_video_path": str,
  "overlay_report_path": str,
  "hero_video_path": str,
  "score_report_path": str,
  "claim_boundaries": list[str],
}
```

#### Typed Flow Example

`TASK-128 DB + run_manifest + policy_evaluation + TASK-102 84s MP4`
-> `oodrive demo-video`
-> `hero_demo_video.json`
-> `oodrive score-demo`
-> if score `<72`, improve the artifact and evidence linkage without lowering
thresholds or inflating fake counts.

#### Execution Steps

1. Verify or reconstruct TASK-128 DB/run/evaluation artifacts locally.
2. Render `task131-score-gated-hero-v1` from the TASK-102 source clip.
3. Score the rendered video with `oodrive score-demo --metric-only`.
4. If blocked, fix missing evidence paths, overlay report fields, event counts,
   or a true source extraction issue.
5. Iterate with versioned run ids until score is at least `72`.
6. Attach ticket evidence with exact commands, MP4/report paths, score, and
   claim boundaries.
7. Run focused checks, full pre-push, review, and history writeback before
   completion claim.

#### Recommendation

Prioritize this score-gated artifact before TASK-129 or fresh CARLA runtime.
TASK-130 already created the quality contract; this ticket feeds it real
evidence and produces the missing judge-facing proof.

#### Options considered

- Use TASK-128 video directly: strongest provenance, but only `30s` and
  visually weak.
- Use TASK-102 source with TASK-128 reasoning artifacts: selected because it has
  the best visible CARLA substrate and can carry the product-loop overlays.
- Start TASK-129 first: useful later, but does not fix demo quality.

#### Blast radius

- Generated MP4 and run artifacts remain ignored under `artifacts/`.
- Score thresholds and claim boundaries remain unchanged.
- Submission docs update only after a passing artifact exists.

#### Risks

- Kasm TASK-128 JSON may be unavailable; reconstruct the minimal local evidence
  from recorded QA and mark provenance explicitly.
- TASK-102 video may not exactly match the TASK-128 scenario; if linkage
  weakens scoring, use TASK-128 video and improve overlays instead.
- Scoring can be gamed; keep inputs traceable and preserve open-loop labels.

### Acceptance Criteria

- [x] AC-1: TASK-131 records the artifact-first execution state.
- [x] AC-2: Local TASK-128 DB/run/evaluation evidence is available or a precise
  blocker is recorded.
- [x] AC-3: A rendered local hero MP4 exists, lasts `30-75s`, and includes
  frame/time, scenario/OOD context, risk telemetry, at least 3 reasoning
  snippets, and at least 3 RAG callouts.
- [x] AC-4: `oodrive score-demo` returns `hero_demo_score >= 72`.
- [x] AC-5: Claim labels remain
  `closed_loop_vla_control=false`, `real_time_vla_control=false`,
  `sampled_open_loop_reasoning=true`, and `time_warped_offline_demo=true`.

### Verification

- PASS: `PYTHONPATH=src python3 -m oodrive score-demo ... --metric-only`
  emitted `METRIC hero_demo_score=100.0000`.
- PASS: `./autoresearch.sh` emitted `METRIC hero_demo_score=100.0000`.
- PASS: `./autoresearch.checks.sh` ran 18 tests, all passing.
- PASS: `PYTHONPATH=src python3 -m unittest tests.test_hero_demo_score tests.test_reasoning_timeline_overlay tests.test_oodrive_cli` ran 14 tests, all passing.
- PASS: `bash scripts/pre_push_check.sh` ran 404 tests with 4 skips and passed.
- PASS: review artifact linked below.

### Evidence

- QA: `tickets/TASK-131/artifacts/qa/score_gated_hero_demo_qa.md`
- Hero MP4:
  `artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/oodrive_hero_demo.mp4`
- Overlay report:
  `artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/hero_demo_video.json`
- Score report:
  `artifacts/runs/task128-oodrive-live-product/demo-scores/task131-score-gated-hero-v2-score/hero_demo_score.md`
- Score JSON:
  `artifacts/runs/task128-oodrive-live-product/demo-scores/task131-score-gated-hero-v2-score/hero_demo_score.json`
- Review: `tickets/TASK-131/artifacts/review/task131-review.json`

### Blockers

- None.
