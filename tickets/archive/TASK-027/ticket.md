# TASK-027: OOD Suite Remote Evidence Ingestion

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-025, TASK-026
- location: `src/driverx/pipeline/ood_suite_report.py`, `tests`,
  `tickets/TASK-027/artifacts`
- enter when: TASK-020/TASK-026 remote SimLingo evidence exists but the OOD
  suite report still expects the older `simlingo_result_record.json` shape
- leave when: the suite report can consume either old SimLingo result records
  or new remote-evidence summaries and surface blockers/readiness correctly
- blockers: none for local implementation
- spawned follow-ups: none
- complexity: S

## Summary

Extend the OOD suite report so `--simlingo-result` accepts both TASK-019
`simlingo_result_record.json` artifacts and TASK-026
`remote_simlingo_evidence.json` artifacts. Regenerate the suite report so the
current H100 CARLA/Vulkan blocker is visible in the top-level submission
evidence packet.

## Acceptance Criteria

- [x] AC-1: OOD report detects remote SimLingo evidence JSON by `state` and
  `blockers`.
- [x] AC-2: Remote evidence contributes `success`, `state`, selected route/log
  paths, diagnostics path, and blocker text to the SimLingo component.
- [x] AC-3: Existing TASK-019 result-record behavior remains compatible.
- [x] AC-4: Tests cover both SimLingo result shapes.
- [x] AC-5: Fresh OOD suite report references TASK-020 H100 CARLA/Vulkan
  blocker.

## Evidence

- Fresh suite manifest:
  `tickets/TASK-027/artifacts/ood-suite-report-task20-blocker/ood_suite_manifest.json`
- Fresh suite report:
  `tickets/TASK-027/artifacts/ood-suite-report-task20-blocker/ood_suite_report.md`
- Report highlights: `simlingo_success=false`,
  `simlingo_state=route_infrastructure_blocked`, route log path
  `tickets/TASK-020/artifacts/task20-remote/run_one_route_with_carla.log`,
  diagnostics path
  `tickets/TASK-020/artifacts/task20-remote/carla_runtime_diagnostics.md`,
  and the TASK-020 H100 CARLA/Vulkan blocker in open blockers.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_ood_suite_report tests.test_cli_ood_suite_report`
  passed with `6` tests.
- Local gate: `bash scripts/pre_push_check.sh` passed with `161` tests.
- Review:
  `tickets/TASK-027/artifacts/review/2026-05-05_171900_review.md`
  passed with overall score `4.0`.

## Blockers

- None currently.
