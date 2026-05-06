# TASK-098: Promote RunPod OOD Evidence Into Submission Browser

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-097
- location: `src/driverx/scenarios/catalog.py`, `tests/test_scenario_catalog.py`, `tickets/TASK-097/artifacts`
- enter when: TASK-097 has pulled RunPod campaign and overlay video evidence locally
- leave when: the pulled RunPod evidence indexes as a quality-passed hero scenario and the V6 browser/dossier links the overlay video
- blockers: none
- spawned follow-ups: TASK-099 Alpamayo reasoning overlay on the RunPod hero scenario
- complexity: S

### Description

The RunPod campaign produced the first credible 60s CARLA OOD video, but the
best annotated overlay MP4 was a standalone `ood_video_evidence.json` artifact.
The scenario catalog only understood campaign, CARLA demo, and Alpamayo batch
summaries, so the browser could miss the artifact that judges should see.

### Goal

Index standalone OOD video evidence, resolve pulled RunPod paths back to local
artifact files, promote the quality-passed scenario to hero, and generate a
submission browser/dossier around the real RunPod video.

### Acceptance Criteria

- [x] AC-1: Scenario catalog indexes `ood_video_evidence.json`.
- [x] AC-2: Pulled RunPod paths such as `artifacts/runs/<run-id>/...` resolve
  to local extracted artifact files.
- [x] AC-3: When campaign evidence and overlay evidence refer to the same
  scenario, the catalog keeps road-alignment quality and prefers the overlay
  video path.
- [x] AC-4: The RunPod hero scenario is promoted and exported as a selectable
  `hero` with video and road-alignment gates.
- [x] AC-5: The submission browser and V6 dossier build from the promoted
  RunPod catalog.

### Build Notes

- Added OOD video evidence indexing to `driverx.scenarios.catalog`.
- Added artifact path resolution for pulled RunPod bundles where JSON still
  contains remote-style `artifacts/runs/...` paths.
- Added a regression fixture proving overlay evidence wins over the raw
  campaign video path.

### Evidence

- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_scenario_catalog tests.test_submission_scenario_browser`.
- Full gate:
  `bash scripts/pre_push_check.sh` passed with `357` tests, `2` skips, and
  compileall lint.
- Ticket metadata checker:
  `python3 tickets/scripts/check_ticket_metadata.py` could not run because the
  repository does not contain `tickets/scripts/check_ticket_metadata.py`; this
  is a repo-tooling gap, not a TASK-098 runtime blocker.
- Review fix: a reviewer found the first generated browser had non-resolving
  artifact links from the HTML output directory; v4 regenerates the browser
  with relative links and a regression test verifies emitted hrefs resolve.
- Catalog:
  `tickets/TASK-097/artifacts/task97-scenario-catalog-v3/scenario_catalog.json`.
- Promoted hero catalog:
  `tickets/TASK-097/artifacts/task97-scenario-catalog-hero-v3/scenario_catalog.json`.
- Hero selection:
  `tickets/TASK-097/artifacts/task97-hero-selection-v3/runpod-hero-scenarios.json`.
- Submission browser:
  `tickets/TASK-097/artifacts/task97-submission-browser-runpod-v4/scenario_browser.html`.
- Submission dossier:
  `tickets/TASK-097/artifacts/task97-submission-browser-runpod-v4/submission_dossier_v6.md`.
- Video script:
  `tickets/TASK-097/artifacts/task97-submission-browser-runpod-v4/video_script_v6.md`.
- Review:
  `tickets/TASK-098/artifacts/review/task97-098-review.json` passes with
  overall score `4.2`.

### Blockers

- None.
