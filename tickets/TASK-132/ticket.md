# TASK-132: 90-Point Submission Readiness Scorecard

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-131
- location: `src/driverx/evaluation`, `src/driverx/scenarios`, `autoresearch.*`, `tests`, `tickets/TASK-132/artifacts`
- enter when: TASK-131 has a passing hero video, but `hero_demo_score` is saturated and no longer measures whether the whole submission is 90th-percentile ready
- leave when: `./autoresearch.sh` emits `METRIC submission_readiness_score=<score>`, target fixtures can score `>=90`, overclaim fixtures block, and the real TASK-131/TASK-128 evidence bundle has a baseline with explicit next blockers
- blockers: none
- spawned follow-ups: TASK-133 for the judge-facing pack, TASK-134 for product-loop hardening
- complexity: M

### Summary

Replace the now-saturated hero-video-only metric with a submission-level
readiness score. The new score should treat the hero MP4 as one proof surface,
not the whole submission: it must reward the actual commission criteria:
technical excellence, novelty, feasibility, adherence to minimal-shot autonomy,
randomized scenario generation, visible navigation evidence, latency/compute
honesty, motivation, and failure-case understanding.

### Scope

- In scope: new submission readiness scorer, product-facing CLI entrypoint,
  score JSON/Markdown output, autoresearch session contract, regression tests,
  and baseline measurement against the TASK-131 artifact set.
- Out of scope: lowering `hero_demo_score` thresholds, closed-loop VLA claims,
  fresh CARLA runtime work, and subjective manual judge scoring.

### Plan

#### Change

Add a mechanical readiness scorer and make it the primary autoresearch metric:

```bash
PYTHONPATH=src python3 -m oodrive score-submission \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --run artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/run_manifest.json \
  --evaluation artifacts/runs/task128-oodrive-live-product/reasoning/evaluations/task128-oodrive-live-alpamayo-fresh-evaluation/policy_evaluation.json \
  --hero-score artifacts/runs/task128-oodrive-live-product/demo-scores/task131-score-gated-hero-v2-score/hero_demo_score.json \
  --overlay-report artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/hero_demo_video.json \
  --metric-only
```

`./autoresearch.sh` should emit:

```text
METRIC submission_readiness_score=<number>
METRIC hero_demo_score=<number>
METRIC challenge_adherence=<number>
METRIC minimal_shot_simulation_environment=<number>
METRIC judge_comprehension_pack=<number>
METRIC operator_reproducibility=<number>
METRIC code_quality=<number>
```

#### Why

TASK-131 proves a 72+ hero artifact, but the commission is not a leaderboard.
Judges want bold ideas and execution: a simulation environment, a navigation
demo, randomized scenario generation, realistic compute/latency constraints,
and a short story that explains motivation and failure understanding. The
current metric cannot see those gaps.

#### Before -> After

- Before: `hero_demo_score=100` can pass even if the submission is confusing,
  not reproducible, or poorly packaged.
- After: `submission_readiness_score>=90` requires a judge-visible artifact set
  with linked evidence, explicit claim boundaries, a runnable product loop, and
  green checks.

#### Touch

- `src/driverx/evaluation/submission_readiness_score.py`
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/scenarios/studio_product_runtime.py`
- `src/driverx/scenarios/studio_product_reports.py`
- `src/driverx/cli_extensions.py`
- `tests/test_submission_readiness_score.py`
- `tests/test_oodrive_cli.py`
- `autoresearch.md`
- `autoresearch.sh`
- `autoresearch.checks.sh`
- `autoresearch.jsonl`
- `tickets/TASK-132/artifacts/*`

#### Inspect

- `src/driverx/evaluation/hero_demo_score.py`
- `src/driverx/scenarios/studio_product_runtime.py`
- `src/driverx/scenarios/studio_product_reports.py`
- `src/driverx/workbench/report.py`
- `src/driverx/workbench/bundle.py`
- `tickets/TASK-131/ticket.md`
- `tickets/TASK-128/ticket.md`
- `docs/prd.md`
- `docs/MEMORY.md`
- `docs/TROUBLES.md`

#### Signature Delta

```python
load_submission_readiness_inputs(
    *,
    db_path: Path,
    run_manifest_path: Path,
    evaluation_path: Path,
    hero_score_path: Path | None,
    overlay_report_path: Path | None,
    pack_manifest_path: Path | None = None,
    checks_report_path: Path | None = None,
) -> SubmissionReadinessInputs

score_submission_readiness(
    inputs: SubmissionReadinessInputs,
) -> SubmissionReadinessResult

run_studio_score_submission(
    db_path: Path,
    *,
    run_manifest_path: Path,
    evaluation_path: Path,
    hero_score_path: Path | None,
    overlay_report_path: Path | None,
    output_root: Path | None,
    run_id: str | None,
    metric_only: bool = False,
) -> StudioCommandResult
```

#### Type Sketch

```python
SubmissionReadinessInputs = {
  "hero_demo_score": float | None,
  "artifact_paths": dict[str, str],
  "command_names": list[str],
  "claim_boundaries": list[str],
  "artifact_paths": dict[str, str],
  "pack_sections": list[str],
  "failure_case_count": int,
  "motivation_present": bool,
  "code_quality_signals": dict[str, int | bool | str],
}

SubmissionReadinessResult = {
  "submission_readiness_score": float,
  "status": "passed" | "blocked",
  "threshold": 90.0,
  "components": {
    "challenge_adherence": float,
    "minimal_shot_simulation_environment": float,
    "navigation_and_risk_evidence": float,
    "reasoning_memory_latency": float,
    "judge_comprehension_pack": float,
    "operator_reproducibility": float,
    "code_quality": float,
  },
  "blockers": list[str],
  "recommendations": list[str],
}
```

#### Typed Flow Example

`TASK-128 DB + TASK-128 run + TASK-128 evaluation + TASK-131 hero score`
-> `load_submission_readiness_inputs`
-> component scores with blockers for missing pack, manual inference, and weak
code quality
-> `submission_readiness_score`
-> `autoresearch.sh`
-> `autoresearch-exec` keeps only changes that increase the score without
breaking guards.

#### Execution Steps

1. Define the component scoring rubric with explicit weights and hard blockers.
2. Implement the scorer as pure evaluation code with fixture-backed tests.
3. Add `oodrive score-submission` and report output under ignored run artifacts.
4. Update `autoresearch.md`, `autoresearch.sh`, `autoresearch.checks.sh`, and
   initialize `autoresearch.jsonl` for the new primary metric.
5. Baseline the current TASK-131 artifact set and record why the score is below
   or above `90`.
6. Add regression fixtures for a weak pack, a target pack, and overclaim
   penalties.
7. Run focused tests, `./autoresearch.sh`, `./autoresearch.checks.sh`, full
   pre-push, and review before completion.

#### Recommendation

Do this first. It prevents the team from optimizing the already-maxed video
metric and gives TASK-133/TASK-134 an objective keep/discard loop.

#### Options Considered

- Keep optimizing `hero_demo_score`: rejected because it already reports
  `100` and cannot see the remaining submission gaps.
- Use a manual reviewer checklist: useful as context, but rejected as the
  primary metric because autoresearch needs a mechanical number.
- Build the submission pack first: tempting, but the pack needs a scorecard so
  iterations optimize for trust instead of decoration.

#### Blast Radius

- New scorer is additive.
- Existing `score-demo` and TASK-131 evidence remain valid.
- Autoresearch primary metric changes from hero-video quality to submission
  readiness; old hero metric remains a secondary signal.

#### Risks

- A scorecard can be gamed; use hard blockers for false closed-loop claims,
  missing artifact paths, and absent product-loop commands.
- Code-quality signals can become arbitrary; start with coarse signals that
  match existing repo checks and large-file warnings.
- `score-submission` may initially fail because TASK-133/TASK-134 outputs do
  not exist; report those as blockers rather than inventing credit.

### Gap Analysis

- Current proof has a strong hero video but does not yet prove commission
  readiness.
- Missing metric coverage: motivation, one-glance judge comprehension,
  failure-case understanding, latency/compute honesty, operator
  reproducibility, and code-quality/review evidence.
- The challenge asks for a simulation environment and a vehicle/robot
  navigation demo; extra points go to realistic compute/latency constraints and
  randomized scenario generation.
- OODrive should compete as a minimal-shot scenario generation/evaluation
  harness, not as an official CARLA leaderboard entrant. The 90-point target is
  an internal commission-readiness score, not a driving-score claim.

### Autoresearch Session Contract

- Goal: raise OODrive from a passing hero demo to a 90-point submission packet.
- Primary metric: `submission_readiness_score` (`0-100`, higher is better).
- Verify: `./autoresearch.sh`
- Guard: `./autoresearch.checks.sh`
- Full gate: `bash scripts/pre_push_check.sh` before ticket completion.
- Max iterations: `12`
- Keep rule: keep changes only when the primary score improves by at least
  `2.0` points or removes a hard blocker without reducing any secondary score.
- Noise policy: deterministic score; rerun any surprising gain above `8.0`
  points before keeping.
- Editable scope: scorer, report/pack builders, product CLI glue, tests, README
  and ticket/docs evidence.
- Read-only: generated MP4s, model outputs, TASK-128/TASK-131 source evidence.
- Off limits: secrets, model weights, dataset caches, threshold lowering, and
  false closed-loop/real-time claims.

### Acceptance Criteria

- [x] AC-1: `oodrive score-submission --help` exists and is product-facing.
- [x] AC-2: `./autoresearch.sh` emits a primary
  `METRIC submission_readiness_score=<number>` line and secondary diagnostic
  metrics.
- [x] AC-3: The current TASK-131/TASK-128 artifact set receives a real baseline
  with explicit blockers or passes `>=90`.
- [x] AC-4: Overclaiming closed-loop or real-time VLA control produces a hard
  blocker.
- [x] AC-5: Unit fixtures prove weak, current, and target submission states.
- [x] AC-6: `autoresearch.md` and `autoresearch.jsonl` let a fresh agent resume
  without chat memory.

### Verification

- PASS: `PYTHONPATH=src python3 -m unittest tests.test_submission_readiness_score tests.test_oodrive_cli` ran 13 tests.
- PASS: `./autoresearch.sh` emitted `METRIC submission_readiness_score=72.3500`.
- PASS: `./autoresearch.checks.sh` ran 22 tests.
- PASS: `bash scripts/pre_push_check.sh` ran 408 tests with 4 skips and passed.
- PASS: implementation review artifact linked below.

### Refs

- Operator-provided SoTA Commission I brief: technical excellence, novelty,
  feasibility, adherence to minimal-shot autonomy, randomized scenario
  generation, realistic compute/latency constraints, 1-5 minute video or slide
  deck, repo, motivation, and failure understanding.

### Evidence

- Plan review:
  `tickets/TASK-132/artifacts/review/task132-134-planning-review.json`
- Implementation review:
  `tickets/TASK-132/artifacts/review/task132-implementation-review.json`
- Autoresearch baseline:
  `autoresearch.jsonl` run `4`, `submission_readiness_score=72.35`
- QA:
  `tickets/TASK-132/artifacts/qa/submission_readiness_qa.md`
- Checks report:
  `tickets/TASK-132/artifacts/qa/checks_report.json`

### Blockers

- None.
