# TASK-008 Review: Live CARLA Probe And Docker Bridge

Reviewed: 2026-05-04 18:58 +0800

## Scope

- Changed files: CARLA probe module, simulator exports, CLI, Docker helper,
  tests, docs, roadmap/tickets.
- Rubrics: code quality, integration readiness, evidence quality.
- Context checked: `docs/prd.md`, `docs/specs/minimal-shot-vla-roadmap.md`,
  `docs/MEMORY.md`, `tickets/archive/TASK-008/ticket.md`, TASK-007 simulator adapter
  seams.

## Verdict

Overall score: **4.4 / 5.0**

Verdict: **pass**

TASK-008 cleanly upgrades the CARLA boundary from TCP-only smoke to Python API
probing while preserving dependency-light local tests. The Docker helper keeps
CARLA's Linux client wheel out of the Mac Python environment, and the probe
returns actionable JSON when the package or server is unavailable.

## Findings

No blocking findings.

## Notes

- Live evidence reached `host.docker.internal:2000` from Docker and reported
  `Carla/Maps/Town10HD_Opt`, actor count `23`, and server/client version
  `0.9.16`.
- The probe is intentionally read-only. Actor spawning belongs in TASK-009.
- The Docker helper installs `carla==0.9.16` in a disposable container; a later
  optimization can build a cached local image if repeated runs become slow.

## Evidence Reviewed

- `bash scripts/pre_push_check.sh`: PASS, 61 tests.
- `PYTHONPATH=src python3 -m driverx smoke-carla --config configs/carla_local.sample.yaml`: live TCP reachable.
- `bash scripts/run_carla_client_docker.sh python -m driverx probe-carla --host host.docker.internal --port 2000 --timeout-s 10 --run-id task8-carla-probe`: PASS.
- `artifacts/runs/task8-carla-probe/carla_probe.json`.

## Next Action

Proceed to TASK-009: ego spawn, camera capture, entity track logging, and
cleanup proof.
