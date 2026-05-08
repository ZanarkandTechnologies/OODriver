# TASK-143: CARLA Bad-Path Video Gate

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-142
- location: `src/driverx/evaluation`, `src/driverx/simulators`, `artifacts/runs/task143-carla-bad-path-score`, `tickets/TASK-143`
- enter when: TASK-142 has a CARLA MP4 or partial CARLA evidence, but the artifact still needs a ruthless quality gate so it cannot pass while looking off-lane, unclear, or generic.
- leave when: `oodrive` can score the CARLA bad-path artifact for lane alignment, hazard visibility, ego response, duration, telemetry overlays, and claim honesty, with a pass threshold for promotion.
- blockers: needs at least one TASK-142 artifact or blocker fixture to score.
- spawned follow-ups: TASK-144 final packet refresh.
- complexity: S

### Description

Add or reuse a mechanical scoring/report path for the bad-path CARLA video. The gate should punish exactly what the user caught: driving out of the lane, unclear obstacle avoidance, missing hazard visibility, and vague presentation that does not prove the system generated a meaningful OOD case.

### Goal

Make bad-path CARLA promotion evidence-based instead of vibe-based. A skeptical judge should be able to see why the artifact passes or why it is blocked.

### Acceptance Criteria
- [ ] AC-1: Score report checks MP4 presence/duration, RGB/frame evidence, hazard/object visibility metadata, entity-track lane corridor, ego response states, and claim boundaries.
- [ ] AC-2: Report fails or blocks if `lane_departure_proxy=true`, missing frames, missing object tracks, or no visible stop/slow/swerve/recover event.
- [ ] AC-3: The selected TASK-142 artifact is scored and either passes promotion or gives a short defect list.
- [ ] AC-4: Focused tests cover pass, lane-departure fail, missing-video block, and claim-boundary fail.

### Agent Contract
- Open: `src/driverx/evaluation/hero_demo_score.py`, `src/driverx/evaluation/generator_runtime_score.py`, `src/driverx/pipeline/bad_path_stress_demo.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_bad_path_stress_demo tests.test_generated_carla_runtime tests.test_oodrive_cli`
- Stabilize: do not lower thresholds to pass a weak clip; fix the artifact or mark blocked.
- Inspect: score JSON/Markdown, video path, track/path metadata, claim labels.
- Expected artifacts: `carla_bad_path_score.json`, `carla_bad_path_score.md`.

### Metric Sketch

Target: `carla_bad_path_score >= 85`

Components:

- `video_presence_duration`
- `hazard_visibility`
- `lane_alignment`
- `ego_response_legibility`
- `object_track_evidence`
- `claim_honesty`

### Required Evidence
- [ ] Score command output.
- [ ] Score JSON/Markdown linked.
- [ ] Focused tests pass.
- [ ] Review before completion claim.
