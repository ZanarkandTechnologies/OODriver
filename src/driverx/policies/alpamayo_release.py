"""Alpamayo release contract extraction without loading model weights."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.policies.alpamayo_probe import DEFAULT_ALPAMAYO_MODEL_ID

DEFAULT_ALPAMAYO_RELEASE_ROOT = Path("../external/alpamayo1.5")

CAMERA_DISPLAY_NAMES: dict[int, str] = {
    0: "Front left camera",
    1: "Front camera",
    2: "Front right camera",
    3: "Rear left camera",
    4: "Rear camera",
    5: "Rear right camera",
    6: "Front telephoto camera",
}
DEFAULT_CAMERA_INDICES = [0, 1, 2, 6]
DEFAULT_NUM_FRAMES_PER_CAMERA = 4
DEFAULT_HISTORY_STEPS = 16
DEFAULT_FUTURE_STEPS = 64
DEFAULT_HZ = 10
DRIVERX_TARGET_STEPS = 20
DRIVERX_TARGET_HZ = 4


@dataclass(frozen=True)
class AlpamayoReleaseContract:
    model_id: str
    release_root: Path
    source_available: bool
    source_commit: str | None
    environment: dict[str, Any]
    hardware_requirements: list[dict[str, Any]]
    camera_contract: dict[str, Any]
    input_contract: dict[str, Any]
    inference_methods: list[dict[str, Any]]
    output_contract: dict[str, Any]
    driverx_adapter_plan: list[str]
    setup_commands: list[str]
    blockers: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "release_root": str(self.release_root),
            "source_available": self.source_available,
            "source_commit": self.source_commit,
            "environment": self.environment,
            "hardware_requirements": self.hardware_requirements,
            "camera_contract": self.camera_contract,
            "input_contract": self.input_contract,
            "inference_methods": self.inference_methods,
            "output_contract": self.output_contract,
            "driverx_adapter_plan": self.driverx_adapter_plan,
            "setup_commands": self.setup_commands,
            "blockers": self.blockers,
        }


def inspect_alpamayo_release(
    release_root: Path = DEFAULT_ALPAMAYO_RELEASE_ROOT,
    *,
    model_id: str = DEFAULT_ALPAMAYO_MODEL_ID,
) -> AlpamayoReleaseContract:
    """Inspect a local Alpamayo release checkout without importing it."""

    root = release_root.expanduser()
    readme = _read_text(root / "README.md")
    loader = _read_text(root / "src" / "alpamayo1_5" / "load_physical_aiavdataset.py")
    helper = _read_text(root / "src" / "alpamayo1_5" / "helper.py")
    model = _read_text(root / "src" / "alpamayo1_5" / "models" / "alpamayo1_5.py")
    base_model = _read_text(root / "src" / "alpamayo1_5" / "models" / "base_model.py")
    test_inference = _read_text(root / "src" / "alpamayo1_5" / "test_inference.py")

    blockers = _blockers(root, readme, loader, model)
    source_available = not blockers or all(
        not blocker.startswith("Missing Alpamayo release") for blocker in blockers
    )

    return AlpamayoReleaseContract(
        model_id=model_id,
        release_root=root,
        source_available=source_available,
        source_commit=_git_commit(root),
        environment=_environment_contract(readme),
        hardware_requirements=_hardware_requirements(readme),
        camera_contract=_camera_contract(loader, helper),
        input_contract=_input_contract(loader),
        inference_methods=_inference_methods(readme, model, base_model),
        output_contract=_output_contract(readme, model, test_inference),
        driverx_adapter_plan=_driverx_adapter_plan(),
        setup_commands=_setup_commands(readme),
        blockers=blockers,
    )


def write_alpamayo_release_contract(
    run_dir: Path,
    *,
    release_root: Path = DEFAULT_ALPAMAYO_RELEASE_ROOT,
    model_id: str = DEFAULT_ALPAMAYO_MODEL_ID,
) -> dict[str, Any]:
    """Write JSON and Markdown contract artifacts for a local release checkout."""

    run_dir.mkdir(parents=True, exist_ok=True)
    contract = inspect_alpamayo_release(release_root, model_id=model_id)
    payload = contract.to_jsonable()
    json_path = run_dir / "alpamayo_release_contract.json"
    report_path = run_dir / "alpamayo_release_contract.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _git_commit(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
    except Exception:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _blockers(root: Path, readme: str, loader: str, model: str) -> list[str]:
    blockers: list[str] = []
    if not root.exists():
        blockers.append(f"Missing Alpamayo release checkout: {root}")
    if not readme:
        blockers.append("Missing Alpamayo README.md; using conservative defaults.")
    if not loader:
        blockers.append("Missing load_physical_aiavdataset.py; input tensor shapes are inferred.")
    if not model:
        blockers.append("Missing models/alpamayo1_5.py; method signatures are inferred.")
    return blockers


def _environment_contract(readme: str) -> dict[str, Any]:
    python_version = _first_match(readme, r"Python\s+([0-9.]+)") or "3.12"
    cuda_version = _first_match(readme, r"CUDA Toolkit\s+([0-9.x]+)") or "12.x"
    return {
        "python": python_version,
        "cuda_toolkit": cuda_version,
        "package_manager": "uv",
        "attention_default": "flash-attn 2 when nvcc is available",
        "attention_fallback": "PyTorch SDPA via uv sync --active --no-install-package flash-attn",
        "model_weights_gb": 22,
        "requires_hf_model_access": True,
        "requires_hf_dataset_access": True,
    }


def _hardware_requirements(readme: str) -> list[dict[str, Any]]:
    rows = [
        {
            "mode": "single_sample",
            "num_traj_samples": 1,
            "cfg": False,
            "vram_gb": 24,
        },
        {
            "mode": "multi_sample",
            "num_traj_samples": 16,
            "cfg": False,
            "vram_gb": 40,
        },
        {
            "mode": "multi_sample_cfg",
            "num_traj_samples": 16,
            "cfg": True,
            "vram_gb": 60,
        },
    ]
    if "Measured on an NVIDIA H100 80GB GPU" in readme:
        for row in rows:
            row["measured_on"] = "NVIDIA H100 80GB"
    return rows


def _camera_contract(loader: str, helper: str) -> dict[str, Any]:
    camera_indices = _camera_indices_from_loader(loader) or DEFAULT_CAMERA_INDICES
    return {
        "default_camera_indices": camera_indices,
        "default_camera_names": [CAMERA_DISPLAY_NAMES[index] for index in camera_indices],
        "all_camera_display_names": CAMERA_DISPLAY_NAMES,
        "num_frames_per_camera": _int_default_from_signature(
            loader,
            "num_frames",
            DEFAULT_NUM_FRAMES_PER_CAMERA,
        ),
        "message_order": "camera-major, then temporal frame index per camera",
        "camera_id_annotations": "first frame of each camera group is prefixed with camera display name",
        "helper_camera_names_found": all(name in helper for name in CAMERA_DISPLAY_NAMES.values()),
    }


def _input_contract(loader: str) -> dict[str, Any]:
    history_steps = _int_default_from_signature(loader, "num_history_steps", DEFAULT_HISTORY_STEPS)
    future_steps = _int_default_from_signature(loader, "num_future_steps", DEFAULT_FUTURE_STEPS)
    time_step = _float_default_from_signature(loader, "time_step", 0.1)
    hz = round(1.0 / time_step) if time_step > 0 else DEFAULT_HZ
    return {
        "image_frames": {
            "shape": "N_cameras x num_frames x 3 x H x W",
            "dtype": "uint8 tensor",
        },
        "camera_indices": {
            "shape": "N_cameras",
            "dtype": "int64 tensor",
        },
        "ego_history_xyz": {
            "shape": f"1 x 1 x {history_steps} x 3",
            "frame": "ego-local at current timestamp",
            "rate_hz": hz,
        },
        "ego_history_rot": {
            "shape": f"1 x 1 x {history_steps} x 3 x 3",
            "frame": "ego-local rotation matrices",
            "rate_hz": hz,
        },
        "navigation": {
            "nav_text": "optional text inside <|route_start|>...<|route_end|>",
            "examples": ["Turn left in 11m", "Turn right in 30m"],
        },
        "future_reference": {
            "ego_future_xyz": f"1 x 1 x {future_steps} x 3",
            "used_for": "offline ADE only, not required for live policy input",
        },
    }


def _inference_methods(readme: str, model: str, base_model: str) -> list[dict[str, Any]]:
    methods = [
        {
            "name": "sample_trajectories_from_data_with_vlm_rollout",
            "kind": "trajectory_policy",
            "returns": ["pred_xyz", "pred_rot", "extra when return_extra=True"],
            "supports_reasoning": True,
            "supports_navigation": "sample_trajectories_from_data_with_vlm_rollout_cfg_nav" in model
            or "Navigation conditioning" in readme,
        },
        {
            "name": "generate_text",
            "kind": "visual_question_answering",
            "returns": ["cot", "meta_action", "answer"],
            "supports_reasoning": True,
            "supports_navigation": False,
        },
    ]
    if "generate_text" not in base_model:
        methods[1]["blocker"] = "generate_text not found in local base_model.py"
    return methods


def _output_contract(readme: str, model: str, test_inference: str) -> dict[str, Any]:
    future_steps = DEFAULT_FUTURE_STEPS
    if "64 waypoints at 10 Hz" in readme:
        future_steps = 64
    return {
        "native_pred_xyz": {
            "shape": f"B x num_traj_sets x num_traj_samples x {future_steps} x 3",
            "rate_hz": DEFAULT_HZ,
            "horizon_s": future_steps / DEFAULT_HZ,
            "coordinate_frame": "ego-local xyz",
        },
        "native_pred_rot": {
            "shape": f"B x num_traj_sets x num_traj_samples x {future_steps} x 3 x 3",
            "rate_hz": DEFAULT_HZ,
            "required_for_driverx_first_pass": False,
        },
        "extra_reasoning": {
            "field": "extra['cot']",
            "shape": "B x num_traj_sets x num_traj_samples",
            "present_when": "return_extra=True",
            "observed_in_test_script": "extra[\"cot\"]" in test_inference,
        },
        "driverx_policy_target": {
            "shape": f"{DRIVERX_TARGET_STEPS} x 2",
            "rate_hz": DRIVERX_TARGET_HZ,
            "horizon_s": DRIVERX_TARGET_STEPS / DRIVERX_TARGET_HZ,
            "conversion": "select/rank one native sample, take xy, resample 10 Hz to 4 Hz over first 5 seconds",
        },
        "method_signature_found": "sample_trajectories_from_data_with_vlm_rollout" in model,
    }


def _driverx_adapter_plan() -> list[str]:
    return [
        "Capture CARLA RGB into Alpamayo camera-major windows with four frames per camera.",
        "Map CARLA sensors to Alpamayo camera ids 0, 1, 2, and optionally 6 for front telephoto.",
        "Convert recent CARLA ego transforms into ego_history_xyz and ego_history_rot in ego-local frame.",
        "Inject route or scenario guidance as nav_text when the route command is known.",
        "Run num_traj_samples=1 first on 24GB+ VRAM; expand samples only after latency and VRAM are measured.",
        "Convert native pred_xyz samples to DriverX 20 x 2 trajectory chunks by xy extraction and 10Hz-to-4Hz resampling.",
        "Persist CoC reasoning and selected trajectory metadata for OOD failure-memory retrieval.",
    ]


def _setup_commands(readme: str) -> list[str]:
    commands = [
        "curl -LsSf https://astral.sh/uv/install.sh | sh",
        "uv venv a1_5_venv",
        "source a1_5_venv/bin/activate",
        "uv sync --active",
        "hf auth login",
        "python src/alpamayo1_5/test_inference.py",
    ]
    if "--no-install-package flash-attn" in readme:
        commands.insert(4, "uv sync --active --no-install-package flash-attn")
    return commands


def _camera_indices_from_loader(loader: str) -> list[int]:
    features = [
        ("CAMERA_CROSS_LEFT_120FOV", 0),
        ("CAMERA_FRONT_WIDE_120FOV", 1),
        ("CAMERA_CROSS_RIGHT_120FOV", 2),
        ("CAMERA_FRONT_TELE_30FOV", 6),
    ]
    indices = [index for token, index in features if token in loader]
    return indices if len(indices) >= 3 else []


def _int_default_from_signature(text: str, name: str, fallback: int) -> int:
    matched = _first_match(text, rf"{re.escape(name)}:\s*[^=]+=\s*([0-9_]+)")
    if matched is None:
        return fallback
    return int(matched.replace("_", ""))


def _float_default_from_signature(text: str, name: str, fallback: float) -> float:
    matched = _first_match(text, rf"{re.escape(name)}:\s*[^=]+=\s*([0-9.]+)")
    if matched is None:
        return fallback
    return float(matched)


def _first_match(text: str, pattern: str) -> str | None:
    matched = re.search(pattern, text)
    return matched.group(1) if matched else None


def _markdown(payload: dict[str, Any]) -> str:
    hardware = payload.get("hardware_requirements", [])
    lines = [
        "# Alpamayo Release Contract",
        "",
        f"- model_id: `{payload.get('model_id')}`",
        f"- release_root: `{payload.get('release_root')}`",
        f"- source_available: `{payload.get('source_available')}`",
        f"- source_commit: `{payload.get('source_commit')}`",
        "",
        "## Runtime",
        "",
        f"- python: `{payload.get('environment', {}).get('python')}`",
        f"- cuda_toolkit: `{payload.get('environment', {}).get('cuda_toolkit')}`",
        f"- attention_fallback: {payload.get('environment', {}).get('attention_fallback')}",
        "",
        "## Hardware",
        "",
        "| mode | samples | cfg | vram_gb |",
        "|---|---:|---|---:|",
    ]
    for row in hardware:
        lines.append(
            f"| {row.get('mode')} | {row.get('num_traj_samples')} | {row.get('cfg')} | {row.get('vram_gb')} |"
        )
    camera = payload.get("camera_contract", {})
    output = payload.get("output_contract", {})
    lines.extend(
        [
            "",
            "## Cameras",
            "",
            f"- default_camera_indices: `{camera.get('default_camera_indices')}`",
            f"- default_camera_names: `{camera.get('default_camera_names')}`",
            f"- num_frames_per_camera: `{camera.get('num_frames_per_camera')}`",
            "",
            "## Native Output",
            "",
            f"- pred_xyz: `{output.get('native_pred_xyz', {}).get('shape')}`",
            f"- driverx target: `{output.get('driverx_policy_target', {}).get('shape')}`",
            "",
            "## Adapter Plan",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload.get("driverx_adapter_plan", []))
    blockers = payload.get("blockers", [])
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {blocker}" for blocker in blockers)
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "AlpamayoReleaseContract",
    "DEFAULT_ALPAMAYO_RELEASE_ROOT",
    "inspect_alpamayo_release",
    "write_alpamayo_release_contract",
]
