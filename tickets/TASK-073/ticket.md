# TASK-073: Long Video Assembler And Evidence Overlay

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-072
- location: `src/driverx/simulators`, `src/driverx/pipeline`, tests,
  `tickets/TASK-073/artifacts`
- enter when: TASK-072 can produce RGB frames and entity tracks, or fixture
  frames are available for a no-CARLA proof
- leave when: a long MP4 and Markdown evidence report can be assembled with
  scenario, telemetry, risk, and claim-boundary overlays
- blockers: live long video waits on TASK-072 frames; fixture overlay tests can
  proceed immediately
- spawned follow-ups: TASK-077
- complexity: M

### Summary
Turn raw CARLA RGB frames and entity tracks into a submission-ready video
artifact. The video should be longer than the 0.5s TASK-071 proof and carry
lightweight overlays that explain what scenario is being tested.

### Scope
- In scope: frame discovery, overlay rendering onto copied frames, MP4 assembly,
  video metadata, report with artifact map and duration.
- Out of scope: editing the final narration, generating a full slide deck, or
  running Alpamayo inference.

### Gap Analysis
- Current state: `assemble-route-video` can create MP4 from frames, but it does
  not annotate scenario/risk/model context.
- Production expectation: judges should understand the OOD case while watching
  the video without reading raw JSON.
- Missing gaps: overlay frame renderer, entity-track summary, duration checks,
  and video report that distinguishes full demo vs partial evidence.
- Recommendation: add a reusable video overlay stage now so both CARLA scripted
  video and future Fail2Drive video share the same evidence language.

### Plan

#### Change
Add `assemble-ood-video` to render overlays over frame sequences, assemble MP4,
and write `ood_video_report.json/md`.

#### Why
A longer video is only useful if it tells the viewer what changed in the scene
and where the failure/risk occurs.

#### Before -> After
- Before: MP4 assembly proves frames exist but carries no scenario semantics.
- After: video evidence includes scenario id, OOD tags, behavior id, timestamp,
  nearest actor distance, and claim boundaries.

#### Touch
- `src/driverx/simulators/ood_video_overlay.py`: overlay frame renderer.
- `src/driverx/simulators/route_video_assembly.py`: reuse assembly plan/run.
- `src/driverx/pipeline/ood_video_evidence.py`: video report builder.
- `src/driverx/cli.py`, `src/driverx/simulators/__init__.py`,
  `src/driverx/pipeline/__init__.py`.
- `tests/test_ood_video_overlay.py`, `tests/test_ood_video_evidence.py`.
- `README.md`, `docs/progress.md`.

#### Inspect
- `src/driverx/simulators/route_video_assembly.py`
- `src/driverx/simulators/local_ood_sim.py`
- `tickets/TASK-071/artifacts/town13-early-video-assembly/route_video_assembly.json`

#### Signature Delta
```python
src/driverx/simulators/ood_video_overlay.py / render_ood_video_overlay(config: OodVideoOverlayConfig) -> OodVideoOverlayResult
src/driverx/pipeline/ood_video_evidence.py / build_ood_video_evidence(run_dir: Path, inputs: OodVideoEvidenceInputs) -> dict[str, Any]
```

#### Type Sketch
```python
OodVideoOverlayConfig = {
  "rgb_folder": Path,
  "tracks_path": Path | None,
  "output_frame_dir": Path,
  "scenario_id": str,
  "behavior_id": str,
  "ood_tags": list[str],
  "claim_label": "scripted_carla_ood_demo",
}

OodVideoEvidence = {
  "status": "passed" | "partial" | "blocked",
  "input_frame_count": int,
  "overlay_frame_count": int,
  "duration_s": float,
  "video_path": str | None,
  "worst_risk": dict[str, Any] | None,
  "claim_boundaries": list[str],
}
```

#### Typed Flow Example
`carla_ood_demo.json + rgb/*.png + entity_tracks.json`
-> overlay frames under `overlay_rgb/`
-> `assemble_route_video_from_watch`
-> `ood_video.mp4`
-> `ood_video_evidence.md` with duration and worst-risk summary.

#### Execution Steps
1. Implement a dependency-light overlay renderer with Pillow if installed and a
   clear blocker if unavailable; tests can use generated PNG fixtures.
2. Extract nearest-distance/risk summary from entity tracks when tracks exist.
3. Assemble overlay frames into MP4 using the existing ffmpeg seam.
4. Add CLI args for RGB folder, tracks, scenario id, behavior id, output video,
   FPS, and run id.
5. Add tests for overlay rendering, missing tracks, missing ffmpeg, and report
   status classification.
6. Generate one fixture video evidence report even if live CARLA frames are not
   available.

#### Recommendation
Use one reusable overlay pipeline rather than special-casing TASK-072. It will
also improve Fail2Drive and Alpamayo reasoning videos later.

#### Options Considered
- Raw video only: fastest but weak for judges.
- Full video editor/deck automation: too much for this ticket.
- Lightweight overlays plus Markdown evidence: best now/later boundary.

#### Blast Radius
- Video assembly and pipeline docs only.
- No CARLA control or policy behavior changes.

#### Risks
- Pillow may be absent; add optional dependency guidance and test fallback.
- Large videos must stay ignored and out of git.
- Overlays can obscure important frame detail; keep text compact and top-left.

### Acceptance Criteria
- [ ] AC-1: `assemble-ood-video` can create a video from fixture frames without
  CARLA.
- [ ] AC-2: Overlay report includes duration, frame count, scenario id,
  behavior id, OOD tags, and claim boundaries.
- [ ] AC-3: If entity tracks exist, report includes nearest-distance or
  worst-risk summary.
- [ ] AC-4: Missing frames, missing tracks, or missing ffmpeg produce
  actionable blockers rather than tracebacks.

### Verification
- Focused:
  `PYTHONPATH=src python3 -m unittest tests.test_ood_video_overlay tests.test_ood_video_evidence`
- Regression:
  `PYTHONPATH=src python3 -m unittest tests.test_route_video_assembly tests.test_submission_demo_pack`
- Full gate:
  `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- Can proceed using generated fixture PNGs if TASK-072 live frames are missing.
- Needs no GPU, no CARLA, and no model runtime for the core implementation.

### Refs
- PRD FR-5, FR-8, FR-9.
- TASK-071 short-video evidence.

### Evidence
- Planning created 2026-05-06 18:16 +0800.
- Review: `docs/reviews/TASK-072-077-impl-plan-review.md`.
- Implementation review: `docs/reviews/TASK-072-077-implementation-review.md`.
- Build: `src/driverx/simulators/ood_video_overlay.py`,
  `src/driverx/pipeline/ood_video_evidence.py`,
  `src/driverx/pipeline/ood_video_evidence_cli.py`, and
  `tests/test_ood_video_evidence.py`.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_ood_video_evidence`.
- Fixture proof:
  `tickets/TASK-073/artifacts/fixture-long-ood-video-v2/ood_video_evidence.md`
  produced a 20.0s MP4 with `source_kind=fixture`.

### Blockers
- Live long video artifact waits on TASK-072 frame output. Fixture overlay and
  assembly proof is complete and explicitly labeled as non-live evidence.
