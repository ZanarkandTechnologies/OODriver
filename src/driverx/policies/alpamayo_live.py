"""Open-loop Alpamayo live policy adapter and artifact writer."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.core.types import DrivingIntent, TrajectoryCandidate
from driverx.policies.alpamayo_materializer import (
    AlpamayoTensorManifest,
    materialize_alpamayo_input,
    write_alpamayo_tensor_materialization,
)
from driverx.policies.alpamayo_probe import DEFAULT_ALPAMAYO_MODEL_ID
from driverx.policies.alpamayo_trajectory import alpamayo_prediction_to_trajectory
from driverx.policies.types import (
    PolicyAction,
    PolicyAdapter,
    PolicyContext,
    PolicyDecision,
    PolicySetupError,
)


@dataclass(frozen=True)
class AlpamayoLiveDecisionBundle:
    decision: PolicyDecision
    manifest: AlpamayoTensorManifest
    prediction_summary: dict[str, Any]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "policy_decision": self.decision.to_jsonable(),
            "tensor_manifest": self.manifest.to_jsonable(),
            "prediction_summary": self.prediction_summary,
            "open_loop_policy_evaluation": True,
        }


class AlpamayoLiveAdapter:
    """Open-loop adapter that consumes saved live Alpamayo prediction payloads."""

    policy_id = "alpamayo-live"

    def decide(self, context: PolicyContext) -> PolicyDecision:
        package_path = _metadata_path(context, "alpamayo_package_path")
        prediction_json = _metadata_path(context, "alpamayo_prediction_json")
        if package_path is None or prediction_json is None:
            raise PolicySetupError(
                "Use run-alpamayo-live, or pass --alpamayo-package and "
                "--alpamayo-prediction-json to run-policy-fixture before selecting alpamayo-live."
            )
        bundle = build_alpamayo_live_decision(
            package_path=package_path,
            prediction_json=prediction_json,
            model_id=str(context.metadata.get("alpamayo_model_id", DEFAULT_ALPAMAYO_MODEL_ID)),
            run_id=str(context.metadata.get("alpamayo_run_id", "policy-fixture")),
        )
        return bundle.decision


def build_alpamayo_live_decision(
    *,
    package_path: Path,
    prediction_json: Path,
    model_id: str = DEFAULT_ALPAMAYO_MODEL_ID,
    run_id: str = "alpamayo-live",
    sample_index: int = 0,
) -> AlpamayoLiveDecisionBundle:
    """Build a DriverX policy decision from a live Alpamayo prediction payload."""

    manifest = materialize_alpamayo_input(package_path)
    if manifest.validation_errors:
        raise ValueError(
            "Alpamayo package is not torch-ready: " + "; ".join(manifest.validation_errors)
        )
    prediction_payload = _load_prediction_payload(prediction_json)
    pred_xyz = _prediction_value(prediction_payload, "pred_xyz")
    trajectory = alpamayo_prediction_to_trajectory(
        pred_xyz,
        sample_index=sample_index,
        source="alpamayo_live_open_loop",
        score=_trajectory_score(prediction_payload),
        reasoning=_cot_summary(prediction_payload),
    )
    prediction_summary = _prediction_summary(
        prediction_payload,
        prediction_json=prediction_json,
        model_id=model_id,
        run_id=run_id,
    )
    decision = _policy_decision(
        manifest=manifest,
        trajectory=trajectory,
        prediction_summary=prediction_summary,
        reasoning=_cot_summary(prediction_payload),
    )
    return AlpamayoLiveDecisionBundle(
        decision=decision,
        manifest=manifest,
        prediction_summary=prediction_summary,
    )


def run_alpamayo_live_package(
    *,
    package_path: Path,
    prediction_json: Path,
    output_root: Path,
    run_id: str,
    model_id: str = DEFAULT_ALPAMAYO_MODEL_ID,
    sample_index: int = 0,
) -> dict[str, Any]:
    """Write open-loop Alpamayo policy artifacts from a saved live prediction."""

    run_dir = prepare_run_dir(output_root, run_id)
    bundle = build_alpamayo_live_decision(
        package_path=package_path,
        prediction_json=prediction_json,
        model_id=model_id,
        run_id=run_dir.name,
        sample_index=sample_index,
    )
    manifest_summary = write_alpamayo_tensor_materialization(run_dir, bundle.manifest)
    payload = bundle.to_jsonable()
    payload["manifest_path"] = manifest_summary["json_path"]
    payload["run_dir"] = str(run_dir)
    json_path = run_dir / "alpamayo_policy_decision.json"
    report_path = run_dir / "alpamayo_policy_report.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    payload["json_path"] = str(json_path)
    payload["report_path"] = str(report_path)
    return payload


def _metadata_path(context: PolicyContext, key: str) -> Path | None:
    value = context.metadata.get(key)
    if value is None:
        return None
    return value if isinstance(value, Path) else Path(str(value))


def _load_prediction_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {"pred_xyz": payload}
    return payload


def _prediction_value(payload: dict[str, Any], key: str) -> Any:
    if key in payload:
        return payload[key]
    outputs = payload.get("outputs")
    if isinstance(outputs, dict) and key in outputs:
        return outputs[key]
    raise ValueError(f"Alpamayo prediction payload is missing {key}.")


def _prediction_summary(
    payload: dict[str, Any],
    *,
    prediction_json: Path,
    model_id: str,
    run_id: str,
) -> dict[str, Any]:
    pred_xyz = _prediction_value(payload, "pred_xyz")
    pred_rot = payload.get("pred_rot")
    return {
        "prediction_json": str(prediction_json),
        "model_id": str(payload.get("model_id") or model_id),
        "run_id": str(payload.get("run_id") or run_id),
        "latency_ms": _maybe_number(payload.get("latency_ms")),
        "vram_peak_mb": _maybe_number(payload.get("vram_peak_mb")),
        "output_shapes": {
            "pred_xyz": payload.get("output_shapes", {}).get("pred_xyz")
            if isinstance(payload.get("output_shapes"), dict)
            else _nested_shape(pred_xyz),
            "pred_rot": payload.get("output_shapes", {}).get("pred_rot")
            if isinstance(payload.get("output_shapes"), dict)
            else _nested_shape(pred_rot),
            "extra.cot": payload.get("output_shapes", {}).get("extra.cot")
            if isinstance(payload.get("output_shapes"), dict)
            else None,
        },
        "cot_summary": _cot_summary(payload),
    }


def _policy_decision(
    *,
    manifest: AlpamayoTensorManifest,
    trajectory: TrajectoryCandidate,
    prediction_summary: dict[str, Any],
    reasoning: str,
) -> PolicyDecision:
    target_speed = _estimate_initial_speed(trajectory.points_xy)
    intent = DrivingIntent(
        scene_type=f"alpamayo_carla_capture:{manifest.frame_name}",
        hazards=["open-loop live Alpamayo trajectory", *(_memory_hazard(manifest))],
        ego_intent="evaluate Alpamayo trajectory intent without closed-loop actuation",
        target_behavior="open_loop_trajectory_eval",
        speed_profile="trajectory_chunk",
        lateral_bias="center",
        uncertainty=0.4 if reasoning else 0.55,
    )
    action = PolicyAction(
        mode="trajectory_chunk_open_loop",
        trajectory=trajectory,
        control={
            "target_speed_mps": target_speed,
            "closed_loop_control": False,
            "open_loop_policy_evaluation": True,
            "model_latency_ms": prediction_summary.get("latency_ms") or 0.0,
            "vram_peak_mb": prediction_summary.get("vram_peak_mb") or 0.0,
        },
        safety_notes=[
            "Alpamayo output is evaluated as trajectory intent only; CARLA steering is not enabled in TASK-039.",
            "Trajectory is converted from native 64x3 at 10Hz to DriverX 20x2 at 4Hz.",
        ],
    )
    return PolicyDecision(
        policy_id="alpamayo-live",
        adapter_kind="alpamayo_open_loop",
        intent=intent,
        action=action,
        latency_ms=float(prediction_summary.get("latency_ms") or 0.0),
        reason_summary=reasoning or "Alpamayo produced a trajectory without a usable chain-of-causation excerpt.",
        retrieved_memory_ids=[],
    )


def _memory_hazard(manifest: AlpamayoTensorManifest) -> list[str]:
    if manifest.memory_context_count <= 0:
        return []
    return [f"{manifest.memory_context_count} retrieved DriverX memory entries were provided prompt-side"]


def _cot_summary(payload: dict[str, Any]) -> str:
    for key in ("cot_summary", "cot", "reasoning"):
        value = payload.get(key)
        if value is not None:
            return _first_text(value)
    extra = payload.get("extra")
    if isinstance(extra, dict) and extra.get("cot") is not None:
        return _first_text(extra["cot"])
    return ""


def _first_text(value: Any) -> str:
    if isinstance(value, str):
        return value[:1000]
    if isinstance(value, list | tuple):
        current = value
        while isinstance(current, list | tuple) and current:
            current = current[0]
        return str(current)[:1000]
    return str(value)[:1000]


def _trajectory_score(payload: dict[str, Any]) -> float:
    value = payload.get("score")
    number = _maybe_number(value)
    return number if number is not None else 0.0


def _estimate_initial_speed(points_xy: list[tuple[float, float]]) -> float:
    if len(points_xy) < 2:
        return 0.0
    dx = points_xy[1][0] - points_xy[0][0]
    dy = points_xy[1][1] - points_xy[0][1]
    return round((dx * dx + dy * dy) ** 0.5 * 4.0, 4)


def _maybe_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _nested_shape(value: Any) -> list[int] | None:
    if value is None:
        return None
    shape: list[int] = []
    current = value
    while isinstance(current, list):
        shape.append(len(current))
        if not current:
            break
        current = current[0]
    return shape


def _markdown(payload: dict[str, Any]) -> str:
    decision = payload["policy_decision"]
    summary = payload["prediction_summary"]
    return "\n".join(
        [
            "# Alpamayo Live Policy Decision",
            "",
            f"- policy_id: `{decision['policy_id']}`",
            f"- adapter_kind: `{decision['adapter_kind']}`",
            f"- open_loop_policy_evaluation: `{payload['open_loop_policy_evaluation']}`",
            f"- model_id: `{summary['model_id']}`",
            f"- latency_ms: `{summary['latency_ms']}`",
            f"- vram_peak_mb: `{summary['vram_peak_mb']}`",
            f"- pred_xyz_shape: `{summary['output_shapes']['pred_xyz']}`",
            f"- action_mode: `{decision['action']['mode']}`",
            "",
            "## Chain Of Causation",
            "",
            summary.get("cot_summary") or "No chain-of-causation excerpt was available.",
            "",
        ]
    )


__all__ = [
    "AlpamayoLiveAdapter",
    "AlpamayoLiveDecisionBundle",
    "build_alpamayo_live_decision",
    "run_alpamayo_live_package",
]
