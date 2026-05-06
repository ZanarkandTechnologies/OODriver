# TASK-089 through TASK-095 Impl-Plan Review

Date: 2026-05-06 21:34 +0800

## Verdict

PASS for planning. The batch is correctly re-centered on the actual SoTA
submission contribution: a road-aligned, quality-gated OOD scenario generator
and management harness, with Alpamayo retained as supporting policy evidence
rather than the only deliverable.

Overall score: 4.1 / 5.0
Threshold: 4.0
Verdict: pass
Rerun required: false

## Search Scope

- Active tickets:
  - `tickets/archive/TASK-089/ticket.md`
  - `tickets/archive/TASK-090/ticket.md`
  - `tickets/archive/TASK-091/ticket.md`
  - `tickets/archive/TASK-092/ticket.md`
  - `tickets/archive/TASK-093/ticket.md`
  - `tickets/archive/TASK-094/ticket.md`
  - `tickets/archive/TASK-095/ticket.md`
- Neighboring docs:
  - `docs/prd.md`
  - `ARCHITECTURE.md`
  - `docs/progress.md`
  - `docs/MEMORY.md`
- Relevant implementation surfaces:
  - `src/driverx/simulators/carla_ood_demo.py`
  - `src/driverx/simulators/carla_script.py`
  - `src/driverx/behaviors/library.py`
  - `src/driverx/scenarios/generator.py`
  - `src/driverx/pipeline/scripted_ood_campaign.py`

## Rubrics

### Spec Contract

Score: 4.2 / 5.0
Threshold: 4.0
Pass: yes

Dimension scores:

- story-coherence: 4.4
- parallelization-fit: 4.0
- ticket-sizing: 4.0
- acceptance-testability: 4.2
- scope-clarity: 4.2

The tickets form a coherent contribution sequence and each ticket is testable
as a unit. The split is real because road geometry, catalog management,
environment generation, behavior generation, quality gates, policy evaluation,
and packaging have different ownership boundaries.

### Implementation Plan

Score: 4.1 / 5.0
Threshold: 4.0
Pass: yes

Dimension scores:

- human-readability: 4.0
- bloatability: 4.0
- modularity: 4.2
- proof-clarity: 4.2
- execution-order: 4.4
- risk-clarity: 4.0
- decision-tone: 4.2
- autonomy-readiness: 4.0

The plan names concrete files, signatures, proof commands, and fallback paths.
The strongest point is sequencing: geometry correctness comes before campaign
scale, and model evidence only consumes quality-passed generated scenarios.

### Evidence Quality

Score: 4.0 / 5.0
Threshold: 4.0
Pass: yes

Dimension scores:

- sufficiency: 4.0
- reproducibility: 3.9
- traceability: 4.1
- consistency: 4.0
- inspectability: 4.0
- autonomy-readiness: 4.0

This is a planning review, so evidence is not runtime proof. The plan still
passes because every ticket defines specific future proof artifacts and links
the review result. Reproducibility is the weakest dimension because live CARLA
availability remains an external condition for video evidence.

## Findings

- No blocking planning issues found.
- The first ticket is correctly sequenced as TASK-089 because current evidence
  can start off-road; scaling generation before fixing geometry would produce
  more low-quality artifacts.
- TASK-090 through TASK-095 create a coherent chain:
  road frame -> catalog -> environment generator -> behavior DSL -> quality
  gates -> policy evaluation -> submission browser.

## Risks To Watch During Build

- Road-frame validation must not reject intentional shoulder cases unless the
  scenario declares the shoulder as an allowed zone.
- Alpamayo evidence must remain labeled as open-loop unless the CARLA controller
  actually consumes its outputs in the live loop.
- Old videos should move into legacy/failure evidence status once the catalog
  exists, rather than being silently reused as hero artifacts.

## Recommended Build Order

1. TASK-089
2. TASK-090
3. TASK-092
4. TASK-091
5. TASK-093
6. TASK-094
7. TASK-095

This order gets geometry correctness first, then management/catalog scaffolding,
then diversity primitives, then campaign quality and model evidence.

## Hard Gates

- None.

## Next Action

Start TASK-089. Do not promote any new CARLA video as hero evidence until the
road-alignment report passes.
