# RunPod/Kasm CARLA Quickstart

This is the friend-facing path for a graphics-capable RunPod/Kasm desktop pod.
It installs CARLA 0.9.16, creates the Python 3.12 CARLA client environment,
syncs this repo, and runs the OODrive loop.

## What You Need

- A RunPod pod with a Kasm/Desktop image and an NVIDIA GPU.
- SSH access to the pod and the private key for that pod.
- Enough disk for CARLA under `/workspace/carla`.
- Hugging Face access only if you run real Alpamayo. Install tokens from the
  web terminal or direct SSH; do not paste secrets through the proxy sync path.

Expected remote paths:

- repo: `/workspace/0xDriver`
- CARLA: `/workspace/carla/CARLA_0.9.16`
- Python venv: `/workspace/driverx_py312`
- remote artifacts: `/workspace/driverx_remote_artifacts`

## 1. Resolve Or Set SSH

If your `.env` has a RunPod API key, resolve the current SSH endpoint:

```bash
PYTHONPATH=src python3 -m driverx resolve-runpod-ssh \
  --env-file .env \
  --ssh-key ~/.ssh/id_ed25519_runpod \
  --run-id runpod-current
```

Or use the host shown in the RunPod Connect tab directly:

```bash
export DRIVERX_RUNPOD_HOST="root@ssh.runpod.io"
export DRIVERX_RUNPOD_KEY="$HOME/.ssh/id_ed25519_runpod"
```

## 2. Sync The Repo Through The RunPod Proxy

```bash
bash scripts/sync_runpod_proxy_workspace.sh \
  "$DRIVERX_RUNPOD_HOST" \
  "$DRIVERX_RUNPOD_KEY" \
  /workspace/0xDriver
```

The sync intentionally excludes `.git`, `.env`, datasets, artifacts, virtual
envs, caches, and generated media.

## 3. Install CARLA + Python On The Pod

Run this inside the pod:

```bash
cd /workspace/0xDriver
bash scripts/setup_runpod_carla_0916_graphics.sh
```

The script installs system packages, downloads/extracts CARLA 0.9.16, creates
`/workspace/driverx_py312`, installs the CARLA wheel and Pillow, writes a
per-process NVIDIA Vulkan ICD file, launches a smoke CARLA server on port
`2000`, and verifies a Python client connection.

## 4. Run The OODrive Product Loop

```bash
cd /workspace/0xDriver

PYTHONPATH=src /workspace/driverx_py312/bin/python -m oodrive generate \
  "wet Kuala Lumpur roadwork, scooter filtering, cones blocking the curb lane" \
  --run-id runpod-oodrive-demo \
  --count 4

PYTHONPATH=src /workspace/driverx_py312/bin/python -m oodrive place \
  --db artifacts/runs/runpod-oodrive-demo/oodrive.sqlite \
  --live \
  --run-id runpod-oodrive-live
```

For a minimal closed-loop trace without real Alpamayo steering:

```bash
PYTHONPATH=src /workspace/driverx_py312/bin/python -m oodrive closed-loop-run \
  --backend carla-live \
  --policy fake-trajectory \
  --steps 3 \
  --run-id runpod-closed-loop-smoke
```

## 5. Run Alpamayo Evidence

Use `fake` mode for a local contract check:

```bash
PYTHONPATH=src /workspace/driverx_py312/bin/python -m oodrive infer \
  --package artifacts/runs/<live-run>/alpamayo_package.json \
  --mode fake \
  --run-id alpamayo-contract
```

Use `remote-kasm` only after the pod has a working Alpamayo environment and HF
auth:

```bash
PYTHONPATH=src /workspace/driverx_py312/bin/python -m oodrive infer \
  --package artifacts/runs/<live-run>/alpamayo_package.json \
  --mode remote-kasm \
  --alpamayo-python /workspace/alpamayo1.5/a1_5_venv/bin/python \
  --run-id alpamayo-live
```

Then attach reasoning plus retrieved memory:

```bash
PYTHONPATH=src /workspace/driverx_py312/bin/python -m oodrive reason \
  --db artifacts/runs/runpod-oodrive-demo/oodrive.sqlite \
  --prediction-json artifacts/runs/alpamayo-live/prediction.json \
  --run-id runpod-reasoning
```

## Useful Scripts

- `scripts/setup_runpod_carla_0916_graphics.sh`: Kasm pod CARLA install and
  smoke launch.
- `scripts/sync_runpod_proxy_workspace.sh`: proxy-safe repo sync.
- `scripts/run_remote_alpamayo_carla_inference.sh`: older host-driven Alpamayo
  package runner.
- `scripts/remote_gpu_snapshot.sh`: remote GPU/package snapshot helper.
- `scripts/pre_push_check.sh`: local validation before sharing.

## Claim Boundaries

- `oodrive place --live` proves CARLA object placement/capture when its manifest
  records live CARLA success.
- `oodrive infer --mode fake` proves package shape only.
- Sampled Alpamayo reasoning is open-loop unless a closed-loop trace shows
  observe -> infer -> act -> observe recurrence.
- Time-warped videos are acceptable demo media only when labeled as not
  real-time VLA control.
