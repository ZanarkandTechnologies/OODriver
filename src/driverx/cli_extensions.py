"""Registration hub for feature CLI extensions."""

from __future__ import annotations

import argparse


def register_dynamic_parsers(subparsers: argparse._SubParsersAction) -> None:
    from driverx.environments.cli import register_environment_forge_parser
    from driverx.perception.risk_timeline_cli import register_risk_timeline_parser
    from driverx.pipeline.alpamayo_ood_batch_cli import register_alpamayo_ood_batch_parser
    from driverx.pipeline.alpamayo_ood_evaluation_cli import register_alpamayo_ood_evaluation_parser
    from driverx.pipeline.alpamayo_ood_scene_cli import register_alpamayo_ood_scene_parser
    from driverx.pipeline.end_to_end_ood_demo_cli import register_end_to_end_ood_demo_parser
    from driverx.pipeline.fail2drive_extension_report_cli import register_fail2drive_extension_report_parser
    from driverx.pipeline.final_submission_pack_cli import register_final_submission_pack_parser
    from driverx.pipeline.final_submission_pack_v8_cli import register_final_submission_pack_v8_parser
    from driverx.pipeline.generated_ood_suite_cli import register_generated_ood_suite_parser
    from driverx.pipeline.ood_video_evidence_cli import register_ood_video_evidence_parser
    from driverx.pipeline.policy_evaluation_campaign_cli import register_policy_evaluation_campaign_parser
    from driverx.pipeline.reasoning_video_pack_cli import register_reasoning_video_pack_parser
    from driverx.pipeline.reasoning_overlay_video_cli import register_reasoning_overlay_video_parser
    from driverx.pipeline.route_evidence_cli import register_route_evidence_parser
    from driverx.pipeline.scripted_ood_campaign_cli import register_scripted_ood_campaign_parser
    from driverx.pipeline.submission_demo_pack_cli import register_submission_demo_pack_parser
    from driverx.pipeline.submission_dossier_cli import register_submission_dossier_parser
    from driverx.pipeline.submission_eval_matrix_cli import register_submission_eval_matrix_parser
    from driverx.pipeline.submission_scenario_browser_cli import register_submission_scenario_browser_parser
    from driverx.policies.alpamayo_input_cli import register_alpamayo_input_parser
    from driverx.policies.alpamayo_live_cli import register_alpamayo_live_parser
    from driverx.policies.alpamayo_materializer_cli import register_alpamayo_materializer_parser
    from driverx.policies.alpamayo_offline_cli import register_alpamayo_offline_parser
    from driverx.policies.alpamayo_ood_package_cli import register_alpamayo_ood_package_parser
    from driverx.policies.alpamayo_probe_cli import register_alpamayo_probe_parser
    from driverx.policies.alpamayo_release_cli import register_alpamayo_release_parser
    from driverx.policies.alpamayo_shape_probe_cli import register_alpamayo_shape_probe_parser
    from driverx.policies.alpamayo_trajectory_cli import register_alpamayo_trajectory_parser
    from driverx.policies.runtime_matrix_cli import register_policy_runtime_matrix_parser
    from driverx.remote.runpod_cli import register_runpod_remote_parser
    from driverx.scenarios.agentic_loop_cli import register_agentic_ood_loop_parser
    from driverx.scenarios.catalog_cli import register_scenario_catalog_parser
    from driverx.scenarios.studio_cli import register_scenario_studio_parser
    from driverx.scenarios.studio_product_cli import register_oodriver_parser
    from driverx.simulators.carla_alpamayo_capture_cli import register_carla_alpamayo_capture_parser
    from driverx.simulators.carla_cached_ood_replay_cli import register_carla_cached_ood_replay_parser
    from driverx.simulators.carla_maps_cli import register_carla_maps_parser
    from driverx.simulators.carla_ood_demo_cli import register_carla_ood_demo_parser
    from driverx.simulators.carla_policy_replay_cli import register_carla_policy_replay_parser
    from driverx.simulators.fail2drive_host_plan_cli import register_fail2drive_host_plan_parser
    from driverx.simulators.fail2drive_route_runner_cli import register_fail2drive_route_runner_parser
    from driverx.simulators.gpu_host_cli import register_gpu_host_parser
    from driverx.simulators.route_video_assembly_cli import register_route_video_assembly_parser
    from driverx.simulators.simlingo_cli import register_simlingo_parsers
    from driverx.simulators.video_timewarp_cli import register_video_timewarp_parser
    from driverx.workbench.cli import register_scenario_workbench_parser

    register_generated_ood_suite_parser(subparsers)
    register_fail2drive_extension_report_parser(subparsers)
    register_final_submission_pack_parser(subparsers)
    register_final_submission_pack_v8_parser(subparsers)
    register_policy_evaluation_campaign_parser(subparsers)
    register_end_to_end_ood_demo_parser(subparsers)
    register_ood_video_evidence_parser(subparsers)
    register_reasoning_video_pack_parser(subparsers)
    register_reasoning_overlay_video_parser(subparsers)
    register_scripted_ood_campaign_parser(subparsers)
    register_route_evidence_parser(subparsers)
    register_environment_forge_parser(subparsers)
    register_alpamayo_ood_evaluation_parser(subparsers)
    register_alpamayo_ood_batch_parser(subparsers)
    register_alpamayo_ood_scene_parser(subparsers)
    register_alpamayo_input_parser(subparsers)
    register_alpamayo_ood_package_parser(subparsers)
    register_alpamayo_live_parser(subparsers)
    register_alpamayo_materializer_parser(subparsers)
    register_alpamayo_offline_parser(subparsers)
    register_alpamayo_probe_parser(subparsers)
    register_alpamayo_shape_probe_parser(subparsers)
    register_alpamayo_release_parser(subparsers)
    register_alpamayo_trajectory_parser(subparsers)
    register_policy_runtime_matrix_parser(subparsers)
    register_runpod_remote_parser(subparsers)
    register_oodriver_parser(subparsers)
    register_scenario_catalog_parser(subparsers)
    register_scenario_studio_parser(subparsers)
    register_agentic_ood_loop_parser(subparsers)
    register_simlingo_parsers(subparsers)
    register_carla_alpamayo_capture_parser(subparsers)
    register_carla_maps_parser(subparsers)
    register_carla_cached_ood_replay_parser(subparsers)
    register_carla_policy_replay_parser(subparsers)
    register_carla_ood_demo_parser(subparsers)
    register_gpu_host_parser(subparsers)
    register_route_video_assembly_parser(subparsers)
    register_fail2drive_route_runner_parser(subparsers)
    register_fail2drive_host_plan_parser(subparsers)
    register_video_timewarp_parser(subparsers)
    register_submission_dossier_parser(subparsers)
    register_submission_eval_matrix_parser(subparsers)
    register_submission_demo_pack_parser(subparsers)
    register_submission_scenario_browser_parser(subparsers)
    register_scenario_workbench_parser(subparsers)
    register_risk_timeline_parser(subparsers)


__all__ = ["register_dynamic_parsers"]
