# TASK-040: Submission Demo Pack

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-034, TASK-036, optional TASK-038/TASK-039
- location: `docs`, `tickets/TASK-040/artifacts`, reports
- enter when: at least one route video or route-evidence bundle exists
- leave when: a 1-5 minute video/deck outline, failure case, repo evidence map,
  and short write-up draft exist
- blockers: live route video still missing; demo pack names this as the first
  understood failure case rather than claiming it is solved
- spawned follow-ups: none
- complexity: M

## Summary

Assemble the submission story from generated scenarios, route videos, policy
results, blockers, and future-work claims.

## Acceptance Criteria

- [x] Demo outline references concrete artifacts.
- [x] Failure case is included and understood.
- [x] Write-up separates shipped proof from future work.
- [x] Model/asset/data declarations are explicit.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_submission_demo_pack`
- `PYTHONPATH=src python3 -m driverx build-demo-pack --generated-suite artifacts/runs/task36-suite-1b/generated_ood_suite.json --policy-matrix artifacts/runs/task37-policy-matrix-review/policy_runtime_matrix.json --alpamayo-probe artifacts/runs/task38-local-probe/alpamayo_probe_report.json --blockers blockers.md --progress docs/progress.md --output-root artifacts/runs --run-id task40-demo-pack`

## Evidence

- Code: `src/driverx/pipeline/submission_demo_pack.py`
- CLI: `python -m driverx build-demo-pack`
- Report: `artifacts/runs/task40-demo-pack/submission_demo_pack.md`
- JSON: `artifacts/runs/task40-demo-pack/submission_demo_pack.json`
- Review: `tickets/TASK-040/artifacts/review/20260505T193200-review.json`

## Blockers

- Live route video remains missing because the external Fail2Drive checkout
  lacks `tools/generate_video.py` and the generated suite has not yet produced
  route result/video artifacts. The demo pack turns this into the named failure
  case for the current submission story.
