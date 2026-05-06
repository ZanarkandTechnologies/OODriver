# Environment Forge

- environment_recipes: `6`
- asset_requests: `11`
- families: `construction, pedestrian_occlusion, regional_market, regional_traffic, visibility, weather_surface`

| recipe | family | severity | assets | pressure |
|---|---|---|---|---|
| env-construction-lane-closure-s3-0007 | construction | 3 | 2 | Slow down, bias away from closure, and avoid overreacting to cones outside the drivable corridor. |
| env-roadside-market-occlusion-s3-0008 | regional_market | 3 | 2 | Creep around occlusion and preserve clearance around shoulder clutter. |
| env-flooded-road-s3-0009 | weather_surface | 3 | 2 | Reduce speed for wet surface and route around low-profile waterlogged obstacles. |
| env-night-rain-fog-s3-0010 | visibility | 3 | 1 | Maintain lane discipline despite glare and avoid treating reflective clutter as a drivable target. |
| env-dense-regional-traffic-s3-0011 | regional_traffic | 3 | 1 | Account for unsignaled lateral motion and two-wheelers appearing in small gaps. |
| env-school-zone-unstructured-crossing-s3-0012 | pedestrian_occlusion | 3 | 3 | Anticipate a hidden pedestrian near the crossing, slow early, and avoid swerving toward the dropped object. |
