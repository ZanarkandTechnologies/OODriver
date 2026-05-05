# TASK-031: Submission Dossier Builder

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-027, TASK-028, TASK-029, TASK-030
- location: `src/driverx/pipeline`, CLI, tests,
  `tickets/TASK-031/artifacts`
- enter when: OOD suite and GPU host evidence exist but the submission story is
  spread across ticket artifacts
- leave when: one command writes a concise Markdown/JSON dossier for the SoTA
  submission narrative and demo planning
- blockers: none for local implementation
- spawned follow-ups: none
- complexity: S

## Summary

Build a lightweight submission dossier generator. It should consume the current
OOD suite report, GPU host suitability report, progress ledger, and blocker
ledger, then emit one auditable Markdown summary of what the system does, what
evidence exists, what is blocked, and what the next demo step should be.

## Acceptance Criteria

- [x] AC-1: Generate `submission_dossier.json` and `submission_dossier.md`.
- [x] AC-2: Include OOD readiness, metric highlights, GPU host verdict,
  blocker summary, and a demo outline.
- [x] AC-3: Add CLI entrypoint `build-submission-dossier`.
- [x] AC-4: Tests cover dossier generation and CLI output without CARLA/GPU.
- [x] AC-5: Generate a current dossier from TASK-027/TASK-029 evidence.

## Evidence

- Current dossier JSON:
  `tickets/TASK-031/artifacts/current-submission-dossier/submission_dossier.json`
- Current dossier Markdown:
  `tickets/TASK-031/artifacts/current-submission-dossier/submission_dossier.md`
- Dossier highlights: generated OOD readiness is present; RAG driving score
  delta is `37.0`; GPU host verdict is `blocked`; demo outline ends with the
  graphics-capable NVIDIA host run.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_submission_dossier` passed
  with `2` tests.
- Local gate: `bash scripts/pre_push_check.sh` passed with `168` tests.
- Review:
  `tickets/TASK-031/artifacts/review/2026-05-05_174900_review.md`
  passed with overall score `4.0`.

## Blockers

- None currently.
