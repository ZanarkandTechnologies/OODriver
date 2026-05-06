# 0xDriver Minimal-Shot OOD Driving Harness

## Submission Angle

A randomized CARLA/Fail2Drive scenario forge plus retrieval-guided policy harness for testing frozen driving policies on weird but plausible long-tail situations without fine-tuning on those cases.

## 1-5 Minute Demo Outline

| time | beat | visual | narration |
|---|---|---|---|
| 0:00-0:20 | Problem | Title over generated CARLA/Bench2Drive route and OOD tags. | Minimal-shot autonomy should be judged on new long-tail scenes, not only memorized routes. |
| 0:20-0:55 | Runnable Local OOD Demo | Open the generated local simulator HTML with actor, ego, baseline, memory, and hybrid tracks. | The dependency-light demo runs now: recipe generated-base-animals-0076-regional-driving-behavior-000 uses behavior motorcycle_filtering and finds worst risk near_miss_proxy at 1.9679m. |
| 0:55-1:20 | Scenario Forge | Show generated recipe ids, mutations, route pack, and overlay plan paths. | The harness generated 1 scenario recipe(s) with deterministic mutations and reusable route artifacts. |
| 1:20-1:55 | Policy Harness | Show policy runtime matrix and mock/memory/hybrid readiness rows. | Local policies and Fail2Drive dry-run adapters are ready while heavier VLA rows remain setup-gated; ready rows: 3. |
| 1:55-2:25 | Fixture OOD Video Proof | Play the fixture OOD video proving overlays, risk tracks, and MP4 assembly while the live CARLA bridge is fixed. | The fixture video path produced 20.0s of annotated OOD evidence for fixture-malaysia-motorcycle-filtering; live CARLA frame capture remains the next runtime blocker. |
| 2:25-3:00 | Alpamayo Memory Test | Show Alpamayo no-memory vs memory CoC snippets and trajectory delta. | Alpamayo is linked to the generated scene: latency not available, CoC snippet available=False, memory changed trajectory final L2 by 2.8886m. |
| 3:00-3:30 | Next Run | Show blockers.md and the exact next live command. | 2026-05-06 19:20 +0800 \| carla,docker,scripted-ood,video \| TASK-072 scripted OOD runner implementation passed fake-CARLA tests, but the live Docker client attempt timed out waiting for local CARLA at `host.docker.internal:2000`. The runner wrote a clean blocked report with no RGB frames. Evidence: `tickets/TASK-072/artifacts/task72-live-candidate/carla_ood_demo.md`. Next unblock path: keep `CARLA.app` open until the town is fully loaded, then rerun `bash scripts/run_carla_client_docker.sh python -m driverx run-carla-ood-demo --config configs/carla_ood_demo.local.sample.yaml --tick-count 240 --run-id task72-live-retry`. If Docker still cannot reach `host.docker.internal`, run the same command from inside the known-good CARLA client container after verifying `python -c "import carla; print(carla.Client('host.docker.internal', 2000).get_world().get_map().name)"`. |

## Understood Failure Case

- scenario_id: `generated-base-animals-0076-regional-driving-behavior-000`
- status: `near_miss_proxy`
- route_path: `fail2drive_split/Base_Animals_0076.xml`
- summary: Baseline `policy` policy reaches 1.9679m from the OOD actor in the motorcycle_filtering case; the memory-guided row slows/yields earlier, making this a concrete minimal-shot retrieval failure case.
- artifact: `tickets/TASK-064/artifacts/local-ood-demo/local-sim/local_ood_sim.html`

## Artifact Map

- `local_demo_path`: `tickets/TASK-064/artifacts/local-ood-demo/end_to_end_demo.json`
- `local_sim_html`: `tickets/TASK-064/artifacts/local-ood-demo/local-sim/local_ood_sim.html`
- `local_sim_svg`: `tickets/TASK-064/artifacts/local-ood-demo/local-sim/local_ood_sim.svg`
- `local_sim_json`: `tickets/TASK-064/artifacts/local-ood-demo/local-sim/local_ood_sim.json`
- `scenario_summary_path`: `None`
- `route_pack_path`: `None`
- `overlay_plan_path`: `None`
- `overlay_evidence_path`: `None`
- `policy_matrix_path`: `tickets/TASK-064/artifacts/local-ood-demo/policy/policy_reaction_matrix.json`
- `alpamayo_probe_path`: `tickets/TASK-059/artifacts/physicalai-shape-probe-summary/alpamayo_shape_probe_report.json`
- `route_evidence_path`: `tickets/TASK-071/artifacts/town13-early-route-evidence/run_evidence.json`
- `alpamayo_comparison_path`: `tickets/TASK-075/artifacts/scenario-linked-memory-comparison-v2/alpamayo_ood_comparison.json`
- `ood_video_evidence_path`: `tickets/TASK-073/artifacts/fixture-long-ood-video-v2/ood_video_evidence.json`
- `alpamayo_scene_path`: `tickets/TASK-074/artifacts/generated-scene-open-loop-blocker-v2/alpamayo_ood_scene.json`
- `generated_asset_evidence_path`: `tickets/TASK-076/artifacts/stock-proxy-assets/asset_summary.json`
- `cached_replay_path`: `tickets/TASK-062/artifacts/cached-alpamayo-replay/carla_policy_replay.json`
- `blockers_path`: `blockers.md`

## Live Evidence

- route_status: `partial`
- route_video: `tickets/TASK-071/artifacts/town13-early-video-after-restart/Generalization_PedestriansOnRoad_1088_early.mp4`
- alpamayo_open_loop: `True`
- trajectory_delta: `{'available': True, 'point_count': 20, 'mean_l2_m': 0.9666, 'max_l2_m': 2.8886, 'final_l2_m': 2.8886}`
- cached_replay: `{'available': True, 'closed_loop_control': 'cached_replay', 'trajectory_frame': 'ego', 'command_count': 20, 'applied_count': 0, 'dry_run': True, 'safety_clamp_count': 20}`

## Claim Boundaries

- Generated CARLA/Fail2Drive OOD scenarios and route artifacts are real repo outputs.
- Alpamayo comparisons are open-loop trajectory-intent evaluations unless a route controller consumes them.
- Alpamayo comparison closed_loop_control=False.
- Current OOD video is fixture evidence for the overlay/video pipeline, not a live CARLA run.
- Alpamayo scene reasoning closed_loop_control=False.
- Cached replay converts a saved policy decision into bounded controls, but dry_run=True and it is not real-time VLA steering.
- Model weights, CARLA installs, videos, and credentials are not committed.

## Model Declarations

- `mock`: DriverX local deterministic or mock policy (ready)
- `mock`: DriverX local deterministic or mock policy (ready)
- `hybrid`: DriverX local deterministic or mock policy (ready)
- `alpamayo-probe`: nvidia/Alpamayo-1.5-10B (dataset_shape_observed)
- `alpamayo-live-ood-comparison`: nvidia/Alpamayo-1.5-10B (linked_cached_evidence_with_warnings)
- `alpamayo-generated-ood-scene`: nvidia/Alpamayo-1.5-10B (blocked)

## Data And Asset Declarations

- Fail2Drive-style route/scenario seeds are used as scenario references; external checkout is not vendored.
- Generated OOD recipes, route packs, overlay plans, evidence reports, and blocker ledgers are small local artifacts.
- Waymo E2E remains a supporting open-loop track; no dataset shards are committed.
- Model weights, generated videos, CARLA installs, and credentials are excluded from git.
- Current fixture OOD video evidence: tickets/TASK-073/artifacts/fixture-long-ood-video-v2/fixture-malaysia-motorcycle-filtering_ood.mp4 (20.0s)
- Current generated object evidence uses stock CARLA proxy assets; artifact: tickets/TASK-076/artifacts/stock-proxy-assets/asset_manifests.json
- Current local end-to-end simulator evidence: tickets/TASK-064/artifacts/local-ood-demo/local-sim/local_ood_sim.html
- Current local route video evidence: tickets/TASK-071/artifacts/town13-early-video-after-restart/Generalization_PedestriansOnRoad_1088_early.mp4 (0.5s, 507730 bytes)

## Short Write-Up Draft

### Motivation

Autonomy systems fail when they only work on distributions they have already seen. 0xDriver treats minimal-shot driving as an evaluation and orchestration problem: generate plausible out-of-distribution pressure cases, run frozen policies through the same artifact contract, and preserve the failures as retrieval memory.

### Architecture

The current implementation builds deterministic scenario recipes, exports route-compatible CARLA/Bench2Drive artifacts, plans companion overlay actors, bundles route evidence, and tracks policy readiness. A retrieval layer can guide local policy decisions today, while SimLingo and Alpamayo remain swappable live-policy adapters.

### What Worked

The local harness is reproducible: local demo status is `ready`, behavior is `motorcycle_filtering`, policy runtime ready rows are `3`, and the Alpamayo probe status is `dataset_shape_observed`. Fixture OOD video duration is `20.0` seconds. Alpamayo scene reasoning latency is `not provided` ms. The linked cached Alpamayo memory comparison changed trajectory final L2 by `2.8886` metres while staying explicitly open-loop. Cached replay produced `20` bounded control command(s) from a saved policy decision without claiming real-time VLA control.

### What Did Not Work

The current CARLA route gap is `Generalization_PedestriansOnRoad_1088`: video evidence exists (0.5s) but driving_score=`None` and route_completion=`None` because the early-video run stops before full scoring. This keeps the submission claim bounded: we have visible CARLA/OOD evidence now, while full closed-loop score evidence remains the next runtime step.

### Next Funding Step

Use the prize budget for a graphics-capable NVIDIA CARLA host, a confirmed reasoning-VLA checkpoint/runtime, and enough GPU hours to run generated OOD suites closed-loop with video, latency, infractions, and failure-memory comparisons.
