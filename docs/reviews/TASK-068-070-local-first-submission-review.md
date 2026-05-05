# TASK-068/TASK-070 Local-First Submission Review

Reviewed at: 2026-05-06 04:33 +0800

## Verdict

- overall_score: `4.1 / 5.0`
- threshold: `4.0`
- verdict: `pass`
- rerun_required: `false`

## Scope

- Tickets: `tickets/TASK-068/ticket.md`, `tickets/TASK-070/ticket.md`,
  supporting updates in `tickets/TASK-060/ticket.md`,
  `tickets/TASK-061/ticket.md`, and `tickets/TASK-069/ticket.md`.
- Code: `src/driverx/pipeline/route_evidence.py`,
  `src/driverx/pipeline/route_evidence_cli.py`,
  `src/driverx/pipeline/submission_demo_pack.py`,
  `src/driverx/pipeline/submission_demo_pack_cli.py`.
- Tests: `tests/test_route_evidence.py`, `tests/test_submission_demo_pack.py`.
- Evidence: TASK-064 local demo, TASK-068 Town13 route partial evidence, TASK-070
  submission pack V2, `blockers.md`, `docs/progress.md`, `README.md`,
  `ARCHITECTURE.md`.

## Findings

- No blocking findings.
- Low caveat: `src/driverx/pipeline/submission_demo_pack.py` is now 665 lines
  and appears in the pre-push large-file warning. It is below the current guard
  threshold and still modular enough to pass, but future submission-pack work
  should extract local-demo/storyboard helpers before adding more branches.
- Low caveat: `python3 tickets/scripts/check_ticket_metadata.py` could not run
  because that helper is absent in this repo checkout. This is a tooling surface
  gap, not a failure of the implemented tickets.

## Rubric Scores

- code-quality: `4.0 / 5.0`
  - The changes are localized to evidence aggregation and submission-pack
    generation, reuse existing CLI/run-dir patterns, and add tests for the new
    route-run blocker and local-demo pack inputs.
- evidence-quality: `4.2 / 5.0`
  - The main claims map to concrete artifacts: TASK-064 local HTML/JSON report,
    TASK-068 route-run JSON/logs/partial video evidence, and TASK-070 final pack.
    The remaining CARLA limitation is explicit rather than hidden.
- integration-readiness: `4.0 / 5.0`
  - The local-first pack is ready to hand off. Live closed-loop CARLA and
    route-aligned Alpamayo remain correctly separated into TASK-060/TASK-069
    blockers.

## Verification

- Focused:
  `PYTHONPATH=src python3 -m unittest tests.test_route_evidence tests.test_submission_demo_pack tests.test_end_to_end_ood_demo tests.test_behaviors tests.test_local_ood_sim`
  passed with 19 tests.
- Gate: `bash scripts/pre_push_check.sh` passed with 288 tests.
- Metadata helper: `python3 tickets/scripts/check_ticket_metadata.py` was
  attempted but the script is absent from this checkout.

## Next Action

Advance TASK-064 through TASK-068 and TASK-070 as local/demo-pack complete.
Keep TASK-060 and TASK-069 open as live-runtime follow-ups requiring a faster
graphics-capable CARLA host or a longer local route run.
