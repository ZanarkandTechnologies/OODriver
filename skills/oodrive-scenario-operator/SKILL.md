---
name: oodrive-scenario-operator
description: Use when generating, curating, running, evaluating, replaying, or exporting OODrive out-of-distribution driving scenarios through the DriverX CLI database.
---

# OODrive Scenario Operator

OODrive is the out-of-distribution scenario generator for 0xDriver. This skill
uses Codex as the creative scenario author and experiment operator while the CLI
remains the durable database and evidence layer.

## Core Rule

Every durable scenario decision must be written through:

```bash
PYTHONPATH=src python3 -m driverx oodrive ...
```

Do not keep hidden scenario state in chat. Use `scenario_studio_db.json`,
Markdown reports, run manifests, evaluation records, replay bundles, and export
packs as the source of truth.

## Product Loop

1. Start or open a DB.

```bash
PYTHONPATH=src python3 -m driverx oodrive init \
  --output-root artifacts/runs \
  --run-id oodrive-demo \
  --force
```

2. Generate scenario briefs. Prefer weird-but-plausible cases that pressure
minimal-shot reasoning:

- regional driving behavior: Malaysian motorbike filtering, no-signal braking,
  shoulder creep, informal right-of-way
- environment shift: night market, monsoon flood, school-zone occlusion,
  construction taper, fog/glare
- visual novelty: irrelevant objects near but outside the drivable corridor,
  occluding stalls, unusual low-profile actors
- solvable conflict: the safe policy should slow, yield, creep, hold lane, or
  create space, not simply freeze forever

3. Ingest each brief.

```bash
PYTHONPATH=src python3 -m driverx oodrive ingest-brief \
  --db artifacts/runs/oodrive-demo/scenario_studio_db.json \
  --prompt "Malaysian wet roadwork: motorbike filters while a lorry brakes without signal" \
  --author codex \
  --tag malaysian_driving \
  --tag motorcycle_filtering
```

4. Compile and queue.

```bash
PYTHONPATH=src python3 -m driverx oodrive compile \
  --db artifacts/runs/oodrive-demo/scenario_studio_db.json \
  --count 12 \
  --severity 4 \
  --seed 42

PYTHONPATH=src python3 -m driverx oodrive queue \
  --db artifacts/runs/oodrive-demo/scenario_studio_db.json \
  --accept top:3
```

5. Run the safest available policy path.

```bash
PYTHONPATH=src python3 -m driverx oodrive run \
  --db artifacts/runs/oodrive-demo/scenario_studio_db.json \
  --policy mock
```

Use `--policy carla-autopilot --config ...` only when a CARLA host is reachable.
Use Alpamayo through `oodrive evaluate`, not by claiming live control.

6. Evaluate, replay, and export.

```bash
PYTHONPATH=src python3 -m driverx oodrive evaluate \
  --db artifacts/runs/oodrive-demo/scenario_studio_db.json \
  --policy alpamayo-trajectory \
  --memory auto

PYTHONPATH=src python3 -m driverx oodrive replay \
  --db artifacts/runs/oodrive-demo/scenario_studio_db.json

PYTHONPATH=src python3 -m driverx oodrive export \
  --db artifacts/runs/oodrive-demo/scenario_studio_db.json
```

## Claim Boundaries

Always preserve these distinctions:

- `closed_loop_carla_execution=true` only when a run manifest links video/tracks
  from a live CARLA route execution.
- `sampled_open_loop_reasoning=true` only when Alpamayo or another VLA produced
  reasoning for the scenario or attached capture.
- `real_time_vla_control=true` only after live control latency and actuation are
  proven. This project normally does not claim that.
- Missing CARLA/GPU/VLA runtime is not a failure; record it as a blocker and
  continue with compile, queue, replay, and export.

## Quick Local Proof

```bash
PYTHONPATH=src python3 -m driverx oodrive quickstart \
  --prompt "Night market scooter shoulder pass with sudden brake and roadside vendor occlusion" \
  --output-root artifacts/runs \
  --run-id oodrive-skill-smoke \
  --count 3 \
  --seed 11
```

Inspect:

- `scenario_studio_db.json`
- `scenario_dataset_queue.md`
- `run_manifest.md`
- `policy_evaluation.md`
- `scenario_run_bundle.html`
- `scenario_generator_cli_pack.html`

