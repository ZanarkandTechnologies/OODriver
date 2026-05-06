# Alpamayo OOD Scene

- scenario_id: `fixture-malaysia-motorcycle-filtering`
- package_scenario_id: `fixture-malaysia-motorcycle-filtering`
- scenario_report_id: `generated-base-animals-0076-regional-driving-behavior-000`
- video_scenario_id: `fixture-malaysia-motorcycle-filtering`
- open_loop_policy_evaluation: `True`
- closed_loop_control: `False`
- model_id: `nvidia/Alpamayo-1.5-10B`
- latency_ms: `None`
- vram_peak_mb: `None`
- video_evidence_path: `tickets/TASK-073/artifacts/fixture-long-ood-video-v2/ood_video_evidence.json`

## Claim Boundaries

- `alpamayo_open_loop_policy_evaluation=true`
- `closed_loop_carla_control=false`
- `model_weights_frozen=true`

## Linkage Warnings

- Scenario report status is 'blocked'; this is setup evidence, not a successful generated-scene capture.
- Attached video evidence is source_kind='fixture'; it proves the overlay pipeline, not live CARLA capture.
- Package, scenario report, and video ids do not all match; treat this as linked evidence rather than same-capture proof.

## Blocker

- Alpamayo policy decision was not supplied; run remote inference or pass --policy-decision.
