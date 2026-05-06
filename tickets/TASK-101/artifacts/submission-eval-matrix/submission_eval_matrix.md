# Submission Evaluation Matrix

- Matrix id: `submission-eval-matrix-001`
- Cases: `6`
- Hero cases: `1`

## Why These Cases

This matrix freezes the final sprint queue around generated OOD simulation, Alpamayo/RAG reaction, and Fail2Drive-style reference framing.

## Case Table

| case | role | scenario | family | behavior | quality | next |
|---|---|---|---|---|---|---|
| case-01 | hero | generated-base-animals-0076-visual-noise-000 | visual | wrong_way_shoulder_creep | passed | TASK-104_alpamayo_baseline, TASK-104_rag_comparison, TASK-105_fail2drive_reference |
| case-02 | support | generated-generalization-customobstacles-1028-occlusion-001 | occlusion | sudden_brake | legacy_passed | TASK-102_high_fidelity_carla_video, TASK-104_alpamayo_baseline, TASK-104_alpamayo_memory, TASK-104_rag_comparison, TASK-105_fail2drive_reference |
| case-03 | support | generated-base-animals-0076-regional-driving-behavior-000 | regional |  | open_loop_only | TASK-102_high_fidelity_carla_video, TASK-103_behavior_binding, TASK-104_alpamayo_memory, TASK-105_fail2drive_reference |
| case-04 | support | generated-generalization-pedestriansonroad-1088-lane-blockage-002 | lane | unsignaled_u_turn | legacy_passed | TASK-102_high_fidelity_carla_video, TASK-104_alpamayo_baseline, TASK-104_alpamayo_memory, TASK-104_rag_comparison, TASK-105_fail2drive_reference |
| case-05 | failure | generated-generalization-customobstacles-1028-visual-noise-007 | visual | sudden_brake | blocked | TASK-102_high_fidelity_carla_video, TASK-104_alpamayo_baseline, TASK-104_alpamayo_memory, TASK-104_rag_comparison, TASK-105_fail2drive_reference |
| case-06 | failure | generated-base-animals-0076-obstacle-substitution-003 | obstacle | motorcycle_filtering | blocked | TASK-102_high_fidelity_carla_video, TASK-104_alpamayo_baseline, TASK-104_alpamayo_memory, TASK-104_rag_comparison, TASK-105_fail2drive_reference |

## Claims

- `case-01` `generated-base-animals-0076-visual-noise-000`: Primary generated OOD CARLA case with road-aligned video; use it to show the simulator and anchor Alpamayo/RAG comparison.
- `case-02` `generated-generalization-customobstacles-1028-occlusion-001`: Candidate scenario family for additional generated evidence; currently useful for breadth or failure analysis, not hero promotion.
- `case-03` `generated-base-animals-0076-regional-driving-behavior-000`: Candidate scenario family for additional generated evidence; currently useful for breadth or failure analysis, not hero promotion.
- `case-04` `generated-generalization-pedestriansonroad-1088-lane-blockage-002`: Candidate scenario family for additional generated evidence; currently useful for breadth or failure analysis, not hero promotion.
- `case-05` `generated-generalization-customobstacles-1028-visual-noise-007`: Candidate scenario family for additional generated evidence; currently useful for breadth or failure analysis, not hero promotion.
- `case-06` `generated-base-animals-0076-obstacle-substitution-003`: Candidate scenario family for additional generated evidence; currently useful for breadth or failure analysis, not hero promotion.

## Claim Boundaries

- `submission_eval_matrix_is_selection_planning=true`
- `closed_loop_carla_execution=false`
- `alpamayo_inference_executed_by_this_ticket=false`
