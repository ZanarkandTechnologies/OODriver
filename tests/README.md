# Tests

The test suite is intentionally broad because 0xDriver has many runtime seams:
CARLA, Fail2Drive, Alpamayo, SimLingo, Waymo, Docker wrappers, and final
submission artifacts.

Before adding tests:

- extend the nearest existing test file when a public seam already exists
- create a new file only for a new module or command family
- avoid duplicate smoke tests that only assert a command exists
- keep generated videos, frames, datasets, and model outputs out of git

Historical audit notes live in `docs/archive/legacy-docs/test-audit.md`.
