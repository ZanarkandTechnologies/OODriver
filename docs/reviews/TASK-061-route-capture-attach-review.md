# TASK-061 Route Capture Attach Review

## Review Result

- work_type: backend, simulator integration, evidence
- reviewed_at: 2026-05-06 03:34 +0800
- verdict: partial_pass
- rerun_required: true for live route-aligned proof
- overall_score: 4.0 / 5.0 for the implemented fake-attach seam
- threshold: 4.0
- evidence_quality: pass for AC-1
- integration_readiness: pass for AC-1
- traceability: pass
- freshness: pass

## Search Scope

- Ticket: `tickets/archive/TASK-061/ticket.md`
- Code:
  - `src/driverx/simulators/carla_alpamayo_capture.py`
  - `src/driverx/simulators/carla_alpamayo_capture_cli.py`
  - `src/driverx/simulators/__init__.py`
- Tests:
  - `tests/test_carla_alpamayo_capture.py`
  - `tests/test_alpamayo_live.py`
  - `tests/test_alpamayo_ood_evaluation.py`
- Docs:
  - `README.md`
  - `src/driverx/simulators/README.md`
  - `docs/progress.md`
  - `docs/HISTORY.md`

## Rubrics Used

### Code Quality: 4.0 / 5.0

- pass: true
- dimension_scores:
  - modularity-reusability: 4.0
  - bloatability: 4.0
  - readability: 4.0
  - boundary-clarity: 4.1
  - error-handling: 4.0
  - maintainability: 4.0

The attach seam stays inside the CARLA capture module and preserves the existing
spawned-ego path. `CarlaActorAttachConfig` makes actor-id, role-name,
blueprint-filter, and fallback behavior explicit. Attached route actors are not
destroyed by cleanup.

### Evidence Quality: 4.0 / 5.0

- pass: true for AC-1
- dimension_scores:
  - sufficiency: 4.0
  - reproducibility: 4.0
  - traceability: 4.0
  - consistency: 4.0
  - inspectability: 4.0
  - autonomy-readiness: 4.0

Focused tests prove actor discovery, attach without destruction, route metadata
package writing, and the no-fallback error path. Live route-aligned evidence
remains explicitly blocked on TASK-060.

### Integration Readiness: 4.0 / 5.0

- pass: true for AC-1
- dimension_scores:
  - integration-safety: 4.1
  - contract-correctness: 4.0
  - dependency-readiness: 3.8
  - coupling-risk: 4.0
  - merge-readiness: 4.0

The seam is safe to merge as a local foundation because it does not require
Town13 or a live route to validate. The full ticket still needs TASK-060 before
AC-2 through AC-4 can close.

## Finding Log

- No blocking findings for the implemented AC-1 seam.
- Medium severity: full TASK-061 remains incomplete until a live Town13
  Fail2Drive route provides the hero actor and route evidence. This is already
  recorded as the active blocker.

## Next Action

Keep TASK-061 open in `building` with AC-1 complete. Resume live capture and
Alpamayo comparison after TASK-060 produces route evidence.
