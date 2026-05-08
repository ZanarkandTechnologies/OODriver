# TASK-160: Live Kasm Paused Alpamayo Closed-Loop Proof

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-157, TASK-158, TASK-159
- location: `src/driverx/scenarios`, `src/driverx/pipeline`, `artifacts/runs`, `tickets/TASK-160`
- enter when: closed-loop scorer, paused runner, and Alpamayo inference bridge exist locally.
- leave when: one Kasm CARLA run proves Alpamayo outputs are applied to CARLA controls across at least two receding-horizon iterations, with video/tracks/control trace/score/report and honest claim boundaries.
- blockers: none for local implementation; live proof is available on Kasm CARLA when RunPod preserves the logged-in Hugging Face auth home.
- spawned follow-ups: final submission refresh if score passes.
- complexity: L

### Summary

Run the real proof. Use Kasm CARLA in synchronous/fixed-delta mode, capture checkpoint frames, run Alpamayo per checkpoint, apply bounded controls, advance CARLA, and score the trace. This is the first ticket allowed to claim `closed_loop_vla_control=paused_receding_horizon`.

Operator update 2026-05-08: implement the expanded "Live Kasm Paused Closed-Loop Hero Video" plan under this ticket because the visible `TASK-166` id is already occupied by the CARLA capability-suite work. This pass adds the missing `carla-live` runner behavior, `closed-loop-video`, `score-closed-loop-video`, richer trace fields, and RunPod evidence attempts.

### Gap Analysis

- Current state: Kasm CARLA live generated scenario proof exists; Alpamayo open-loop inference exists; local control replay exists.
- Production expectation: live artifact proves model output affected simulator state, and later observations were captured after those actions.
- Missing gaps: no live scored trace, no video overlay of model-action-observation recurrence, no final claim upgrade.
- Recommendation: one short two-to-four step proof over a simple blocker/stop case, not a full complex route.

### Plan

#### Change

Run:

```bash
PYTHONPATH=src /workspace/driverx_py312/bin/python -m oodrive closed-loop-run \
  --db /workspace/0xDriver/artifacts/runs/task141-realistic-ood-generation-v1/scenario_studio_db.json \
  --scenario-id <static-blocker-or-compound-case> \
  --policy alpamayo-remote \
  --backend carla-live \
  --config configs/carla_ood_demo.runpod.high_fidelity.yaml \
  --steps 2 \
  --control-ticks-per-step 4 \
  --run-id task160-live-paused-alpamayo-loop
```

Then:

```bash
PYTHONPATH=src python3 -m oodrive score-closed-loop \
  --trace artifacts/runs/task160-live-paused-alpamayo-loop/closed_loop_trace.json \
  --metric-only
```

#### Why

This is the difference between a good submission and a potentially winning one: the model's trajectory actually changes the next simulator state.

#### Before -> After

- Before: open-loop Alpamayo reasoning overlays and cached replays.
- After: paused receding-horizon Alpamayo/CARLA evidence with measured latency and action recurrence.

#### Touch

- `src/driverx/scenarios/studio_product_closed_loop_runtime.py`
- `src/driverx/pipeline/final_submission_pack.py` or current final pack builder after proof passes
- `docs/HISTORY.md`
- `tickets/TASK-160/ticket.md`
- Generated artifacts under ignored `artifacts/runs/task160-*`

#### Inspect

- `tickets/TASK-141/ticket.md`
- `tickets/TASK-145` through `TASK-148` evidence
- `configs/carla_ood_demo.runpod.high_fidelity.yaml`
- `scripts/setup_runpod_carla_0916_graphics.sh`
- `scripts/sync_runpod_proxy_workspace.sh`
- `docs/MEMORY.md` MEM-0025, MEM-0027, MEM-0038, MEM-0042

#### Signature Delta

No new core signatures beyond TASK-157 through TASK-159 unless runtime exposes a missing field.

#### Type Sketch

```python
LiveClosedLoopArtifactSet = {
  "closed_loop_trace_path": str,
  "score_report_path": str,
  "video_path": str,
  "entity_tracks_path": str,
  "control_trace_paths": list[str],
  "prediction_paths": list[str],
  "claim_boundaries": [
    "closed_loop_vla_control=paused_receding_horizon",
    "real_time_vla_control=false",
    "alpamayo_outputs_applied_to_carla_controls=true"
  ]
}
```

#### Typed Flow Example

Step 0 at frame 40 sees blocker, Alpamayo predicts slow/stop or bypass, controller applies 4 control ticks. Step 1 at frame 44 captures a new ego pose and new camera frame caused by those controls. Score passes only if both steps and action recurrence are present.

#### Execution Steps

1. Sync current repo to Kasm without secrets.
2. Start CARLA 0.9.16 with Kasm graphics path.
3. Run one short static blocker case first.
4. If successful, repeat with compound detour case.
5. Pull only JSON/report/video artifacts locally.
6. Run `oodrive score-closed-loop`.
7. If score passes, refresh final submission pack claims; otherwise record blocker and keep current open-loop claims.

#### Recommendation

Do the simplest blocker/stop case first. A clean stop caused by Alpamayo is more convincing than a shaky swerve.

#### Options Considered

- Compound detour first: impressive but higher failure risk.
- Real-time serving first: not feasible with current latency.
- Two-step paused proof first: best win condition under deadline.

#### Blast Radius

- Mostly generated artifacts and docs.
- Final submission claims change only after score passes.

#### Risks

- Alpamayo latency makes run painfully slow. Mitigation: only two steps, paused loop, explicit latency evidence.
- Controller path deviates off-road. Mitigation: safety clamps and score gate.
- Kasm unavailable. Mitigation: blocker only, no claim upgrade.

### Acceptance Criteria

- [x] AC-1: Live Kasm trace contains at least two Alpamayo inference steps and at least two CARLA post-action observations.
- [x] AC-2: Trace records prediction paths, control traces, planned-vs-actual path, latency/VRAM, and safety clamps.
- [x] AC-3: `score-closed-loop` passes the paused closed-loop threshold.
- [x] AC-4: Video/report show model-action-observation recurrence.
- [x] AC-5: Claim boundaries remain `real_time_vla_control=false`.

### Verification

```bash
PYTHONPATH=src python3 -m oodrive score-closed-loop --trace <trace> --metric-only
PYTHONPATH=src python3 -m unittest tests.test_closed_loop_control_score tests.test_carla_closed_loop_runner tests.test_alpamayo_inference_bridge
bash scripts/pre_push_check.sh
```

### Implementation Evidence - 2026-05-08

- Implemented `carla-live` behavior in `run_paused_closed_loop`: live CARLA connection/map/weather setup, ego/camera/blocker actors, synchronized pre/post checkpoints, Alpamayo package writing, inference bridge execution/cache seam, trajectory-to-control conversion, safety clamps, control application, tracks, RGB frame folders, and richer per-step trace fields.
- Added `oodrive closed-loop-video` and `oodrive score-closed-loop-video`; video scoring now requires live CARLA provenance, at least two recurrences, model-driven `alpamayo-remote` inference/cache hits, duration/frame count, road-alignment proxy, overlay legibility, and explicit claim honesty.
- Local QA passed: `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_handoff tests.test_carla_closed_loop_runner tests.test_closed_loop_video tests.test_oodrive_cli` -> 18 tests OK.
- Full QA passed: `bash scripts/pre_push_check.sh` -> 475 tests OK, 6 skipped.
- RunPod live CARLA fake-policy proof passed as simulator/control evidence: `/workspace/0xDriver/artifacts/runs/task160-live-fake-policy-final/closed_loop_trace.json`, `closed_loop_score=87.5000`, `closed_loop_integration_score=92.5000`, two recurrences, eight controls applied, and `/workspace/0xDriver/artifacts/runs/task160-live-fake-policy-final-video/closed_loop_hero.mp4`.
- RunPod video promotion gate intentionally blocked the fake-policy video despite strong live CARLA components: `closed_loop_video_score=84.0000`, `model_driven_policy=0.0000`; this preserves the rule that fake/cached-only control is not a hero Alpamayo proof.
- RunPod Alpamayo remote smoke initially failed with a false gated-auth blocker because the temporary wrapper exported `HF_HOME`/`XDG_CACHE_HOME` to `/workspace/.cache/driverx`, hiding the accepted/login token at `/home/kasm-user/.cache/huggingface/token`.
- Auth root-cause check: RunPod `/workspace/alpamayo1.5/a1_5_venv` reports `whoami=KenjiPcx`, token role `read`, and default-auth `model_info` access for `nvidia/Cosmos-Reason2-8B`; the same command with `XDG_CACHE_HOME=/workspace/.cache/driverx` loses the token and returns a gated-repo 401.
- Fixed remote Alpamayo scripts to preserve the logged-in HF auth home while using `HF_HUB_CACHE`/`TRANSFORMERS_CACHE` for workspace model caches; see `MEM-0049`.
- RunPod live Alpamayo proof after auth fix passed: `/workspace/0xDriver/artifacts/runs/task160-live-alpamayo-authfix-2step/closed_loop_trace.json`, policy `alpamayo-remote`, backend `carla-live`, two observe/infer/act iterations, eight controls applied, `closed_loop_score=87.5000`, `closed_loop_integration_score=92.5000`.
- RunPod Alpamayo inference details: step prediction states completed under `nvidia/Alpamayo-1.5-10B`; one-step isolation run measured `latency_ms=99412.3`, `vram_peak_mb=21482.25`, and reasoning snippet `Nudge to the right to clear the cone blocking the center of our lane`.
- RunPod hero video proof after auth fix passed: `/workspace/0xDriver/artifacts/runs/task160-live-alpamayo-authfix-2step-video/closed_loop_hero.mp4`, 60.0s, 720 frames, `closed_loop_video_score=110.0000`, `model_driven_policy=10.0000`, `live_carla_provenance=18.0000`.
- Implementation review: `tickets/TASK-160/artifacts/review/task160-authfix-review.json` -> verdict `pass`; auth blocker resolved, live Alpamayo/CARLA recurrence and video gates pass, with only the expected remote-only MP4 export caveat for final packaging.

### Visual Quality Recovery Evidence - 2026-05-09

- Root cause: the first pulled hero video looked static because the renderer stretched sparse checkpoint frames over 60s, used the ego/front camera so the vehicle could not be visible, and the initial trajectory-to-control conversion produced too little throttle for visible motion.
- Autoresearch was re-scoped to `closed_loop_video_score` with a deterministic fixture that rewards source-frame density, ego visibility, action-tick visibility, and honest paused-loop claims; `./autoresearch.sh` now reports `METRIC closed_loop_video_score=99.0000`, and `./autoresearch.checks.sh` passes the focused closed-loop video guard suite.
- Implemented a live spectator-chase visual camera in `carla-live`, captured pre/action/post visual frames per step, made `closed-loop-video` prefer dense visual/action frames with auto-duration instead of stretching sparse stills, and made `score-closed-loop-video` block no-ego or over-stretched renders.
- Tightened trajectory control with `min_throttle_when_moving`; the live RunPod fake-policy visual proof moved the ego from `x=227.0598` to `x=225.8062` and produced a car/cone third-person MP4, while remaining blocked for hero promotion because `model_driven_policy=0.0000`.
- RunPod live Alpamayo visual proof passed and was pulled locally: `artifacts/runs/task160-visual-spectator-alpamayo-proof-video/closed_loop_hero.mp4`, 800x450, 88 frames, 24fps, 3.667s, `source_frame_count=44`, `action_rgb_frame_count=40`, `seconds_per_source_frame=0.0833`, `ego_vehicle_visible=true`, `visual_camera_role=spectator_chase`, `closed_loop_video_score=98.6667`, blockers `[]`.
- Claim-boundary cleanup: fake-policy closed-loop traces now emit `alpamayo_outputs_applied_to_carla_controls=false` and `closed_loop_policy=<policy>` instead of inheriting the Alpamayo-control claim.
- Focused QA passed after the visual recovery patch: `PYTHONPATH=src python3 -m unittest tests.test_trajectory_control tests.test_carla_closed_loop_runner tests.test_closed_loop_video tests.test_oodrive_cli` -> 21 tests OK.

### Autonomy Readiness

- Requires Kasm RunPod, CARLA 0.9.16, `/workspace/driverx_py312`, `/workspace/alpamayo1.5/a1_5_venv`, and HF auth already installed through safe channel.
- Do not send secrets through Kasm proxy SSH heredocs.
- Stop condition: if CARLA or Alpamayo is unavailable, record blocker and preserve open-loop claims.

### Blockers

- No current auth blocker. The remaining promotion caveat is media export: the 60s Alpamayo hero MP4 is proved on the RunPod filesystem and should be pulled or hosted before final submission media is marked `local_file` or `public_url`.

### Plan Review

- `tickets/TASK-157/artifacts/review/task157-160-closed-loop-plan-review.json`
