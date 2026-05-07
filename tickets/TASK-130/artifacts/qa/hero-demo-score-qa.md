# TASK-130 QA: Hero Demo Score And Reasoning Video Contract

## Verdict

PASS for local implementation proof. The production OODrive commands exist and
the fixture contract now distinguishes the current weak video shape from the
target judge-facing demo shape.

## Commands

```bash
./autoresearch.sh
./autoresearch.checks.sh
PYTHONPATH=src python3 -m unittest tests.test_hero_demo_score tests.test_oodrive_cli
bash scripts/pre_push_check.sh
```

## Evidence

- Weak fixture score:
  `tickets/TASK-130/artifacts/qa/weak-fixture-score/hero_demo_score.json`
- Target fixture score:
  `tickets/TASK-130/artifacts/qa/target-fixture-score/hero_demo_score.json`
- Weak fixture result: `blocked`, score `30.4889 / 100`
- Target fixture result: `passed`, score `100.0 / 100`
- `oodrive demo-video` smoke is covered by
  `tests.test_hero_demo_score.HeroDemoScoreTest.test_demo_video_renders_frame_time_reasoning_and_rag_overlay`.

## Acceptance Reconciliation

- AC-1: PASS. `oodrive score-demo --help` and `oodrive demo-video --help` are
  registered.
- AC-2: PASS. Weak fixture blocks with specific blockers for speed, risk,
  reasoning, RAG, and frame/time coverage.
- AC-3: PASS. Target fixture scores above threshold.
- AC-4: PASS. Score reports include duration, motion, visible OOD count, risk,
  reasoning, RAG, Alpamayo evidence, frame/time coverage, penalties, and claim
  boundaries.
- AC-5: PASS. Demo-video smoke renders a frame/time + reasoning/RAG overlay
  from synthetic MP4/DB/run/evaluation fixtures without CARLA.
- AC-6: PASS. `./autoresearch.sh` emits
  `METRIC hero_demo_score=30.4889`.
- AC-7: PASS. README now documents `score-demo` as the promotion gate rather
  than accepting raw MP4 presence.

## Claim Boundary

This QA proves local scoring and overlay plumbing. It does not claim the current
TASK-128 live video became good; it proves the weak shape is rejected and gives
the next live run a mechanical target.
