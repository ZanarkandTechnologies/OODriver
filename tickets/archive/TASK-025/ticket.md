# TASK-025: OOD Suite Evidence Report

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-018, TASK-021, TASK-023, TASK-024
- location: `src/driverx/pipeline`, CLI, tests, docs
- enter when: generated scenarios, route packs, overlay plans, and policy/run
  artifacts exist as separate evidence surfaces
- leave when: one command writes a compact JSON/Markdown manifest that explains
  what the generated OOD suite is ready to run, what already ran, and what
  remains blocked
- blockers: none for local report generation
- spawned follow-ups: live H100 suite execution after TASK-020
- complexity: M

## Summary

Create the connective evidence surface for the final submission. The project now
has many useful pieces, but the reviewer/demo path needs one manifest that says:
which scenarios were generated, which Bench2Drive route pack they became, which
overlay actors will run, what sidecar runner evidence exists, what policy/RAG
comparison says, and what live model blockers remain.

## Acceptance Criteria

- [x] AC-1: Load optional JSON artifacts for scenario summaries, route packs,
  overlay plans, sidecar plans/runs, RAG comparisons, SimLingo results, and the
  blocker ledger.
- [x] AC-2: Write `ood_suite_manifest.json` with normalized component status,
  key metrics, evidence paths, and blockers.
- [x] AC-3: Write `ood_suite_report.md` with readiness summary, component table,
  metric highlights, and open blockers.
- [x] AC-4: Add CLI entrypoint `build-ood-suite-report`.
- [x] AC-5: Add unit and CLI tests with fixture artifacts; no CARLA, SimLingo,
  or GPU required.
- [x] AC-6: Run `bash scripts/pre_push_check.sh`.

## Implementation Plan

1. Add `driverx.pipeline.ood_suite_report`.
2. Keep the builder intentionally artifact-oriented: inputs are paths to
   existing JSON/Markdown artifacts, not live external services.
3. Treat missing optional path inputs as report blockers instead of crashing.
4. Add a CLI command that accepts the known ticket artifact paths and writes a
   run directory under `artifacts/runs` or a ticket QA path.
5. Prove the command with temp fixture artifacts in tests.
6. Update docs and progress after the local gate passes.

## Evidence

- OOD suite manifest:
  `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/ood-suite-report/ood_suite_manifest.json`
- OOD suite report:
  `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/ood-suite-report/ood_suite_report.md`
- RAG comparison input:
  `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/rag-comparison/rag_comparison.json`
- Report proof highlights: `2` generated recipes, `2` Bench2Drive routes, `2`
  companion actors, sidecar sample run success, mock RAG driving score delta
  `37.0`, and prior SimLingo Blackwell CUDA blocker preserved.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_ood_suite_report tests.test_cli_ood_suite_report`
  passed with `5` tests.
- Local gate: `bash scripts/pre_push_check.sh` passed with `150` tests.
- Post-fix QA result:
  `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/qa/2026-05-05_160200_postfix-verification/result.json`
- Post-fix QA report:
  `tickets/TASK-025/artifacts/qa/2026-05-05T155329+0800/qa/2026-05-05_160200_postfix-verification/report.md`

## Blockers

- No TASK-025 implementation blocker remains. The generated suite evidence
  intentionally preserves downstream live-runtime blockers from its inputs:
  local sidecar plan readiness still points at Darwin-local missing runtime
  paths, and the prior SimLingo result still records the RTX PRO 6000
  Blackwell CUDA `sm_120` blocker while TASK-020 reruns on H100.
