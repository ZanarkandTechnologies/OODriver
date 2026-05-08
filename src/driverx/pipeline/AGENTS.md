# Pipeline Module Rules

## Stress Demo Evidence

- Local stress-demo evidence is a scripted 2D proof, not CARLA visual evidence.
- Guarded stress-demo traces must fail if they avoid a hazard by leaving the drivable corridor. See `MEM-0041`.
- Keep claim boundaries explicit: no closed-loop VLA or real-time Alpamayo control unless a live model-driven CARLA control trace exists.
