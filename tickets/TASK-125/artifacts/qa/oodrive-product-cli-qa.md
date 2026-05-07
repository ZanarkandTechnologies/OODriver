# TASK-125 QA: OODrive Product CLI And AI Generator

Captured: 2026-05-07 18:08 +0800

## Commands

```bash
PYTHONPATH=src python3 -m unittest tests.test_oodrive_cli
PYTHONPATH=src python3 -m oodrive --help
PYTHONPATH=src python3 -m driverx oodrive --help
PYTHONPATH=src python3 -m oodrive ai-generate \
  --prompt "Malaysian wet night roadwork chaos with scooter filtering" \
  --output-root artifacts/runs \
  --run-id oodrive-ai-smoke \
  --count 4 \
  --seed 11 \
  --compile \
  --queue
PYTHONPATH=src python3 -m oodrive quickstart \
  --prompt "Malaysian wet roadwork: motorcycle filtering and unsignaled lorry brake" \
  --output-root artifacts/runs \
  --run-id oodrive-product-smoke \
  --count 2 \
  --seed 19
PYTHONPATH=src python3 -m compileall -q src tests
bash scripts/pre_push_check.sh
```

## Results

- Focused unit tests: PASS, 6 tests.
- Product help smoke: PASS, `oodrive` lists `ai-generate`, `quickstart`, and
  the DB lifecycle commands.
- Compatibility help smoke: PASS, `python -m driverx oodrive --help` still
  works.
- AI generation smoke: PASS.
  - DB: `artifacts/runs/oodrive-ai-smoke/scenario_studio_db.json`
  - Generated briefs: 4
  - Compiled candidates: 4
  - Queued scenarios: 4
  - Provider: `codex-template`
  - Claim boundary: `scenario_generation_ai_provider=codex-template`
  - Next commands use `PYTHONPATH=src python3 -m oodrive`.
- Product quickstart smoke: PASS with expected partial evaluation boundary.
  - DB: `artifacts/runs/oodrive-product-smoke/scenario_studio_db.json`
  - Export pack: `artifacts/runs/oodrive-product-smoke/exports/oodrive-product-smoke-export/scenario_generator_cli_pack.json`
  - HTML pack: `artifacts/runs/oodrive-product-smoke/exports/oodrive-product-smoke-export/scenario_generator_cli_pack.html`
  - Expected blocker: no Alpamayo prediction JSON supplied for dependency-free
    local smoke.
- Compileall: PASS.
- Full pre-push gate: PASS, 398 tests, 3 skipped.

## Edge Checks

- `ai-generate --queue` without `--compile` now fails before writing a DB.
- Generated next commands were scanned under the smoke artifact roots and did
  not contain `driverx oodrive`.

## Verdict

PASS. The CLI is usable as `python -m oodrive`, AI-assisted DB generation works
without CARLA/GPU, and legacy DriverX command paths remain compatible.
