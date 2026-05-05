# TASK-019: SimLingo Result Ingestion

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-017 result JSON or blocker artifacts
- location: `src/driverx/simulators`, CLI, tests, docs
- enter when: SimLingo/Bench2Drive route artifacts exist locally or remotely
- leave when: result JSONs can be parsed into stable 0xDriver reports
- blockers: none for local ingestion
- spawned follow-ups: H100 rerun, generated OOD route ingestion
- complexity: M

### Summary
Turn raw SimLingo/Bench2Drive output into a stable 0xDriver report. TASK-017
proved the closed-loop runtime reaches route execution and captured a precise
Blackwell CUDA blocker; this ticket makes those artifacts easy to inspect,
compare, and reuse in the final submission narrative.

### Acceptance Criteria
- [x] Parse Bench2Drive `seed_*_res.json` into a typed record.
- [x] Preserve route id, scenario name, town, route completion, driving score,
  infraction penalty, status, sensors, and exception summary.
- [x] Optionally include CUDA compatibility and route log blocker context.
- [x] Write JSON and Markdown report artifacts.
- [x] Add CLI entrypoint for local artifact ingestion.
- [x] Add tests for failed route parsing and blocker report output.
- [x] Run `bash scripts/pre_push_check.sh`.

### Evidence
- QA report:
  `tickets/TASK-019/artifacts/qa/2026-05-04T200000Z/result-ingestion/simlingo_result_report.md`
- JSON record:
  `tickets/TASK-019/artifacts/qa/2026-05-04T200000Z/result-ingestion/simlingo_result_record.json`
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_simlingo_result_ingestion`
  `PYTHONPATH=src python3 -m unittest tests.test_cli`
- Upstream sample check:
  `PYTHONPATH=src python3 -m driverx ingest-simlingo-result --result ../external/simlingo/Bench2Drive/pdm_lite_b2d_traj/eval_bench2drive220_0.json --output-root /tmp/driverx-ingest-test --run-id upstream-sample`
  reported `Completed`, `success=true`, `route_count=55`, and global
  `driving_score=99.285864`.
- Upstream sample report:
  `tickets/TASK-019/artifacts/qa/2026-05-04T200000Z/upstream-sample/simlingo_result_report.md`
- Local gate: `bash scripts/pre_push_check.sh` passed with `118` tests.
- Review:
  `docs/reviews/TASK-019-simlingo-result-ingestion-review.md`
