# Alpamayo OOD Input Package

- frame_name: `driverx_ood_generated-base-animals-0076-regional-driving-behavior-000`
- camera_indices: `[0, 1, 2]`
- camera_windows: `3`
- memory_entries: `1`
- source: `{'rgb_folder': 'tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb', 'tracks_path': 'tickets/TASK-078/artifacts/task78-live-ood-capture-v3/entity_tracks.json', 'scenario_report_path': 'tickets/TASK-078/artifacts/task78-live-ood-capture-v3/carla_ood_demo.json', 'video_evidence_path': 'tickets/TASK-079/artifacts/task79-live-ood-video/ood_video_evidence.json'}`

## Notes

- Package was built from a live DriverX scripted CARLA OOD demo.
- The source capture has one ego RGB camera; the four selected frames are duplicated across Alpamayo front-left/front/front-right camera indices for same-scene open-loop reasoning.
- This package is for open-loop VLA reasoning evidence, not calibrated production multi-camera autonomy.
- scenario_report_path=tickets/TASK-078/artifacts/task78-live-ood-capture-v3/carla_ood_demo.json
- video_evidence_path=tickets/TASK-079/artifacts/task79-live-ood-video/ood_video_evidence.json
- behavior_id=motorcycle_filtering
