# TASK-155: Research Dataset Export And Scenario Library

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-152, TASK-153, TASK-154
- location: `src/driverx/scenarios`, `src/driverx/pipeline`, `src/oodrive`, `tests`, `tickets/TASK-155`
- enter when: scenarios can be generated, run, scored, and curated, but accepted cases are not packaged as reproducible research datasets.
- leave when: OODrive exports accepted scenarios into a portable library bundle with packs, graph exports, asset manifests, run evidence, metrics, curation status, license/provenance, and exact rerun commands.
- blockers: public hosting is out of scope; local export must still be complete.
- spawned follow-ups: external benchmark adapters can consume exported bundles later.
- complexity: M

### Summary

Make outputs useful beyond one demo. A production-grade research generator should leave behind a scenario library that another researcher can inspect, rerun, filter, and cite locally.

### Scope

- In scope: scenario library index, accepted/rejected curation export, artifact copy/link policy, manifest validation, README generation, reproducibility commands, and tests.
- Out of scope: uploading to Hugging Face/DVC/S3, DOI minting, official benchmark scoring, and bundling large videos/assets into git.

### Gap Analysis

- Current state: final submission packs and run artifacts exist, but they are challenge-oriented and not a reusable scenario-library export.
- Production expectation: accepted generated scenarios are packaged with provenance, assets, graph exports, evidence, and reproducibility instructions.
- Missing gaps: no library index, no curation-aware export, no asset/run evidence completeness validator, and no clean separation of local files versus remote/missing media.
- Recommended boundary: local portable export first, with media references and optional copy mode.

### Plan

#### Change

Add:

```bash
PYTHONPATH=src python3 -m oodrive export-library \
  --workbench artifacts/runs/task154-workbench/workbench_summary.json \
  --run-id task155-scenario-library \
  --include-media refs
```

#### Why

Real researchers need datasets, not just a generator command. Export turns generated scenarios into durable, reviewable units.

#### Before -> After

- Before: artifacts are scattered by run id.
- After: `scenario_library.json`, `scenario_library.md`, per-scenario folders, and optional media references/copies are written.

#### Touch

- `src/driverx/scenarios/scenario_library_export.py` (new)
- `src/driverx/scenarios/studio_product_cli.py`
- `src/oodrive/cli.py`
- `src/driverx/pipeline/final_submission_pack.py` only if shared artifact helpers are needed
- `tests/test_scenario_library_export.py` (new)
- `tests/test_oodrive_cli.py`
- `docs/HISTORY.md`

#### Inspect

- `src/driverx/pipeline/final_submission_pack.py`
- `src/driverx/pipeline/submission_scenario_browser.py`
- `src/driverx/scenarios/studio_db.py`
- `src/driverx/scenarios/run_manifest.py`
- `tickets/TASK-154/ticket.md`
- `docs/MEMORY.md` MEM-0033

#### Signature Delta

```python
export_scenario_library(
    *,
    workbench_summary_path: Path,
    output_root: Path,
    run_id: str,
    include_media: Literal["refs", "copy", "none"],
) -> dict[str, Any]

validate_scenario_library_export(export: dict[str, Any]) -> ScenarioLibraryValidation
```

#### Type Sketch

```python
ScenarioLibraryRecord = {
  "scenario_id": str,
  "curation_status": "accepted" | "rejected" | "needs_review",
  "pack_path": str,
  "graph_path": str | None,
  "open_scenario_path": str | None,
  "asset_manifest_paths": list[str],
  "run_manifest_paths": list[str],
  "media": [{"kind": "video" | "frames", "availability": "local_file" | "remote_only" | "missing", "path": str | None}],
  "rerun_commands": list[str],
}
```

#### Typed Flow Example

An accepted scenario with local video exports a record with media availability `local_file`; a remote-only Kasm path remains `remote_only` and cannot be marked proved until exported.

#### Execution Steps

1. Define scenario-library records and validation.
2. Load workbench summary and curation decisions.
3. Gather packs, graphs, sidecars, asset manifests, run manifests, metrics, and media references.
4. Apply media policy: reference, copy, or omit large files.
5. Write per-scenario folders and top-level index/report.
6. Include exact rerun commands and claim boundaries.
7. Add tests for accepted/rejected filtering, media availability, missing artifacts, and CLI registration.

#### Recommendation

Use a local folder export with media-reference mode by default. Copy mode can be opt-in for handoff bundles.

#### Options Considered

- Submission pack reuse: too judge-specific.
- Cloud dataset export first: premature and has credentials/storage risks.
- Local library export: recommended because it is reproducible and safe.

#### Blast Radius

Additive. It reads artifacts and writes a new export directory.

#### Risks

- Export can silently include missing media; validation must make availability explicit.
- Large file copying can be slow; default to references.

### Acceptance Criteria

- [x] AC-1: `oodrive export-library` writes JSON/Markdown index and per-scenario records.
- [x] AC-2: Export records curation status, provenance, asset manifests, graph/OpenSCENARIO outputs, run manifests, metrics, media availability, and rerun commands.
- [x] AC-3: Missing or remote-only media cannot be marked proved.
- [x] AC-4: Large generated artifacts remain out of git.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_scenario_library_export tests.test_oodrive_cli`
- `PYTHONPATH=src python3 -m oodrive export-library --workbench <summary> --run-id task155-smoke --include-media refs`
- Inspect library report and media availability fields.

### Autonomy Readiness

- Inputs: workbench summary and curation decisions.
- Compute: local only.
- External services: none.
- Stop gates: do not upload or copy huge media unless explicitly requested.

### Refs

- Media availability invariant: `docs/MEMORY.md` MEM-0033

### Evidence

- Planning review: `tickets/TASK-149/artifacts/review/production-generator-plan-review.json`
- Implementation proof: `artifacts/runs/task155-production-library-proof/scenario_library.json`
- Report proof: `artifacts/runs/task155-production-library-proof/scenario_library.md`

### Blockers

- None.
