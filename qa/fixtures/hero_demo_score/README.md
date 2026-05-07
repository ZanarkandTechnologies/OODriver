# Hero Demo Score Fixtures

Purpose: tiny dependency-light fixtures for planning and validating the
`hero_demo_score` autoresearch loop before the full `oodrive score-demo`
command exists.

Public entrypoint:

```bash
python3 qa/fixtures/hero_demo_score/score_fixture.py \
  qa/fixtures/hero_demo_score/candidate_demo.json
```

The fixture scorer intentionally mirrors the planned TASK-130 metric shape:
duration, motion, visible OOD objects, risk events, frame/time coverage,
Alpamayo reasoning, RAG memory callouts, and hard penalties for videos that are
slow, off-road, or missing evidence. It is not the final product scorer.

How to test:

```bash
./autoresearch.sh
./autoresearch.checks.sh
```
