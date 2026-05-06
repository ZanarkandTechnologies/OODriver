# OOD Video Evidence

- status: `partial`
- scenario_id: `generated-generalization-customobstacles-1028-occlusion-001`
- behavior_id: `sudden_brake`
- duration_s: `24.0`
- video_path: `None`
- overlay_frame_count: `120`
- worst_risk: `None`

## Claim Boundaries

- `scripted_carla_ood_campaign=true`
- `video_overlay_is_evidence_surface=true`
- `closed_loop_vla_control=false`

## Blockers

- Pillow is unavailable for text overlay rendering: No module named 'PIL'. Copied raw frames as fallback.
- ffmpeg not found on PATH; install ffmpeg or pass --ffmpeg-path.
