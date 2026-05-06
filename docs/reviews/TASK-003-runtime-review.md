# TASK-003 Runtime Review

Date: 2026-05-02 19:32 +0800

## Verdict

PASS. Overall score: 4.5 / 5.0.

## Scope

- `tickets/archive/TASK-003/ticket.md`
- `README.md`
- `pyproject.toml`
- `docker/waymo.Dockerfile`
- `.dockerignore`
- `requirements/waymo-linux.txt`
- `src/driverx/waymo_runtime.py`
- `src/driverx/datasets/waymo_e2e.py`
- `src/driverx/submission/waymo_packager.py`
- `tests/test_waymo_loader.py`
- `tests/test_submission_packager.py`
- `qa/reports/TASK-002-final-qa.md`

## Findings

No blocking findings.

The stale `.[waymo]` install path is gone from live guidance. The only remaining
occurrence is explanatory ticket text documenting why that path was removed.
Linux native guidance points to `requirements/waymo-linux.txt`, and the Docker
runtime is the primary Apple Silicon path.

## Evidence

- `bash scripts/pre_push_check.sh`: PASS, 28 tests.
- `scripts/build_waymo_docker.sh`: PASS, exported `driverx-waymo:local`.
- Docker import smoke: PASS, `tensorflow=2.13.0`, `waymo_e2e_proto=ok`,
  `driverx=ok`.
- `scripts/run_waymo_docker.sh`: PASS, loaded frame
  `11d68b183960928432c0ab7af24ac86d-058` with three front cameras.
- Docker real-frame baseline: PASS, run `waymo-docker-baseline-003` completed
  with ADE `11.482393`.
- Native dependency guidance: PASS, missing official deps now point to Docker
  and `requirements/waymo-linux.txt`.
- Linux native dry-run: PASS, `python -m pip install --dry-run -r
  requirements/waymo-linux.txt` resolves `jaxlib==0.4.13`.

## Residual Risk

The Waymo dependency image is practically repeatable, with the base image digest
and pip version pinned, but the Waymo package still controls its transitive
dependency set. A future production image can add a fully hashed lockfile after
the GPU/VLA serving surface settles.
