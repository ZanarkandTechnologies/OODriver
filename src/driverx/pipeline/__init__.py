"""Pipeline orchestration."""

from driverx.pipeline.batch_run import run_batch
from driverx.pipeline.experiment_run import run_experiment
from driverx.pipeline.fail2drive_extension_report import (
    Fail2DriveExtensionReportConfig,
    build_fail2drive_extension_report,
    run_fail2drive_extension_report,
)
from driverx.pipeline.final_submission_pack import (
    build_final_submission_pack,
    run_final_submission_pack,
)
from driverx.pipeline.generated_ood_suite import GeneratedOodSuiteConfig, run_generated_ood_suite
from driverx.pipeline.end_to_end_ood_demo import (
    EndToEndOodDemoConfig,
    run_end_to_end_ood_demo,
    write_end_to_end_ood_demo,
)
from driverx.pipeline.alpamayo_ood_evaluation import (
    AlpamayoOodEvaluationInputs,
    build_alpamayo_ood_evaluation,
)
from driverx.pipeline.alpamayo_ood_scene import (
    AlpamayoOodSceneInputs,
    build_alpamayo_ood_scene_report,
    write_alpamayo_ood_scene_report,
)
from driverx.pipeline.bad_path_stress_demo import build_bad_path_stress_demo
from driverx.pipeline.ood_suite_report import build_ood_suite_report
from driverx.pipeline.ood_video_evidence import (
    OodVideoEvidenceInputs,
    build_ood_video_evidence,
    write_ood_video_evidence,
)
from driverx.pipeline.environment_demo_pack import (
    build_environment_demo_pack,
    render_environment_demo_html,
    render_environment_demo_storyboard,
)
from driverx.pipeline.environment_reasoned_carla_video import (
    build_environment_reasoned_carla_video,
    write_environment_reasoned_carla_video,
)
from driverx.pipeline.keyframe_analysis import (
    build_keyframe_analysis,
    select_carla_keyframes,
    write_keyframe_analysis,
)
from driverx.pipeline.rag_comparison import run_rag_comparison
from driverx.pipeline.route_evidence import RouteEvidenceInputs, build_route_evidence
from driverx.pipeline.scene_run import inspect_scene, run_loaded_scene, run_scene
from driverx.pipeline.submission_story_pack import build_submission_story_pack

__all__ = [
    "AlpamayoOodEvaluationInputs",
    "AlpamayoOodSceneInputs",
    "build_alpamayo_ood_evaluation",
    "build_alpamayo_ood_scene_report",
    "build_bad_path_stress_demo",
    "build_environment_demo_pack",
    "build_environment_reasoned_carla_video",
    "build_fail2drive_extension_report",
    "build_final_submission_pack",
    "build_keyframe_analysis",
    "build_ood_suite_report",
    "build_route_evidence",
    "build_submission_story_pack",
    "GeneratedOodSuiteConfig",
    "EndToEndOodDemoConfig",
    "Fail2DriveExtensionReportConfig",
    "OodVideoEvidenceInputs",
    "render_environment_demo_html",
    "render_environment_demo_storyboard",
    "select_carla_keyframes",
    "inspect_scene",
    "RouteEvidenceInputs",
    "run_batch",
    "run_experiment",
    "run_fail2drive_extension_report",
    "run_final_submission_pack",
    "run_generated_ood_suite",
    "run_end_to_end_ood_demo",
    "build_ood_video_evidence",
    "run_loaded_scene",
    "run_rag_comparison",
    "run_scene",
    "write_end_to_end_ood_demo",
    "write_environment_reasoned_carla_video",
    "write_keyframe_analysis",
    "write_ood_video_evidence",
    "write_alpamayo_ood_scene_report",
]
