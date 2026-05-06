# TASK-081: Same-Capture Alpamayo Memory Comparison

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-080, RunPod Alpamayo lane
- location: `src/driverx/policies`, `src/driverx/pipeline`, `tickets/TASK-081/artifacts`
- enter when: TASK-080 has a torch-ready package or a precise package blocker
- leave when: baseline and memory-augmented Alpamayo decisions are compared for the same generated scene, or the remote run blocker is precise
- blockers: none for same-capture open-loop comparison
- spawned follow-ups: TASK-082
- complexity: L

### Description
Run or prepare the same-capture Alpamayo no-memory versus memory comparison for
the generated OOD scene. This is the main minimal-shot reasoning evidence.

### Goal
Produce `alpamayo_ood_comparison.json/md` with CoC snippets, trajectory deltas,
memory ids, latency/VRAM, and explicit open-loop labels.

### Acceptance Criteria
- [x] AC-1: Same-capture package is used when torch-ready.
- [x] AC-2: If remote inference cannot run, the report emits rerunnable commands and setup blockers.
- [x] AC-3: Comparison distinguishes cached/linked evidence from same-capture evidence.
- [x] AC-4: No closed-loop control claims are made.

### Agent Contract
- Open: `src/driverx/policies/alpamayo_live.py`, `src/driverx/pipeline/alpamayo_ood_evaluation.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_ood_evaluation tests.test_alpamayo_live`
- Stabilize: use cached decisions only as explicitly labeled fallback.
- Inspect: `tickets/TASK-080/artifacts`, `scripts/run_remote_alpamayo_carla_inference.sh`
- Expected artifacts: comparison JSON/MD and memory-augmented package/report.

### Evidence
- Created 2026-05-06 for the live CARLA retry batch.
- Baseline Alpamayo remote inference completed on RunPod RTX 6000 Ada with
  eager attention. Summary:
  `tickets/TASK-081/artifacts/task81-live-same-scene-baseline-summary/alpamayo_policy_report.md`.
- Memory-augmented remote inference completed on the same capture. Summary:
  `tickets/TASK-081/artifacts/task81-live-same-scene-memory-summary/alpamayo_policy_report.md`.
- Same-capture comparison:
  `tickets/TASK-081/artifacts/task81-live-same-scene-comparison/alpamayo_ood_comparison.md`.
  It records open-loop labels, CoC snippets, latency/VRAM, memory ids, and a
  2.6886m final trajectory delta between baseline and memory decisions.

### Blockers
- None for this ticket. Remaining project blocker is closed-loop route control,
  not Alpamayo same-capture reasoning.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
