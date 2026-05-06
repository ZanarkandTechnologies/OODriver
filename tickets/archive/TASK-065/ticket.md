# TASK-065: OOD Simulator Visual Evidence Surface

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-064
- location: `src/driverx/simulators`, `src/driverx/pipeline`, tests,
  `tickets/TASK-065/artifacts`
- enter when: TASK-064 local simulator exists
- leave when: local simulator output is a judge-visible playback/report surface
- blockers: none
- spawned follow-ups: none
- complexity: S

### Description
TASK-064 ships the first local simulator loop. This follow-up improves the
visual evidence into a more presentation-ready timeline with policy overlays,
failure markers, and artifact links.

### Goal
Make the local OOD simulator legible enough for the final deck/video without
requiring a live CARLA run.

### Acceptance Criteria
- [x] AC-1: Simulator HTML contains timeline rows for ego, OOD actor, baseline
  policy, and memory-guided policy.
- [x] AC-2: SVG/HTML labels include behavior pressure, closest approach, and
  collision-risk proxy.
- [x] AC-3: Visual output remains deterministic and testable without browser
  automation.
- [x] AC-4: README quickstart points at the visual artifact.

## Evidence
- Shipped as part of TASK-064 local simulator output:
  `tickets/TASK-064/artifacts/local-ood-demo/local-sim/local_ood_sim.html`.
- Focused tests: `tests.test_local_ood_sim` and `tests.test_end_to_end_ood_demo`.
- QA report: `tickets/TASK-064/artifacts/qa_report.md`.
- Review: `docs/reviews/TASK-064-067-local-ood-review.md`.

## Blockers
- None.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
