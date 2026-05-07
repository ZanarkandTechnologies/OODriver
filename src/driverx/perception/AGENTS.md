# Perception Module Rules

- Label simulator-derived perception as CARLA ground truth, not camera/CV
  inference.
- Keep risk outputs compact enough for video overlays and reports.
- Do not add heavyweight CV dependencies in this module before there is a
  ticket that explicitly asks for image-based perception.
