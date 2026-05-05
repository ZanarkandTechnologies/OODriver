# TASK-030: Extract SimLingo CLI Registration

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-029
- location: `src/driverx/cli.py`, `src/driverx/simulators`, tests
- enter when: `src/driverx/cli.py` is at the repo size ceiling and future
  commands would fail the pre-push gate
- leave when: SimLingo/sidecar command handlers and parser registration live in
  a simulator-owned CLI module and existing commands still work
- blockers: none for local implementation
- spawned follow-ups: none
- complexity: S

## Summary

Refactor SimLingo command handlers out of the central CLI file so future
commands can be added without tripping the 1000-line source-size gate. This is
a behavior-preserving modularity pass.

## Acceptance Criteria

- [x] AC-1: Move SimLingo readiness, run planning, result ingestion, evidence,
  sidecar planning, and sidecar run handlers into a simulator-owned CLI module.
- [x] AC-2: `src/driverx/cli.py` drops safely below the 1000-line gate.
- [x] AC-3: Existing SimLingo CLI tests still pass.
- [x] AC-4: Full pre-push gate passes.

## Evidence

- Extracted module: `src/driverx/simulators/simlingo_cli.py`
- Central CLI line count: `823` lines after extraction.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_cli_simlingo_result tests.test_simlingo_evidence tests.test_cli_simlingo_sidecar tests.test_cli_simlingo_sidecar_runner`
  passed with `9` tests.
- Help smoke:
  `PYTHONPATH=src python3 -m driverx --help | rg "simlingo|assess-gpu-host|sidecar"`
  still lists SimLingo, sidecar, and GPU host commands.
- Local gate: `bash scripts/pre_push_check.sh` passed with `166` tests.
- Review:
  `tickets/TASK-030/artifacts/review/2026-05-05_174000_review.md`
  passed with overall score `4.0`.

## Blockers

- None currently.
