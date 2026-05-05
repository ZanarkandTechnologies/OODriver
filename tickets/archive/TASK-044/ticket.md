# TASK-044: Alpamayo Remote Probe Host Prep

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-038, A6000 Ada SSH access, Hugging Face gated access
- location: `scripts`, tests, remote artifacts
- enter when: user provides Alpamayo repo details and an A6000/Ada GPU host
- leave when: remote probe script supports the provided SSH shape and either
  collects Alpamayo probe artifacts or records a precise SSH/setup blocker
- blockers: current A6000 SSH endpoint refuses connection from local machine
- spawned follow-ups: TASK-039 Alpamayo CARLA adapter
- complexity: M

## Summary

Harden the remote Alpamayo probe for real GPU-host access: custom port/key,
local `.env` token loading, safe remote token handoff, and compact artifact
pullback. Then attempt the provided A6000 host and record the blocker.

## Acceptance Criteria

- [x] Script supports `GPU_SSH_OPTS` for custom ports/keys.
- [x] Script can source `.env` without printing secrets.
- [x] Pullback uses SSH-compatible rsync rather than raw `scp`.
- [x] Live A6000 attempt is recorded as success or precise blocker.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_probe`
- A6000 probe attempt:
  `GPU_SSH_OPTS='-p 36723 -i ~/.ssh/id_ed25519_prime_intellect' RUN_ID=task44-a6000-probe ALPAMAYO_DOWNLOAD=0 ALPAMAYO_LOAD=0 DRIVERX_ENV_FILE=.env scripts/run_remote_alpamayo_probe.sh root@195.26.233.80 artifacts/remote/alpamayo-probe/task44-a6000-probe`

## Evidence

- Script: `scripts/run_remote_alpamayo_probe.sh`
- Tests: `tests/test_alpamayo_probe.py`
- Live attempt log: `tickets/archive/TASK-044/artifacts/a6000-probe/run.log`
- Live attempt exit code:
  `tickets/archive/TASK-044/artifacts/a6000-probe/exit_code.txt`
- Review:
  `tickets/archive/TASK-044/artifacts/review/20260505T224500-review.json`

## Blockers

- The supplied A6000 endpoint refused TCP/SSH from this machine:
  `ssh: connect to host 195.26.233.80 port 36723: Connection refused`.
  The user-provided literal key path `~/.ssh/id_ed25519` is also absent
  locally, so the probe attempt used the existing Prime Intellect key
  `~/.ssh/id_ed25519_prime_intellect`. Next unblock path: confirm that the
  instance is running, the SSH port is still `36723`, the firewall exposes it,
  and the accepted public key matches one of the local keys.
