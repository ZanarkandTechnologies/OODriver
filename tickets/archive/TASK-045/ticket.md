# TASK-045: Alpamayo Release Contract Extractor

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-044, external Alpamayo checkout
- location: `src/driverx/policies`, tests, docs
- enter when: Alpamayo release repo is available locally but live GPU probing is blocked
- leave when: DriverX can produce a structured Alpamayo input/output/runtime
  contract from the release checkout without loading the model
- blockers: live A6000 SSH remains blocked, so this ticket must avoid GPU/model execution
- spawned follow-ups: TASK-039 Alpamayo CARLA adapter
- complexity: M

## Summary

Turn the Alpamayo release notes and source patterns into a repo-owned contract
artifact. The goal is to make the future CARLA adapter concrete while we wait
for GPU access: camera ordering, temporal window, egomotion tensor shapes,
native trajectory shape, downsampling target, hardware modes, and setup
commands.

## Acceptance Criteria

- [x] Add a pure-Python Alpamayo release contract inspector.
- [x] Add CLI output that writes JSON and Markdown artifacts.
- [x] Record default cameras, four-frame windows, 16 history steps, 64 future
  waypoints at 10 Hz, CoC text output, and VQA method support.
- [x] Keep the inspector GPU-free and safe when the external checkout is absent.
- [x] Tests cover contract fields and CLI artifact writing.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_release tests.test_alpamayo_probe`
- `PYTHONPATH=src python3 -m driverx inspect-alpamayo-release --repo ../external/alpamayo1.5 --output-root artifacts/runs --run-id task45-alpamayo-release-contract`
- `bash scripts/pre_push_check.sh`

## Evidence

- Module: `src/driverx/policies/alpamayo_release.py`
- CLI: `src/driverx/policies/alpamayo_release_cli.py`
- Tests: `tests/test_alpamayo_release.py`
- Real local contract JSON:
  `artifacts/runs/task45-alpamayo-release-contract/alpamayo_release_contract.json`
- Real local contract report:
  `artifacts/runs/task45-alpamayo-release-contract/alpamayo_release_contract.md`
- Review: `tickets/archive/TASK-045/artifacts/review/20260505T225100-review.json`

## Result

The local Alpamayo checkout at `../external/alpamayo1.5` produced a contract
with source commit `2eff703`, Python `3.12`, CUDA Toolkit `12.x`, 22GB model
weights, single-sample VRAM `24GB`, multi-sample VRAM `40GB`, CFG multi-sample
VRAM `60GB`, default cameras `[0, 1, 2, 6]`, four frames per camera, 16 ego
history steps, native `64 x 3` trajectory output at 10 Hz, and a DriverX
conversion target of `20 x 2` at 4 Hz over 5 seconds.
