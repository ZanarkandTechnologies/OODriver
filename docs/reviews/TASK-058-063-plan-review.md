# TASK-058 Through TASK-063 Plan Review

- reviewed_at: `2026-05-06 03:02 +0800`
- scope: next ticket batch after PhysicalAI approval and Town13 unblock request
- work_type: implementation-plan, integration-readiness, evidence-quality
- verdict: pass
- overall_score: 4.1 / 5.0

## Search Scope

- Product/docs: `docs/prd.md`, `docs/specs/minimal-shot-vla-roadmap.md`,
  `ARCHITECTURE.md`, `README.md`, `docs/progress.md`, `blockers.md`
- Active plans:
  - `tickets/TASK-058/ticket.md`
  - `tickets/TASK-059/ticket.md`
  - `tickets/TASK-060/ticket.md`
  - `tickets/TASK-061/ticket.md`
  - `tickets/TASK-062/ticket.md`
  - `tickets/TASK-063/ticket.md`
- Existing seams:
  - `scripts/run_remote_alpamayo_shape_probe.sh`
  - `scripts/run_carla_client_docker.sh`
  - `src/driverx/simulators/fail2drive_video.py`
  - `src/driverx/simulators/fail2drive_route_runner.py`
  - `src/driverx/simulators/carla_alpamayo_capture.py`
  - `src/driverx/policies/alpamayo_live.py`
  - `src/driverx/pipeline/route_evidence.py`
- External grounding:
  - CARLA 0.9.16 docs/release assets list `AdditionalMaps_0.9.16` packages for
    Ubuntu and Windows.

## Rubrics

### Implementation Plan

- score: 4.1 / 5.0
- threshold: 4.0
- pass: yes

The batch is sequenced around real blockers instead of arbitrary ticket slices:
Town13 install/probe first, dataset-backed Alpamayo proof first, then route
evidence, route-aligned Alpamayo comparison, cached control replay, and final
submission refresh. Each ticket names touched files, signatures, data shapes,
typed flow, execution order, blast radius, and verification.

### Integration Readiness

- score: 4.0 / 5.0
- threshold: 4.0
- pass: yes

Plans reuse existing local seams instead of inventing new runtime ownership:
Docker CARLA bridge, Fail2Drive route planner/runner, Alpamayo shape probe, live
adapter, and route evidence. Human gates are explicit. Main caveat: TASK-058 may
need local CARLA root discovery and the Kegworks wrapper layout may not match
plain Windows CARLA installs.

### Evidence Quality

- score: 4.0 / 5.0
- threshold: 4.0
- pass: yes

Each ticket states concrete proof artifacts and commands. The evidence chain is
auditable from setup proof to final submission refresh. The plans preserve claim
boundaries: open-loop Alpamayo, stock route evidence, and cached replay are
separate labels.

## Findings

- None blocking.

## Next Action

Move TASK-058 and TASK-059 to build when execution starts. They are independent:
Town13 install/probe can run locally while the PhysicalAI-backed Alpamayo probe
runs on the kept-alive RunPod host.
