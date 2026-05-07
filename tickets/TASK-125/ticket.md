# TASK-125: OODrive Product CLI And AI Scenario Generator

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-114, TASK-120
- location: `src/oodrive`, `src/driverx/scenarios`, `pyproject.toml`, `docs`, `tests`
- enter when: OODrive exists as `driverx oodrive` but the user-facing product should no longer expose DriverX as the command prefix
- leave when: `python -m oodrive ...` and installed `oodrive` script run the OODrive loop, `oodrive ai-generate` writes scenario briefs into the DB, docs use the product command, and QA proves the loop usable without CARLA
- blockers: none
- spawned follow-ups: none
- complexity: M

### Summary

Make OODrive the product-facing command surface and add a first AI-assisted
scenario generator command. `driverx` remains an internal package and backward
compatibility path, but operator-facing docs, generated next commands, and smoke
commands should use `oodrive ...`.

### Scope

- In scope: top-level `oodrive` Python module/console script, product parser,
  `ai-generate` command, DB-backed generated brief records, command transcript
  cleanup, docs, focused tests, QA evidence, review.
- Out of scope: network LLM API calls, live CARLA execution, Alpamayo inference,
  a full web app. Provider-backed generation can be added after this command
  has a stable DB contract.

### Plan

#### Change

Add a top-level OODrive command wrapper and an AI-generation command that turns
one prompt into several structured scenario briefs, writes them into
`scenario_studio_db.json`, and optionally compiles/queues them.

#### Why

The product contribution should read as OODrive, not as an internal DriverX
subcommand. We also need the AI-powered loop to be explicit in the artifact
database instead of relying on chat-only Codex behavior.

#### Before -> After

- Before: canonical UX is `PYTHONPATH=src python3 -m driverx oodrive ...`; AI
  scenario creation is external to the CLI and mostly implicit.
- After: canonical UX is `PYTHONPATH=src python3 -m oodrive ...` or installed
  `oodrive ...`; AI-assisted generation is `oodrive ai-generate ...` and the DB
  records provider, generated prompt variants, tags, region, and next commands.

#### Touch

- `pyproject.toml`
- `src/oodrive/__init__.py`
- `src/oodrive/__main__.py`
- `src/oodrive/cli.py`
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/scenarios/studio_product.py`
- `src/driverx/scenarios/studio_product_helpers.py`
- `src/driverx/scenarios/queue.py`
- `README.md`
- `src/driverx/scenarios/README.md`
- `docs/specs/scenario-generator-cli-v1.md`
- `docs/MEMORY.md`
- `docs/HISTORY.md`
- `tests/test_oodrive_cli.py`

#### Inspect

- `docs/prd.md`
- `docs/specs/scenario-generator-cli-v1.md`
- `docs/MEMORY.md`
- `docs/TROUBLES.md`
- `src/driverx/cli.py`
- `src/driverx/scenarios/studio_product.py`
- `src/driverx/scenarios/studio_product_reports.py`

#### Signature Delta

```python
src/oodrive/cli.py / main(argv: Sequence[str] | None = None): int
src/driverx/scenarios/studio_product_cli.py / build_oodrive_parser(): argparse.ArgumentParser
src/driverx/scenarios/studio_product.py / run_studio_ai_generate(...): StudioCommandResult
src/driverx/scenarios/studio_product.py / generate_ai_scenario_briefs(prompt, count, provider, seed): list[dict[str, Any]]
```

CLI:

```bash
PYTHONPATH=src python3 -m oodrive ai-generate \
  --prompt "Malaysian wet night roadwork chaos" \
  --run-id oodrive-ai-smoke \
  --count 4 \
  --compile \
  --queue
```

#### Type Sketch

```python
GeneratedScenarioBrief = {
  "brief_id": str,
  "prompt": str,
  "author": "provider",
  "provider": "codex-template",
  "source_prompt": str,
  "region": str | None,
  "requested_tags": list[str],
  "target_policy_pressure": str | None,
  "generation_notes": list[str],
}

AiGenerateSummary = {
  "generated_count": int,
  "provider": str,
  "db_path": str,
  "compiled": bool,
  "queued": bool,
  "candidate_count": int,
  "queue_count": int,
}
```

#### Typed Flow Example

`oodrive ai-generate --prompt "Malaysian wet roadwork..." --count 4 --compile --queue`
-> load or create `scenario_studio_db.json`
-> append four `author=provider` briefs with stressor tags
-> `run_studio_compile(...)` creates deterministic candidates
-> `run_studio_queue(...)` selects top records
-> stdout returns artifact paths and product next commands using `oodrive`.

#### Execution Steps

1. Add a product parser that exposes the existing OODrive subcommands directly.
2. Add the `src/oodrive` module and console script mapping.
3. Add deterministic AI-brief generation with provider metadata and DB command
   logging.
4. Rewrite generated next commands to prefer `python3 -m oodrive`.
5. Update docs/spec/memory so `driverx` is internal compatibility, not the
   canonical product UX.
6. Add focused unit tests and CLI smoke tests for `python -m oodrive`.
7. Write QA and review evidence.
8. Run focused tests, compileall, and full pre-push gate.

#### Recommendation

Keep `driverx` as the internal package/legacy command, but make `oodrive` the
only product-facing command in new docs and generated next commands.

#### Options Considered

- Rename the whole Python package from `driverx` to `oodrive`: cleaner branding,
  but high churn across hundreds of imports and not worth the regression risk.
- Keep `driverx oodrive`: stable, but confusing product UX and contradicts the
  OODrive name.
- Recommended: add a top-level `oodrive` module/script and keep DriverX as
  compatibility internals.

#### Blast Radius

Medium. CLI docs, generated next commands, and tests change, but runtime
modules keep existing imports.

#### Risks

- AI generator may be mistaken for a network LLM. Mitigate with provider/claim
  boundaries: default provider is deterministic `codex-template`; network
  providers are future work.
- Existing scripts may expect `driverx oodrive`. Mitigate by keeping all legacy
  aliases working.

### Acceptance Criteria

- [x] AC-1: `PYTHONPATH=src python3 -m oodrive --help` and
  `PYTHONPATH=src python3 -m oodrive quickstart ...` work.
- [x] AC-2: `oodrive ai-generate` creates/updates a Studio DB with generated
  provider-authored briefs and optional compile/queue artifacts.
- [x] AC-3: New generated next commands use `PYTHONPATH=src python3 -m oodrive`
  while `python -m driverx oodrive` remains compatible.
- [x] AC-4: Docs/spec/memory reflect OODrive as the product CLI and DriverX as
  internal compatibility.

### Agent Contract
- Open: `src/driverx/scenarios/studio_product_cli.py`, `src/oodrive/cli.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_oodrive_cli`
- Stabilize: keep generation deterministic and dependency-free
- Inspect: `artifacts/runs/oodrive-ai-smoke/scenario_studio_db.json`
- Key screens/states: generated CLI evidence pack HTML
- QA cookbook: run `oodrive --help`, `oodrive ai-generate --compile --queue`,
  `oodrive quickstart`, and compatibility `driverx oodrive --help`
- Taste refs: product-facing commands should say OODrive, not DriverX
- Expected artifacts: DB/report/export paths plus QA/review docs
- Delegate with: TASK-125 ticket and OODrive CLI tests

### Evidence Checklist
- [x] Help smoke
- [x] AI-generate smoke
- [x] Quickstart smoke
- [x] Unit tests
- [x] Pre-push check
- [x] QA report linked
- [x] Review linked

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_oodrive_cli`
- `PYTHONPATH=src python3 -m oodrive --help`
- `PYTHONPATH=src python3 -m oodrive ai-generate --prompt "Malaysian wet night roadwork chaos" --run-id oodrive-ai-smoke --count 4 --compile --queue`
- `PYTHONPATH=src python3 -m oodrive quickstart --prompt "Malaysian wet roadwork: motorcycle filtering and unsignaled lorry brake" --run-id oodrive-product-smoke --count 2 --seed 19`
- `PYTHONPATH=src python3 -m driverx oodrive --help`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Inputs: no secrets, no GPU, no CARLA.
- Compute: local Python only.
- Human gates: none.
- External side effects: none beyond local ignored artifacts and final git push.

### Evidence

- Product help: `PYTHONPATH=src python3 -m oodrive --help`.
- Compatibility help: `PYTHONPATH=src python3 -m driverx oodrive --help`.
- AI generation smoke:
  `PYTHONPATH=src python3 -m oodrive ai-generate --prompt "Malaysian wet night roadwork chaos with scooter filtering" --output-root artifacts/runs --run-id oodrive-ai-smoke --count 4 --seed 11 --compile --queue`.
- AI DB: `artifacts/runs/oodrive-ai-smoke/scenario_studio_db.json`.
- Product quickstart smoke:
  `PYTHONPATH=src python3 -m oodrive quickstart --prompt "Malaysian wet roadwork: motorcycle filtering and unsignaled lorry brake" --output-root artifacts/runs --run-id oodrive-product-smoke --count 2 --seed 19`.
- Export pack:
  `artifacts/runs/oodrive-product-smoke/exports/oodrive-product-smoke-export/scenario_generator_cli_pack.html`.
- Unit tests: `PYTHONPATH=src python3 -m unittest tests.test_oodrive_cli` passed with 6 tests.
- Full gate: `bash scripts/pre_push_check.sh` passed with 398 tests and 3 skipped.
- QA report:
  `tickets/TASK-125/artifacts/qa/oodrive-product-cli-qa.md`.
- Review:
  `docs/reviews/TASK-125-oodrive-product-cli-review.md`.

### Blockers

None.
