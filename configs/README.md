# Configs

Future runtime configs should live here. Start with sample configs only; keep
local secrets, cloud endpoints, credentials, and absolute dataset paths out of
git.

- `scenario_studio.sample.json`: final-sprint prompt-to-OOD Scenario Studio
  batch. JSON is used here because the dependency-light config parser supports
  prompt arrays in JSON without adding a YAML dependency.
- `oodrive_flagship_malaysia.yaml`: flagship OODrive case-study contract for
  the H100/CARLA + Alpamayo sprint.
