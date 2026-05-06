"""Behavior template DSL for deterministic OOD actor traces."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from driverx.behaviors.library import default_behavior_plans
from driverx.behaviors.types import BehaviorPlan


@dataclass(frozen=True)
class BehaviorParameterSpec:
    name: str
    default: float | str | bool
    min_value: float | None = None
    max_value: float | None = None
    severity_weight: float = 1.0

    def sample(self, rng: random.Random, severity: int) -> float | str | bool:
        if self.min_value is None or self.max_value is None or isinstance(self.default, (str, bool)):
            return self.default
        severity_alpha = max(0.0, min(1.0, (severity - 1) / 4.0))
        jitter = rng.uniform(-0.2, 0.2) * (self.max_value - self.min_value)
        value = self.min_value + (self.max_value - self.min_value) * severity_alpha * self.severity_weight
        return round(max(self.min_value, min(self.max_value, value + jitter)), 4)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "default": self.default,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "severity_weight": self.severity_weight,
        }


@dataclass(frozen=True)
class BehaviorTemplate:
    template_id: str
    actor_kind: str
    duration_s: float
    dt_s: float
    parameter_specs: tuple[BehaviorParameterSpec, ...]
    tags: list[str]
    expected_pressure: str

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "actor_kind": self.actor_kind,
            "duration_s": self.duration_s,
            "dt_s": self.dt_s,
            "parameter_specs": [spec.to_jsonable() for spec in self.parameter_specs],
            "tags": self.tags,
            "expected_pressure": self.expected_pressure,
        }


@dataclass(frozen=True)
class BehaviorParameters:
    values: dict[str, float | str | bool]
    severity: int = 3
    variant_seed: int = 0

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "values": self.values,
            "severity": self.severity,
            "variant_seed": self.variant_seed,
        }


def default_behavior_templates() -> list[BehaviorTemplate]:
    templates: list[BehaviorTemplate] = []
    for plan in default_behavior_plans():
        templates.append(
            BehaviorTemplate(
                template_id=plan.behavior_id,
                actor_kind=plan.actor_kind,
                duration_s=plan.duration_s,
                dt_s=plan.dt_s,
                parameter_specs=tuple(_parameter_spec(key, value) for key, value in plan.parameters.items()),
                tags=list(plan.tags),
                expected_pressure=plan.expected_pressure,
            )
        )
    return templates


def compile_behavior_template(
    template: BehaviorTemplate,
    params: BehaviorParameters,
) -> BehaviorPlan:
    values = {spec.name: spec.default for spec in template.parameter_specs}
    values.update(params.values)
    return BehaviorPlan(
        behavior_id=template.template_id,
        actor_kind=template.actor_kind,
        duration_s=template.duration_s,
        dt_s=template.dt_s,
        parameters=values,
        tags=sorted(set([*template.tags, f"severity_{params.severity}", f"variant_{params.variant_seed}"])),
        expected_pressure=template.expected_pressure,
    )


def generate_behavior_variants(
    template_id: str,
    *,
    count: int,
    random_seed: int,
    severity: int,
    templates: list[BehaviorTemplate] | None = None,
) -> list[BehaviorPlan]:
    if count <= 0:
        raise ValueError("count must be positive.")
    template = _template_by_id(template_id, templates or default_behavior_templates())
    plans: list[BehaviorPlan] = []
    for index in range(count):
        variant_seed = random_seed + index
        rng = random.Random(f"{template_id}:{severity}:{variant_seed}")
        values = {
            spec.name: spec.sample(rng, severity)
            for spec in template.parameter_specs
        }
        plans.append(
            compile_behavior_template(
                template,
                BehaviorParameters(values=values, severity=severity, variant_seed=variant_seed),
            )
        )
    return plans


def _template_by_id(template_id: str, templates: list[BehaviorTemplate]) -> BehaviorTemplate:
    for template in templates:
        if template.template_id == template_id:
            return template
    raise ValueError(f"Unknown behavior template_id: {template_id}")


def _parameter_spec(key: str, value: float | str | bool) -> BehaviorParameterSpec:
    if isinstance(value, bool):
        return BehaviorParameterSpec(name=key, default=value)
    if isinstance(value, str):
        return BehaviorParameterSpec(name=key, default=value)
    numeric = float(value)
    if key in {"speed_mps", "approach_speed_mps"}:
        return BehaviorParameterSpec(key, numeric, max(0.2, numeric * 0.55), numeric * 1.45)
    if key in {"final_speed_mps"}:
        return BehaviorParameterSpec(key, numeric, max(0.0, numeric * 0.3), max(numeric * 1.8, numeric + 0.5))
    if key in {"brake_time_s", "push_start_s", "swerve_start_s"}:
        return BehaviorParameterSpec(key, numeric, max(0.2, numeric - 0.8), numeric + 0.8, severity_weight=0.35)
    if "y" in key or key in {"weave_m", "radius_m"}:
        return BehaviorParameterSpec(key, numeric, numeric - 1.0, numeric + 1.0, severity_weight=0.8)
    if "x" in key:
        return BehaviorParameterSpec(key, numeric, numeric - 4.0, numeric + 4.0, severity_weight=0.6)
    return BehaviorParameterSpec(key, numeric, numeric * 0.7, numeric * 1.3)


__all__ = [
    "BehaviorParameterSpec",
    "BehaviorParameters",
    "BehaviorTemplate",
    "compile_behavior_template",
    "default_behavior_templates",
    "generate_behavior_variants",
]
