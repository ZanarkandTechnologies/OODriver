# Closed-Loop Video Autoresearch Ideas

- Add a spectator chase camera if the attached third-person camera does not show
  the vehicle body reliably.
- Use more `control_ticks_per_step` for visual proof runs so the car visibly
  approaches the cone before the next Alpamayo pause.
- Add real MP4 frame-difference sampling to catch repeated frames even when a
  manifest claims enough source frames.
- Generate a short 6-12s hero clip by default; reserve 60s videos for runs with
  enough unique CARLA action frames.
