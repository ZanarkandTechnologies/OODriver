# 0xDriver Minimal-Shot OOD Driving Harness

## Submission Angle

A randomized CARLA/Fail2Drive scenario forge plus retrieval-guided policy harness for testing frozen driving policies on weird but plausible long-tail situations without fine-tuning on those cases.

## 1-5 Minute Demo Outline

| time | beat | visual | narration |
|---|---|---|---|
| 0:00-0:20 | Problem | Title over generated CARLA/Bench2Drive route and OOD tags. | Minimal-shot autonomy should be judged on new long-tail scenes, not only memorized routes. |
| 0:20-0:55 | Scenario Forge | Show generated recipe ids, mutations, route pack, and overlay plan paths. | The harness generated 1 scenario recipe(s) with deterministic mutations and reusable route artifacts. |
| 0:55-1:30 | Policy Harness | Show policy runtime matrix and mock/memory/hybrid readiness rows. | Local policies and Fail2Drive dry-run adapters are ready while heavier VLA rows remain setup-gated; ready rows: 5. |
| 1:30-2:10 | Route Video Evidence | Play the Town10 CARLA route video and show the route evidence report. | The local route proof produced video=True while keeping missing route-score/entity-track limitations explicit. |
| 2:10-2:45 | Alpamayo Memory Test | Show Alpamayo no-memory vs memory CoC snippets and trajectory delta. | Alpamayo is now a live open-loop policy probe: status dataset_shape_observed, memory changed trajectory final L2 by 2.8886m, and cached replay produced 20 bounded commands labeled cached_replay. |
| 2:45-3:20 | Next Run | Show blockers.md and the exact next live command. | 2026-05-06 01:50 +0800 \| fail2drive,carla,map \| TASK-054B proved the Docker Fail2Drive client can reach local CARLA, but the stock Fail2Drive split routes in `fail2drive_split/` all require `Town13`, which is not installed in the local CARLA 0.9.16 package. Evidence: `tickets/archive/TASK-054B/artifacts/docker-route-run-town13-map-blocker-classified/fail2drive_route_run.md`. Next unblock path: install/provide a CARLA package containing Town13 or use a compatible route generator for installed maps such as Town10HD_Opt. |

## Understood Failure Case

- scenario_id: `None`
- status: `partial`
- route_path: `None`
- summary: Live route video exists, but the bounded smoke run has no completed route score or route completion.
- artifact: `provided route evidence path`

## Artifact Map

- `scenario_summary_path`: `artifacts/runs/task36-suite-1b/scenario-forge/scenario_suite_summary.json`
- `route_pack_path`: `artifacts/runs/task36-suite-1b/route-pack/bench2drive_route_pack.json`
- `overlay_plan_path`: `artifacts/runs/task36-suite-1b/overlay-plan/overlay_injection_plan.json`
- `overlay_evidence_path`: `artifacts/runs/task36-suite-1b/overlay-evidence/overlay_evidence.json`
- `policy_matrix_path`: `artifacts/runs/task37-policy-matrix/policy_runtime_matrix.json`
- `alpamayo_probe_path`: `tickets/TASK-059/artifacts/physicalai-shape-probe-summary/alpamayo_shape_probe_report.json`
- `route_evidence_path`: `tickets/archive/TASK-055/artifacts/town10-route-evidence/run_evidence.json`
- `alpamayo_comparison_path`: `tickets/archive/TASK-056/artifacts/town10-memory-comparison/alpamayo_ood_comparison.json`
- `cached_replay_path`: `tickets/TASK-062/artifacts/cached-alpamayo-replay/carla_policy_replay.json`
- `blockers_path`: `blockers.md`

### Recipe Artifacts

- `generated-base-animals-0076-visual-noise-000` -> `artifacts/runs/task36-suite-1b/recipes/000_generated-base-animals-0076-visual-noise-000/route-evidence/run_evidence.json`

## Live Evidence

- route_status: `partial`
- route_video: `tickets/archive/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/routes_town10.mp4`
- alpamayo_open_loop: `True`
- trajectory_delta: `{'available': True, 'point_count': 20, 'mean_l2_m': 0.9666, 'max_l2_m': 2.8886, 'final_l2_m': 2.8886}`
- cached_replay: `{'available': True, 'closed_loop_control': 'cached_replay', 'trajectory_frame': 'ego', 'command_count': 20, 'applied_count': 0, 'dry_run': True, 'safety_clamp_count': 20}`

## Claim Boundaries

- Generated CARLA/Fail2Drive OOD scenarios and route artifacts are real repo outputs.
- Alpamayo comparisons are open-loop trajectory-intent evaluations unless a route controller consumes them.
- Alpamayo comparison closed_loop_control=False.
- Cached replay converts a saved policy decision into bounded controls, but dry_run=True and it is not real-time VLA steering.
- Model weights, CARLA installs, videos, and credentials are not committed.

## Model Declarations

- `mock`: DriverX local deterministic or mock policy (ready)
- `mock-memory`: DriverX local deterministic or mock policy (ready)
- `hybrid`: DriverX local deterministic or mock policy (ready)
- `fail2drive-basic`: Fail2Drive stock CARLA policy/agent path (dry_run_ready)
- `fail2drive-expert`: Fail2Drive stock CARLA policy/agent path (dry_run_ready)
- `simlingo`: SimLingo / CARLA VLA checkpoint, setup-gated (blocked)
- `alpamayo`: Alpamayo reasoning VLA, setup-gated (blocked)
- `alpamayo-probe`: nvidia/Alpamayo-1.5-10B (dataset_shape_observed)
- `alpamayo-live-ood-comparison`: nvidia/Alpamayo-1.5-10B (live_memory_comparison_ready)

## Data And Asset Declarations

- Fail2Drive-style route/scenario seeds are used as scenario references; external checkout is not vendored.
- Generated OOD recipes, route packs, overlay plans, evidence reports, and blocker ledgers are small local artifacts.
- Waymo E2E remains a supporting open-loop track; no dataset shards are committed.
- Model weights, generated videos, CARLA installs, and credentials are excluded from git.
- Current route pack evidence: artifacts/runs/task36-suite-1b/route-pack/bench2drive_route_pack.json
- Current local route video evidence: tickets/archive/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/routes_town10.mp4 (4.1s, 7886364 bytes)

## Short Write-Up Draft

### Motivation

Autonomy systems fail when they only work on distributions they have already seen. 0xDriver treats minimal-shot driving as an evaluation and orchestration problem: generate plausible out-of-distribution pressure cases, run frozen policies through the same artifact contract, and preserve the failures as retrieval memory.

### Architecture

The current implementation builds deterministic scenario recipes, exports route-compatible CARLA/Bench2Drive artifacts, plans companion overlay actors, bundles route evidence, and tracks policy readiness. A retrieval layer can guide local policy decisions today, while SimLingo and Alpamayo remain swappable live-policy adapters.

### What Worked

The local harness is reproducible: generated suite status is `blocked`, policy runtime ready rows are `5`, and the Alpamayo probe status is `dataset_shape_observed`. The live Alpamayo memory comparison changed trajectory final L2 by `2.8886` metres while staying explicitly open-loop. Cached replay produced `20` bounded control command(s) from a saved policy decision without claiming real-time VLA control.

### What Did Not Work

The current named failure is `Live route video exists, but the bounded smoke run has no completed route score or route completion.`. This blocks a polished live route video but gives a precise next step instead of an ambiguous model-quality claim.

### Next Funding Step

Use the prize budget for a graphics-capable NVIDIA CARLA host, a confirmed reasoning-VLA checkpoint/runtime, and enough GPU hours to run generated OOD suites closed-loop with video, latency, infractions, and failure-memory comparisons.
