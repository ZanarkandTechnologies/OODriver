# TASK-133: Judge-Intuitive OODrive Submission Pack

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-131, TASK-132
- location: `src/driverx/pipeline`, `src/driverx/scenarios`, `src/driverx/workbench`, `README.md`, `tickets/TASK-133/artifacts`
- enter when: a hero video exists but the submission still requires too much project context to understand what OODrive uniquely contributes
- leave when: a local submission pack makes the OODrive loop understandable in under two minutes and passes the TASK-132 readiness score target
- blockers: none
- spawned follow-ups: none
- complexity: M

### Summary

Build the judge-facing packet around the product loop, not around raw simulator
media. The pack should show, in one glance and one short read, how OODrive turns
a minimal prompt into a CARLA OOD scenario, live placement evidence, sampled
Alpamayo reasoning, RAG/memory callouts, and a scored demo artifact.

### Scope

- In scope: a concise local HTML/Markdown submission pack, claim-to-evidence
  matrix, hero video reference, artifact manifest, source command transcript,
  uniqueness narrative, and README/final demo references after score passes.
- Out of scope: new simulator rendering, new model inference, public hosting,
  and closed-loop claims.

### Plan

#### Change

Add a first-class pack builder around the existing evidence:

```bash
PYTHONPATH=src python3 -m oodrive export-submission \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --run artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/run_manifest.json \
  --evaluation artifacts/runs/task128-oodrive-live-product/reasoning/evaluations/task128-oodrive-live-alpamayo-fresh-evaluation/policy_evaluation.json \
  --hero-video artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/oodrive_hero_demo.mp4 \
  --hero-score artifacts/runs/task128-oodrive-live-product/demo-scores/task131-score-gated-hero-v2-score/hero_demo_score.json \
  --run-id task133-submission-pack-v1
```

Output a pack directory containing:

- `index.html`
- `README.md`
- `submission_manifest.json`
- `claim_matrix.json`
- `commands.sh`
- `artifact_inventory.json`
- `scorecard.md`

#### Why

The current artifact can score well mechanically, but a skeptical human still
has to infer why it matters. A 90th-percentile submission needs to be instantly
legible: what was generated, what was live CARLA evidence, where reasoning came
from, what is unique, and what is honestly not claimed.

#### Before -> After

- Before: the user has to read tickets, remember remote paths, and mentally
  connect DB/run/evaluation/video artifacts.
- After: the pack opens with the full OODrive loop, then links every claim to a
  concrete local or public artifact.

#### Touch

- `src/driverx/pipeline/submission_demo_pack.py`
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/scenarios/studio_product_runtime.py`
- `src/driverx/scenarios/studio_product_reports.py`
- `src/driverx/workbench/report.py`
- `src/driverx/workbench/types.py`
- `tests/test_submission_demo_pack.py`
- `tests/test_oodrive_cli.py`
- `README.md`
- `docs/HISTORY.md`
- `tickets/TASK-133/artifacts/*`

#### Inspect

- `tickets/TASK-131/artifacts/qa/score_gated_hero_demo_qa.md`
- `tickets/TASK-128/ticket.md`
- `docs/prd.md`
- `src/driverx/workbench/bundle.py`
- `src/driverx/workbench/report.py`
- `src/driverx/scenarios/studio_product_reports.py`

#### Signature Delta

```python
build_submission_story_pack(
    *,
    db_path: Path,
    run_manifest_path: Path,
    evaluation_path: Path,
    hero_video_path: Path,
    hero_score_path: Path,
    readiness_score_path: Path | None,
    output_root: Path,
    run_id: str,
) -> SubmissionStoryPack

render_submission_pack_markdown(pack: SubmissionStoryPack) -> str

render_submission_pack_html(pack: SubmissionStoryPack) -> str
```

#### Type Sketch

```python
SubmissionStoryPack = {
  "pack_id": str,
  "product_name": "OODrive",
  "headline_claim": str,
  "loop_steps": list[{"name": str, "command": str, "artifact": str}],
  "claim_matrix": list[{"claim": str, "status": str, "evidence": list[str]}],
  "unique_contributions": list[str],
  "hero_media": {"local_file": str, "duration_s": float, "score": float},
  "limitations": list[str],
  "readiness_score": float | None,
}
```

#### Typed Flow Example

`TASK-128 evidence + TASK-131 hero MP4 + TASK-132 score`
-> `build_submission_story_pack`
-> claim matrix and artifact inventory
-> `index.html` for judges
-> `oodrive score-submission`
-> pass only if the pack explains the loop and preserves claim boundaries.

#### Execution Steps

1. Define the pack narrative order: prompt, generated scenario, live placement,
   sampled reasoning, RAG/memory evidence, scored artifact, limitations.
2. Extract existing artifact metadata and command lineage from DB/run/eval/score
   files.
3. Render Markdown first, then a simple static HTML page without external
   dependencies.
4. Add claim-to-evidence rows for every strong statement and every limitation.
5. Add tests for pack manifest completeness and claim-boundary preservation.
6. Score the pack with TASK-132 and iterate until the readiness score is at
   least `90`.
7. Update README and HISTORY only after the score passes.

#### Recommendation

Build this second, immediately after TASK-132. It turns the existing proof into
something a judge can understand without reading the entire ticket archive.

#### Options Considered

- More video polish: rejected as primary work because video quality is already
  mechanically maxed.
- A long paper-style report: too slow to parse and less useful for a demo judge.
- Static HTML plus Markdown: selected because it is local, durable, reviewable,
  and easy to score mechanically.

#### Blast Radius

- Additive pack output under ignored artifacts and ticket evidence.
- README/demo references change only after a passing pack exists.
- No product claim boundary changes.

#### Risks

- The pack can become marketing fluff; require every claim to map to an
  artifact path or an explicit limitation.
- Local-only media can be invisible outside the machine; inventory must label
  `local_file`, `public_url`, `remote_only`, and `missing`.
- TASK-102 source video is visually strong but not perfect provenance; the pack
  must state how TASK-128 evidence and TASK-102 source are combined.

### Gap Analysis

- Current proof is not self-explanatory: it requires ticket context, command
  memory, and local path knowledge.
- The first viewport does not yet answer "what is OODrive?" in a way a judge
  can repeat back.
- The contribution is unique when framed as a scenario generator/evaluation
  harness with reasoning and memory overlays; it is weaker when framed as
  another CARLA driving agent.

### Acceptance Criteria

- [x] AC-1: `oodrive export-submission --help` exists.
- [x] AC-2: A pack directory contains `index.html`, `README.md`,
  `submission_manifest.json`, `claim_matrix.json`, `commands.sh`,
  `artifact_inventory.json`, and `scorecard.md`.
- [x] AC-3: The pack includes the exact claim labels
  `closed_loop_vla_control=false`, `real_time_vla_control=false`,
  `sampled_open_loop_reasoning=true`, and
  `time_warped_offline_demo=true`.
- [x] AC-4: A judge can identify the product loop, unique contribution, and
  limitations from the first screen and the first two minutes of reading.
- [x] AC-5: `oodrive score-submission` reports
  `submission_readiness_score >= 90` for the pack.

### Verification

- PASS: `PYTHONPATH=src python3 -m unittest tests.test_submission_story_pack tests.test_submission_readiness_score tests.test_oodrive_cli` ran 15 tests.
- PASS: `PYTHONPATH=src python3 -m oodrive export-submission ...` generated the pack files.
- PASS: `PYTHONPATH=src python3 -m oodrive score-submission ...` reported `submission_readiness_score=96.35`, status `passed`.
- PASS: `./autoresearch.sh` emitted `METRIC submission_readiness_score=96.3500`.
- PASS: `bash scripts/pre_push_check.sh` ran 410 tests with 4 skips and passed.
- PASS: implementation review artifact linked below.

### Evidence

- Plan review:
  `tickets/TASK-132/artifacts/review/task132-134-planning-review.json`
- QA:
  `tickets/TASK-133/artifacts/qa/submission_pack_qa.md`
- Review:
  `tickets/TASK-133/artifacts/review/task133-implementation-review.json`
- Pack index:
  `artifacts/runs/task128-oodrive-live-product/submission-packs/task133-submission-pack-v1/index.html`
- Pack manifest:
  `artifacts/runs/task128-oodrive-live-product/submission-packs/task133-submission-pack-v1/submission_manifest.json`
- Score report:
  `artifacts/runs/task128-oodrive-live-product/submission-scores/task133-submission-pack-v1-score/submission_readiness_score.md`

### Blockers

- None.
