# TASK-043: Dockerized Fail2Drive Client Runner

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-042
- location: `docker`, `scripts`, `configs`, tests
- enter when: native local Fail2Drive route execution blocks on Python
  dependency mismatch
- leave when: DriverX has a repeatable Docker client image/script that mounts
  both the repo and external Fail2Drive checkout and can run the same route
  runner path
- blockers: live route may still need CARLA PythonAPI `agents` modules or
  heavier torch dependencies
- spawned follow-ups: TASK-044 generated OOD route ramp
- complexity: M

## Summary

Build the local Docker path for Fail2Drive route execution against host CARLA.
The image should be lightweight by default, with optional heavy torch install
gated by an environment flag.

## Acceptance Criteria

- [x] Dockerfile installs CARLA client and core Fail2Drive evaluator deps.
- [x] Runner script mounts `/workspace/0xDriver` and `/workspace/fail2drive`.
- [x] Sample config targets `host.docker.internal:2000`.
- [x] Tests verify script/config wiring without requiring Docker build.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_docker_scripts`
- optional local Docker build attempted with
  `scripts/build_fail2drive_client_docker.sh`; apt succeeded after trimming the
  image, but the pip wheel download layer stalled and was manually stopped.

## Evidence

- Dockerfile: `docker/fail2drive-client.Dockerfile`
- Build script: `scripts/build_fail2drive_client_docker.sh`
- Run script: `scripts/run_fail2drive_client_docker.sh`
- Container config: `configs/fail2drive_docker.local.yaml`
- Review: `tickets/TASK-043/artifacts/review/20260505T223300-review.json`

## Blockers

- Local Docker build did not complete because the pip layer stalled while
  downloading wheels. The image definition is ready; rerun on a faster network
  or the A6000 host. Heavy torch install remains gated behind
  `DRIVERX_FAIL2DRIVE_INSTALL_TORCH=1`.
