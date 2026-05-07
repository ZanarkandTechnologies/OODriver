# AGENTS.md

Scenario generation module for closed-loop CARLA/Fail2Drive work.

- Keep this module dependency-light; do not import CARLA, TensorFlow, or model
  packages here.
- Accept external Fail2Drive paths as config/input only. Do not commit benchmark
  assets, simulator files, or generated videos.
- Preserve deterministic generation under an explicit random seed.
- Keep `oodrive ...` as the canonical product CLI for scenario DB work;
  `driverx oodrive`, `driverx oodriver`, and `driverx studio` are compatibility
  aliases for older docs/tickets.
