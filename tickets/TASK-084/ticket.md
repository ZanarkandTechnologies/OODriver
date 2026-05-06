# TASK-084: Reasoning And Trajectory Overlay Video Pack

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-079, TASK-080, TASK-081
- location: `src/driverx/pipeline`, `src/driverx/simulators`, tests, `tickets/TASK-084/artifacts`
- enter when: live OOD video and same-scene Alpamayo comparison exist
- leave when: one reviewable video/HTML evidence pack overlays CARLA footage with Alpamayo reasoning, memory ids, trajectory deltas, and claim boundaries
- blockers: none; can run from existing artifacts without CARLA or GPU
- spawned follow-ups: TASK-088
- complexity: M

### Summary

Create the missing judge-facing reasoning surface: a video or HTML pack that
shows the CARLA OOD scene and the model reasoning side by side. This turns the
current JSON/Markdown Alpamayo evidence into something a human can understand
in a 1-5 minute submission.

### Scope

- In scope: rendered reasoning cards, trajectory delta summaries, memory ids,
  worst-risk tick, CoC snippets, artifact links, and optional MP4 composition
  from existing frames/video.
- Out of scope: rerunning CARLA, rerunning Alpamayo, editing a polished final
  narration, or inventing hidden model claims.

### Plan

#### Change

Add a `build-reasoning-video-pack` command that consumes TASK-079 video
evidence, TASK-080 scene report, and TASK-081 comparison. It writes a compact
HTML/Markdown/JSON pack, plus optional overlay frames/MP4 when source RGB or
video frames are available.

#### Why

The repo now has strong evidence, but the reasoning is split across files. A
single visual proof surface makes the submission easier to judge and reduces
the risk that the demo becomes "here are JSON artifacts."

#### Before -> After

- Before: CARLA video, CoC, trajectory deltas, and memory ids live in separate
  artifacts.
- After: one pack shows the scene, what Alpamayo said, what memory was
  supplied, and how the trajectory changed.

#### Touch

- `src/driverx/pipeline/reasoning_video_pack.py`: new builder.
- `src/driverx/pipeline/reasoning_video_pack_cli.py`: CLI registration.
- `src/driverx/simulators/ood_video_overlay.py`: reuse or extend annotation
  primitives only if needed.
- `src/driverx/pipeline/submission_demo_pack.py`: optionally link reasoning
  pack in artifact map.
- `src/driverx/cli.py`.
- `tests/test_reasoning_video_pack.py`.
- `README.md`, `docs/progress.md`.

#### Inspect

- `src/driverx/pipeline/ood_video_evidence.py`
- `src/driverx/pipeline/alpamayo_ood_scene.py`
- `src/driverx/pipeline/alpamayo_ood_evaluation.py`
- `tickets/TASK-079/artifacts/task79-live-ood-video/ood_video_evidence.json`
- `tickets/TASK-081/artifacts/task81-live-same-scene-comparison/alpamayo_ood_comparison.json`

#### Signature Delta

```python
src/driverx/pipeline/reasoning_video_pack.py / build_reasoning_video_pack(run_dir: Path, inputs: ReasoningVideoPackInputs) -> dict[str, Any]
src/driverx/pipeline/reasoning_video_pack.py / write_reasoning_video_pack(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]
```

#### Type Sketch

```python
ReasoningVideoPackInputs = {
  "ood_video_evidence_path": Path,
  "alpamayo_scene_path": Path,
  "alpamayo_comparison_path": Path,
  "source_rgb_folder": Path | None,
  "fps": 5,
}

ReasoningVideoPack = {
  "status": "ready" | "partial" | "blocked",
  "scenario_id": str,
  "video_path": str | None,
  "html_path": str,
  "cot_snippets": {"baseline": str | None, "memory": str | None},
  "memory_ids": list[str],
  "trajectory_delta": dict,
  "claim_boundaries": list[str],
}
```

#### Typed Flow Example

`ood_video_evidence.json + alpamayo_ood_scene.json + alpamayo_ood_comparison.json`
-> `build_reasoning_video_pack`
-> `reasoning_pack.html`
-> optional `reasoning_overlay.mp4`
-> V5 demo pack links this as the reasoning proof.

#### Execution Steps

1. Implement JSON extraction helpers for scene/video/comparison artifacts.
2. Render a static HTML evidence pack first; avoid video dependency for the
   primary proof.
3. Add optional frame overlay/MP4 assembly when `source_rgb_folder` exists.
4. Add tests for missing CoC, missing MP4, and memory/no-memory comparison.
5. Wire CLI and update demo pack artifact map.

#### Recommendation

Make HTML the canonical artifact and MP4 the bonus. HTML is easier to commit,
inspect, and link; MP4 can remain ignored.

#### Options Considered

- Only update the V4 Markdown: fast, but not visually compelling.
- Generate a polished narrated video now: too presentation-heavy before final
  evidence stabilizes.
- Build a reusable reasoning pack: best balance; durable and demo-ready.

#### Blast Radius

- New pipeline module plus optional demo-pack link.
- No CARLA/model runtime changes.

#### Risks

- CoC text may be short or unchanged between memory/no-memory; the pack should
  show trajectory delta and memory ids so the comparison still has substance.
- MP4 generation can fail if frame paths are missing; HTML remains the primary
  pass path.

### Acceptance Criteria

- [ ] AC-1: Builder writes JSON, Markdown, and HTML reasoning pack from existing TASK-079/TASK-081 artifacts.
- [ ] AC-2: Pack includes CoC snippets, memory ids, trajectory delta, video/source labels, and claim boundaries.
- [ ] AC-3: Optional MP4 generation is skipped or marked partial without failing the HTML pack.
- [ ] AC-4: V5/demo surfaces can link the pack without requiring heavy artifacts in git.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_reasoning_video_pack tests.test_submission_demo_pack`
- `PYTHONPATH=src python3 -m driverx build-reasoning-video-pack --ood-video-evidence tickets/TASK-079/artifacts/task79-live-ood-video/ood_video_evidence.json --alpamayo-scene tickets/TASK-080/artifacts/task80-live-same-scene-alpamayo-scene-v2/alpamayo_ood_scene.json --alpamayo-comparison tickets/TASK-081/artifacts/task81-live-same-scene-comparison/alpamayo_ood_comparison.json --run-id task84-reasoning-pack`

### Autonomy Readiness

- Fully local.
- No CARLA, GPU, HF, or API key required.

### Evidence

- Planned 2026-05-06 from existing TASK-079/TASK-081 evidence.
- Plan review: `docs/reviews/TASK-083-088-impl-plan-review.md`.

### Blockers

- None.
