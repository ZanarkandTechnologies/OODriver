# TASK-058 Town13 Install Review

## Review Result

- work_type: simulator integration, local runtime evidence
- reviewed_at: 2026-05-06 03:34 +0800
- verdict: pass_with_followup_blocker
- rerun_required: false for TASK-058, true for TASK-060 after CARLA restart
- overall_score: 4.1 / 5.0
- threshold: 4.0
- evidence_quality: pass
- integration_readiness: pass
- traceability: pass
- freshness: pass

## Search Scope

- Ticket: `tickets/TASK-058/ticket.md`
- Code:
  - `src/driverx/simulators/carla_maps.py`
  - `tests/test_carla_maps.py`
- Evidence:
  - `tickets/TASK-058/artifacts/town13-map-install-real-002/carla_maps_install.json`
  - `tickets/TASK-058/artifacts/town13-map-install-real-002/carla_maps_install.md`
  - `tickets/TASK-058/artifacts/town13-map-probe-after-install/carla_map_inventory.json`
  - `tickets/TASK-058/artifacts/town13-map-probe-after-install-long/carla_map_inventory.json`
  - `tickets/TASK-058/artifacts/town13-map-probe-no-load-after-timeout/carla_map_inventory.json`
- Docs:
  - `blockers.md`
  - `docs/progress.md`
  - `docs/HISTORY.md`

## Rubrics Used

### Code Quality: 4.1 / 5.0

- pass: true
- dimension_scores:
  - modularity-reusability: 4.1
  - bloatability: 4.0
  - readability: 4.0
  - boundary-clarity: 4.2
  - error-handling: 4.1
  - maintainability: 4.1

The installer/probe path remains localized to CARLA maps utilities. The probe
now handles the observed CARLA behavior where `load_world` times out after the
server has already switched maps, which keeps the report closer to real runtime
state.

### Evidence Quality: 4.1 / 5.0

- pass: true
- dimension_scores:
  - sufficiency: 4.1
  - reproducibility: 4.0
  - traceability: 4.2
  - consistency: 4.1
  - inspectability: 4.1
  - autonomy-readiness: 4.0

The install report proves the official package path, CARLA root, package size,
extraction count, and Town13 disk markers. The probes prove `Town13` appears in
`available_maps` and that the live server reached `Carla/Maps/Town13/Town13`
before becoming unresponsive.

### Integration Readiness: 4.0 / 5.0

- pass: true for TASK-058
- dimension_scores:
  - integration-safety: 4.0
  - contract-correctness: 4.1
  - dependency-readiness: 4.0
  - coupling-risk: 4.0
  - merge-readiness: 4.0

The original blocker, "Town13 not installed," is resolved. TASK-060 still
requires the human-visible CARLA app to be quit/relaunched and re-probed because
the current process timed out after the first Town13 load.

## Finding Log

- No blocking findings for TASK-058.
- Medium severity follow-up: TASK-060 must not start until a fresh no-load probe
  responds after CARLA is relaunched.

## Next Action

Ask the operator to quit and relaunch local `CARLA.app`, wait for it to finish
loading, then run `probe-carla-maps --no-load` before starting the stock
Fail2Drive Town13 route.
