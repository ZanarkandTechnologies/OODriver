# 0xDriver Video Script

## 0:00-0:25

- visual: Scenario forge and CARLA OOD scene
- narration: 0xDriver generates long-tail driving cases, then runs them in CARLA. The current proof centers on generated-base-animals-0076-regional-driving-behavior-000.

## 0:25-0:55

- visual: Reasoning pack with Alpamayo CoC and memory
- narration: A frozen Alpamayo 1.5 policy is evaluated open-loop with and without retrieved safety memory; no generated-case fine-tuning is used.

## 0:55-1:25

- visual: Cached replay or campaign risk table
- narration: The control layer can replay cached VLA trajectory intent conservatively; campaign status is passed.

## 1:25-1:55

- visual: Latency and hardware evidence
- narration: Alpamayo batch status is passed; RTX 6000 Ada is enough for single-sample open-loop inference.

## 1:55-2:20

- visual: Claim boundaries and next steps
- narration: The current submission claims randomized OOD generation and open-loop reasoning evidence, not production autonomous driving.

## 2:20-2:35

- visual: Blocker table
- narration: Main remaining blocker: 2026-05-06 11:48 +0800 | fail2drive,carla,town13,score,capture | TASK-060 long-score attempt `town13-long-score-attempt-001` started the stock `Generalization_PedestriansOnRoad_1088` route and reached game time `0.600s` at about `0.142x`, then stopped making observable progress. A concurrent route-aligned Alpamayo capture attempt with a 60s CARLA timeout also failed waiting for the simulator. I terminated the route evaluator cleanly to avoid burning the full 1200s timeout on a stalled local Mac/Wine simulation. Evidence: `tickets/TASK-060/artifacts/town13-long-score-attempt-001-evidence/run_evidence.md` and `tickets/TASK-069/artifacts/town13-live-attach-attempt-004/carla_alpamayo_capture.json`. Next unblock path: use a graphics-capable Linux NVIDIA CARLA host for Fail2Drive scoring/capture, or rerun locally only after confirming CARLA can sustain route ticks and serve a second Python client during synchronous mode.
