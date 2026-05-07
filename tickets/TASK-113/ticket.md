# TASK-113: Paper-Style Final Demo And Submission Pack V8

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-108, TASK-109, TASK-110, TASK-111, TASK-112
- location: `scripts`, `src/driverx/pipeline`, `tickets/TASK-113/artifacts`
- enter when: workbench bundle, generation loop, risk timeline, reasoning overlay, and time-warped video evidence exist
- leave when: final V8 demo video/browser/write-up foreground the novel Scenario Studio + CARLA + RAG + VLA reasoning loop
- blockers: waits on upstream ticket artifacts; can ship with precise partial rows
- spawned follow-ups: none before submission
- complexity: M

### Summary

Rebuild the final submission around the actual contribution: an agentic CARLA
OOD scenario generator and evidence flywheel. The final video should feel like
a paper/demo: scenario generation, simulator run, risk perception, memory
retrieval, VLA reasoning, curation, and future real-time VLA work.

### Scope

- In scope: V8 final pack builder or extension, demo video script/renderer,
  browser update, two-page write-up refresh, artifact map, claim-boundary audit,
  and final review.
- Out of scope: new simulator/model features after this point.

### Plan

#### Change

Create a V8 submission pack that consumes the new workbench artifacts and
replaces the current generic draft with the product/research story.

#### Why

The current draft video is not wrong, but it does not explain the novelty. V8
must show "here is what 0xDriver contributes to minimal-shot autonomy."

#### Before -> After

- Before: title cards + CARLA clip.
- After: paper-style demo with generated scenario queue, CARLA time-warped
  clip, risk timeline, retrieved memory, VLA reasoning panels, and curation
  flywheel.

#### Touch

- Extend `src/driverx/pipeline/final_submission_pack.py` or add
  `src/driverx/pipeline/final_submission_pack_v8.py`
- Update `scripts/build_final_demo_video.sh` or add
  `scripts/build_paper_demo_video.sh`
- Add `tickets/TASK-113/artifacts/final-submission-pack-v8/`
- Update README current packet links after V8 lands
- Add tests in `tests/test_final_submission_pack_v8.py` if new builder exists

#### Inspect

- `src/driverx/pipeline/final_submission_pack.py`
- `scripts/build_final_demo_video.sh`
- `tickets/TASK-107/artifacts/final_demo_packet.md`
- New artifacts from TASK-108 through TASK-112.

#### Signature Delta

```python
build_final_submission_pack_v8(run_dir: Path, inputs: FinalPackV8Inputs) -> dict[str, Any]
build_paper_demo_video(inputs: PaperDemoVideoInputs) -> PaperDemoVideoResult
```

#### Type Sketch

```python
FinalPackV8Inputs = {
  "workbench_bundle": Path,
  "agentic_loop": Path,
  "risk_timeline": Path,
  "reasoning_overlay_video": Path,
  "timewarp_video": Path,
  "alpamayo_batch": Path,
}
```

#### Typed Flow Example

TASK-108 bundle + TASK-111 overlay video + TASK-112 timewarp evidence
-> V8 scorecard
-> `scenario_browser_v8.html`
-> `writeup_2page_v8.md`
-> final 1-5 minute demo MP4.

#### Execution Steps

1. Freeze final evidence inputs from TASK-108 through TASK-112.
2. Build V8 scorecard around generation, perception, RAG, reasoning, and video.
3. Generate browser/write-up/video script with explicit future-work section:
   real-time VLA serving is next phase, not current claim.
4. Render final demo video or packet from reasoning overlay and title cards.
5. Run final evidence review and pre-push gate.

#### Recommendation

This is the final packaging stop. After TASK-113, do not add features unless a
reviewer finds a blocking defect.

#### Options Considered

- Patch TASK-107 only: quicker but keeps weak story.
- Make a full UI product: too much for one day.
- Recommended: paper-style V8 pack with structured workbench evidence.

#### Blast Radius

Medium. Final packaging surfaces change, but source systems remain stable.

#### Risks

- Overclaiming real-time reasoning. Mitigation: every video/report labels
  time-warped offline demo and sampled open-loop VLA reasoning.

### Gap Analysis

The final artifact needs to look like the project you want to fund: a simulator
data engine plus minimal-shot reasoning evaluator. V8 makes that obvious.

### Acceptance Criteria

- [x] AC-1: Final video/deck shows scenario generation, risk detection, RAG, VLA reasoning, and curation.
- [x] AC-2: V8 write-up clearly states real-time VLA is future work.
- [x] AC-3: Browser/pack links all new evidence artifacts and no heavy videos are tracked.
- [x] AC-4: Final review passes evidence-quality and demo/video-quality rubrics.

### Verification

- Unit tests for V8 pack builder if added.
- JSON validation over V8 pack and artifact map.
- `ffprobe` duration check for final MP4.
- Secret/heavy-artifact scan.
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Inputs: upstream ticket artifacts.
- Compute: local video assembly; optional CARLA host already isolated in TASK-112.
- Human gates: final subjective approval of demo cut only.

### Evidence

- Built: `tickets/TASK-113/artifacts/final-submission-pack-v8/`
- Built ignored final MP4: `artifacts/exported/final_sota_demo_v8.mp4`
- Review: `tickets/TASK-113/artifacts/review/task108-113-impl-review.md`

### Blockers

- Upstream artifact gaps become partial rows, not hidden blockers.
