# TASK-055: Live CARLA Route Video Evidence

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-041, TASK-054B
- location: `src/driverx/pipeline/route_evidence.py`, `tickets/TASK-055/artifacts`
- enter when: Docker Fail2Drive route path can reach local CARLA and produce RGB frames
- leave when: live CARLA route/video evidence is bundled into reviewable JSON/Markdown, with blockers clearly separating Town13 stock-split limits from Town10 fallback proof
- blockers: stock Fail2Drive split routes require `Town13`, which is absent from the local CARLA 0.9.16 install
- spawned follow-ups: TASK-056 Alpamayo OOD evaluation harness
- complexity: M

### Description
TASK-054B proved the Docker client can run Fail2Drive against local CARLA and
produce Town10 RGB frames/MP4. TASK-055 turns that proof into judge-visible
route evidence while keeping the true Fail2Drive OOD split blocker explicit.

### Goal
Produce one live CARLA video evidence bundle now, without pretending it is the
full Town13 Fail2Drive OOD split.

### Acceptance Criteria
- [x] AC-1: Route evidence uses the Town10 live CARLA fallback MP4 assembled by
  DriverX.
- [x] AC-2: Route evidence links result JSON, stdout/stderr logs, video path,
  duration, and metrics where parseable.
- [x] AC-3: Stale dry-run blockers are not carried into final evidence when the
  actual video/RGB artifact exists.
- [x] AC-4: Town13 stock Fail2Drive split map blocker remains documented.
- [x] AC-5: Generated MP4/JPG artifacts remain ignored and uncommitted.

### Agent Contract
- Open: `src/driverx/pipeline/route_evidence.py`,
  `tests/test_route_evidence.py`, TASK-054B artifacts
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_route_evidence`
- Stabilize: route evidence must describe evidence honestly; no claims of full
  closed-loop OOD completion unless the route actually completed.
- Expected artifacts: `tickets/TASK-055/artifacts/*`

### Evidence Checklist
- [x] Route evidence JSON: `tickets/TASK-055/artifacts/town10-route-evidence/run_evidence.json`
- [x] Route evidence report: `tickets/TASK-055/artifacts/town10-route-evidence/run_evidence.md`
- [x] Focused tests: `tickets/TASK-055/artifacts/focused_tests.log`
- [x] Full local gate: `tickets/TASK-055/artifacts/pre_push_check.log`
- [x] QA report: `tickets/TASK-055/artifacts/qa_report.md`

### Build Notes
- Added route-evidence stale-plan-blocker filtering. If DriverX later assembles
  a video from RGB frames, the original dry-run blockers for missing
  Fail2Drive video helper and pre-run missing RGB are suppressed.
- Built Town10 fallback route evidence from TASK-054B:
  - result JSON exists but has no completed score because the run was bounded
    by a smoke timeout;
  - video exists (`41` frames, `4.1s`, about `7.9MB`);
  - stdout/stderr route logs are linked;
  - entity tracks are absent and therefore no track metric is claimed.
- Town13 remains the real stock Fail2Drive split blocker because local CARLA
  only has Town01-05, Town10HD, optimized variants, and AnnotationColorLandscape.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS
- AC-5: PASS

### Artifact Links
- `tickets/TASK-055/artifacts/town10-route-evidence/run_evidence.json`
- `tickets/TASK-055/artifacts/town10-route-evidence/run_evidence.md`

### User Evidence
- Supporting evidence: live CARLA route produced RGB frames and DriverX MP4 in
  TASK-054B ignored artifacts; TASK-055 commits only compact evidence.
- QA report: `tickets/TASK-055/artifacts/qa_report.md`
- Review: `tickets/TASK-055/artifacts/review.md`
- Final verdict: complete; ready for TASK-056.

### Required Evidence
- [x] Unit/integration/e2e tests pass (as applicable)
- [x] Lint passes
