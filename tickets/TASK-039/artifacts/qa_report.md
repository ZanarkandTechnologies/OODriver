# TASK-039 QA Report

- verdict: `pass`
- focused tests: `tickets/TASK-039/artifacts/focused_tests.log`
- pre-push gate: `tickets/TASK-039/artifacts/pre_push_check.log`
- fake open-loop proof:
  `tickets/TASK-039/artifacts/fake-live-policy/alpamayo_policy_report.md`
- live RunPod proof:
  `tickets/TASK-039/artifacts/live-capture-summary/alpamayo_policy_report.md`

## Acceptance Criteria

- Observation transform: PASS. TASK-054 materialization is reused to validate
  CARLA camera windows, camera ids, PNG dimensions, ego history, and rotations.
  Live RunPod input shapes were `image_frames=[3,4,3,90,160]`,
  `camera_indices=[3]`, `ego_history_xyz=[1,1,16,3]`, and
  `ego_history_rot=[1,1,16,3,3]`.
- Trajectory conversion: PASS. Live Alpamayo output
  `pred_xyz=[1,1,1,64,3]` converts to a DriverX 20-point open-loop trajectory.
- Adapter tests: PASS. Unit tests cover setup blockers, adapter metadata,
  fake prediction replay, CLI paths, invalid package handling, and remote
  script syntax/secret cleanup.

## Live Evidence

- Remote host: RunPod RTX 6000 Ada through
  `root@195.26.233.80 -p 55050 -i ~/.ssh/id_ed25519_runpod`
- Model: `nvidia/Alpamayo-1.5-10B`
- Attention: `eager`
- Inference state: `completed`
- Latency: `99795.97ms`
- Peak VRAM: `23235.75MB`
- CoC excerpt:
  `Accelerate to proceed through the intersection since the traffic light turns green`
- Closed-loop control: `false`

## Commands

```bash
PYTHONPATH=src python3 -m unittest tests.test_alpamayo_live tests.test_alpamayo_materializer tests.test_alpamayo_offline tests.test_alpamayo_trajectory tests.test_alpamayo_remote_bootstrap_script
bash scripts/pre_push_check.sh
RUN_ID=task039-live-capture ALPAMAYO_ATTN_IMPLEMENTATION=eager GPU_SSH_OPTS='-p 55050 -i ~/.ssh/id_ed25519_runpod' scripts/run_remote_alpamayo_carla_inference.sh artifacts/runs/task51-live-alpamayo-capture/alpamayo_carla_input_package.json root@195.26.233.80 tickets/TASK-039/artifacts/live-capture
```
