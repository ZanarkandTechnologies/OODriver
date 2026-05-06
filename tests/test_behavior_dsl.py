import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.behaviors import (
    BehaviorParameters,
    BehaviorConstraints,
    compile_behavior_template,
    default_behavior_templates,
    generate_behavior_variants,
    simulate_behavior,
    validate_behavior_plan,
    write_behavior_validation_report,
)
from driverx.cli import main


class BehaviorDslTest(unittest.TestCase):
    def test_default_templates_compile_to_supported_plans(self) -> None:
        templates = default_behavior_templates()
        template = next(item for item in templates if item.template_id == "motorcycle_filtering")
        plan = compile_behavior_template(
            template,
            params=_params_from_defaults(template),
        )
        trace = simulate_behavior(plan)

        self.assertEqual(plan.behavior_id, "motorcycle_filtering")
        self.assertGreater(len(trace.samples), 10)
        self.assertIn("motorcycle", plan.tags)

    def test_generate_behavior_variants_is_deterministic(self) -> None:
        first = generate_behavior_variants(
            "no_signal_cut_in",
            count=3,
            random_seed=5,
            severity=4,
        )
        second = generate_behavior_variants(
            "no_signal_cut_in",
            count=3,
            random_seed=5,
            severity=4,
        )

        self.assertEqual([plan.to_jsonable() for plan in first], [plan.to_jsonable() for plan in second])
        self.assertEqual(len({plan.tags[-1] for plan in first}), 3)

    def test_behavior_validator_reports_conflict_metrics(self) -> None:
        plan = generate_behavior_variants(
            "sudden_brake",
            count=1,
            random_seed=9,
            severity=3,
        )[0]
        report = validate_behavior_plan(plan, BehaviorConstraints(conflict_distance_m=4.0))

        self.assertIn("min_ego_distance_m", report.metrics)
        self.assertIn("time_to_conflict_s", report.metrics)
        self.assertTrue(report.passes or report.blockers)

    def test_behavior_validation_report_writes_artifacts(self) -> None:
        plans = generate_behavior_variants(
            "motorcycle_filtering",
            count=2,
            random_seed=2,
            severity=3,
        )
        reports = [validate_behavior_plan(plan) for plan in plans]
        with TemporaryDirectory() as tmp:
            summary = write_behavior_validation_report(Path(tmp), reports)

            self.assertEqual(summary["report_count"], 2)
            self.assertTrue(Path(summary["json_path"]).exists())
            self.assertTrue(Path(summary["report_path"]).exists())

    def test_generate_behaviors_cli_supports_variants_and_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "generate-behaviors",
                        "--template-id",
                        "motorcycle_filtering",
                        "--count",
                        "2",
                        "--seed",
                        "3",
                        "--severity",
                        "4",
                        "--validate",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "behaviors",
                    ]
                )
            summary = json.loads(stream.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["num_behaviors"], 2)
        self.assertIn("validation_path", summary)


def _params_from_defaults(template):
    return BehaviorParameters(
        values={spec.name: spec.default for spec in template.parameter_specs},
        severity=3,
        variant_seed=0,
    )


if __name__ == "__main__":
    unittest.main()
