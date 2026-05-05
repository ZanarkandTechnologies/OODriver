# Memory Bank

- Entries: `3`

## mem-0000-generalization-animals-1078

- Situation: Generalization_Animals_1078 with tags 1078, an, and, animal, animals, as, generalization, ignored, like, noise, object, obstacle, occupied, on, policy, route, space, the, treated, unknown, visual
- Observed failure: Policy ignored an unknown animal-like object on the route and treated occupied space as visual noise.
- Principle: Unknown objects on the drivable route should be treated as occupied space.
- Recommended behavior: Slow early, treat the object as occupied space, and proceed only after the path is clear.
- Source scenario: `Generalization_Animals_1078`

## mem-0001-generalization-pedestriansonroad-1088

- Situation: Generalization_PedestriansOnRoad_1088 with tags 1088, a, and, around, committed, creep, crossing, early, failed, generalization, hazard, hidden, occlusion, pedestrian, pedestriansonroad, policy, through, to, too
- Observed failure: Policy committed too early around a hidden pedestrian crossing and failed to creep through occlusion.
- Principle: Occluded cross-traffic risk should reduce commitment speed until visibility improves.
- Recommended behavior: Creep forward with low speed and preserve stopping margin until the hidden area is visible.
- Source scenario: `Generalization_PedestriansOnRoad_1088`

## mem-0002-fixture-prior-motorcycle-filtering

- Situation: fixture_prior::motorcycle_filtering with tags animals, assertively, behavior, between, driving, drove, during, fast, filtering, filters, fixture, lanes, lateral, motorcycle, obstacle, occupied, policy, prior, regional, space, too, two, uncertainty, unknown, weave, wheeler, with
- Observed failure: Prior policy drove too assertively during motorcycle_filtering; Fast two-wheeler filters between lanes with lateral weave.
- Principle: Unknown objects on the drivable route should be treated as occupied space.
- Recommended behavior: Slow early, treat the object as occupied space, and proceed only after the path is clear.
- Source scenario: `fixture_prior::motorcycle_filtering`
