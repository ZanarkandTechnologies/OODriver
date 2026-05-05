# TASK-028: GPU Host Suitability Report

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-020, TASK-026, TASK-027
- location: `src/driverx/simulators`, CLI, tests,
  `tickets/TASK-028/artifacts`
- enter when: TASK-020 has precise CUDA/CARLA runtime evidence but the next GPU
  host choice still depends on scattered notes
- leave when: one local command turns available remote evidence into a compact
  ready/blocked host suitability JSON/Markdown report
- blockers: none for local implementation
- spawned follow-ups: none
- complexity: S

## Summary

Add a local GPU host suitability assessor for SimLingo/CARLA runs. The assessor
should combine CUDA model-compatibility evidence, CARLA graphics/Vulkan
diagnostics, remote evidence state, and an optional GPU snapshot into a single
recommendation before we spend more time or money on a host.

## Acceptance Criteria

- [x] AC-1: Assess CUDA/model readiness from `torch_cuda_compatibility.json`.
- [x] AC-2: Assess CARLA graphics readiness from diagnostics or remote evidence
  blockers.
- [x] AC-3: Write JSON and Markdown reports with overall state, blockers,
  warnings, checks, and a next-host recommendation.
- [x] AC-4: Add CLI entrypoint `assess-gpu-host`.
- [x] AC-5: Tests cover an H100 CARLA/Vulkan blocker and a Blackwell
  torch-architecture blocker without requiring a GPU.
- [x] AC-6: Generate a TASK-020-based suitability report for the current H100
  evidence.

## Evidence

- Host suitability JSON:
  `tickets/TASK-028/artifacts/h100-host-suitability/gpu_host_suitability.json`
- Host suitability Markdown:
  `tickets/TASK-028/artifacts/h100-host-suitability/gpu_host_suitability.md`
- Current verdict: `overall_state=blocked`; `cuda_model=ready` for H100
  `sm_90`; `carla_graphics=blocked` from the Vulkan/port evidence; storage is
  a warning because the root disk is `20GB`.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_gpu_host_suitability` passed
  with `4` tests.
- Local gate: `bash scripts/pre_push_check.sh` passed with `165` tests.
- Review:
  `tickets/TASK-028/artifacts/review/2026-05-05_173600_review.md`
  passed with overall score `4.0`.

## Blockers

- None currently.
