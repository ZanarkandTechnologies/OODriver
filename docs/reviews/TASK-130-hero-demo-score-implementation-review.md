# TASK-130 Implementation Review

## Verdict

- Overall score: `4.1 / 5`
- Threshold: `4.0`
- Verdict: `pass`
- Rerun required: `false`
- Work type: code, product CLI, evidence, autoresearch

## Scope Reviewed

- Ticket: `tickets/TASK-130/ticket.md`
- Product CLI: `src/driverx/scenarios/studio_product_cli.py`
- Product runtime: `src/driverx/scenarios/studio_product_runtime.py`
- Scorer: `src/driverx/evaluation/hero_demo_score.py`
- Overlay renderer: `src/driverx/simulators/reasoning_timeline_overlay.py`
- Tests: `tests/test_hero_demo_score.py`, `tests/test_oodrive_cli.py`
- Autoresearch: `autoresearch.md`, `autoresearch.sh`,
  `autoresearch.checks.sh`, `autoresearch.jsonl`
- QA: `tickets/TASK-130/artifacts/qa/hero-demo-score-qa.md`

## Rubric Scores

| Rubric | Score | Threshold | Pass |
| --- | ---: | ---: | --- |
| code-quality | 4.0 | 4.0 | yes |
| evidence-quality | 4.2 | 4.0 | yes |
| integration-readiness | 4.1 | 4.0 | yes |

## Findings

- No blocking findings.
- Minor caveat: `hero_demo_score.py` and `studio_product_runtime.py` are now
  large enough to trigger the repo's warning threshold. This is not a hard gate
  failure, but a follow-up cleanup should split scorer loading/writing and
  product demo orchestration if this surface grows again.
- Minor caveat: the full pre-push path skips the demo-video render test when
  Pillow is unavailable. The command still has direct fixture coverage when
  Pillow is installed, and score-demo remains dependency-light.

## Evidence

- `./autoresearch.sh`: `METRIC hero_demo_score=30.4889`
- `./autoresearch.checks.sh`: 18 tests pass
- Focused tests: `tests.test_hero_demo_score tests.test_oodrive_cli` pass
- Full gate: `bash scripts/pre_push_check.sh` passes with 404 tests, 4 skipped
- Weak score artifact:
  `tickets/TASK-130/artifacts/qa/weak-fixture-score/hero_demo_score.json`
- Target score artifact:
  `tickets/TASK-130/artifacts/qa/target-fixture-score/hero_demo_score.json`

## Claim Check

The implementation does not claim that the current TASK-128 live video became
good. It claims the opposite in a useful way: the weak video shape is now
mechanically rejected, and future hero videos must show frame/time, VLA
reasoning, RAG memory, risk, motion, duration, and claim boundaries before
promotion.

## Next Action

Use `oodrive demo-video` on the best live CARLA MP4, then run
`oodrive score-demo` with the generated overlay report. The next work should
optimize the actual live artifact until it clears the `72` score threshold.
