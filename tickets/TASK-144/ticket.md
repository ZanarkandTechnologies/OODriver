# TASK-144: Judge Packet Refresh With CARLA Bad Paths

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-142, TASK-143
- location: `README.md`, `docs/HISTORY.md`, `artifacts/runs/*submission*`, `tickets/TASK-144`
- enter when: A CARLA bad-path artifact exists and has been score-gated, or the blocker is precise enough to explain honestly in the submission.
- leave when: the judge-facing packet leads with OODrive's strongest story: generate realistic OOD scenarios, place/run them in CARLA, show bad-path behavior, attach open-loop Alpamayo/RAG reasoning where available, and state limits clearly.
- blockers: depends on TASK-142/TASK-143 artifact status.
- spawned follow-ups:
- complexity: S

### Description

Refresh the submission packet so it no longer relies on the local stress reel as if it were CARLA proof. The final story should be simple: OODrive generates realistic rare-event scenarios, CARLA renders/proves them where available, local stress tests explain the desired behavior, and Alpamayo reasoning remains open-loop.

### Goal

Make the submission understandable in one pass by a judge or real-world autonomy implementer. No ambiguous UI/demo layers, no hidden claim upgrades, no "car just drove away" artifacts.

### Acceptance Criteria
- [ ] AC-1: Submission artifact map distinguishes local scripted stress proof, fake-CARLA/generator proof, live CARLA visual proof, and open-loop Alpamayo reasoning.
- [ ] AC-2: CARLA bad-path MP4 or blocker is linked in the main packet.
- [ ] AC-3: README/current packet references use the lane-safe v3 stress reel only as supporting explanation, not as CARLA evidence.
- [ ] AC-4: Final copy includes the four claim boundaries: `closed_loop_vla_control=false`, `real_time_vla_control=false`, `sampled_open_loop_reasoning=true`, and `time_warped_offline_demo=true` where relevant.

### Agent Contract
- Open: `README.md`, `docs/HISTORY.md`, `tickets/TASK-140/ticket.md`, `tickets/TASK-141/ticket.md`, TASK-142/TASK-143 artifacts.
- Test hook: `./autoresearch.checks.sh` and relevant score command from TASK-143.
- Stabilize: do not relabel local scripted stress proof as CARLA evidence.
- Inspect: final packet index/write-up, artifact map, claim matrix.
- Expected artifacts: refreshed packet index/report, artifact map, score summary.

### Required Evidence
- [ ] Packet/report path linked.
- [ ] Score or blocker summary linked.
- [ ] `./autoresearch.checks.sh` pass or blocker recorded.
- [ ] Review before completion claim.
