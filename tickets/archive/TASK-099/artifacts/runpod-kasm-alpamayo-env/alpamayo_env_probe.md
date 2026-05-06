# RunPod Kasm Alpamayo Env Probe

- remote: `poz4gv6ryu2571-644111cc@ssh.runpod.io`
- python: `/workspace/alpamayo1.5/a1_5_venv/bin/python`
- torch: `2.8.0+cu128`
- transformers: `4.57.1`
- huggingface_hub: `0.36.0`
- Pillow: `12.0.0`
- cuda_available: `true`
- cuda_device: `NVIDIA RTX 6000 Ada Generation`
- cuda_capability: `8.9`
- upstream Alpamayo checkout: `/workspace/alpamayo1.5`

## Token State

No Hugging Face token file exists on the Kasm pod at the checked locations:

- `/home/kasm-user/.cache/huggingface/token`
- `/workspace/.cache/driverx/huggingface/token`
- `/workspace/alpamayo1.5/.hf_token`

The Kasm SSH proxy currently requires a PTY and echoes command input, so Codex
should not transmit HF tokens through this path. Use the Kasm web terminal to
run `hf auth login`, or provide a direct TCP SSH endpoint that supports
non-interactive file transfer.
