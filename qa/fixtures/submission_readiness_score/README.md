# Submission Readiness Score Fixtures

These fixtures exercise the SoTA Commission readiness metric. The metric is an
internal promotion gate for the OODrive submission packet, not an official CARLA
driving score.

- `weak_submission.json`: plausible hero proof but not commission-ready.
- `target_submission.json`: complete packet with motivation, failure case,
  traceability, latency, randomized scenarios, and honest claim boundaries.
- `overclaim_submission.json`: otherwise strong packet that is blocked because
  it claims closed-loop/real-time VLA control.
