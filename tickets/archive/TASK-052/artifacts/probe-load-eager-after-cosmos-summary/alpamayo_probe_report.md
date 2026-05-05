# Alpamayo Probe Report

- model_id: `nvidia/Alpamayo-1.5-10B`
- status: `model_loaded`
- blocked: `False`
- model_load_state: `loaded`
- latency_ms: `32108.99`
- vram_peak_mb: `21141.57`

## Blockers

- none

## Artifacts

| artifact | present | bytes |
|---|---:|---:|
| `alpamayo_probe.json` | `True` | `443` |
| `gpu_snapshot.txt` | `True` | `66` |
| `package_versions.json` | `True` | `150` |
| `package_versions.txt` | `True` | `2115` |
| `memory_usage.json` | `True` | `217` |
| `probe.log` | `True` | `0` |

## Expected Adapter Schema

- status: `unverified_adapter_stub`
- trajectory target: `20 x 2` waypoints for 5 seconds at 4 Hz when available
- TASK-039 must replace this with observed input/output shape evidence before live CARLA control.

## Redacted Excerpt

```text

NVIDIA RTX 6000 Ada Generation, 570.124.06, 49140 MiB, 2 MiB, 8.9

Using Python 3.12.13 environment at: /workspace/alpamayo1.5/a1_5_venv
accelerate==1.12.0
-e file:///workspace/alpamayo1.5
antlr4-python3-runtime==4.9.3
asttokens==3.0.1
av==16.0.1
certifi==2025.11.12
cfgv==3.5.0
charset-normalizer==3.4.4
colorlog==6.10.1
comm==0.2.3
contourpy==1.3.3
cycler==0.12.1
debugpy==1.8.17
decorator==5.2.1
distlib==0.4.0
einops==0.8.1
executing==2.2.1
filelock==3.25.1
fonttools==4.61.0
fsspec==2025.10.0
hf-xet==1.2.0
huggingface-hub==0.36.0
hydra-colorlog==1.2.0
hydra-core==1.3.2
identify==2.6.17
idna==3.11
iniconfig==2.3.0
ipykernel==6.29.3
ipython==9.7.0
ipython-pygments-lexers==1.1.1
ipywidgets==8.1.8
jedi==0.19.2
jinja2==3.1.6
jupyter-client==8.6.3
jupyter-core==5.9.1
jupyterlab-widgets==3.0.16
kiwisolver==1.4.9
markupsafe==3.0.3
matplotlib==3.10.7
matplotlib-inline==0.2.1
mediapy==1.2.4
mpmath==1.3.0
nest-asyncio==1.6.0
networkx==3.6
nodeenv==1.10.0
numpy==2.3.5
nvidia-cublas-cu12==12.8.4.1
nvidia-cuda-cupti-cu12==12.8.90
nvidia-cuda-nvrtc-cu12==12.8.93
nvidia-cuda-runtime-cu12==12.8.90
nvidia-cudnn-cu12==9.10.2.21
nvidia-cufft-cu12==11.3.3.83
nvidia-cufile-cu12==1.13.1.3
nvidia-curand-cu12==10.3.9.90
nvidia-cusolver-cu12==11.7.3.90
nvidia-cusparse-cu12==12.5.8.93
nvidia-cusparselt-cu12==0.7.1
nvidia-nccl-cu12==2.27.3
nvidia-nvjitlink-cu12==12.8.93
nvidia-nvtx-cu12==12.8.90
omegaconf==2.3.0
packaging==25.0
pandas==2.3.3
parso==0.8.5
pexpect==4.9.0
physical-ai-av==0.2.0
pillow==12.0.0
platformdirs==4.5.0
pluggy==1.6.0
pre-commit==4.5.1
prompt-toolkit==3.0.52
psutil==7.1.3
ptyprocess==0.7.0
pure-eval==0.2.3
pyarrow==22.0.0
pygments==2.19.2
pyparsing==3.2.5
pytest==9.0.2
python-dateutil==2.9.0.post0
python-discovery==1.1.3
pytz==2025.2
pyyaml==6.0.3
pyzmq==27.1.0
regex==2025.11.3
requests==2.32.5
safetensors==0.7.0
scipy==1.16.3
seaborn==0.13.2
setuptools==80.9.0
six==1.17.0
stack-data==0.6.3
sympy==1.14.0
tokenizers==0.22.1
torch==2.8.0
torchvision==0.23.0
tornado==6.5.2
tqdm==4.67.1
traitlets==5.14.3
transformers==4.57.1
triton==3.4.0
typing-extensions==4.15.0
tzdata==2025.2
urllib3==2.5.0
virtualenv==21.2.0
wcwidth==0.2.14
widgetsnbextension==4.0.15

{"attn_implementation": "eager", "download_requested": false, "latency_ms": 32108.99, "load_requested": true, "model_class": "Alpamayo1_5", "model_id": "nvidia/Alpamayo-1.5-10B", "model_info": {"gated": false, "id": 
```
