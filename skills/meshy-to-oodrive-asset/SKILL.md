---
name: meshy-to-oodrive-asset
version: 1.0.0
description: Use when an agent needs to generate custom 3D assets with Meshy and hand them to OODrive as external asset manifests for CARLA/Fail2Drive scenario work. Trigger for requests like "generate a 3D asset", "make a crane/animal/object for CARLA", "use Meshy", or "create custom objects for OODrive".
allowed-tools: Read, Grep, Glob, Bash
---

# Meshy To OODrive Asset

## Purpose

Generate custom 3D assets through Meshy, download simulator-friendly files, and
write OODrive-compatible external asset manifests. OODrive remains the asset
registry, CARLA package/probe, Fail2Drive XML, and evidence layer.

## Source Of Truth

- Repo: `/Users/kenjipcx/SOTA/0xDriver`
- Helper: `skills/meshy-to-oodrive-asset/scripts/meshy_to_oodrive_asset.py`
- Example asset batch: `skills/meshy-to-oodrive-asset/references/showcase_assets.json`
- Main OODrive ingest command:

```bash
PYTHONPATH=src python3 -m oodrive generate-assets \
  --scenario-pack <scenario_pack.json> \
  --provider external-manifest \
  --external-manifest <asset_manifests.json>
```

## Workflow

1. **Load key safely.**
   Put `MESHY_API_KEY=...` in ignored `my.env` or export it in the shell.
2. **Generate assets.**
   Prefer `text-to-3d` for speed. Use `text-image-to-3d` when a reference image
   improves shape control.
3. **Request CARLA-friendly formats.**
   Download `glb` as the primary OODrive registry path, plus `fbx` for Unreal
   packaging and `obj` for cleanup.
4. **Write OODrive manifest.**
   The helper writes `asset_manifests.json`, one `<asset_id>/asset_manifest.json`
   per object, Meshy task responses, and downloaded files.
5. **Ingest into OODrive.**
   Run `oodrive generate-assets --provider external-manifest`.
6. **Package/probe before claims.**
   Run `oodrive package-asset`, then `probe-asset-blueprint`, then
   `spawn-custom-asset` only after a blueprint exists.

## Commands

Generate the default high-value OOD asset batch:

```bash
cd /Users/kenjipcx/SOTA/0xDriver
python3 skills/meshy-to-oodrive-asset/scripts/meshy_to_oodrive_asset.py \
  --assets-json skills/meshy-to-oodrive-asset/references/showcase_assets.json \
  --env-file my.env \
  --output-root artifacts/runs \
  --run-id meshy-oodrive-assets \
  --workflow text-to-3d
```

Generate one object:

```bash
python3 skills/meshy-to-oodrive-asset/scripts/meshy_to_oodrive_asset.py \
  --asset-id fallen-crane-arm \
  --prompt "fallen yellow construction crane arm blocking a wet urban lane, low-poly game-ready asset" \
  --tag crane --tag construction --tag lane_obstacle \
  --length 6.0 --width 1.0 --height 1.2 \
  --env-file my.env \
  --run-id meshy-fallen-crane-arm
```

## Claim Boundaries

- `custom_mesh_generated=true` only means Meshy produced and OODrive downloaded a mesh.
- `carla_blueprint_registered=false` until a live CARLA blueprint probe passes.
- `spawned_in_carla=false` until `oodrive spawn-custom-asset` captures proof.
- Stock proxy fallback remains fallback evidence, not custom asset proof.

## Output Contract

The batch manifest must be one of the shapes already accepted by OODrive:

```json
{
  "asset_manifests": [
    {
      "asset_id": "meshy-fallen-crane-arm",
      "provider": "external_manifest",
      "status": "generated",
      "prompt": "...",
      "semantic_tags": ["crane", "construction", "lane_obstacle"],
      "dimensions_m": {"length": 6.0, "width": 1.0, "height": 1.2},
      "collision_proxy": {"kind": "box", "length": 6.0, "width": 1.0, "height": 1.2},
      "intended_placement": {"surface": "road", "relative_to": "lane_center", "x_m": 25.0, "y_m": 0.0},
      "license": "meshy-generated-for-oodrive-demo",
      "local_path": "artifacts/runs/.../model.glb",
      "metadata": {
        "provider": "meshy",
        "thumbnail_path": "artifacts/runs/.../thumbnail.png",
        "alternate_formats": {"fbx": "...", "obj": "..."},
        "custom_mesh_generated": true,
        "carla_blueprint_registered": false,
        "spawned_in_carla": false
      }
    }
  ]
}
```
