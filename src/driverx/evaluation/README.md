# Evaluation

## Purpose

Compute local proxy metrics and reports over saved run artifacts.

## Public API

- `average_displacement_error(prediction, ground_truth)`
- `evaluate_run_dir(run_dir)`
- `score_hero_demo(inputs, thresholds)`
- `write_hero_demo_score(run_dir, report)`

## Minimal Example

```python
ade = average_displacement_error(prediction, future)
```

```bash
PYTHONPATH=src python3 -m oodrive score-demo \
  --score-input qa/fixtures/hero_demo_score/candidate_demo.json
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_evaluation tests.test_hero_demo_score
```
