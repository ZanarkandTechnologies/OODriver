# OOD Video Evidence

- status: `passed`
- scenario_id: `generated-base-animals-0076-visual-noise-000`
- behavior_id: `wrong_way_shoulder_creep`
- duration_s: `60.0`
- video_path: `artifacts/runs/task97-runpod-campaign-v2/cases/000-generated-base-animals-0076-visual-noise-000-wrong_way_shoulder_creep/video/generated-base-animals-0076-visual-noise-000_ood.mp4`
- overlay_frame_count: `300`
- worst_risk: `None`

## Claim Boundaries

- `scripted_carla_ood_campaign=true`
- `video_overlay_is_evidence_surface=true`
- `closed_loop_vla_control=false`

## Blockers

- Pillow is unavailable for text overlay rendering: No module named 'PIL'. Copied raw frames as fallback.
