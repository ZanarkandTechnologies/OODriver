# Repo Tidy Review

Date: 2026-05-09 06:41 +0800

## Scope

Changed surfaces reviewed:

- `README.md`
- `docs/runpod-kasm-quickstart.md`
- `docs/archive/`
- `docs/specs/README.md`
- `PROJECT_RULES.md`
- `ARCHITECTURE.md`
- `scripts/README.md`
- `scripts/archive/simlingo/`
- SimLingo compatibility wrappers in `scripts/`
- submission CLI progress defaults
- `blockers.md`
- `tests/test_carla_docker_scripts.py`

Neighboring surfaces checked:

- `src/oodrive/cli.py`
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/scenarios/studio_product_closed_loop_cli.py`
- `src/driverx/remote/README.md`
- `tests/README.md`

## Verdict

Overall score: 4.0 / 5.0

Verdict: pass

Hard-gate failures: none

## Rubric Scores

- User intent satisfaction: 4.0 / 5.0
- Debloatability: 4.0 / 5.0
- Integration readiness: 4.0 / 5.0
- Evidence quality: 4.0 / 5.0

## Findings

No blocking findings.

Minor caveats:

- Historical review files still mention old paths such as `docs/progress.md`.
  They are archived review records, so this is acceptable, but future doc
  gardening should avoid treating `docs/reviews/` as the current reader path.
- SimLingo/CarLLaVA implementation modules remain in `src/driverx/simulators`
  because tests and old reports still cover them. The cleanup moved the remote
  scripts out of the primary scripts surface and labels the code as support
  track rather than deleting a still-tested adapter.

## Evidence

Commands run:

```bash
PYTHONPATH=src python3 -m oodrive --help
bash scripts/sync_runpod_proxy_workspace.sh --help
python3 -m compileall -q src tests
PYTHONPATH=src python3 -m unittest tests.test_carla_docker_scripts tests.test_submission_demo_pack tests.test_submission_dossier
PYTHONPATH=src python3 -m oodrive quickstart --prompt "wet roadwork scooter" --run-id repo-tidy-smoke --output-root artifacts/tmp --count 1
```

Results:

- OODrive help rendered successfully.
- RunPod proxy sync help rendered successfully.
- Compile check passed.
- 21 targeted tests passed.
- OODrive quickstart completed with `run_status=passed`; Alpamayo evaluation was
  correctly marked blocked because no prediction JSON was supplied.

## Next Action

Ready to share as a cleaner repo surface. Do not promote the archived SimLingo
scripts back into the main README unless that lane becomes active again.
