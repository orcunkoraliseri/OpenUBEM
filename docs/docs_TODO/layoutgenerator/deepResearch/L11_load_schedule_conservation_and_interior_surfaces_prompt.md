# Deep-Research Prompt L11 — LOAD/SCHEDULE CONSERVATION & INTERIOR SURFACES (making the generated layout physically correct)

> SCOPE GUARD — READ FIRST. This prompt closes the physics loop: once `layoutGenerator.py` has produced
> zones (`L05`/`L06`) and assigned each a DOE space type (`L07`), the model must (1) **conserve the
> building's total internal loads, schedules, and conditioned area** so a room-level model of a building
> matches the floor-level/single-zone model's totals, and (2) treat **interior partitions / inter-zone
> surfaces** correctly (adiabatic vs. heat-transfer, inter-floor surfaces, the courtyard/donut fatal).
> Deliver the conservation rules and the surface-treatment conventions. Do NOT re-specify the geometry
> (`L05`) or the per-archetype programs (`L07`–`L10`). See `00_README_layoutgenerator_prompt_set.md`.

---

## What this document is

The physical-correctness reference. Refining a building from 1 zone to N zones must not change how much
lighting/equipment/people/OA the building has, nor its conditioned floor area (the EUI denominator is
fixed at `footprint_area_m2 × num_floors`). And the new interior surfaces the zones create must be modeled
with the right boundary conditions — get this wrong and either heat flows through phantom walls or the
model fatals (exactly OpenUBEM's current courtyard failure). This prompt gives the manager the rules that
keep a room-level model *consistent* with the coarser resolutions it's meant to refine.

## Role

EnergyPlus zoning / building-physics research analyst. Ground the conservation rules in EnergyPlus
documentation (the Input/Output Reference on `ZoneList`, `Zone Multiplier`, internal-gains objects, and
the `Space`/`SpaceType` feature) and in ASHRAE/DOE zoning practice; ground the interior-surface treatment
in the EnergyPlus surface boundary-condition docs (`Surface,...,Adiabatic`; `Zone`; inter-zone surface
pairing; `Construction:InternalSource`) and in BEM zoning-guidance literature on when interior walls are
adiabatic vs. heat-transfer. Address the specific geomeppy inter-floor vertex-matching failure OpenUBEM
hits on donut cores.

## Why this matters (so you scope correctly)

This is where fidelity can silently corrupt results. If load intensities are applied per-zone-floor-area
but the corridor was double-counted, the building's total EPD drifts. If all interior walls are made
heat-transfer with default constructions, inter-zone conduction appears that the floor-level model never
had, changing EUI for reasons unrelated to resolution. The manager needs the conservation invariants and
the surface conventions pinned so room-level is a *faithful refinement*, not a different building.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Conservation invariants (what must be preserved across resolutions)

| Quantity | Invariant across single/floor/zone resolution | How to enforce in E+ | Source |
|---|---|---|---|
| Conditioned floor area (EUI denominator) | = `footprint_area_m2 × num_floors` |  |  |
| Total lighting power (LPD × area) |  |  |  |
| Total equipment power (EPD × area) |  |  |  |
| Total occupancy (ppl/area × area) |  |  |  |
| Total outdoor-air / ventilation |  |  |  |
| Total exterior envelope area |  |  |  |
| Schedules (fractions unchanged per space type) |  |  |  |

### Table 2 — Distributing DOE loads to generated zones

| Approach | How loads are apportioned | Conserves totals? | Fits zero-fitted-parameters? | Source |
|---|---|---|---|---|
| Per-zone-floor-area × space-type intensity |  |  |  |  |
| Space-type-weighted (corridor vs. unit intensities) |  |  |  |  |
| E+ `Space`/`SpaceType` objects (native) |  |  |  |  |
| Zone-multiplier for repeated units |  |  |  |  |

### Table 3 — Interior / inter-zone surface treatment

| Surface | Boundary condition to use | Rationale | E+ object | Source |
|---|---|---|---|---|
| Interior partition between two conditioned zones (same temp) | adiabatic? or heat-transfer inter-zone? |  |  |  |
| Corridor ↔ unit wall |  |  |  |  |
| Floor/ceiling between stacked floors | inter-zone / adiabatic |  |  |  |
| Perimeter ↔ core wall |  |  |  |  |
| Courtyard inner wall (exterior, faces court) | exterior with own solar/shading |  |  |  |

### Table 4 — Robustness: avoiding the E+ fatal

| Failure | Cause | Fix | Source |
|---|---|---|---|
| Donut/courtyard core → mismatched inter-floor vertices (OpenUBEM current) |  |  |  |
| Interior surfaces not matched between zones |  |  |  |
| Zone with < min area / degenerate geometry |  |  |  |
| Load double-counting at corridor/core boundary |  |  |  |

---

## Part C — Synthesis (the conservation + surfaces spec)

Give: (1) the **conservation invariant list** the generator must satisfy, and the E+ mechanism for each;
(2) the **recommended load-distribution method** (per-area × space-type intensity, with corridor/unit
weighting) that provably conserves totals and stays zero-fitted-parameters; (3) the **interior-surface
boundary-condition table** — which walls adiabatic vs. heat-transfer, with rationale; (4) the **robustness
recipe** that eliminates the courtyard/donut fatal and load double-counting. This section is the physics
contract the plan will encode and test.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C conservation+surfaces spec.
3. Cite the E+ I/O Reference object and, separately, any zoning-guidance source.
4. **"Confidence and caveats":** which surface-treatment choice is least settled in the literature.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **State the exact E+ mechanism** (object name) for each conservation invariant and surface treatment.
- **The load-distribution method must provably conserve building totals** — show the arithmetic.
- **Give the concrete fix for the courtyard/donut inter-floor fatal.**
- **No fabricated precision;** flag GAPs. **Stay on topic** — conservation & surfaces only, not geometry
  (`L05`) or programs (`L07`–`L10`).
