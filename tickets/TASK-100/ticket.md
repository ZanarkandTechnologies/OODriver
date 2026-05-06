# TASK-100: Live Alpamayo Reasoning On RunPod Hero Scenario

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-097, TASK-099
- location: `tickets/TASK-100/artifacts`, `src/driverx/policies/alpamayo_live.py`
- enter when: the Kasm RunPod pod has a Hugging Face login and the hero CARLA OOD package from TASK-099 is ready
- leave when: live Alpamayo output is pulled back, converted into a DriverX open-loop policy decision, and the claim boundary is documented
- blockers: none for open-loop live inference; closed-loop CARLA control and high-fidelity dense traffic remain follow-up work
- spawned follow-ups: TASK-101 high-fidelity CARLA scenario runner, TASK-102 AI scenario studio, TASK-103 Alpamayo-to-CARLA replay/control bridge
- complexity: S

### Description

User logged into Hugging Face on the Kasm RunPod pod, unblocking the live
Alpamayo path. This ticket records the first end-to-end proof that the
RunPod-hosted Alpamayo 1.5 model can consume the DriverX hero CARLA OOD package
and return reasoning plus a native trajectory.

### Goal

Convert "Alpamayo is installed" into durable submission evidence: real model
output, shapes, latency, VRAM, chain-of-causation text, and a DriverX
`PolicyDecision` artifact.

### Acceptance Criteria

- [x] AC-1: Pull compact live Alpamayo artifacts from the Kasm pod without
  copying model weights, caches, datasets, or secrets.
- [x] AC-2: Record live inference completion with `pred_xyz` shape,
  `pred_rot` shape, CoC summary, latency, and peak VRAM.
- [x] AC-3: Convert the live prediction JSON into a DriverX
  `alpamayo-live` open-loop policy decision.
- [x] AC-4: Document that this is open-loop VLA evaluation over captured
  frames, not real-time closed-loop CARLA driving.
- [x] AC-5: Run focused QA/review and update final evidence after the next
  local gate.

### Agent Contract

- Open: inspect `tickets/TASK-097/artifacts/task99-hero-alpamayo-package/` and
  `tickets/TASK-100/artifacts/hero-alpamayo-live/`.
- Test hook: `PYTHONPATH=src python3 -m driverx run-alpamayo-live --package
  tickets/TASK-097/artifacts/task99-hero-alpamayo-package/alpamayo_carla_input_package.json
  --prediction-json tickets/TASK-100/artifacts/hero-alpamayo-live/alpamayo_live_prediction.json
  --output-root tickets/TASK-100/artifacts --run-id task100-hero-alpamayo-policy`
- Stabilize: keep the live VLA decision separate from CARLA actuation until a
  replay/control ticket explicitly bridges them.
- Inspect: review `alpamayo_policy_report.md`, `alpamayo_policy_decision.json`,
  and `alpamayo_live_summary.md`.
- Key screens/states: no UI surface changed.
- QA cookbook: run focused Alpamayo adapter tests and the pre-push check before
  closing.
- Taste refs: not applicable.
- Expected artifacts: live prediction JSON, GPU snapshot, policy decision JSON,
  policy report, status summary.
- Delegate with: QA/review only if broader source edits are introduced.

### Evidence Checklist

- [x] Snapshot: `tickets/TASK-100/artifacts/hero-alpamayo-live/alpamayo_live_prediction.json`
- [x] Snapshot: `tickets/TASK-100/artifacts/hero-alpamayo-live/gpu_snapshot.txt`
- [x] Snapshot: `tickets/TASK-100/artifacts/task100-hero-alpamayo-policy/alpamayo_policy_decision.json`
- [x] Report: `tickets/TASK-100/artifacts/task100-hero-alpamayo-policy/alpamayo_policy_report.md`
- [x] Report: `tickets/TASK-100/artifacts/hero-alpamayo-live/alpamayo_live_summary.md`
- [x] QA report linked: `tickets/TASK-100/artifacts/qa/task100-qa.md`
- [x] Review linked: `tickets/TASK-100/artifacts/review/task100-review.json`

### Build Notes

- Live Alpamayo completed on the Kasm RunPod RTX 6000 Ada lane with eager
  attention.
- The run consumed the TASK-099 hero package built from the 60s CARLA OOD
  overlay video.
- The payload produced `pred_xyz` shape `[1, 1, 1, 64, 3]`, `pred_rot` shape
  `[1, 1, 1, 64, 3, 3]`, and `extra.cot` shape `[1, 1, 1]`.
- Measured model latency was `111765.05ms`; peak VRAM was `23559.71MB`.
- CoC summary: `Yield to the cut-in vehicle since it is turning into our lane ahead`.
- Converted DriverX trajectory contains 20 points at the Waymo-style 4Hz target
  horizon, resampled from Alpamayo's native 64-step trajectory.
- The current CARLA video is low-density and scripted. It is useful as a
  deterministic OOD proof surface, but it is not yet the simulator contribution
  the final submission should lead with.

### QA Reconciliation

- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS
- AC-5: PASS
- Screen: NOT PROVABLE
- Evidence item: CAPTURED

### Artifact Links

- Live prediction:
  `tickets/TASK-100/artifacts/hero-alpamayo-live/alpamayo_live_prediction.json`
- GPU snapshot:
  `tickets/TASK-100/artifacts/hero-alpamayo-live/gpu_snapshot.txt`
- Live summary:
  `tickets/TASK-100/artifacts/hero-alpamayo-live/alpamayo_live_summary.md`
- Policy decision:
  `tickets/TASK-100/artifacts/task100-hero-alpamayo-policy/alpamayo_policy_decision.json`
- Policy report:
  `tickets/TASK-100/artifacts/task100-hero-alpamayo-policy/alpamayo_policy_report.md`
- QA report:
  `tickets/TASK-100/artifacts/qa/task100-qa.md`
- Review:
  `tickets/TASK-100/artifacts/review/task100-review.json`

### User Evidence

- Hero proof: Alpamayo 1.5 returned a reasoning trace and native 64-waypoint
  trajectory for the DriverX hero CARLA OOD package.
- Supporting evidence: DriverX converted the prediction into a 20-point
  open-loop `PolicyDecision`.
- QA report: `tickets/TASK-100/artifacts/qa/task100-qa.md`.
- Review: `tickets/TASK-100/artifacts/review/task100-review.json`.
- Final verdict: Alpamayo is running; closed-loop control and higher-fidelity
  scenario generation are the next contribution tickets.

### Required Evidence

- [x] Unit/integration/e2e tests pass (as applicable)
- [ ] Typecheck passes (not configured in `scripts/pre_push_check.sh`)
- [x] Lint passes
