# TASK-176: Custom CARLA Map Import Readiness Path

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-165, TASK-166
- location: `src/driverx/simulators`, `src/driverx/assets`, `src/driverx/scenarios`, `scripts`, `tests`, `docs`
- enter when: OODrive can select installed CARLA towns and weather, but cannot prepare or validate custom map import packages.
- leave when: OODrive can create/validate a custom map import manifest for `.fbx` geometry plus `.xodr` OpenDRIVE, emit CARLA import commands for package/source builds, and prove installed-map detection when available.
- blockers: real map import requires CARLA package/source build tooling and valid `.fbx`/`.xodr` assets; OODrive must not claim runtime prompt-generated city geometry.
- spawned follow-ups: live custom-map import proof on Kasm/source CARLA build.
- complexity: M
- assignee: generalPurpose

### Description
CARLA custom maps are not runtime prompt magic. They require a real asset/import path. This ticket gives OODrive a productized custom map lane: validate map assets, generate import plans, detect installed maps, and label blockers honestly.

### Goal
Make “custom environment geometry” an explicit import workflow with proof and blocker artifacts.

### Integration Decision
Do not build a CARLA map generator. CARLA custom maps require external geometry/OpenDRIVE assets and CARLA import tooling. OODrive should validate `.fbx`/`.xodr` packages, generate import commands, and probe whether CARLA can load the result.

### Plan

#### Change
Add map import planning, validation, and live map probe commands for custom CARLA maps.

#### Why
Users will ask for custom environments. The honest product path is to expose the real CARLA import boundary rather than pretending runtime prompts create new drivable map geometry.

#### Before -> After
- Before: OODrive can select installed towns and weather only.
- After: OODrive can prepare a custom-map import manifest, validate prerequisites, emit package/source import commands, and prove whether the map is loadable.

#### Touch
- `src/driverx/simulators/carla_custom_map.py` new import manifest/validation module.
- `src/driverx/scenarios/studio_product_map_cli.py` new CLI registration.
- `src/driverx/scenarios/studio_product_map_runtime.py` new runtime wrapper.
- `src/driverx/scenarios/studio_product_cli.py` register commands.
- `src/driverx/evaluation/carla_custom_map_score.py` optional readiness score.
- `tests/test_carla_custom_map_import.py` new tests.
- `tests/test_oodrive_cli.py` command registration.

#### Inspect
- `src/driverx/simulators/carla_catalog.py`
- `src/driverx/simulators/carla_control.py`
- `src/driverx/scenarios/studio_product_carla_composer_runtime.py`
- `docs/MEMORY.md` MEM-0047

#### Signature Delta
- `prepare_custom_map_import(fbx_path: Path, xodr_path: Path, map_name: str, mode: str, output_dir: Path) -> CustomMapImportManifest`
- `validate_custom_map_import(manifest_path: Path) -> CustomMapImportValidation`
- `probe_carla_map(map_name: str, host: str, port: int, output_dir: Path) -> CarlaMapProbeResult`

#### Type Sketch
```python
CustomMapImportManifest = {
  "schema_version": "oodrive.custom_map_import.v1",
  "map_name": str,
  "geometry_fbx": str,
  "opendrive_xodr": str,
  "import_mode": "package|source_build|manual_unreal",
  "commands": list[str],
  "claim_boundaries": ["custom_unreal_map_import=false"],
}
```

#### Typed Flow Example
`OODriveCustom01.fbx` + `OODriveCustom01.xodr` -> `prepare-map-import` writes manifest and command script -> `validate-map-import` passes file/prereq checks -> `carla-map-probe` loads/probes map on Kasm -> only then claim can become `custom_unreal_map_import=true`.

#### Execution Steps
1. Add manifest dataclass/dict builders and command script generation.
2. Add validator for files, extensions, map name, mode, and known CARLA import prerequisites.
3. Add live map probe wrapper using existing CARLA control/catalog patterns.
4. Add scoring/claim guard that blocks custom map claims without load proof.
5. Add tests for missing files, fixture files, installed-town probe shape, and claim guards.

#### Recommendation
Implement import readiness first. Live custom map import proof can follow only when valid `.fbx`/`.xodr` assets and packaging runtime exist.

#### Options Considered
- Generate new road networks internally: rejected; CARLA/RoadRunner/OpenDRIVE already define this domain.
- Only document the blocker: too weak for product usability.
- Build import manifest/validation/probe: recommended; it creates a real agent-operable lane.

#### Blast Radius
Low to moderate. Adds map-import commands without changing installed-town composition.

#### Risks
- Users may expect instant new worlds; command outputs must state import prerequisites and blockers clearly.
- Live probe may load maps slowly or fail; probe must restore/record state and not hide failures.

### Acceptance Criteria
- [ ] AC-1: `oodrive prepare-map-import` writes a map import manifest from `.fbx` and `.xodr` inputs.
- [ ] AC-2: Manifest records geometry path, OpenDRIVE path, map name, package/source-build mode, pedestrian navigation requirement, expected CARLA install location, and claim labels.
- [ ] AC-3: `oodrive validate-map-import` checks file presence, extensions, OpenDRIVE readability where possible, map naming, and import-mode prerequisites.
- [ ] AC-4: `oodrive carla-map-probe --map <custom-map>` detects whether the map is installed/loadable in CARLA and writes proof or blocker output.
- [ ] AC-5: Tests prevent `custom_unreal_map_import=true` unless a manifest plus installed/loadable map proof exists.

### Agent Contract
- Open: `src/driverx/simulators/carla_catalog.py`, `src/driverx/simulators/carla_control.py`, `src/driverx/scenarios/studio_product_carla_composer_cli.py`, `src/driverx/scenarios/studio_product_carla_composer_runtime.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_carla_custom_map_import tests.test_carla_control_cli tests.test_oodrive_cli`
- Stabilize: do not generate fake FBX/XODR in git; tests use tiny fixtures or missing-file blockers.
- Inspect: map import manifest, validation report, import command script, map probe result.
- QA cookbook: run blocker path with missing files, run fixture validation, then Kasm map probe for installed towns and any imported custom map.
- Expected artifacts: `custom_map_import_manifest.json`, `custom_map_import_report.md`, `map_probe.json`, optional screenshot.

### Build Notes
- Installed maps remain the default path: Town01, Town02, Town03, Town04, Town05, Town10HD and `_Opt` variants.
- New map generation/import should be described as RoadRunner/Unreal/CARLA packaging work until live import proof exists.

### Verification
- `PYTHONPATH=src python3 -m oodrive prepare-map-import --fbx <map.fbx> --xodr <map.xodr> --map-name OODriveCustom01 --run-id task176-map`
- `PYTHONPATH=src python3 -m oodrive validate-map-import --manifest <manifest> --metric-only`
- `PYTHONPATH=src python3 -m oodrive carla-map-probe --map OODriveCustom01 --run-id task176-probe`
- `bash scripts/pre_push_check.sh`

### Evidence
- Import manifest
- Validation report
- Import command script
- Installed/loadable map proof or blocker
- Planning review: `tickets/TASK-174/artifacts/review/task174-180-integration-plan-review.json`
