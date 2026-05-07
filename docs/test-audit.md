# Test Audit

Last audit: 2026-05-07.

## Result

- Test files: `91`
- Test cases discovered by AST scan: `388`
- Exact duplicate test bodies found: `0`
- Repeated high-level names with four or more copies: `0`
- Intentional skips found: `3`

The count is high for a small repo because the project now spans many external
runtime seams: CARLA, Fail2Drive, Alpamayo, SimLingo, Waymo, Docker wrappers,
submission packaging, and video generation. The audit did not find safe exact
duplicates to delete without reducing coverage on those seams.

## Decision

No tests were deleted in this pass. The useful pruning target is not "remove
count"; it is "avoid redundant integration-smoke growth." Future tickets should
prefer adding one focused test per new public seam and extending existing CLI or
artifact tests only when the behavior is truly new.

## Current Useful Families

- `test_cli.py`: command registration and argument compatibility across the
  dynamic CLI surface.
- `test_carla_*`, `test_fail2drive_*`: simulator wrappers, Docker/runtime
  planning, route evidence, and maps.
- `test_alpamayo_*`: model probe, tensor materialization, live/offline adapter,
  trajectory conversion, and OOD comparison artifacts.
- `test_submission_*`, `test_final_submission_pack_*`: judge-facing packet and
  browser artifacts.
- `test_*video*`: video assembly, evidence, overlay, and retiming paths.
- `test_waymo_*`: retained real-data support track.

## Prune Later

- Consolidate old SimLingo tests if the SimLingo lane remains deprioritized
  after submission.
- Merge adjacent CLI smoke tests only after CLI command names stabilize.
- Remove historical compatibility tests only after their source tickets are
  explicitly marked unsupported, not merely because their count looks large.
