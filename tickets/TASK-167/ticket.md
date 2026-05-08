# TASK-167: Live CARLA Capability Matrix Reel And Snapshot Gate

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-165, TASK-166
- location: `src/driverx/simulators`, `src/driverx/scenarios`, `artifacts/runs`, `tests`
- enter when: TASK-166 has a 10-case suite and the Kasm CARLA host is available for live map/weather/camera control.
- leave when: the suite has live CARLA snapshots for all runnable cases, a contact sheet/reel, and a score/report proving map/weather/anchor/camera/blueprint/image diversity before any case enters the generator gallery.
- blockers: requires Kasm CARLA host or another CARLA 0.9.16 host with Python API; local Mac absence is not a failure.
- spawned follow-ups: TASK-168 consumes the best cases for behavior simulation video.
- complexity: M
- assignee: generalPurpose

### Description
Run live CARLA snapshot capture for the ten generated cases and, before that, iterate the installed-map/weather/anchor/camera/blueprint matrix enough to prove the generator is not just changing prompt text. The output should be something a user can immediately look at: a grid or short reel of different CARLA towns/weather/road contexts, not just manifests.

### Goal
Answer “show me snapshots of what they look like” with real local image artifacts pulled from the CARLA host, and block weak-looking cases from the generator gallery.

### Acceptance Criteria
- [ ] AC-1: `oodrive carla-suite-snapshots` or equivalent consumes the TASK-166 suite manifest.
- [ ] AC-2: For each case, it calls or records the exact `driverx control-carla`/`oodrive carla-control` command with town/map, weather, capture, camera pose, spawn index, and blueprint/proxy family.
- [ ] AC-3: At least 8 of 10 cases produce local `*.png` screenshots when CARLA is available; failures are recorded with blockers.
- [ ] AC-4: A contact sheet image and Markdown/HTML gallery link every screenshot to its case manifest and claim labels.
- [ ] AC-5: Score/report proves at least four distinct map names, four distinct weather presets, three distinct camera/anchor styles, and at least four object/blueprint/proxy families among successful screenshots.
- [ ] AC-6: `image_diversity_score` and `prompt_visual_match_score` must pass before screenshots are marked gallery-ready; blocked cases remain visible as QA evidence but not promoted.

### Agent Contract
- Open: `src/driverx/simulators/carla_control.py`, `src/driverx/scenarios/studio_product_carla_composer_runtime.py`, `src/driverx/scenarios/studio_product_carla_composer_cli.py`, `tickets/TASK-165/ticket.md`
- Test hook: local unit tests use fake control results; live Kasm run is evidence, not unit-test requirement.
- Stabilize: never send secrets over Kasm proxy heredocs; use existing RunPod paths/venvs.
- Inspect: screenshot PNGs, control JSONs, contact sheet, gallery, map/weather diversity report.
- QA cookbook: run one local blocked control test, then one live Kasm batch when host is reachable.
- Expected artifacts: `carla_suite_snapshots_manifest.json`, `carla_capability_reel_manifest.json`, `contact_sheet.png`, `gallery.html`, optional short reel MP4, per-case `carla_control.json`, per-case `carla_control_screenshot.png`.

### Plan

#### Change
Add a snapshot batch runner around `carla-control`, a contact-sheet/reel builder, and a promotion score for live image diversity and prompt visual match.

#### Why
The user needs visual proof. The current fake-CARLA artifacts prove configuration, not appearance, and weak prompt variation should not enter the generator gallery.

#### Before -> After
- Before: two individual live screenshots prove map/weather capability.
- After: one suite grid/reel shows 8-10 varied CARLA scenes, with weak or visually repetitive cases blocked from gallery promotion.

#### Touch
- `src/driverx/scenarios/studio_product_carla_composer_runtime.py`
- `src/driverx/scenarios/studio_product_carla_composer_cli.py`
- `src/driverx/pipeline/carla_snapshot_contact_sheet.py` (new)
- `src/driverx/evaluation/carla_image_diversity_score.py` (new if the metric needs its own module)
- `tests/test_carla_scenario_composer.py`

#### Signature Delta
- `run_studio_carla_suite_snapshots(suite_manifest_path: Path, live: bool, output_root: Path | None, run_id: str) -> StudioCommandResult`
- `build_carla_snapshot_contact_sheet(snapshot_manifest: dict, output_dir: Path) -> dict[str, str]`
- `score_carla_snapshot_diversity(snapshot_manifest: dict) -> dict`

#### Type Sketch
```python
SnapshotRecord = {
  "case_id": str,
  "map_name": str,
  "weather_preset": str,
  "status": "passed" | "blocked",
  "screenshot_path": str | None,
  "control_json_path": str,
  "image_diversity_score": float,
  "prompt_visual_match_score": float,
  "gallery_ready": bool,
  "blockers": list[str]
}
```

#### Typed Flow Example
TASK-166 suite manifest -> iterate case configs -> live `control_carla_world` -> per-case PNG/JSON -> image diversity/prompt visual match score -> contact sheet row -> gallery-ready gate.

#### Execution Steps
1. Add batch snapshot runtime.
2. Add contact-sheet builder using Pillow if available; otherwise HTML gallery is still required.
3. Add live-image diversity scorer using metadata first and screenshot differencing when local PNGs are available.
4. Add local fake tests for contact sheet data shape, promotion gates, and blocked CARLA handling.
5. Run live Kasm snapshot batch.
6. Pull PNGs locally and update ticket evidence.
7. Record blockers for any failed case without failing the whole batch if 8/10 pass.
8. Promote only gallery-ready screenshots into the generator gallery/reel.

#### Recommendation
Run the live capability matrix/reel before behavior simulation. Visual diversity is the highest-leverage trust gap.

#### Options Considered
- Jump straight to videos: slower and harder to debug when map/anchor is bad.
- Snapshot grid first: recommended; fast, inspectable, and reusable in the final demo.
- Static HTML cards only: insufficient for the user’s CARLA-specific ask.
- Prompt-only variation: rejected; it does not prove simulator capability.

#### Blast Radius
Batch command and generated artifacts only; no simulator semantics changed.

#### Risks
- Some towns may be unavailable on a future CARLA install. The runner should record available maps and skip/replace missing maps.
- Screenshots can still look visually similar across towns if camera anchors are poor. Camera/anchor diversity must be scored, not assumed.

### Verification
- `PYTHONPATH=src python3 -m oodrive carla-suite-snapshots --suite-manifest <...> --run-id task167-live-snapshots`
- `PYTHONPATH=src python3 -m oodrive score-carla-snapshots --snapshot-manifest <...> --metric-only`
- `PYTHONPATH=src python3 -m unittest tests.test_carla_scenario_composer`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- External host: Kasm CARLA desktop pod.
- Required permissions: SSH or Kasm terminal access, no secrets in proxy heredocs.
- Human gate: none if host is reachable and no secrets are required.

### Evidence
- Contact sheet image
- Gallery HTML
- Per-case screenshot/control JSON
- Diversity score/report with gallery-ready flags
- Planning review: `tickets/TASK-166/artifacts/review/task166-169-plan-review.json`
