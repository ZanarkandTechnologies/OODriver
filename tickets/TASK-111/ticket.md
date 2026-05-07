# TASK-111: Reasoning And RAG Timeline Video Overlay

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-108, TASK-110, TASK-104
- location: `src/driverx/simulators`, `src/driverx/pipeline`, `tickets/TASK-111/artifacts`
- enter when: risk timeline and Alpamayo/RAG evidence exist but the video still does not show the reasoning loop
- leave when: an annotated MP4 shows risk detection, retrieved memory, VLA reasoning snapshot, and intended response as time-aligned panels
- blockers: none for cached/open-loop evidence; live Alpamayo rerun is optional
- spawned follow-ups: TASK-113
- complexity: M

### Summary

Upgrade the video from "CARLA footage" to "paper demo." TASK-111 overlays the
actual system loop onto frames: detected risk, retrieved memory, VLA reasoning
snapshot, recommended behavior, and claim boundary. Alpamayo remains sampled
open-loop reasoning, which is fine because the demo is time-warped rather than
real-time control.

### Scope

- In scope: overlay event schema, frame-to-event scheduler, PIL overlay renderer,
  MP4 assembly, cached reasoning/RAG support, fixture tests, and evidence report.
- Out of scope: real-time VLA serving, live closed-loop steering, SimLingo.

### Plan

#### Change

Add a richer overlay builder that consumes `ScenarioRunBundle`,
`risk_timeline.json`, and Alpamayo/RAG comparison artifacts.

#### Why

The current demo does not make the contribution visible. The overlay is the
place where viewers see "what the system knows and why it reacts."

#### Before -> After

- Before: one small overlay panel with id/tags.
- After: structured overlay panels show risk, memory retrieval, VLA reasoning,
  and action intent at key timestamps.

#### Touch

- Add `src/driverx/simulators/reasoning_timeline_overlay.py`
- Add pipeline wrapper `src/driverx/pipeline/reasoning_overlay_video.py`
- Add CLI `build-reasoning-overlay-video`
- Reuse/extend `src/driverx/simulators/route_video_assembly.py`
- Add tests in `tests/test_reasoning_timeline_overlay.py`

#### Inspect

- `src/driverx/simulators/ood_video_overlay.py`
- `src/driverx/pipeline/reasoning_video_pack.py`
- `src/driverx/pipeline/alpamayo_ood_evaluation.py`
- `src/driverx/pipeline/final_submission_pack.py`

#### Signature Delta

```python
build_reasoning_overlay_events(bundle: ScenarioRunBundle, risk: RiskTimeline, comparison: dict) -> list[ReasoningOverlayEvent]
render_reasoning_timeline_overlay(config: ReasoningOverlayConfig) -> ReasoningOverlayResult
build_reasoning_overlay_video(run_dir: Path, inputs: ReasoningOverlayInputs) -> dict[str, Any]
```

#### Type Sketch

```python
ReasoningOverlayEvent = {
  "start_s": float,
  "end_s": float,
  "risk": str,
  "memory_id": str | None,
  "memory_principle": str | None,
  "vla_reasoning": str | None,
  "action_intent": str,
  "claim": "sampled_open_loop_reasoning",
}
```

#### Typed Flow Example

`risk_event@12s + memory MEM-motorcycle-filtering + Alpamayo CoT`
-> overlay panel:
`Detected: motorcycle filtering front-left 2.4m`
`RAG: leave lateral clearance`
`VLA: slow and bias away`
-> `reasoning_overlay.mp4`.

#### Execution Steps

1. Define overlay event builder from bundle/risk/comparison artifacts.
2. Schedule events over video time; support time-warped video speed.
3. Render legible panels with larger typography and color-coded risk/memory/model rows.
4. Assemble MP4 from rendered frames.
5. Write `reasoning_overlay_video.json` with event counts and claim boundaries.
6. Add tests for event construction and rendered frame creation.

#### Recommendation

Implement before recording more footage. It will make even existing footage much
more understandable, then TASK-112 can improve the source video.

#### Options Considered

- Record narration only: helpful, but not machine-verifiable.
- Build a web UI: too slow for final sprint.
- Recommended: video overlay from structured artifacts.

#### Blast Radius

Medium. Touches video pipeline but should be additive.

#### Risks

- Text can become unreadable. Mitigation: fixed panel dimensions, large fonts,
  max line lengths, and a visual frame sample test.

### Gap Analysis

Fail2Drive-style demos feel strong because the viewer understands the failure.
0xDriver needs the same: visible risk, reasoning, and response. This ticket adds
that explanatory layer.

### Acceptance Criteria

- [ ] AC-1: Output MP4 includes risk, memory, VLA reasoning, and action intent panels.
- [ ] AC-2: Overlay supports time-warped playback and reports the speed factor.
- [ ] AC-3: Claim boundary says sampled/open-loop reasoning, not real-time control.
- [ ] AC-4: A fixture frame render test proves text fits and event rows appear.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_reasoning_timeline_overlay`
- `PYTHONPATH=src python3 -m driverx build-reasoning-overlay-video ...`
- `ffprobe` duration/size check.
- Visual sample PNG under ticket artifacts.
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Inputs: existing exported MP4, TASK-104 reasoning batch, TASK-110 risk timeline.
- Compute: local if source MP4 is local; RunPod only if we rerender source footage.
- Human gates: none.

### Evidence

- Pending: `tickets/TASK-111/artifacts/<run-id>/reasoning_overlay_video.json`
- Pending: ignored MP4 under `artifacts/exported/`
- Pending: sample frame PNG if small enough to track.

### Blockers

- None.
