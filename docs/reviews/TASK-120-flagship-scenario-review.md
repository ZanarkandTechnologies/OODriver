# TASK-120 Flagship Scenario Review

## Verdict

- Overall score: `4.0 / 5.0`
- Threshold: `4.0`
- Verdict: pass
- Rerun required: no
- Evidence quality: pass
- Integration readiness: pass
- Traceability: pass

## Scope Reviewed

- `src/driverx/scenarios/flagship.py`
- `src/driverx/scenarios/flagship_cli.py`
- `src/driverx/cli_extensions.py`
- `configs/oodrive_flagship_malaysia.yaml`
- `tests/test_oodrive_flagship.py`
- `README.md`
- `tickets/TASK-120/ticket.md`
- `tickets/TASK-120/artifacts/qa/flagship-scenario-qa.md`

## Findings

No blocking findings.

## Rubrics

- Code quality: `4.0 / 5.0`. The builder is dependency-light, deterministic,
  and keeps live CARLA/Alpamayo behavior out of the local contract step. The
  data shape is explicit enough for the H100 tickets.
- Integration readiness: `4.0 / 5.0`. The new CLI is registered through the
  existing dynamic parser, writes artifacts under the standard run root, and
  leaves existing OODrive/studio commands untouched.
- Evidence quality: `4.0 / 5.0`. Focused tests cover scenario complexity,
  command planning, artifact writing, and CLI invocation. The full pre-push
  gate passed after implementation.

## Notes

- TASK-120 intentionally does not claim live closed-loop Alpamayo control.
- The next proof boundary is TASK-121: live CARLA checkpoint capture on the
  H100/Kasm VM.

## Verification

```bash
PYTHONPATH=src python3 -m unittest tests.test_oodrive_flagship
PYTHONPATH=src python3 -m unittest tests.test_oodrive_cli tests.test_oodrive_flagship tests.test_scripted_ood_campaign tests.test_carla_ood_demo
PYTHONPATH=src python3 -m driverx build-flagship-oodrive-scenario --config configs/oodrive_flagship_malaysia.yaml --output-root artifacts/runs --run-id flagship-malaysia-smoke
bash scripts/pre_push_check.sh
```

Full gate result: `395` tests passed, `3` skipped.
