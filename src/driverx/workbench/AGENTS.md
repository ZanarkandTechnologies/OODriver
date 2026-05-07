# Workbench Module Rules

- Keep this module artifact-first: it links existing evidence and must not copy
  heavy videos, model weights, datasets, or CARLA captures.
- Every bundle must carry claim boundaries for offline/time-warped/open-loop
  evidence so demos do not imply real-time VLA control.
- Linkage mismatches must be represented as warnings, not silently hidden.
