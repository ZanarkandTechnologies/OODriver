# 0xDriver Two-Page Write-Up Draft

## Motivation

If autonomy depends on collecting examples of every weird road situation, it will always lag reality. 0xDriver reframes minimal-shot driving as a stress-test and memory problem: generate plausible OOD cases, run frozen policies through them, and preserve failures as reusable context.

## Architecture

The system has a Scenario Studio compiler, deterministic environment and behavior generators, CARLA/Fail2Drive-compatible evidence paths, a failure-memory bank, and an Alpamayo open-loop evaluation harness. Scenario Studio emits the curation queue; CARLA produces video and tracks; Alpamayo is evaluated with and without retrieved memory; final reports keep claim boundaries explicit.

## What Worked

The final sprint generated 20 OOD candidates from 10 briefs, selected 6 judge-facing cases, linked 26 cases to Fail2Drive references, and summarized 3 Frozen Alpamayo+memory comparisons. The hero video evidence is 60.0 seconds.

## What Did Not Work

The model evidence is open-loop and slow, not real-time closed-loop control. Full official Fail2Drive scoring remains a future runtime task. Current open blockers: 2026-05-07 01:40 +0800 | alpamayo,runpod,kasm,huggingface,secrets | TASK-099 prepared the RunPod hero video as a torch-ready Alpamayo package and proved the Kasm Alpamayo env has CUDA on RTX 6000 Ada, but live inference cannot proceed safely through the current SSH proxy because it requires a PTY and echoes command input. Probe evidence shows no token file at `/home/kasm-user/.cache/huggingface/token`, `/workspace/.cache/driverx/huggingface/token`, or `/workspace/alpamayo1.5/.hf_token`. User unblock path: run `cd /workspace/alpamayo1.5 && source a1_5_venv/bin/activate && hf auth login` inside the Kasm web terminal, or provide a direct TCP SSH endpoint that supports non-PTY file transfer. Evidence: `tickets/TASK-099/artifacts/runpod-kasm-alpamayo-env/alpamayo_env_probe.md`.

## Where Prize Money Goes

The next prototype step is a persistent graphics-capable CARLA host plus GPU time for closed-loop VLA experiments, higher-fidelity generated assets, and enough repeated runs to convert partial candidates into accepted dataset rows.

## Model And Data Declarations

- Base model: nvidia/Alpamayo-1.5-10B, used as a frozen non-commercial research model.
- No AV fine-tuning is performed for these generated scenarios.
- Alpamayo batch status: passed; open-loop only.
- Fail2Drive reference sources: ['fixture_result', 'fixture_seed']; official score claim is false.
- Model weights, datasets, videos, credentials, CARLA installs, and remote caches are excluded from git.
