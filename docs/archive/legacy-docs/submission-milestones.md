# Submission Milestones

Last updated: 2026-05-07 12:32 +0800

## Decision

We have one more day, so the decision is no longer "freeze now." The useful
axis is whether the demo clearly shows the novel product loop: scenario
generation, CARLA execution, risk detection, RAG memory, frozen VLA reasoning,
and dataset curation.

Current recommendation: execute Scenario Workbench V2, tracked by TASK-108
through TASK-113. Detailed direction lives in
`docs/archive/legacy-docs/scenario-workbench-v2-plan.md`.

## Evaluation Criteria

- Judge-visible contribution to the SoTA brief.
- Direct support for minimal-shot generalization.
- Evidence quality: video, model reasoning, RAG comparison, failure analysis.
- Deadline safety.
- Low setup risk.

## Options

### Option 1: Conservative Submission Freeze

Ship from current proof plus light packaging.

Pros:

- Lowest risk.
- Already has an exported 84s RunPod CARLA OOD video and live Alpamayo reasoning.
- Leaves time to make the write-up and video coherent.

Cons:

- Scenario generation may look more like infrastructure than a full simulator.
- Only one strong live Alpamayo proof.
- Weakest on the model+RAG comparison claim.

Best if: runtime starts breaking again or time drops below one day.

### Option 2: Focused Evidence Sprint

Implement TASK-101 through TASK-106 in order, stopping at the first strong V7
pack.

Pros:

- Best alignment with the prompt: randomized generation, simulation evidence,
  minimal-shot model reaction, failure memory, and final deliverables.
- Keeps scope sharp: no SimLingo, no Meshy, no FlashDrive optimization.
- Adds the model+RAG comparison that makes the project feel research-shaped.

Cons:

- Completed one stronger high-fidelity CARLA video; final stretch is editorial
  assembly, not more setup.
- Requires RunPod Alpamayo only if we choose extra inference beyond the current
  batch evidence.
- Final packaging must be disciplined to avoid overclaiming.

Best if: RunPod Kasm and HF auth remain available.

### Option 3: Aggressive Research Stretch

After TASK-101 through TASK-106, attempt one stretch: stock Fail2Drive score,
custom object import, or serving acceleration.

Pros:

- Could make the submission feel more ambitious.
- A stock benchmark or custom asset path would be flashy.

Cons:

- High setup risk.
- Likely steals time from narrative, QA, and video polish.
- Not needed to satisfy the commission if TASK-101 through TASK-106 land.

Best if: V7 pack is done early and the core evidence is already coherent.

## Recommendation

Choose Scenario Workbench V2.

This accepts a sharp cut: do not chase real-time VLA control this sprint. Hammer
the shortest path to a visible contribution. The core artifact should be:

> a randomized OOD CARLA scenario workbench that generates edge cases, runs
> quality gates, detects simulator-grounded risk, retrieves failure memory,
> records sampled Alpamayo reasoning, and curates the result as minimal-shot
> autonomy evidence.

## Tradeoff Accepted

We accept that this is not a new driving policy and not a perfect real-time VLA
stack. The submission becomes a strong evaluation/generation environment with a
frozen SOTA VLA probe, not a claim that Alpamayo is safely driving CARLA
closed-loop.

## Milestone Ladder

### M0: Board Hygiene

Status: done.

Old tickets TASK-058 through TASK-100 are archived as historical evidence.
TASK-101 through TASK-107 are complete as V7 evidence. The new active planning
board is:

- TASK-108: Scenario Workbench evidence bundle
- TASK-109: agentic OOD scenario generation loop
- TASK-110: CARLA risk and perception timeline
- TASK-111: reasoning and RAG timeline video overlay
- TASK-112: longer smooth time-warped CARLA render
- TASK-113: paper-style final demo and submission pack V8

### M1: Select The Final Evidence Set

Ticket: TASK-101.

Output:

- final scenario matrix
- hero/support/failure/backup labels
- explicit missing evidence per case

Why it matters:

- prevents random extra work
- tells us which CARLA and Alpamayo runs are actually worth doing

Stop line:

- must finish before any more live inference or video work

### M2: Improve The Simulator Video

Ticket: TASK-102.

Output:

- one better high-fidelity CARLA OOD video or exact live blocker
- density, smoothness, camera, and quality metrics

Why it matters:

- the commission asks for a simulation environment
- the current video is useful but visually thin

Stop line:

- one strong video is enough; do not chase many videos

### M3: Add Scenario Studio

Ticket: TASK-103.

Output:

- prompt-to-OOD DSL compiler
- 10+ scenario briefs
- generated batch gallery

Why it matters:

- makes "AI generates edge cases" legible
- turns deterministic generators into a usable simulator authoring layer

Stop line:

- deterministic prompt compiler is enough
- live LLM provider is optional polish

### M4: Evaluate Alpamayo + RAG

Ticket: TASK-104.

Output:

- baseline vs memory Alpamayo reports for 3 selected cases, or precise blockers
- CoC snippets
- trajectory deltas
- latency and VRAM

Why it matters:

- this is the minimal-shot research claim
- shows whether retrieved prior failures change frozen model behavior

Stop line:

- 3 rich cases beat 20 shallow cases
- keep open-loop label unless actual CARLA control consumes output

### M5: Attach Fail2Drive Reference Layer

Ticket: TASK-105.

Output:

- generated cases linked to Fail2Drive families and memory principles
- official-score claim boundary

Why it matters:

- grounds the simulator in a known OOD benchmark
- avoids looking like arbitrary CARLA scripts

Stop line:

- reference-layer report is enough
- full stock Fail2Drive scoring is stretch only

### M6: Final V7 Submission Pack

Ticket: TASK-106.

Output:

- final scenario browser
- final dossier
- 1-5 minute video script
- two-page write-up draft
- proved/partial/blocked claim table

Why it matters:

- this is what the judges actually consume

Stop line:

- once V7 is coherent, stop feature work

## Stretch Queue

Only attempt after M6 is coherent:

1. Stock Fail2Drive route score.
2. Meshy/custom GLB object import.
3. SimLingo/CarLLaVA rerun.
4. FlashDrive-style serving optimization.
5. Closed-loop Alpamayo controller instead of cached/open-loop replay.

## Hard No For This Sprint

- Do not train models.
- Do not port Alpamayo into another architecture.
- Do not rebuild CARLA or SimLingo unless the core V7 pack is already done.
- Do not chase full real-time VLA serving before the simulator/evaluation
  contribution is packaged.
- Do not promote low-quality or sparse videos as final hero evidence.

## Final Cut Guidance

If there is one day left:

- finish TASK-101, TASK-104 if possible, and TASK-106.

If there is half a day left:

- skip TASK-102/TASK-103 implementation depth and package current evidence with
  precise future-work framing.

If everything is going well:

- finish TASK-101 through TASK-106 and attempt exactly one stretch.
