# TASK-064 Through TASK-067 QA Report

- QA date: `2026-05-06 04:08 +0800`
- Scope: local OOD end-to-end runner, visual simulator, behavior pack v2, local
  policy reaction matrix.
- Verdict: `pass`

## Commands

```bash
PYTHONPATH=src python3 -m unittest tests.test_behaviors tests.test_local_ood_sim tests.test_end_to_end_ood_demo tests.test_policies tests.test_rag_comparison
```

Result: `21 tests OK`.

```bash
PYTHONPATH=src python3 -m driverx run-end-to-end-ood-demo \
  --output-root tickets/TASK-064/artifacts \
  --run-id local-ood-demo \
  --behavior-id motorcycle_filtering \
  --mutation regional_driving_behavior
```

Result: wrote `tickets/TASK-064/artifacts/local-ood-demo/end_to_end_demo.md`,
`local-sim/local_ood_sim.html`, `local-sim/local_ood_sim.svg`, and
`policy/policy_reaction_matrix.md`.

```bash
PYTHONPATH=src python3 -m driverx generate-behaviors \
  --output-root tickets/TASK-066/artifacts \
  --run-id behavior-pack-v2
```

Result: wrote an 8-behavior suite report at
`tickets/TASK-066/artifacts/behavior-pack-v2/behavior_report.md`.

```bash
bash scripts/pre_push_check.sh
```

Result: passed with `287 tests OK`. Warnings remain for large but under-limit
tracked files: `src/driverx/cli.py`, `tests/test_cli.py`,
`src/driverx/simulators/carla_maps.py`, and
`src/driverx/pipeline/submission_demo_pack.py`.

## Acceptance Reconciliation

- TASK-064: PASS. One local command produces generated recipe, memory, policy,
  controls, simulator visual, and reports without CARLA/GPU/HF.
- TASK-065: PASS. HTML/SVG simulator evidence includes timeline tracks,
  behavior pressure, closest-approach risk, and policy reaction table.
- TASK-066: PASS. Behavior pack now has 8 deterministic traces with
  coordinate/time assertions for the new regional cases.
- TASK-067: PASS for local scope. The reaction matrix includes mock,
  memory-guided mock, and hybrid rows with latency, target speed, yield, memory
  ids, and safety proxy. Live Alpamayo rows remain optional future input.

## Blockers

- None for TASK-064 through TASK-067.
- CARLA/Town13 live route work remains tracked separately in TASK-068 and
  `blockers.md`.
