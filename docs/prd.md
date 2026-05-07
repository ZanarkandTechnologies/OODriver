# PRD: Scenario Generator Studio For Minimal-Shot Autonomy

Last updated: 2026-05-07 16:55 +0800

## Problem / Context

0xDriver has working pieces: scenario generation, CARLA evidence, risk
timelines, Alpamayo open-loop reasoning, RAG comparison, and a final V8 packet.
The gap is product legibility and closed-loop evaluation. The current demo still
feels like a collection of scripts instead of a scenario-generation product
where a reviewer can author chaos, run it, inspect what the car/model saw, and
curate the result into a minimal-shot dataset.

The submission should now center on:

> A Scenario Generator Studio for generating weird-but-plausible OOD CARLA
> driving cases, running closed-loop policies, showing risk/RAG/VLA reasoning,
> and curating failures into a memory-backed minimal-shot evaluation set.

Alpamayo-in-CARLA is a potentially novel contribution, but only if it is framed
as a closed-loop adapter/evaluator for a reasoning VLA inside CARLA-generated
OOD scenarios. Alpamayo VQA or open-loop trajectory snapshots alone are useful
evidence, but not enough to be the main contribution.

## Audience

- Primary: SoTA Commission I judges evaluating novelty, feasibility, technical
  excellence, and adherence to minimal-shot autonomy.
- Secondary: autonomy researchers who want to stress-test frozen VLA policies
  on new long-tail conditions.
- Internal operator: the project owner using a Mac for orchestration and a
  graphics-capable RunPod/CARLA host for closed-loop runtime.

## JTBD

When I want to test whether a frozen VLA driving policy generalizes to a novel
road situation, I want to generate a scenario, run it in CARLA, inspect the
policy's risk/reasoning/actions over time, and save the outcome as reusable
failure memory, so I can demonstrate minimal-shot autonomy without fine-tuning
or hand-authoring every edge case.

## Parity Research

### Capability + Parity Lens

Compare 0xDriver against credible scenario-based autonomy validation tools. The
target is not a full AV simulator vendor suite; the target is the minimum
credible product loop for scenario generation, execution, analysis, and dataset
curation.

### Local Baseline

Current repo surfaces:

- Scenario Studio prompt compiler and deterministic agentic loop.
- CARLA scripted OOD campaign evidence and video rendering.
- CARLA entity-track risk timeline.
- RAG memory and Alpamayo open-loop comparison artifacts.
- V8 submission pack and scenario browser.

Current missing surfaces:

- A product UI/studio where the generation loop is inspectable and operable.
- A first-class closed-loop run surface on the graphics/CARLA instance.
- A policy adapter that can execute Alpamayo trajectory intent inside CARLA, not
  only produce open-loop evidence.
- A curation dashboard showing accepted/rejected scenarios and next runtime
  targets as a managed dataset.

### Comparable Implementations

- **CARLA ScenarioRunner / OpenSCENARIO support**: supports CARLA execution of
  OpenSCENARIO entities, routes, controllers, conditions, collisions, distance
  checks, traffic signals, speed actions, route assignment, and controller
  actions, with documented limitations. This proves the expected simulator
  product surface: scenario description -> actors/actions/conditions ->
  controller execution -> measurable events.
- **ASAM OpenSCENARIO 2.x**: treats scenarios as composable actors, actions,
  constraints, and coverage goals. It explicitly supports building abstract
  scenarios and specializing them across road, speed, distance, and weather
  conditions.
- **Fail2Drive**: contributes paired in-distribution/OOD CARLA routes, unseen
  long-tail scenario classes, a scenario gallery, quick start, integration
  tutorial, toolbox, and model analysis. This is the closest benchmark parity
  target.
- **NVIDIA Alpamayo / AlpaSim**: Alpamayo 1.5 processes video, ego-motion
  history, navigation, and text inputs; reasons; and generates trajectories.
  NVIDIA positions AlpaSim as a closed-loop evaluation framework where policy
  decisions affect vehicle dynamics and future observations.

### Common Surfaces

Credible scenario products converge on:

- Scenario authoring: actors, environment, behaviors, constraints, seed/random
  controls, and scenario families.
- Coverage/generation: parameterization, mutation, ODD coverage, and accepted
  scenario queues.
- Runtime execution: simulator host config, controller/policy adapter, route,
  sync mode, sensors, output directory, and repeatability.
- Observability: video, entity tracks, collisions, distances, route progress,
  infractions, risk events, and timing.
- Analysis: pass/fail, failure mode, comparison against base cases, and model
  behavior explanations.
- Dataset lifecycle: accepted/rejected state, rationale, lineage, assets, and
  next run target.

### Repo Delta

0xDriver has generation, evidence, and reporting primitives, but lacks the
operator-facing studio and the closed-loop Alpamayo/CARLA evaluator. The next
product slice should not add more isolated scripts; it should assemble the
existing primitives into one app/workbench and use the RunPod CARLA host for at
least one closed-loop policy run.

### Recommendation

Build **Scenario Generator Studio V1** now:

1. A local web app for scenario generation and dataset curation.
2. A RunPod/CARLA closed-loop runner lane.
3. A policy adapter surface with `mock`, `CARLA autopilot`, and
   `alpamayo-trajectory` modes.
4. A demo view showing risk timeline, RAG memory, model reasoning, and action
   intent side-by-side with video.

## Gap Analysis

### Current State

- Backend generation exists through `driverx.scenarios.studio` and
  `driverx.scenarios.agentic_loop`.
- Evidence bundling exists through `driverx.workbench`.
- Risk/perception exists from CARLA entity tracks.
- Alpamayo exists as open-loop package/materialization/comparison.
- Video overlay exists for offline/time-warped demonstration.
- CARLA has been proven on a RunPod graphics host, but the latest pass did not
  use it for a fresh closed-loop run.

### Production Expectation

A credible Scenario Generator Studio should let the operator:

- Generate OOD scenarios from briefs or seed themes.
- Inspect and edit scenario parameters before runtime.
- Run a scenario against a selected policy on a configured CARLA host.
- See live or replayed simulator evidence: video, tracks, risk events, model
  reasoning, RAG retrieval, action intent, and metrics.
- Curate the run into accepted/rejected/draft states with lineage.
- Export a final evidence bundle for submission.

### Missing Gaps

- Product UI: no app that demonstrates the scenario-generation product.
- Closed-loop run: no current Alpamayo-in-CARLA closed-loop artifact.
- Runtime controller seam: Alpamayo trajectory intent is not yet converted into
  CARLA controls in a running loop.
- Scenario editor: generated candidates are JSON/HTML reports, not editable
  scenario cards with parameters.
- Dataset workflow: accepted/rejected curation exists as artifacts but not as a
  studio workflow.
- Live RunPod lane: CARLA host setup exists historically, but the current
  command surface needs one clear "run this closed-loop scenario on the
  instance" entrypoint.

### Recommendation

Do not abandon CARLA. Build the app around CARLA generation and use Alpamayo as
the prestige policy evaluator. Treat Alpamayo-in-CARLA as a stretch-to-core
feature:

- **Core if achieved:** closed-loop Alpamayo trajectory adapter runs one short
  generated scenario in CARLA and produces video/tracks/reasoning/metrics.
- **Fallback if runtime fights back:** CARLA autopilot/mock closed-loop run
  plus Alpamayo open-loop reasoning on captured frames, clearly labeled.

## SLC Slice (Next Release)

Ship **Scenario Generator Studio V1 + one closed-loop CARLA proof**.

This is the smallest complete product slice:

1. Browser app opens to the Scenario Studio, not a static landing page.
2. Operator can generate 10-20 OOD scenarios from seed themes.
3. Operator can inspect a scenario card: environment, actors, behaviors,
   expected failure, memory query, assets, run readiness.
4. Operator can queue one scenario for closed-loop runtime.
5. Runner targets the RunPod/CARLA host and produces a run artifact.
6. App shows replay/evidence: video, risk timeline, RAG memory, reasoning, and
   action intent.
7. App shows curation status and final submission export.

## Goals

- Make the product contribution obvious in the first 10 seconds of the demo.
- Prove at least one closed-loop CARLA run from a generated scenario.
- Attempt Alpamayo-in-CARLA as the highest-signal policy adapter.
- Preserve honest fallbacks and claim boundaries if Alpamayo cannot close the
  loop in time.
- Keep app and artifacts reproducible from tracked code plus ignored video/run
  outputs.

## Non-Goals

- Do not build a new simulator; CARLA remains the simulator.
- Do not rebuild CARLA or SimLingo unless blocked runtime evidence proves it is
  the only path.
- Do not fine-tune Alpamayo or any AV model.
- Do not claim official Fail2Drive score unless a real stock route evaluator
  produces one.
- Do not claim image-based object detection when using simulator tracks.
- Do not claim real-time VLA control unless Alpamayo actually controls CARLA
  live with measured loop timing.
- Do not add Meshy/generated 3D assets to the critical path before the studio
  and closed-loop proof work.

## User Stories

### US-001: Generate Scenario Candidates

**Description:** As a submission operator, I want to generate OOD scenarios from
seed themes so that the system visibly creates new minimal-shot test cases.

**Acceptance Criteria:**

- [ ] App has a Scenario Studio view with seed themes, count, severity, and
  random seed controls.
- [ ] Generate action creates scenario cards with environment, behavior, actors,
  assets, OOD tags, memory query, expected failure, and run readiness.
- [ ] Duplicate/weak candidates are rejected with visible rationale.
- [ ] Generated batch is saved as JSON and can be reloaded by run id.

### US-002: Inspect And Curate Dataset Queue

**Description:** As a researcher, I want to review accepted/rejected generated
cases so that the simulation harness becomes a dataset flywheel.

**Acceptance Criteria:**

- [ ] App has queue tabs for `accepted`, `rejected`, `needs runtime`, and
  `ready for submission`.
- [ ] Each card shows lineage from brief -> scenario -> run -> memory/evidence.
- [ ] Curation records include reason, score, novelty tags, and next action.
- [ ] Export creates a ScenarioRunBundle-compatible artifact.

### US-003: Run Closed-Loop CARLA Scenario

**Description:** As an engineer, I want to run a generated scenario against a
policy in CARLA so that the submission includes actual simulator behavior, not
only static analysis.

**Acceptance Criteria:**

- [ ] App/CLI can target a configured CARLA host on the provided RunPod
  graphics instance.
- [ ] Runner supports at least `mock` or `autopilot` closed-loop policy mode.
- [ ] Runner attempts `alpamayo-trajectory` mode when model/runtime inputs are
  available.
- [ ] Run output includes video, entity tracks, risk timeline, timings, policy
  actions, and claim boundaries.
- [ ] If Alpamayo cannot run closed-loop, the blocker is saved and the fallback
  closed-loop run still completes.

### US-004: Show Reasoning And RAG During Replay

**Description:** As a judge, I want to see what the system thinks it saw and why
it acts so that the demo communicates minimal-shot reasoning.

**Acceptance Criteria:**

- [ ] Replay view shows video alongside risk events, retrieved memory,
  reasoning snippets, action intent, and latency.
- [ ] Timeline scrub selects synchronized risk/reasoning/action state.
- [ ] Every view labels whether reasoning is live closed-loop, sampled
  open-loop, or post-run replay.
- [ ] Exported demo can be rendered to a 1-5 minute MP4.

### US-005: Export Submission Evidence

**Description:** As the project owner, I want one export packet so that I can
submit quickly without hunting through artifacts.

**Acceptance Criteria:**

- [ ] Export includes final video path, scenario browser, write-up, artifact map,
  model declarations, and claim boundaries.
- [ ] Heavy videos remain ignored and referenced, not committed.
- [ ] A review artifact maps claims to evidence.

## Functional Requirements

- FR-1: Scenario Studio app must load existing `agentic_ood_generation_loop.json`
  artifacts and generate new ones.
- FR-2: Scenario cards must expose environment, behavior, assets, actors,
  expected failure, memory query, and curation state.
- FR-3: Closed-loop runner must separate simulator runtime, policy inference,
  control conversion, and result parsing timings.
- FR-4: Policy adapter interface must support `mock`, `carla-autopilot`, and
  `alpamayo-trajectory`.
- FR-5: Alpamayo adapter must consume CARLA camera/history packages and output
  trajectory intent converted to CARLA controls or a clear blocker.
- FR-6: Replay view must work from recorded artifacts without requiring live
  CARLA.
- FR-7: Claim boundaries must be embedded in every run and export artifact.
- FR-8: No credentials, model weights, CARLA installs, generated videos, or
  dataset shards may be committed.

## Constraints

- Security/privacy: `.env`, SSH keys, Hugging Face tokens, RunPod tokens, model
  weights, and datasets stay outside git.
- Performance: app interactions should be instant locally; CARLA/VLA runtime may
  be slow but must log timings honestly.
- Platform: Mac is orchestration/UI; RunPod graphics/CUDA host is the preferred
  CARLA runtime.
- Time: prioritize one impressive end-to-end artifact over broad feature count.
- Budget: keep long GPU/CARLA runs bounded by explicit scenario count and
  duration.
- Licensing: Alpamayo is research/non-commercial; declarations must state this.

## Autonomy Readiness

- Human inputs/assets needed:
  - Current RunPod SSH target and whether the graphics CARLA pod is still alive.
  - Confirmation of the policy mode priority: `alpamayo-trajectory` first, then
    `carla-autopilot` fallback.
  - Optional logo/branding only if the app needs polish.
- Credentials / external services:
  - Hugging Face token available in local/remote env, not committed.
  - SSH key for RunPod host.
  - Meshy key not needed for the next slice.
- Compute or runtime needs:
  - Graphics-capable CARLA 0.9.16 host.
  - Python client environment that can connect to CARLA.
  - Alpamayo environment on CUDA host if attempting live trajectory mode.
- Tooling or testability gaps:
  - Need one command to run the closed-loop scenario on RunPod and pull compact
    evidence back.
  - Need browser visual QA once app exists.
- Hard-to-QA surfaces:
  - Whether Alpamayo trajectory-to-control conversion is stable enough for
    closed-loop driving.
  - Whether the CARLA host can sustain route runtime and camera capture.
- Human gates:
  - Plan approval: not required for same-scope next implementation ticket.
  - QA approval: user reviews final video/app demo.
  - Deploy/publish: ask before public upload.
  - Spend/billing: bounded use of already-provided GPU host is allowed by prior
    instruction; ask before creating new paid resources.
  - Destructive/migration actions: ask before deleting remote instance data.
- Agent decision boundaries:
  - If Alpamayo closed-loop blocks, finish the app and autopilot/mock
    closed-loop fallback, log blocker, and keep moving.
  - Do not spend another full pass on runtime setup unless it directly produces
    a closed-loop artifact or a precise blocker.

## Risks / Unknowns

- Alpamayo outputs trajectories, not direct CARLA control; conversion may be
  unstable without local MPC/safety shield.
- CARLA host may be up historically but unavailable in the current session.
- Full closed-loop Alpamayo may be too slow for real-time; an offline sampled
  controller may need time-warped or step-by-step execution.
- Scenario generation UI could become cosmetic if it does not trigger real
  artifacts; it must be artifact-backed.
- App polish could consume time that should go into the closed-loop run.

## Backpressure / Evidence to Ship

- Tests:
  - Scenario generation app data loaders.
  - Closed-loop run command planner.
  - Policy adapter trajectory-to-control conversion.
  - Replay timeline synchronization.
- QA:
  - Browser screenshot of Scenario Studio.
  - Browser screenshot of replay with risk/RAG/reasoning visible.
  - One closed-loop run artifact.
- Perf checks:
  - CARLA loop timing.
  - Policy inference timing.
  - Control conversion timing.
- Demo:
  - 1-5 minute video showing generator -> run -> reasoning/replay -> curation.
- Review:
  - Evidence review must pass code-quality, integration-readiness,
    evidence-quality, UI quality, and video quality.

## First SLC Boundary

The first SLC is **not** "perfect Alpamayo drives CARLA." It is:

> Scenario Generator Studio V1 with one closed-loop CARLA run and an honest
> Alpamayo trajectory adapter attempt.

Success is one of:

- Best case: Alpamayo trajectory adapter controls a generated CARLA scenario for
  a short closed-loop run, with video, tracks, risk, reasoning, and metrics.
- Acceptable fallback: CARLA autopilot/mock policy completes the closed-loop
  generated scenario, while Alpamayo reasoning is sampled on the same captured
  frames and shown in replay.

## References

- CARLA ScenarioRunner OpenSCENARIO support:
  https://scenario-runner.readthedocs.io/en/latest/openscenario_support/
- ASAM OpenSCENARIO scenario authoring:
  https://publications.pages.asam.net/standards/ASAM_OpenSCENARIO/ASAM_OpenSCENARIO_DSL/latest/conceptual-overview/writing_a_scenario.html
- Fail2Drive project:
  https://simonger.github.io/fail2drive/
- NVIDIA Alpamayo developer page:
  https://developer.nvidia.com/drive/alpamayo
- NVIDIA Alpamayo overview:
  https://www.nvidia.com/en-au/solutions/autonomous-vehicles/alpamayo/
