# TASK-015: SimLingo Backend Readiness And Run Planner

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-013, TASK-014
- location: `src/driverx/simulators`, `configs`, tests, docs
- enter when: policy adapter needs a concrete SimLingo/CarLLaVA backend plan
- leave when: SimLingo checkout readiness, runtime requirements, and dry-run
  evaluation command planning are available without requiring GPU execution
- blockers: live run requires Linux NVIDIA, CARLA 0.9.15, checkpoint path, and
  Hugging Face/model access
- spawned follow-ups: live GPU execution; generated route injection
- complexity: M

## Summary

Add a SimLingo/CarLLaVA integration planner around the upstream
`RenzKa/simlingo` checkout. This ticket does not run the model locally; it
turns the external repo into a known backend with setup checks, requirement
reporting, and a reproducible GPU-machine command plan.

## Acceptance Criteria

- [x] SimLingo checkout discovery reports root, commit, required files, CARLA
  version, Python version, CUDA requirement, and Apple Silicon limitations.
- [x] Dry-run command planner emits a single-route Bench2Drive evaluation
  command with environment variables, ports, checkpoint, route, agent file, and
  expected outputs.
- [x] CLI exposes readiness and command planning artifacts.
- [x] Policy stub guidance points to the SimLingo readiness/planning command.
- [x] Tests cover fake checkout readiness, missing file blockers, and command
  planning without importing SimLingo or CARLA.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_simlingo_adapter tests.test_cli`
- `PYTHONPATH=src python3 -m driverx inspect-simlingo --run-id task15-simlingo-readiness`
- `PYTHONPATH=src python3 -m driverx plan-simlingo-run --run-id task15-simlingo-plan`
- `bash scripts/pre_push_check.sh`

## Blockers

- Live SimLingo evaluation needs Linux NVIDIA, CARLA 0.9.15, a SimLingo
  checkpoint such as `pytorch_model.pt`, and working Hugging Face/model assets.

## Evidence

- External checkout: `../external/simlingo` at commit
  `743b243afd6cf5ff51b9fa1f8cac86f22d569684`.
- Local tests: `PYTHONPATH=src python3 -m unittest tests.test_simlingo_adapter tests.test_cli tests.test_policies` passed with 30 tests.
- Readiness command: `PYTHONPATH=src python3 -m driverx inspect-simlingo --run-id task15-simlingo-readiness`.
- Readiness artifact: `artifacts/runs/task15-simlingo-readiness/simlingo_readiness.json`.
- Dry-run plan command: `PYTHONPATH=src python3 -m driverx plan-simlingo-run --run-id task15-simlingo-plan`.
- Dry-run plan artifact: `artifacts/runs/task15-simlingo-plan-001/simlingo_command_plan.json`.
- Live blockers captured by plan:
  - CARLA 0.9.15 root missing locally.
  - SimLingo checkpoint missing locally.
  - Linux NVIDIA CUDA required for live inference.
