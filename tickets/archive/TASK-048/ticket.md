# TASK-048: Alpamayo Remote Release Bootstrap Script

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-044, TASK-045
- location: `scripts`, tests
- enter when: Alpamayo repo contract exists but remote host access is unstable
- leave when: DriverX has a secret-safe remote bootstrap script that can clone
  the Alpamayo release, install uv, create a Python 3.12 env, and choose
  flash-attn or SDPA dependency sync
- blockers: live execution waits for reachable SSH to the rented GPU host
- spawned follow-ups: TASK-039 Alpamayo CARLA adapter
- complexity: S

## Summary

Prepare the remote GPU setup path without relying on interactive terminal
state. The script should support custom SSH options, local `.env` loading,
safe Hugging Face token handoff, and an SDPA fallback for hosts without `nvcc`
or flash-attn build readiness.

## Acceptance Criteria

- [x] Add a remote Alpamayo bootstrap shell script.
- [x] Support `GPU_SSH_OPTS`, `DRIVERX_ENV_FILE`, `ALPAMAYO_REMOTE_ROOT`,
  `ALPAMAYO_SYNC_MODE`, and optional test inference.
- [x] Avoid printing secrets or pulling model weights by default.
- [x] Tests inspect safety gates and `bash -n` validates syntax.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_remote_bootstrap_script`
- `GPU_SSH_OPTS='-p 36723 -i ~/.ssh/id_ed25519_prime_intellect' DRIVERX_ENV_FILE=.env ALPAMAYO_SYNC_MODE=sdpa ALPAMAYO_RUN_TEST=0 scripts/bootstrap_remote_alpamayo_release.sh root@195.26.233.80`
- `bash scripts/pre_push_check.sh`

## Evidence

- Script: `scripts/bootstrap_remote_alpamayo_release.sh`
- Tests: `tests/test_alpamayo_remote_bootstrap_script.py`
- A6000 bootstrap attempt log:
  `tickets/TASK-048/artifacts/a6000-bootstrap/run.log`
- A6000 bootstrap attempt exit code:
  `tickets/TASK-048/artifacts/a6000-bootstrap/exit_code.txt`
- Review: `tickets/archive/TASK-048/artifacts/review/20260505T230300-review.json`

## Result

The script is ready to run once SSH is reachable. It clones
`https://github.com/NVlabs/alpamayo1.5.git`, installs `uv` if needed, creates
the Python 3.12 virtual environment, syncs in SDPA mode by default, requires
`nvcc` only for flash-attn mode, writes a compact remote environment/GPU
summary, and runs `test_inference.py` only when `ALPAMAYO_RUN_TEST=1`.

## Blockers

- Live bootstrap could not begin because the supplied A6000 endpoint still
  refuses SSH on port `36723`.
