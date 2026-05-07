# Perception

The perception package contains simulator-grounded perception helpers for the
0xDriver demo. It does not claim image-based object detection; instead, it turns
CARLA actor tracks into risk timelines that are easy to show in reports and
video overlays.

## Entrypoints

- `load_entity_tracks(path)`
- `build_risk_timeline(tracks, config)`
- `write_risk_timeline(run_dir, timeline)`
- CLI: `python -m driverx build-risk-timeline --tracks ...`

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_risk_timeline
```
