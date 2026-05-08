# Submission Form Answers

Last updated: 2026-05-09 05:36 +0800

## What is your name?

`[YOUR NAME]`

## Did you work on this with anyone else? List their names here.

I built the project solo, using Codex as an AI coding/research assistant.

Optional shorter answer:

`Solo project; assisted by Codex.`

## What is your email? (So that we can contact you)

`[YOUR EMAIL]`

## Any other additional emails of team members.

`N/A`

## Please provide a one sentence summary of your project.

OODrive is an agent-operable CARLA scenario generator and minimal-shot autonomy
test harness that creates rare driving scenarios, runs them in simulation, and
uses Alpamayo-style VLA reasoning plus retrieved failure memory to evaluate how
an autonomous vehicle should respond.

## Do you have a personal website / public profile? (X / LinkedIn)

`[YOUR WEBSITE / X / LINKEDIN URL]`

## Please provide the github repo for your project.

`[GITHUB REPO URL]`

## Please provide a URL to the submission video or slide deck. (YouTube link, Google Slides, Figma, fileshare)

`[SUBMISSION VIDEO OR SLIDE DECK URL]`

Local video pack before upload:

- `artifacts/viewer_showcase/00_viewer_presentation_full.mp4`
- `artifacts/viewer_showcase/01_cli_overview.mp4`
- `artifacts/viewer_showcase/02_ood_scenario_generation.mp4`
- `artifacts/viewer_showcase/03_rag_alpamayo_reasoning.mp4`
- `artifacts/viewer_showcase/04_evidence_reel.mp4`

## Project writeup: motivation, architecture, what worked, what didn't, where the prize money would take the project next.

I started this project as a one-week experiment to see how far a motivated
outsider could get toward state-of-the-art autonomy using Codex, open-source
research tools, and current VLA models. I knew very little about self-driving
cars at the start, so the project became both an autonomy prototype and a test
of agent-amplified research engineering: could one person use an AI coding
assistant to climb the stack from dataset exploration to simulator control,
model inference, evidence capture, and a submission-grade demo?

The final project is OODrive: a CARLA-based scenario factory and minimal-shot
autonomy evaluation harness. The simulation side lets a human or coding agent
generate rare driving scenarios from short prompts, compose CARLA towns,
weather, actors, objects, and behaviors, run the scenario, capture video and
tracks, and score whether the evidence is good enough to keep. The autonomy
side wraps a frozen reasoning VLA, currently Alpamayo-style reasoning, with
retrieved prior failure memory, simulator-grounded risk context, trajectory
conversion, and safety gates. The intended loop is: observe the CARLA scene,
retrieve relevant failure memories, ask the VLA to reason about the situation,
convert its trajectory intent into bounded controls, tick the simulator, and
record the evidence.

What worked best was the simulation environment and evidence loop. OODrive can
generate weird-but-plausible out-of-distribution driving cases, place them in
CARLA, capture simulator evidence, build reasoning/RAG overlays, and produce
viewer-facing videos and score-gated artifacts. I also connected Alpamayo-style
VLA reasoning to CARLA evidence, which made the project more than a static
scenario generator: the system can show what the model sees, what memory is
retrieved, what it reasons, and what action intent it produces. The project also
now has a paused closed-loop path for observe-infer-act recurrence, with claim
labels separating open-loop reasoning, paused closed-loop proof, fake/cached
traces, and real-time control.

What did not work was trying to solve everything at once. I first explored the
Waymo E2E dataset, which was useful as a real-data support track but not the
best main path for a simulation-environment challenge; generating meaningful
new TFRecord-style driving trajectories was not realistic in this sprint. I
also considered generated images as model inputs, but disconnected images were
not consistent enough for navigation proof. The biggest unfinished piece is
real-time VLA serving. I wanted to reproduce the kind of FlashDrive/Z Lab
optimization path that makes Alpamayo-style driving VLAs fast enough for
real-time control, but that is a serious systems project on its own. For this
submission I kept the latency and claim boundaries explicit instead of
pretending the system was already real-time.

Prize money would make the next prototype much more practical. The two scarce
resources are reliable GPU/simulator runtime and focused engineering time. I
would use the funding to keep a graphics-capable CARLA + CUDA host online, run
many more generated scenarios, expand the scenario library across towns,
weather, traffic, and failure modes, and work on FlashDrive-style latency
optimization such as streaming cache reuse, quantization, CUDA graphs,
speculative reasoning, and faster action generation. It would also help turn
the current research prototype into a cleaner repeatable service: prompt in,
CARLA scenario out, VLA/RAG evaluation attached, and a scored evidence packet
ready for review.

## Do you have any feedback for us?

This challenge was a great format because it rewarded a working prototype,
clear motivation, and honest evidence rather than only polished benchmark
numbers. The prompt was broad enough to let me discover the real shape of the
problem: the hard part was not just "make a car drive," but building a
simulation and evidence loop where rare scenarios can be generated, inspected,
and used to evaluate reasoning models. I would love to see future versions keep
the emphasis on open-ended prototypes, but maybe add an optional scoring rubric
for claim boundaries: what is simulated, what is real-time, what is open-loop,
and what is actually controlled by the model.
