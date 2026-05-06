# TASK-093: Scenario Campaign Quality Gates And Auto-Rerun

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-089, TASK-090, TASK-091, TASK-092
- location: `src/driverx/pipeline`, `src/driverx/scenarios`, `src/driverx/simulators`, `tests`, docs, `tickets/TASK-093/artifacts`
- enter when: road-alignment, environment generation, behavior validation, and catalog indexing exist
- leave when: campaign runs automatically reject bad starts, missing conflict, invisible actors, missing frames, and off-road evidence, then resample or classify the blocker
- blockers: live proof requires local CARLA; fake quality-gate tests do not
- spawned follow-ups: TASK-094 policy evaluation consumes quality-passed scenarios
- complexity: M

### Summary

Add the missing "this is actually a valid test" layer. The next judge-visible
video should not be manually eyeballed after the fact; the campaign should
measure whether the ego starts on road, actors are visible, a conflict happens,
and the video has enough duration.

### Scope

- In scope: campaign validators, auto-rerun/resampling policy, evidence
  classification, scenario promotion/rejection, and one live quality-passed
  longer video if CARLA is available.
- Out of scope: model scoring, full Fail2Drive benchmark score, or custom mesh
  import.

### Gap Analysis

- Current state: campaigns can produce videos, but a bad scene can still become
  the headline artifact.
- Production expectation: generated OOD suites need quality gates like a test
  harness: valid geometry, enough frames, visible OOD actor, meaningful
  interaction, and reproducible failure labels.
- Missing gaps: validators, skip/rerun policy, scenario quality summary, and
  catalog promotion rules.
- Recommendation: make "quality-passed scenario video" the next milestone after
  road-frame correction.

### Plan

#### Change

Extend scripted campaign execution with preflight and postflight gates, plus a
deterministic retry loop that resamples anchors or scenarios when quality fails.

#### Why

This directly answers the user's concern that the current video looks wrong and
the algorithm is inconsistent.

#### Before -> After

- Before: campaign success means "some frames were captured."
- After: campaign success means "the scenario passed road, visibility,
  conflict, duration, and artifact checks."

#### Touch

- `src/driverx/pipeline/scripted_ood_campaign.py`: preflight/postflight gates,
  retry loop, and quality summary.
- `src/driverx/scenarios/quality.py`: reusable quality report model.
- `src/driverx/scenarios/catalog.py`: promotion status integration.
- `src/driverx/pipeline/route_video.py`: duration/frame-count checks if not
  already centralized.
- `tests/test_scenario_quality.py`, `tests/test_scripted_ood_campaign.py`.
- `configs/scripted_ood_campaign.local.sample.yaml`: add quality thresholds.

#### Inspect

- `src/driverx/pipeline/scripted_ood_campaign.py`
- `src/driverx/pipeline/route_video.py`
- `src/driverx/pipeline/generated_ood_suite.py`
- `tickets/TASK-085/artifacts/task85-live-campaign-2b/`

#### Signature Delta

```python
evaluate_scenario_quality(case: CampaignCaseArtifacts, thresholds: ScenarioQualityThresholds) -> ScenarioQualityReport
select_quality_passed_cases(reports: list[ScenarioQualityReport], limit: int) -> list[str]
run_quality_gated_campaign(config: ScriptedOodCampaignConfig) -> ScriptedOodCampaignSummary
```

#### Type Sketch

```python
ScenarioQualityReport = {
  "scenario_id": str,
  "passed": bool,
  "checks": {
    "road_aligned": QualityCheck,
    "video_duration": QualityCheck,
    "actor_visible": QualityCheck,
    "has_conflict": QualityCheck,
    "artifact_complete": QualityCheck,
  },
  "retry_count": int,
  "promotion_recommendation": "hero" | "failure_case" | "reject" | "blocked",
}
```

#### Typed Flow Example

`campaign config count=5 retry_limit=3`
-> generate recipe
-> preflight road/behavior validation
-> live/fake CARLA run
-> postflight video/tracks/conflict validation
-> catalog promotion or rejection
-> `quality_gated_campaign_report.md`.

#### Execution Steps

1. Add quality model and pure artifact validators.
2. Wire preflight validators from TASK-089/TASK-092 and postflight validators
   from frame/tracks/video evidence.
3. Add retry/resample policy with deterministic seed increments.
4. Run fake tests and a fake campaign proof.
5. If CARLA is live, run a two-case quality-gated campaign and assemble a
   longer promoted video.

#### Recommendation

Make this the "we finally have a credible end-to-end artifact" ticket. It
should produce the first video we are comfortable showing without apologizing
for off-road starts.

#### Options Considered

- Manually inspect and pick the best video: fast but not a simulator harness.
- Quality gates without rerun: useful but brittle.
- Quality gates with deterministic retry: best; turns generation into a
  repeatable test pipeline.

#### Blast Radius

- Moderate: campaign outputs and success criteria become stricter.

#### Risks

- Live CARLA on Mac may be slow or unavailable. Keep fake gates fully tested
  and record live proof as opportunistic evidence.

### Acceptance Criteria

- [x] AC-1: Campaign summary reports quality checks per case.
- [x] AC-2: Off-road starts, missing video, too-short video, and no-conflict
  cases are rejected or blocked, not promoted.
- [x] AC-3: Campaign can retry/resample deterministically when a case fails a
  quality gate.
- [x] AC-4: Cases without strict video and road-alignment proof are blocked
  rather than promoted; live quality-passed video production waits on a
  rendering CARLA host.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_scenario_quality tests.test_scripted_ood_campaign`
- `PYTHONPATH=src python3 -m driverx run-scripted-ood-campaign --config configs/scripted_ood_campaign.local.sample.yaml --run-id task93-quality-gated-campaign --live`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Fake implementation and tests are fully autonomous.
- If local CARLA is down or slow, record that blocker and proceed to TASK-094
  with cataloged prior captures only if quality status is explicit.

### Evidence

- Planned 2026-05-06 as the quality gate needed before any next submission
  video is promoted.
- Plan review: `docs/reviews/TASK-089-095-impl-plan-review.md`.
- Implemented reusable scenario quality gates for duration, frame count, video,
  conflict distance, and road alignment.
- Added deterministic `quality_retry_limit` campaign retries. Strict-duration
  retry proof produced `attempt_count=3`, `quality_retry_limit=2`, and final
  `attempt_index=2`.
- Review follow-up made video and road alignment strict default gates, so fake
  campaigns now produce `quality_blocked` evidence instead of pretending to be
  submission-grade.
- Focused tests passed:
  `PYTHONPATH=src python3 -m unittest tests.test_scripted_ood_campaign tests.test_scenario_quality tests.test_environment_generator`.
- Generated quality-gated campaign evidence:
  `tickets/TASK-093/artifacts/quality-gated-fake-campaign-v3/quality/scenario_quality_summary.md`.
- Generated retry evidence:
  `tickets/TASK-093/artifacts/quality-retry-proof-v2/scripted_ood_campaign_summary.md`.

### Blockers

- Live quality-passed video proof needs a rendering CARLA server. Remote RunPod
  CARLA is installed but blocked on Vulkan; local CARLA remains the current
  rendering path.
