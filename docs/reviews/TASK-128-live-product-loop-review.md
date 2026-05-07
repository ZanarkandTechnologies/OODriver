# TASK-128 Review: Live OODrive Product Loop

## Score

4.3 / 5

## Findings

No blocking implementation defects were found in the proof path. The live
evidence now matches the intended user story much more closely than prior
dry-run/cached-reasoning artifacts: prompt generation, CARLA placement, live RGB
capture, fresh Alpamayo inference, reasoning attachment, and overlay video all
exist in one linked run.

## Strengths

- `oodrive generate` produced a concrete placement plan from natural language.
- `oodrive place --live` passed against a real CARLA server and recorded
  `objects_placed_in_carla=true`.
- Fresh Alpamayo inference was run over the new CARLA frames, not only reused
  from a previous hero scenario.
- The run has usable video evidence: 450 overlay frames and a 30s MP4.
- Claim boundaries remain honest about open-loop VLA reasoning.

## Residual Risks

- Live Alpamayo inference is not yet one OODrive command; a manual remote bridge
  staged the package and invoked the extracted inference script.
- The CARLA behavior is scripted; Alpamayo is not yet controlling the ego
  vehicle.
- The generated prompt mentions Malaysian wet roadwork, but the selected asset
  generator mapped the concrete proxy assets to a school-zone-style bundle.
  That is acceptable for stock-CARLA proxy proof, but the next polish pass
  should make scenario semantics and proxy assets align more tightly.
- The MP4 remains on the remote pod; it is not yet exported or publicly hosted.

## Recommendation

Treat TASK-128 as a passed open-loop product proof. The next highest-signal
ticket is TASK-129: productize the live Alpamayo bridge as `oodrive infer` or
`oodrive reason --live-infer`, then refresh the final submission pack around
this evidence.
