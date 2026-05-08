# TASK-150: Prompt-To-3D Asset Provider Pipeline

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-149
- location: `src/driverx/assets`, `src/driverx/scenarios`, `src/oodrive`, `tests`, `tickets/TASK-150`
- enter when: scenario packs can declare asset requests, but providers still return dry-run or blocked manifests instead of usable mesh artifacts with quality metadata.
- leave when: OODrive can generate or ingest mesh artifacts through provider seams, validate scale/collision/license/thumbnail metadata, and update a scenario pack with asset generation evidence.
- blockers: live remote providers require credentials and provider terms; local fixture/procedural provider must pass without secrets.
- spawned follow-ups: TASK-151 consumes generated/ingested meshes for CARLA import.
- complexity: L

### Summary

Turn asset requests from "prompts with stock proxies" into a production asset-generation pipeline. The first production path should support a local fixture/procedural mesh provider for deterministic tests and an external provider seam for Meshy or equivalent services without embedding secrets.

### Scope

- In scope: provider interface, local fixture/procedural provider, external-provider blocked/pending states, manifest updater, asset QA report, thumbnail/path metadata, CLI command, and tests.
- Out of scope: Unreal/CARLA import, CARLA blueprint registry, paid provider execution without configured credentials, and asset marketplace licensing automation beyond manifest fields.

### Gap Analysis

- Current state: `generate_assets_with_provider` supports `dry_run` and returns `blocked` for Meshy even when a key exists.
- Production expectation: researchers can request assets from prompts, see which provider generated them, inspect local mesh paths/thumbnails, verify dimensions/collision/license, and rerun or swap providers.
- Missing gaps: provider abstraction is hard-coded, statuses are too coarse, no actual mesh artifact path is validated, no thumbnail/geometry QA exists, and no pack-update command exists.
- Recommended boundary: implement deterministic local asset generation/ingest plus provider contracts now; leave CARLA import to TASK-151.

### Plan

#### Change

Add:

```bash
PYTHONPATH=src python3 -m oodrive generate-assets \
  --scenario-pack artifacts/runs/prod-pack/scenario_pack.json \
  --provider local-procedural \
  --run-id task150-assets
```

#### Why

Prompt-to-3D assets cannot be credible if the "asset" is just a CARLA proxy id. This ticket creates real mesh artifacts and the metadata needed to judge them.

#### Before -> After

- Before: asset manifests are planned/blocked and point to hypothetical `generated_assets/*.glb`.
- After: generated/ingested manifests point to real local mesh files or precise provider blockers, with quality metadata and pack patch output.

#### Touch

- `src/driverx/assets/types.py`
- `src/driverx/assets/providers.py` (new)
- `src/driverx/assets/local_procedural.py` (new)
- `src/driverx/assets/quality.py` (new)
- `src/driverx/assets/pipeline.py`
- `src/driverx/scenarios/production_pack.py`
- `src/driverx/scenarios/studio_product_cli.py`
- `src/oodrive/cli.py`
- `tests/test_asset_provider_pipeline.py` (new)
- `tests/fixtures/assets/` (small generated fixtures only)
- `docs/HISTORY.md`

#### Inspect

- `src/driverx/assets/types.py`
- `src/driverx/assets/pipeline.py`
- `src/driverx/assets/AGENTS.md`
- `src/driverx/assets/README.md`
- `src/driverx/scenarios/studio_runtime.py`
- `tickets/TASK-012/ticket.md` if present
- `tickets/TASK-149/ticket.md`

#### Signature Delta

```python
AssetProviderName = Literal["dry_run", "local_procedural", "meshy", "external_blocked"]
AssetStatus = Literal["planned", "blocked", "pending", "generated", "qa_failed"]

class AssetProvider(Protocol):
    name: AssetProviderName
    def generate(self, requests: list[AssetRequest], output_dir: Path) -> list[AssetManifest]: ...

generate_assets_for_pack(pack_path: Path, provider: AssetProviderName, output_root: Path, run_id: str) -> dict[str, Any]
validate_generated_asset_artifact(manifest: AssetManifest) -> AssetQualityReport
patch_pack_with_asset_manifests(pack: dict[str, Any], manifests: list[AssetManifest]) -> dict[str, Any]
```

#### Type Sketch

```python
AssetQualityReport = {
  "asset_id": str,
  "passes": bool,
  "mesh_path_exists": bool,
  "mesh_format": "glb" | "obj" | "fbx",
  "thumbnail_path": str | None,
  "dimensions_match": bool,
  "collision_proxy_valid": bool,
  "license_present": bool,
  "blockers": list[str],
}
```

#### Typed Flow Example

An `AssetRequest` for `roadside_vendor` becomes an `AssetManifest`:

```json
{
  "asset_id": "roadside-vendor-00",
  "provider": "local_procedural",
  "status": "generated",
  "local_path": "artifacts/runs/task150-assets/generated_assets/roadside-vendor-00.glb",
  "metadata": {
    "thumbnail_path": ".../roadside-vendor-00.png",
    "geometry_source": "local_procedural_fixture",
    "quality_passes": true
  }
}
```

#### Execution Steps

1. Extend asset status/provider literals and preserve backward compatibility for old JSON payloads.
2. Define provider protocol and registry.
3. Implement a deterministic local provider that writes tiny valid GLB/OBJ fixture assets outside git-tracked source paths.
4. Implement external-provider blocked/pending responses with setup guidance and no secret echoing.
5. Add asset quality validation for file existence, supported extension, positive dimensions, collision proxy, and license.
6. Add `oodrive generate-assets` to load a scenario pack, generate assets, write `asset_generation_manifest.json`, and write a patched pack.
7. Add tests for local generation, missing mesh blockers, provider setup blockers, and pack patching.

#### Recommendation

Ship a deterministic local provider first and keep remote providers behind the same manifest contract. This gives researchers a real file path and lets CARLA import work proceed without waiting for paid APIs.

#### Options Considered

- Implement Meshy directly first: flashy, but blocks on secrets, quotas, and API behavior.
- Accept only manually supplied GLB files: reliable, but not prompt-to-asset generation.
- Local deterministic provider plus remote seam: recommended because it proves the contract and keeps the external path swappable.

#### Blast Radius

Moderate. Asset type literals are shared by existing tests and runtime specs, so backward compatibility and fixture updates matter.

#### Risks

- Placeholder procedural assets may look too weak for final demos; mitigate by labeling them as local fixtures and allowing remote/manually supplied higher-fidelity assets through the same contract.
- Generated file formats may need optional dependencies; keep validation dependency-light.

### Acceptance Criteria

- [x] AC-1: `oodrive generate-assets` updates a scenario pack with real local mesh paths using a dependency-light provider.
- [x] AC-2: Missing credentials for remote providers produce blocked manifests without crashing or echoing secrets.
- [x] AC-3: Asset QA report covers file existence, format, dimensions, collision proxy, license, and thumbnail metadata.
- [x] AC-4: Existing dry-run asset tests remain compatible.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_asset_provider_pipeline tests.test_assets`
- `PYTHONPATH=src python3 -m oodrive generate-assets --scenario-pack <pack> --provider local-procedural --run-id task150-smoke`
- Inspect `asset_generation_manifest.json`, patched `scenario_pack.json`, and generated mesh files under ignored artifacts.

### Autonomy Readiness

- Inputs: scenario pack.
- Compute: local for `local-procedural`; remote providers disabled unless credentials are already configured by the user.
- External services: optional and blocked by default.
- Stop gates: do not purchase API usage or transmit provider secrets.

### Refs

- CARLA custom prop authoring: https://carla.readthedocs.io/en/latest/content_authoring_props/

### Evidence

- Planning review: `tickets/TASK-149/artifacts/review/production-generator-plan-review.json`
- Implementation proof: `artifacts/runs/task150-production-assets-proof/asset_generation_manifest.json`
- Patched pack: `artifacts/runs/task150-production-assets-proof/scenario_pack.assets.json`
- Tests: `PYTHONPATH=src python3 -m unittest tests.test_production_scenario_generator tests.test_generated_carla_runtime tests.test_oodrive_cli`

### Blockers

- Live Meshy/equivalent provider credentials are optional and not required for this ticket.
