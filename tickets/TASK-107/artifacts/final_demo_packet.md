# Final Demo Packet Draft

Status: `draft_video_rendered`

## Primary Media

- Draft demo video:
  `artifacts/exported/final_sota_demo_draft_v1.mp4`
- Exported CARLA hero clip:
  `artifacts/exported/task102_high_fidelity_hero_v6_full.mp4`
- Builder:
  `scripts/build_final_demo_video.sh`

Both MP4s are intentionally untracked under `artifacts/exported/`.

## Story Arc

1. Minimal-shot autonomy problem: generalization matters more than memorized
   route coverage.
2. Scenario Studio: prompts become OOD scenario candidates with environments,
   behaviors, assets, memory queries, and quality gates.
3. CARLA evidence: the 84s high-fidelity generated OOD campaign shows the
   simulator contribution in motion.
4. Alpamayo plus memory: frozen model reasoning is compared with retrieved
   safety context without fine-tuning.
5. Failure boundary: current model evidence is open-loop and slow; it reasons
   about generated scenes but does not steer CARLA in real time.
6. Contribution: a data engine for generating, scoring, curating, and preserving
   long-tail autonomy failures as minimal-shot memory.

## Submission Checklist

- Include repo with model/data declarations and non-commercial Alpamayo note.
- Include `tickets/TASK-106/artifacts/final-submission-pack-v7-task102/final_submission_pack_v7.md`.
- Include `tickets/TASK-106/artifacts/final-submission-pack-v7-task102/scenario_browser_v7.html`.
- Include the draft video or an edited export derived from
  `artifacts/exported/final_sota_demo_draft_v1.mp4`.
- Mention one understood failure: no official Fail2Drive score and no
  closed-loop real-time VLA control yet.
- Mention prize-money next step: persistent graphics-capable CARLA host plus GPU
  budget for repeated closed-loop VLA trials.

## Claim Boundaries

- Scripted CARLA OOD evidence, not an official Fail2Drive leaderboard result.
- Alpamayo evidence is open-loop trajectory intent plus reasoning, not live
  vehicle control.
- Scenario Studio is deterministic in this repo; live LLM/Meshy generation is a
  future provider-backed extension.
