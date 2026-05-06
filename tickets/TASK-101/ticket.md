# TASK-101: Submission Evaluation Matrix And Scenario Selection

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-097, TASK-098, TASK-100
- location: `src/driverx/scenarios`, `src/driverx/pipeline`, `tickets/TASK-101/artifacts`
- enter when: current RunPod CARLA and Alpamayo proof exists but final submission still lacks a crisp evaluation matrix
- leave when: a short list of judge-facing scenarios is selected with explicit roles, evidence status, model/RAG status, and remaining proof gaps
- blockers: none
- spawned follow-ups: TASK-102, TASK-103, TASK-104, TASK-105, TASK-106
- complexity: S
- assignee: generalPurpose

### Summary

Create the final two-day execution board. The goal is to stop treating every
technical possibility as equal and select the exact scenarios that prove the
submission thesis: generated OOD simulator plus frozen VLA reasoning plus
retrieval memory.

### Scope

- In scope: select 6-10 cases across Fail2Drive seeds, generated environment
  variants, regional behavior variants, and the current RunPod hero; classify
  each as hero/support/failure/backup; define which cases need Alpamayo
  baseline, Alpamayo+memory, CARLA video, and RAG comparison.
- Out of scope: running CARLA, running Alpamayo, generating new videos, or
  changing simulator code.

### Plan

#### Change

Add a selection/evaluation matrix artifact that turns the existing catalog into
a final submission queue.

#### Why

The highest submission risk is not missing infrastructure now; it is diffuse
focus. The matrix makes every later ticket answer one of three questions:
generated scenario, model reaction, or memory improvement.

#### Before -> After

- Before: one hero video and one Alpamayo proof exist, but the final batch is
  implicit.
- After: the repo names the exact cases to run and why each case helps the
  SoTA brief.

#### Touch

- `src/driverx/scenarios/catalog.py`: reuse existing catalog records and
  promotion fields.
- `src/driverx/pipeline/policy_evaluation_campaign.py`: reuse policy evidence
  statuses and quality-blocker fields.
- `tickets/TASK-101/artifacts/submission_eval_matrix.json`: selected matrix.
- `tickets/TASK-101/artifacts/submission_eval_matrix.md`: human report.

#### Inspect

- `tickets/archive/TASK-097/artifacts/task97-scenario-catalog-hero-v3/scenario_catalog.json`
- `tickets/archive/TASK-097/artifacts/task97-submission-browser-runpod-v4/scenario_browser.html`
- `tickets/archive/TASK-100/artifacts/task100-hero-alpamayo-policy/alpamayo_policy_decision.json`
- current `src/driverx/scenarios/catalog.py` filters and quality fields.

#### Signature Delta

```python
src/driverx/pipeline/submission_eval_matrix.py /
  build_submission_eval_matrix(catalog_paths, evidence_paths, output_dir, limit): dict[str, Any]

src/driverx/pipeline/submission_eval_matrix_cli.py /
  register_submission_eval_matrix_parser(subparsers): None
```

#### Type Sketch

```python
EvalMatrixCase = {
  "case_id": str,
  "scenario_id": str,
  "role": "hero" | "support" | "failure" | "backup",
  "scenario_family": str,
  "behavior_id": str | None,
  "evidence": {
    "quality_status": str,
    "video_path": str | None,
    "tracks_path": str | None,
    "alpamayo_baseline": str | None,
    "alpamayo_memory": str | None,
    "rag_comparison": str | None,
  },
  "needed_next": list[str],
  "submission_claim": str,
}
```

#### Typed Flow Example

`scenario_catalog.json + TASK-100 policy decision`
-> `EvalMatrixCase(role="hero", needed_next=["memory_decision", "better_video_optional"])`
-> `submission_eval_matrix.md` lists the first implementation target for
TASK-102 through TASK-104.

#### Execution Steps

1. Load catalog records and known TASK-100/TASK-097 evidence.
2. Rank cases by quality passed, video present, model reasoning present,
   behavioral diversity, and usefulness for failure analysis.
3. Assign roles and `needed_next` fields.
4. Write JSON and Markdown.
5. Add CLI and tests for ranking, missing artifacts, and role assignment.

#### Recommendation

Do this first. It is the cheapest way to turn the remaining two days into a
focused sprint.

#### Options Considered

- Polish the existing browser only: fast, but does not answer what to run next.
- Run more CARLA cases immediately: tempting, but risks creating random
  evidence that does not map to the final story.
- Recommended: build the matrix first, then only run cases that fill visible
  matrix gaps.

#### Blast Radius

Low. Adds a planning/evidence pipeline and CLI; does not affect existing
simulation runs.

#### Risks

- Stale catalog paths can make the matrix look weaker than reality. Mitigate by
  accepting explicit evidence paths in addition to catalog paths.

### Gap Analysis

Current state proves one hero and one open-loop Alpamayo reaction. The
production-grade submission needs a clear panel of scenarios showing breadth:
regional behavior, object novelty, roadwork/environment novelty, failure case,
and model/RAG comparison. This ticket defines that panel.

### Acceptance Criteria

- [ ] AC-1: Matrix names at least 6 candidate scenarios and exactly 1-2 hero
  candidates.
- [ ] AC-2: Each case records quality/video/tracks/Alpamayo/RAG evidence
  status.
- [ ] AC-3: Each case has a concrete `needed_next` field used by TASK-102
  through TASK-104.
- [ ] AC-4: Markdown report clearly explains why the selected cases satisfy the
  SoTA brief.

### Verification

- Focused unit tests for ranking, missing evidence, and role assignment.
- `PYTHONPATH=src python3 -m driverx build-submission-eval-matrix ...`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Inputs available: current local artifacts, catalog, TASK-100 Alpamayo proof.
- Human gates: none.
- Compute: local only.
- Stop condition: matrix written and later tickets have concrete targets.

### Evidence

- `tickets/TASK-101/artifacts/submission_eval_matrix.json`
- `tickets/TASK-101/artifacts/submission_eval_matrix.md`
- `tickets/TASK-101/artifacts/submission-eval-matrix/submission_eval_matrix.json`
- `tickets/TASK-101/artifacts/submission-eval-matrix/submission_eval_matrix.md`
- Batch plan review:
  `tickets/TASK-101/artifacts/review/task101-106-plan-review.json`
- focused test output

### Blockers

- None.
