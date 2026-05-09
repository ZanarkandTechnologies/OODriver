---
name: waymo-multiview-fail2drive-reconstruction
description: Use when turning Waymo multiview camera images into Fail2Drive/CARLA route XML with direction-aware object transcription, approximate placement, render evidence, and visual QA.
---

# Waymo Multiview To Fail2Drive Reconstruction

Use this skill when the goal is to approximate one Waymo frame or short clip as a
Fail2Drive/CARLA scenario. Codex handles the image reasoning and scenario
authoring; Fail2Drive/CARLA handles route XML execution and rendering.

## Core Rule

Do not claim image-grounded reconstruction from a stock scenario name alone.
Every high-confidence nearby object from the images must either:

- appear in the generated XML as an explicit object or actor, or
- be listed in the mapping report with a clear exclusion reason.

For the first useful proof, prefer stock CARLA/Fail2Drive proxies. Use
image-to-3D generation only when no stock proxy can represent a must-have object,
and only after adding a mesh manifest, CARLA import or blueprint probe, and live
spawn evidence.

## Inputs

Expected inputs:

- multiview images with camera direction names such as `front`, `front_left`,
  `front_right`, `side_left`, `side_right`, `rear_left`, `rear`, `rear_right`
- a Fail2Drive route seed or route authoring target
- available CARLA blueprint/catalog data when possible
- an output folder for XML, object mapping, contact sheets, render frames, and
  QA notes

## Workflow

1. Build a contact sheet and object transcript.

For each image, list visible nearby objects with:

- `object_label`: human name from the image
- `camera`: source camera direction
- `bearing`: `front`, `front_left`, `left`, `rear_left`, `rear`, `rear_right`,
  `right`, or `front_right`
- `range_bucket`: `near` about 0-8m, `mid` about 8-25m, `far` about 25-60m
- `side`: `left`, `center`, or `right` in the ego frame
- `confidence`: `high`, `medium`, or `low`
- `suggested_blueprint`: CARLA/Fail2Drive proxy id
- `placement_reason`: short visual cue such as lane edge, curb contact, object
  scale, or overlap with ego lane

2. Fuse duplicates across cameras.

Treat the same physical object seen in adjacent cameras as one object when labels,
position, color, and continuity agree. Keep the strongest view as `primary_view`
and preserve supporting views.

3. Convert to ego-relative placement.

Use Fail2Drive custom object coordinates relative to the scenario construction
anchor:

- `x`: forward from the anchor
- `y`: right from the anchor; negative is left
- `yaw`: object yaw relative to the anchor heading

Direction-name placement heuristic:

| Camera | Default coordinate bias |
|---|---|
| `front` | `x=8..25`, `y=-2..2` based on image side |
| `front_left` | `x=6..20`, `y=-2..-6` |
| `front_right` | `x=6..20`, `y=2..6` |
| `side_left` | `x=-2..8`, `y=-4..-9` |
| `side_right` | `x=-2..8`, `y=4..9` |
| `rear_left` | `x=-15..-3`, `y=-3..-7` |
| `rear` | `x=-20..-5`, `y=-2..2` |
| `rear_right` | `x=-15..-3`, `y=3..7` |

Adjust `x` by range bucket:

- `near`: place close to ego, usually `x=0..8`
- `mid`: use `x=8..25`
- `far`: use scenario context only unless the object matters for the hazard

4. Choose the Fail2Drive scenario type.

- Static hazards near the lane: `CustomObstacle`, `CustomObstacleTwoWays`, or
  `RoadBlocked` with explicit `<objects>`.
- Roadwork/barriers/cones: prefer `CustomObstacle*` with explicit barrier and
  cone objects; do not rely only on `ConstructionObstacleRightLane`.
- Parked vehicles: use `BadParkingObstacle*` for one vehicle, or
  `CustomObstacle*` / `RoadBlocked` with vehicle blueprints for multiple.
- Pedestrians/cyclists/animals crossing: use `DynamicObjectCrossing`,
  `PedestrianCrossing`, or a nearby Fail2Drive crossing scenario.
- Traffic-flow behavior: use stock Fail2Drive vehicle-flow/hard-brake/cut-in
  scenarios when actor motion matters more than object identity.

5. Write XML and object mapping together.

For explicit static placements, use:

```xml
<scenario name="CustomObstacleTwoWays" type="CustomObstacleTwoWays">
  <objects
    a="id=static.prop.streetbarrier x=0.00 y=-1.40 yaw=0.00"
    b="id=static.prop.constructioncone x=10.00 y=-1.05 yaw=0.00"
    c="id=vehicle.tesla.model3 x=18.00 y=3.30 yaw=4.00" />
  <distance value="28" />
  <frequency from="40" to="55" />
  <trigger_point x="4429.7" y="1975.1" z="153.4" yaw="180.2" />
  <speed value="35" />
</scenario>
```

Also write a mapping report that links each image-observed object to one XML
entry, one stock scenario actor, or an exclusion reason.

6. Render and QA.

Render at least one short CARLA run or snapshot set. Then check:

- XML contains explicit entries for the nearest high-confidence objects.
- CARLA frames visibly show the placed objects from the expected side.
- The object count and rough left/right/front placement agree with the image
  transcript.
- Stock proxy limitations are named directly.
- Output includes XML, object mapping, source contact sheet, rendered frames,
  video when possible, and a side-by-side evidence image.

If the render misses the objects, revise coordinates or camera/spectator angle
before claiming success.

## Why This Is Hard

This is reasoning, but it is not only reasoning. The fragile parts are monocular
depth, unknown exact camera calibration, map mismatch between Waymo streets and
CARLA towns, limited stock blueprint fidelity, and visual QA. The practical path
is therefore approximate placement plus render-and-compare QA, not perfect
metric reconstruction on the first pass.
