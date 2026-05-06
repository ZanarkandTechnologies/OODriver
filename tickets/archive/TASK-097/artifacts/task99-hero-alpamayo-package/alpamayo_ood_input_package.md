# Alpamayo OOD Input Package

- frame_name: `driverx_ood_generated-base-animals-0076-visual-noise-000`
- camera_indices: `[0, 1, 2]`
- camera_windows: `3`
- memory_entries: `1`
- source: `{'rgb_folder': 'tickets/TASK-097/artifacts/task99-hero-video-frames/rgb', 'video_path': 'tickets/TASK-097/artifacts/pulled/artifacts/runs/task97-runpod-overlay-v2/generated-base-animals-0076-visual-noise-000_ood.mp4', 'tracks_path': 'tickets/TASK-097/artifacts/pulled/artifacts/runs/task97-runpod-campaign-v2/cases/000-generated-base-animals-0076-visual-noise-000-wrong_way_shoulder_creep/carla/entity_tracks.json', 'scenario_report_path': 'tickets/TASK-097/artifacts/pulled/artifacts/runs/task97-runpod-campaign-v2/cases/000-generated-base-animals-0076-visual-noise-000-wrong_way_shoulder_creep/carla/carla_ood_demo.json', 'video_evidence_path': 'tickets/TASK-097/artifacts/pulled/artifacts/runs/task97-runpod-overlay-v2/ood_video_evidence.json'}`

## Notes

- Package was built from a live DriverX scripted CARLA OOD demo.
- The source capture has one ego RGB camera; the four selected frames are duplicated across Alpamayo front-left/front/front-right camera indices for same-scene open-loop reasoning.
- This package is for open-loop VLA reasoning evidence, not calibrated production multi-camera autonomy.
- scenario_report_path=tickets/TASK-097/artifacts/pulled/artifacts/runs/task97-runpod-campaign-v2/cases/000-generated-base-animals-0076-visual-noise-000-wrong_way_shoulder_creep/carla/carla_ood_demo.json
- video_evidence_path=tickets/TASK-097/artifacts/pulled/artifacts/runs/task97-runpod-overlay-v2/ood_video_evidence.json
- behavior_id=wrong_way_shoulder_creep
