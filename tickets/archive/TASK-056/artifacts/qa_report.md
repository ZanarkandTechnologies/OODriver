# TASK-056 QA Report

## Verdict
PASS

## Evidence
- Focused tests: `tickets/TASK-056/artifacts/focused_tests.log` (`15` tests passed).
- Full local gate: `tickets/TASK-056/artifacts/pre_push_check.log` (`256` tests passed; lint/compile passed; no type/build commands configured).
- Live baseline decision: `tickets/TASK-039/artifacts/live-capture-summary/alpamayo_policy_decision.json`.
- Live memory decision: `tickets/TASK-056/artifacts/live-memory-run-summary/alpamayo_policy_decision.json`.
- Comparison report: `tickets/TASK-056/artifacts/town10-memory-comparison/alpamayo_ood_comparison.md`.
- Comparison JSON: `tickets/TASK-056/artifacts/town10-memory-comparison/alpamayo_ood_comparison.json`.

## Acceptance Reconciliation
- AC-1 PASS: `build-alpamayo-ood-comparison` wrote JSON and Markdown artifacts.
- AC-2 PASS: report includes memory ids, CoC snippets, latency, VRAM, trajectory delta, route video flag, and closed-loop flags.
- AC-3 PASS: unit tests cover missing memory decision behavior and package creation.
- AC-4 PASS: live memory Alpamayo decision was incorporated.
- AC-5 PASS: comparison is labeled `open_loop_policy_evaluation=true` and `closed_loop_control=false`.

## Live Result
- Baseline CoC: `Accelerate to proceed through the intersection since the traffic light turns green`.
- Memory CoC: `Keep lane since the intersection is clear and no lead vehicle is present`.
- Trajectory delta: mean L2 `0.9666m`, final L2 `2.8886m`.
- Latency delta: `611.1ms` additional latency for the memory run.

## Limitations
- This is open-loop policy evaluation from a saved CARLA capture. Alpamayo did not steer the CARLA route.
- TASK-055 route video is a Town10 fallback smoke video, not the full stock Fail2Drive Town13 OOD split.
