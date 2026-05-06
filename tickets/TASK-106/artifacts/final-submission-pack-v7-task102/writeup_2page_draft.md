# 0xDriver Two-Page Write-Up Draft

## Motivation

If autonomy depends on collecting examples of every weird road situation, it will always lag reality. 0xDriver reframes minimal-shot driving as a stress-test and memory problem: generate plausible OOD cases, run frozen policies through them, and preserve failures as reusable context.

## Architecture

The system has a Scenario Studio compiler, deterministic environment and behavior generators, CARLA/Fail2Drive-compatible evidence paths, a failure-memory bank, and an Alpamayo open-loop evaluation harness. Scenario Studio emits the curation queue; CARLA produces video and tracks; Alpamayo is evaluated with and without retrieved memory; final reports keep claim boundaries explicit.

## What Worked

The final sprint generated 20 OOD candidates from 10 briefs, selected 6 judge-facing cases, linked 26 cases to Fail2Drive references, and summarized 3 Frozen Alpamayo+memory comparisons. The hero video evidence is 84.0 seconds.

## What Did Not Work

The model evidence is open-loop and slow, not real-time closed-loop control. Full official Fail2Drive scoring remains a future runtime task. Video export status is local_file. Current open blocker summary: fail2drive,carla,town13,score,capture: TASK-060 long-score attempt `town13-long-score-attempt-001` started the stock `Generalization_Pedest...; fail2drive,carla,town13,score: TASK-071 produced fresh Town13 MP4 evidence from the stock Fail2Drive `Generalization_PedestriansOnR... (+1 more)

## Where Prize Money Goes

The next prototype step is a persistent graphics-capable CARLA host plus GPU time for closed-loop VLA experiments, higher-fidelity generated assets, and enough repeated runs to convert partial candidates into accepted dataset rows.

## Model And Data Declarations

- Base model: nvidia/Alpamayo-1.5-10B, used as a frozen non-commercial research model.
- No AV fine-tuning is performed for these generated scenarios.
- Alpamayo batch status: passed; open-loop only.
- Fail2Drive reference sources: ['fixture_result', 'fixture_seed']; official score claim is false.
- Model weights, datasets, videos, credentials, CARLA installs, and remote caches are excluded from git.
