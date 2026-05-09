# OODrive Architecture Notes

OODrive is the product-facing CLI/control plane. It should not duplicate CARLA, ScenarioRunner, Fail2Drive, or Alpamayo internals. The agent writes scenario intent and files; OODrive validates, runs, captures, scores, and records proof.

Core ownership:

- CARLA owns simulator maps, weather, sensors, actors, and rendering.
- Fail2Drive owns upstream route XML, scenario classes, and evaluator behavior.
- OODrive owns agent-friendly commands, validation reports, evidence bundles, reasoning overlays, demo scoring, and claim boundaries.
- Codex or another harness owns natural-language scenario interpretation unless a ticket explicitly reopens internal prompt generation.

This division prevents the common mistake of rebuilding fragile simulator semantics inside OODrive.
