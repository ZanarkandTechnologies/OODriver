# Review: TASK-126/TASK-127 OODrive Product Loop

## Scope

- Tickets: `tickets/TASK-126/ticket.md`, `tickets/TASK-127/ticket.md`
- Code:
  - `src/driverx/scenarios/studio_runtime.py`
  - `src/driverx/scenarios/studio_product_runtime.py`
  - `src/driverx/scenarios/studio_product_cli.py`
  - `tests/test_oodrive_cli.py`
- Docs/evidence:
  - `README.md`
  - `AGENTS.md`
  - `docs/HISTORY.md`
  - `docs/MEMORY.md`
  - `blockers.md`
  - `tickets/TASK-126/artifacts/qa/generate-placement-qa.md`
  - `tickets/TASK-127/artifacts/qa/place-reason-qa.md`

## Rubrics Used

- `code-quality`
- `integration-readiness`
- `evidence-quality`
- `user-intent-satisfaction`

## Verdict

- Overall score: `4.0 / 5.0`
- Threshold: `4.0`
- Verdict: `pass`
- Rerun required: `false`

## Findings

No blocking findings.

## Scores

| rubric | score | threshold | pass | notes |
| --- | ---: | ---: | --- | --- |
| code-quality | 4.0 | 4.0 | yes | Runtime glue was split out after the first pre-push failure, keeping `studio_product.py` under the line-count hard gate and preserving clear product/runtime seams. |
| integration-readiness | 4.0 | 4.0 | yes | `oodrive generate`, `place`, and `reason` are wired through the product parser and reuse existing DB, asset, behavior, CARLA, evaluation, and replay contracts. Live CARLA remains environment-dependent but now records an actionable blocker. |
| evidence-quality | 4.0 | 4.0 | yes | Focused tests, integration-adjacent tests, smoke artifacts, and the full pre-push gate prove the local product loop. Evidence clearly distinguishes dry-run/cached proof from live placement. |
| user-intent-satisfaction | 4.0 | 4.0 | yes | The CLI now matches the requested product story in shape: prompt to placement plan to placement run to Alpamayo reasoning artifact. The caveat is that this pass did not prove live object spawning because Docker could not reach CARLA. |

## Checked

- `PYTHONPATH=src python3 -m unittest tests.test_oodrive_cli`
- `PYTHONPATH=src python3 -m unittest tests.test_oodrive_cli tests.test_carla_ood_demo tests.test_alpamayo_ood_package tests.test_alpamayo_ood_evaluation`
- `PYTHONPATH=src python3 -m oodrive --help`
- `PYTHONPATH=src python3 -m oodrive generate ...`
- `PYTHONPATH=src python3 -m oodrive place ...`
- `PYTHONPATH=src python3 -m oodrive reason ...`
- `scripts/run_carla_client_docker.sh python -m oodrive place ... --live`
- `bash scripts/pre_push_check.sh`

## Residual Risk

The remaining product-story gap is live environment proof, not local CLI
plumbing: the `--live` command reached the CARLA OOD demo runner but timed out
against `host.docker.internal:2000`. Next high-signal pass should run the same
command on a reachable CARLA host and then feed the resulting RGB/tracks into
live Alpamayo inference.
