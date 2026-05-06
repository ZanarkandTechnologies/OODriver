# TASK-105: Fail2Drive Reference Layer And Generated Extension Report

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-007, TASK-088, TASK-101, TASK-103
- location: `src/driverx/simulators/fail2drive*`, `src/driverx/scenarios`, `src/driverx/memory`, `tickets/TASK-105/artifacts`
- enter when: the final submission needs to connect DriverX-generated cases back to Fail2Drive rather than looking like an isolated toy simulator
- leave when: a report shows which generated cases extend which Fail2Drive seed/failure families and which memory entries came from those references
- blockers: external Fail2Drive checkout path must exist for live route metadata; fixture fallback is acceptable
- spawned follow-ups: TASK-106
- complexity: S
- assignee: generalPurpose

### Summary

Make the "extends Fail2Drive" story concrete. This ticket builds a reference
layer that maps generated DriverX OOD cases back to Fail2Drive scenario
families, failures, and memory principles without betting the deadline on full
stock route scoring.

### Scope

- In scope: ingest fixture/external Fail2Drive route/result metadata, link
  generated scenarios by scenario class/tag/behavior, build memory references,
  and write an extension report.
- Out of scope: running stock Fail2Drive to completion, SimLingo scoring, and
  claiming leaderboard parity.

### Plan

#### Change

Add a report pipeline that says "this generated case is a mutation/extension of
these Fail2Drive OOD families and these prior failure memories."

#### Why

The submission should not look like random CARLA scripts. Fail2Drive gives a
recognized OOD benchmark anchor; DriverX contributes the extension/generation
layer.

#### Before -> After

- Before: Fail2Drive is mostly setup/runtime context and seed inspiration.
- After: final evidence explicitly ties generated cases to Fail2Drive families
  and memory entries.

#### Touch

- `src/driverx/simulators/fail2drive.py` or nearest existing module:
  route/result reference loading if missing.
- `src/driverx/scenarios/generator.py`: expose parent seed/family metadata
  cleanly if needed.
- `src/driverx/memory/bank.py`: reuse memory entries.
- `src/driverx/pipeline/fail2drive_extension_report.py`: new report builder.
- CLI registration and tests.

#### Inspect

- `../external/fail2drive` if present.
- `src/driverx/simulators/fail2drive.py`
- `src/driverx/simulators/fail2drive_route_runner.py`
- `src/driverx/scenarios/generator.py`
- `src/driverx/memory/bank.py`
- archived TASK-007/TASK-088 evidence.

#### Signature Delta

```python
build_fail2drive_extension_report(
  generated_catalog_path: Path,
  fail2drive_root: Path | None,
  memory_bank_path: Path | None,
  output_dir: Path,
): dict[str, Any]
```

#### Type Sketch

```python
Fail2DriveExtensionRecord = {
  "generated_scenario_id": str,
  "driverx_behavior_id": str | None,
  "fail2drive_seed_family": str | None,
  "fail2drive_route_refs": list[str],
  "mutation_summary": str,
  "memory_entry_ids": list[str],
  "claim": "extension" | "fixture_reference" | "unlinked_generated_case",
}
```

#### Typed Flow Example

`generated-base-animals-0076-visual-noise-000 + wrong_way_shoulder_creep`
-> tags `["animals", "visual_noise", "wrong_way"]`
-> Fail2Drive family refs
-> memory ids
-> final report row: "DriverX extends a rare object/visual-noise family with
regional wrong-way shoulder behavior."

#### Execution Steps

1. Load generated catalog/matrix.
2. Load Fail2Drive fixture/external metadata if available.
3. Match by scenario class, route name, tags, and behavior labels.
4. Attach memory entries and mutation summaries.
5. Write JSON/Markdown and a final `what-we-extend.md` section.
6. Add tests with fixture metadata so this does not depend on external checkout.

#### Recommendation

Do this as a report layer, not a full stock Fail2Drive rerun. The stock rerun is
too runtime-risky for the deadline; reference linkage is enough to make the
contribution credible.

#### Options Considered

- Full Fail2Drive route score: strong if it lands, but high runtime risk.
- Ignore Fail2Drive and lead only DriverX: faster, but weaker academic framing.
- Recommended: reference layer now, full score only if spare time remains.

#### Blast Radius

Low. Report-only pipeline plus tests.

#### Risks

- External checkout may be missing. Fixture fallback keeps the ticket passable.

### Gap Analysis

DriverX already generates OOD cases, but the final story needs a benchmark
anchor. This ticket supplies the "we extend Fail2Drive-style OOD families" link
without pretending to be an official benchmark submission.

### Acceptance Criteria

- [ ] AC-1: Report links generated cases to Fail2Drive families or labels them
  unlinked.
- [ ] AC-2: Report distinguishes benchmark reference, generated extension, and
  official-score claim boundary.
- [ ] AC-3: Memory entries are connected to referenced failures when available.
- [ ] AC-4: Fixture tests pass without external Fail2Drive checkout.

### Verification

- Focused tests for fixture matching and missing-checkout fallback.
- CLI smoke over current generated catalog.
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Inputs available: fixture metadata and optional external checkout.
- Human gates: none unless external checkout has moved.
- Compute: local only.
- Stop condition: extension report written.

### Evidence

- `tickets/TASK-105/artifacts/fail2drive_extension_report.json`
- `tickets/TASK-105/artifacts/fail2drive_extension_report.md`

### Blockers

- None for fixture fallback.
