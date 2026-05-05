#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "usage: $0 user@host [local-output-dir]" >&2
  exit 2
fi

REMOTE="$1"
ENV_FILE="${DRIVERX_ENV_FILE:-.env}"
if [ -f "${ENV_FILE}" ]; then
  set -a
  # shellcheck disable=SC1090
  . "${ENV_FILE}"
  set +a
fi
RUN_ID="${RUN_ID:-alpamayo-probe-$(date -u +%Y%m%dT%H%M%SZ)}"
REMOTE_ROOT="${REMOTE_ROOT:-/workspace/0xdriver-artifacts/alpamayo-probe/$RUN_ID}"
LOCAL_OUTPUT="${2:-${LOCAL_OUTPUT:-artifacts/remote/alpamayo-probe/$RUN_ID}}"
MODEL_ID="${ALPAMAYO_REPO_ID:-nvidia/Alpamayo-1.5-10B}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ALPAMAYO_DOWNLOAD="${ALPAMAYO_DOWNLOAD:-0}"
ALPAMAYO_LOAD="${ALPAMAYO_LOAD:-0}"
REMOTE_CACHE_ROOT="${REMOTE_CACHE_ROOT:-/workspace/.cache/driverx}"
SSH_OPTIONS="${GPU_SSH_OPTS:-${SSH_OPTS:-}}"
SSH_RSH="ssh ${SSH_OPTIONS} -o StrictHostKeyChecking=accept-new"

ssh ${SSH_OPTIONS} -o StrictHostKeyChecking=accept-new "$REMOTE" "mkdir -p '$REMOTE_ROOT' '$REMOTE_CACHE_ROOT'"

if [ -n "${HF_TOKEN:-}" ]; then
  printf '%s' "$HF_TOKEN" | ssh ${SSH_OPTIONS} "$REMOTE" "cat > '$REMOTE_ROOT/.hf_token' && chmod 600 '$REMOTE_ROOT/.hf_token'"
fi

ssh ${SSH_OPTIONS} "$REMOTE" "cat > '$REMOTE_ROOT/probe.py'" <<'PY'
from __future__ import annotations

import json
import os
import subprocess
import time
import traceback
from pathlib import Path


def run(command: list[str]) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=45,
        )
        return completed.returncode, completed.stdout
    except Exception as exc:
        return 1, f"{type(exc).__name__}: {exc}"


def redact(text: str) -> str:
    token = os.environ.get("HF_TOKEN", "")
    if token:
        text = text.replace(token, "[REDACTED]")
    return text


remote_root = Path(os.environ["REMOTE_ROOT"])
model_id = os.environ["MODEL_ID"]
download = os.environ.get("ALPAMAYO_DOWNLOAD") == "1"
load_model = os.environ.get("ALPAMAYO_LOAD") == "1"
token_file = remote_root / ".hf_token"
if token_file.exists():
    os.environ["HF_TOKEN"] = token_file.read_text(encoding="utf-8").strip()

log_lines: list[str] = []
probe: dict[str, object] = {
    "model_id": model_id,
    "model_load_state": "not_requested",
    "download_requested": download,
    "load_requested": load_model,
}
memory: dict[str, object] = {}

code, gpu_snapshot = run(
    [
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,memory.used,compute_cap",
        "--format=csv,noheader",
    ]
)
(remote_root / "gpu_snapshot.txt").write_text(gpu_snapshot, encoding="utf-8")
probe["nvidia_smi_exit_code"] = code

code, freeze = run([os.environ.get("PYTHON_BIN", "python3"), "-m", "pip", "freeze"])
if code != 0:
    code, freeze = run(["uv", "pip", "freeze", "--python", os.environ.get("PYTHON_BIN", "python3")])
(remote_root / "package_versions.txt").write_text(redact(freeze), encoding="utf-8")
packages = {"pip_freeze_exit_code": code, "python": os.environ.get("PYTHON_BIN", "python3")}

try:
    import torch

    packages["torch_version"] = torch.__version__
    packages["cuda_available"] = torch.cuda.is_available()
    if torch.cuda.is_available():
        device = torch.cuda.current_device()
        props = torch.cuda.get_device_properties(device)
        memory["torch"] = {
            "device_name": props.name,
            "compute_capability": f"{props.major}.{props.minor}",
            "total_memory_mb": round(props.total_memory / 1024 / 1024, 2),
            "allocated_mb": round(torch.cuda.memory_allocated(device) / 1024 / 1024, 2),
            "reserved_mb": round(torch.cuda.memory_reserved(device) / 1024 / 1024, 2),
        }
    else:
        probe["model_load_state"] = "blocked"
        probe["error"] = "CUDA is not available."
except Exception as exc:
    packages["torch_error"] = f"{type(exc).__name__}: {exc}"
    log_lines.append(traceback.format_exc())

try:
    from huggingface_hub import model_info, snapshot_download

    started = time.perf_counter()
    info = model_info(model_id, token=os.environ.get("HF_TOKEN") or None)
    probe["model_info_latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
    probe["model_info"] = {
        "id": getattr(info, "id", model_id),
        "sha": getattr(info, "sha", None),
        "private": getattr(info, "private", None),
        "gated": getattr(info, "gated", None),
    }
    if download:
        started = time.perf_counter()
        path = snapshot_download(model_id, token=os.environ.get("HF_TOKEN") or None)
        probe["snapshot_path"] = path
        probe["download_latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
except Exception as exc:
    probe["model_load_state"] = "blocked"
    probe["error"] = f"{type(exc).__name__}: {exc}"
    log_lines.append(traceback.format_exc())

if load_model and probe.get("error") is None:
    started = time.perf_counter()
    try:
        import torch
        try:
            from alpamayo1_5.models.alpamayo1_5 import Alpamayo1_5

            Alpamayo1_5.from_pretrained(
                model_id,
                token=os.environ.get("HF_TOKEN") or None,
                dtype=torch.bfloat16,
                attn_implementation="sdpa",
            ).to("cuda")
            probe["model_class"] = "Alpamayo1_5"
        except Exception as alpamayo_exc:
            log_lines.append("Alpamayo1_5 load failed; trying transformers auto fallback.")
            log_lines.append(traceback.format_exc())
            from transformers import AutoModelForCausalLM, AutoModelForVision2Seq, AutoProcessor

            probe["alpamayo_class_error"] = f"{type(alpamayo_exc).__name__}: {alpamayo_exc}"
            AutoProcessor.from_pretrained(model_id, token=os.environ.get("HF_TOKEN") or None, trust_remote_code=True)
            try:
                AutoModelForVision2Seq.from_pretrained(
                    model_id,
                    token=os.environ.get("HF_TOKEN") or None,
                    trust_remote_code=True,
                    torch_dtype=torch.bfloat16,
                    device_map="auto",
                )
                probe["model_class"] = "AutoModelForVision2Seq"
            except Exception:
                AutoModelForCausalLM.from_pretrained(
                    model_id,
                    token=os.environ.get("HF_TOKEN") or None,
                    trust_remote_code=True,
                    torch_dtype=torch.bfloat16,
                    device_map="auto",
                )
                probe["model_class"] = "AutoModelForCausalLM"
        probe["model_load_state"] = "loaded"
    except Exception as exc:
        probe["model_load_state"] = "failed"
        probe["error"] = f"{type(exc).__name__}: {exc}"
        log_lines.append(traceback.format_exc())
    finally:
        probe["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)

try:
    import torch

    if torch.cuda.is_available():
        device = torch.cuda.current_device()
        memory.setdefault("torch", {})
        memory["torch"]["vram_peak_mb"] = round(torch.cuda.max_memory_allocated(device) / 1024 / 1024, 2)
except Exception:
    pass

(remote_root / "package_versions.json").write_text(json.dumps(packages, indent=2), encoding="utf-8")
(remote_root / "memory_usage.json").write_text(json.dumps(memory, indent=2), encoding="utf-8")
(remote_root / "alpamayo_probe.json").write_text(json.dumps(probe, indent=2), encoding="utf-8")
(remote_root / "probe.log").write_text(redact("\n".join(log_lines)), encoding="utf-8")
PY

ssh ${SSH_OPTIONS} "$REMOTE" "PATH=\"\$HOME/.local/bin:\$PATH\" REMOTE_ROOT='$REMOTE_ROOT' MODEL_ID='$MODEL_ID' ALPAMAYO_DOWNLOAD='$ALPAMAYO_DOWNLOAD' ALPAMAYO_LOAD='$ALPAMAYO_LOAD' PYTHON_BIN='$PYTHON_BIN' XDG_CACHE_HOME='$REMOTE_CACHE_ROOT' UV_CACHE_DIR='$REMOTE_CACHE_ROOT/uv' HF_HOME='$REMOTE_CACHE_ROOT/huggingface' TRANSFORMERS_CACHE='$REMOTE_CACHE_ROOT/huggingface' HF_HUB_CACHE='$REMOTE_CACHE_ROOT/huggingface/hub' '$PYTHON_BIN' '$REMOTE_ROOT/probe.py'; rm -f '$REMOTE_ROOT/.hf_token'"

mkdir -p "$LOCAL_OUTPUT"
rsync -rltz --prune-empty-dirs \
  -e "${SSH_RSH}" \
  --no-owner \
  --no-group \
  --include='*/' \
  --include='alpamayo_probe.json' \
  --include='gpu_snapshot.txt' \
  --include='package_versions.json' \
  --include='package_versions.txt' \
  --include='memory_usage.json' \
  --include='probe.log' \
  --exclude='*' \
  "$REMOTE:${REMOTE_ROOT%/}/" \
  "$LOCAL_OUTPUT/" || {
    echo "rsync pullback failed; falling back to ssh tar stream." >&2
    ssh ${SSH_OPTIONS} "$REMOTE" "cd '$REMOTE_ROOT' && files=''; for f in alpamayo_probe.json gpu_snapshot.txt package_versions.json package_versions.txt memory_usage.json probe.log; do if [ -e \"\$f\" ]; then files=\"\$files \$f\"; fi; done; if [ -n \"\$files\" ]; then tar -cf - \$files; fi" \
      | tar -xf - -C "$LOCAL_OUTPUT" || true
  }

PYTHONPATH="${PYTHONPATH:-src}" python3 -m driverx probe-alpamayo \
  --artifact-root "$LOCAL_OUTPUT" \
  --model-id "$MODEL_ID" \
  --output-root "$(dirname "$LOCAL_OUTPUT")" \
  --run-id "$(basename "$LOCAL_OUTPUT")-summary"
