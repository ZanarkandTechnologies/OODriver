# TASK-039: Alpamayo CARLA Adapter

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-038, TASK-053, TASK-054
- location: `src/driverx/policies`, `src/driverx/simulators`, tests
- enter when: Alpamayo offline probe establishes load and trajectory shape
- leave when: CARLA camera/ego/nav observations can be transformed into
  Alpamayo inputs and its trajectory can be converted into open-loop CARLA
  policy intent
- blockers: none for planning; TASK-053 provides live shape evidence from
  synthetic Alpamayo-shaped tensors, while real PhysicalAI sample data remains
  gated
- spawned follow-ups: TASK-040 submission demo pack, TASK-053 live Alpamayo
  inference shape probe, TASK-054 Alpamayo tensor materializer
- complexity: L

## Summary

Build the Alpamayo adapter against the live input/output shapes observed in
TASK-053. Keep v1 open-loop: return trajectory intent and evidence artifacts,
not direct CARLA steering.

## Acceptance Criteria

- [x] Observation transform uses documented/probed camera, egomotion, and route
  fields.
- [x] Trajectory output converts to control intent with validation.
- [x] Adapter has offline replay tests before live CARLA.

## Verification

- Focused local tests:
  `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_live tests.test_alpamayo_materializer tests.test_alpamayo_offline tests.test_alpamayo_trajectory tests.test_alpamayo_remote_bootstrap_script`
- Full gate: `bash scripts/pre_push_check.sh`
- Live RunPod proof:
  `tickets/archive/TASK-039/artifacts/live-capture-summary/alpamayo_policy_report.md`

## Blockers

- TASK-053 observed live Alpamayo inference shapes on the RunPod RTX 6000 Ada
  pod with `ALPAMAYO_ATTN_IMPLEMENTATION=eager`:
  `pred_xyz=[1,1,1,64,3]`, `pred_rot=[1,1,1,64,3,3]`,
  `extra.cot=[1,1,1]`, `extra.meta_action=[1,1,1]`, and
  `extra.answer=[1,1,1]`.
- The upstream PhysicalAI dataset remains gated, so adapter implementation
  should use DriverX/CARLA tensor materialization rather than depend on the
  upstream sample loader.

## Build Notes

- Added `AlpamayoLiveAdapter` and `run-alpamayo-live`, keeping TASK-039
  explicitly open-loop rather than sending steering commands to CARLA.
- Added `scripts/run_remote_alpamayo_carla_inference.sh`, which stages a local
  CARLA capture package, loads Alpamayo on RunPod, writes compact prediction
  artifacts, and runs local DriverX conversion after pullback.
- Added `--alpamayo-package` and `--alpamayo-prediction-json` to
  `run-policy-fixture` so `--policy alpamayo-live` can be exercised from the
  standard policy path.
- Live RunPod inference completed on the TASK-051 CARLA capture with
  `pred_xyz=[1,1,1,64,3]`, `pred_rot=[1,1,1,64,3,3]`,
  `extra.cot=[1,1,1]`, `99795.97ms` latency, and `23235.75MB` peak VRAM.
- The resulting policy decision is labeled
  `open_loop_policy_evaluation=true` and `closed_loop_control=false`.

## QA Reconciliation

- Observation transform: PASS
- Trajectory output conversion: PASS
- Offline/fake replay before live CARLA: PASS
- Live Alpamayo smoke: PASS

## Artifact Links

- Fake replay proof:
  `tickets/archive/TASK-039/artifacts/fake-live-policy/alpamayo_policy_report.md`
- Live prediction payload:
  `tickets/archive/TASK-039/artifacts/live-capture/alpamayo_live_prediction.json`
- Live policy decision:
  `tickets/archive/TASK-039/artifacts/live-capture-summary/alpamayo_policy_report.md`
- Focused tests: `tickets/archive/TASK-039/artifacts/focused_tests.log`
- Pre-push gate: `tickets/archive/TASK-039/artifacts/pre_push_check.log`
- QA report: `tickets/archive/TASK-039/artifacts/qa_report.md`
- Review: `tickets/archive/TASK-039/artifacts/review/20260506T011901-review.md`

## User Evidence

- Supporting evidence:
  `tickets/archive/TASK-039/artifacts/live-capture-summary/alpamayo_policy_report.md`
- QA report: `tickets/archive/TASK-039/artifacts/qa_report.md`
- Final verdict: Alpamayo now runs as a live open-loop CARLA capture policy
  path with measured latency/VRAM and converted trajectory intent; closed-loop
  CARLA actuation remains intentionally out of scope for this ticket.
