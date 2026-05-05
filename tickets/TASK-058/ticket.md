# TASK-058: CARLA Town13 AdditionalMaps Installer And Probe

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: none
- location: `scripts/`, `src/driverx/simulators`, `configs/`, tests
- enter when: user approves unblocking stock Fail2Drive Town13 routes
- leave when: Town13 install/staging is attempted, map availability is probed,
  and the Fail2Drive Town13 blocker is either resolved or replaced by a precise
  local-install blocker
- blockers: local CARLA/Kegworks root may need discovery or user path if
  automatic search cannot find a writable CARLA install
- spawned follow-ups: TASK-060 stock Fail2Drive Town13 route score and video
- complexity: M

### Description
Stock Fail2Drive split routes require `Town13`, while the current local CARLA
0.9.16 proof only shows `Town10HD_Opt`. CARLA 0.9.16 officially publishes
AdditionalMaps packages for Ubuntu and Windows, so the next step is to add a
repeatable installer/probe path instead of hand-editing the Kegworks wrapper.

### Goal
Resolve the map blocker enough to run stock Fail2Drive Town13 routes, or record
exactly what local CARLA path/package operation failed.

## Plan

### Change
Add a CARLA maps utility that can:

- discover likely CARLA install roots, including `/Users/kenjipcx/Applications/Sikarugir/CARLA.app`
- download or reuse `AdditionalMaps_0.9.16` for the correct package type
- stage/extract the additional maps into the CARLA root without committing the package
- probe a running CARLA server for available maps and a `Town13` load attempt

### Why
Town13 is the main blocker to moving from a Town10 smoke video to actual
Fail2Drive OOD split evidence.

### Before -> After
- Before: `blockers.md` says Town13 is absent; route runner falls back to
  Town10, which is not the real Fail2Drive split.
- After: `probe-carla-maps` proves whether Town13 is loadable, and
  `install-carla-additional-maps` leaves an auditable install report.

### Touch
- `src/driverx/simulators/carla_maps.py`: install/probe dataclasses and logic.
- `src/driverx/simulators/carla_maps_cli.py`: `install-carla-additional-maps`
  and `probe-carla-maps` command registration.
- `src/driverx/simulators/__init__.py`: exports.
- `src/driverx/cli.py`: command registration.
- `scripts/install_carla_additional_maps.sh`: shell wrapper for local use.
- `configs/carla_maps.local.sample.yaml`: default URLs/paths and desired maps.
- `tests/test_carla_maps.py`: fake archive and fake CARLA client tests.
- `README.md`, `blockers.md`, `docs/progress.md`: docs/evidence after proof.

### Inspect
- `scripts/remote_simlingo_bootstrap.sh`: existing AdditionalMaps 0.9.15 Linux
  pattern.
- `scripts/run_carla_client_docker.sh`: local CARLA Python API bridge.
- `src/driverx/simulators/carla_probe.py`: existing CARLA probe style.
- Official CARLA 0.9.16 release/download references for AdditionalMaps URLs.

### Signature Delta
```python
src/driverx/simulators/carla_maps.py / discover_carla_install_candidates(search_paths: list[Path]) -> list[CarlaInstallCandidate]
src/driverx/simulators/carla_maps.py / install_carla_additional_maps(config: CarlaMapsInstallConfig) -> CarlaMapsInstallResult
src/driverx/simulators/carla_maps.py / probe_carla_map_inventory(config: CarlaMapProbeConfig) -> CarlaMapInventory
src/driverx/simulators/carla_maps.py / write_carla_maps_report(run_dir: Path, result: CarlaMapsInstallResult | CarlaMapInventory) -> dict[str, Any]
```

### Type Sketch
```python
CarlaMapsInstallConfig = {
  "version": "0.9.16",
  "platform": "windows" | "ubuntu" | "auto",
  "carla_root": Path | None,
  "package_url": str | None,
  "package_path": Path | None,
  "desired_maps": ["Town13"],
  "dry_run": bool,
}

CarlaMapInventory = {
  "connected": bool,
  "server_version": str | None,
  "current_map": str | None,
  "available_maps": list[str],
  "load_attempts": [{"map": "Town13", "success": bool, "error": str | None}],
}
```

### Typed Flow Example
`configs/carla_maps.local.sample.yaml`
-> discover `CARLA.app` root
-> download/stage `AdditionalMaps_0.9.16.zip`
-> extract/import map content
-> `scripts/run_carla_client_docker.sh python -m driverx probe-carla-maps --map Town13`
-> `carla_map_inventory.json` marks `Town13` loadable or records the exact
missing path/import failure.

### Execution Steps
1. Implement fake-archive-safe install/probe module and CLI.
2. Add tests for candidate discovery, URL selection, dry-run install, archive
   validation, and fake CARLA map load.
3. Run dry-run against the local machine to find probable CARLA roots.
4. If a root is found, download/stage AdditionalMaps and run the probe through
   the Docker client.
5. Update `blockers.md`: move Town13 to resolved if probe succeeds, otherwise
   replace it with the exact path/package blocker.

### Recommendation
Use the official Windows AdditionalMaps package for the Kegworks CARLA app first,
because the running local server is the one already proven with Docker clients.
Keep the Ubuntu tarball path in the same utility for a later Linux host.

### Options Considered
- Local Kegworks/Wine Town13 install: best immediate path; uses proven local
  CARLA server.
- Remote Linux CARLA install: reproducible later, but graphics runtime already
  blocked us on H100.
- Rewrite routes for Town10: fastest fallback, but does not resolve the stock
  Fail2Drive OOD split blocker.

### Blast Radius
Docs, scripts, simulator utilities, and ignored external packages only. No model
weights, CARLA binaries, map archives, or media should be committed.

### Risks
- Kegworks wrapper layout may differ from a plain Windows CARLA zip.
- CARLA may need to be closed/restarted after maps are installed.
- AdditionalMaps may be too large for local disk; installer must preflight disk
  space before download/extract.

## Acceptance Criteria
- [ ] AC-1: Dry-run install writes chosen package URL, target root, required
  disk estimate, and expected files without touching CARLA.
- [ ] AC-2: Real install/stage either makes `Town13` loadable or writes a precise
  failure report.
- [ ] AC-3: `probe-carla-maps` reports current map, available maps, and `Town13`
  load result through the Docker CARLA client.
- [ ] AC-4: `blockers.md` accurately reflects the new Town13 state.
- [ ] AC-5: AdditionalMaps archives, extracted CARLA assets, and generated media
  stay out of git.

## Verification
- Unit: `PYTHONPATH=src python3 -m unittest tests.test_carla_maps`
- Regression: `bash scripts/pre_push_check.sh`
- Local proof:
  `scripts/run_carla_client_docker.sh python -m driverx probe-carla-maps --host host.docker.internal --port 2000 --map Town13`
- Evidence:
  `tickets/TASK-058/artifacts/town13-map-probe/carla_map_inventory.md`

## Autonomy Readiness
- I can discover roots, download packages, stage maps, and probe CARLA.
- Human gate only if the CARLA root is not discoverable/writable or CARLA must be
  closed/restarted at a specific moment.

## Refs
- CARLA 0.9.16 docs: `https://carla.readthedocs.io/en/0.9.16/download/`
- CARLA 0.9.16 release assets: `https://github.com/carla-simulator/carla/releases/tag/0.9.16/`

## Evidence
- Pending implementation.

## Blockers
- Pending local CARLA root/package probe.
