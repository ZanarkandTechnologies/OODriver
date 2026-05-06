# TASK-100 QA Evidence

## Commands

- `PYTHONPATH=src python3 -m driverx run-alpamayo-live --package tickets/TASK-097/artifacts/task99-hero-alpamayo-package/alpamayo_carla_input_package.json --prediction-json tickets/TASK-100/artifacts/hero-alpamayo-live/alpamayo_live_prediction.json --output-root tickets/TASK-100/artifacts --run-id task100-hero-alpamayo-policy`
- `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_live tests.test_alpamayo_ood_evaluation tests.test_submission_scenario_browser`
- `bash scripts/pre_push_check.sh`

## Results

- Live prediction conversion: passed.
- Focused tests: `15` tests passed.
- Full local gate: `358` tests passed, `2` skipped.
- Lint/syntax: passed through `scripts/pre_push_check.sh`.
- Typecheck: not configured in `scripts/pre_push_check.sh`.
- Build: not configured in `scripts/pre_push_check.sh`.

## Acceptance Criteria

- AC-1: PASS. Compact remote artifacts were pulled into
  `tickets/TASK-100/artifacts/hero-alpamayo-live/`.
- AC-2: PASS. Live inference completion, shapes, CoC, latency, and VRAM are in
  `alpamayo_live_prediction.json` and `alpamayo_live_summary.md`.
- AC-3: PASS. `run-alpamayo-live` converted the payload into
  `task100-hero-alpamayo-policy/alpamayo_policy_decision.json`.
- AC-4: PASS. Ticket and summary explicitly label this as open-loop
  captured-frame VLA evaluation, not closed-loop CARLA driving.
- AC-5: PASS. Focused tests and full local gate passed.

## Claim Boundary

This ticket proves that Alpamayo 1.5 runs on the RunPod Kasm lane and can react
to a DriverX CARLA OOD package. It does not prove that Alpamayo can drive CARLA
closed-loop in real time, and it does not claim the current video is final
high-fidelity simulator evidence.
