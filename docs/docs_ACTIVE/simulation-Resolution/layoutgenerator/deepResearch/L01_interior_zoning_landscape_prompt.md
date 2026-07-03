# Deep-Research Prompt L01 — INTERIOR-ZONING LANDSCAPE & METHOD TAXONOMY (how a footprint becomes thermal zones)

> SCOPE GUARD — READ FIRST. This is the **framing / taxonomy** task for the whole layoutGenerator set.
> Its job is to map the solution space so every downstream prompt scopes cleanly. Answer two things only:
> (1) **what classes of method exist for turning a 2-D building footprint into an interior set of thermal
> zones** (rule-based / standards-driven, procedural-template, geometric-decomposition, and ML/generative)
> and (2) **when each class is appropriate** as a function of footprint shape, building type, and desired
> fidelity. Do NOT benchmark a specific tool's behaviour (that is `L02`), do NOT specify the geometry
> algorithms (that is `L05`), and do NOT design the corridor-packing method itself (that is `L06`). See
> `00_README_layoutgenerator_prompt_set.md` for shared facts, roster, conventions.

---

## What this document is

A structured landscape survey of **automatic thermal-zone / interior-space subdivision** for building
energy models. OpenUBEM today has exactly one non-trivial interior-zoning method — geomeppy native
core/perimeter (`perimeter_core`), a 4.57 m inward buffer — and it works only for compact, convex,
hole-free footprints; everything else drops to `one_zone_per_floor`. Before building `layoutGenerator.py`
we need the field's own map: which method *families* exist for subdividing a floor plate into zones, what
inputs each needs, what shapes each can handle, and which fidelity tier each targets. This prompt tells
the manager which family the proposed "corridor + DOE-module room packing" method belongs to, and what
its recognized alternatives are.

## Role

UBEM / BEM zoning-methods research analyst. Ground the taxonomy in the recognized sources: **ASHRAE
90.1-2019 Appendix G** and the LEED/PNNL core-perimeter zoning rules (rule-based tier), the **DOE/PNNL
prototype & commercial reference buildings** (Deru et al. 2011) and OpenStudio's geometry measures
(procedural-template tier), the **computational-geometry literature** on offsetting / skeletons /
decomposition (geometric tier), and the **automated-floorplan-generation literature** (Graph2Plan,
HouseGAN, RPLAN — ML/generative tier). Distinguish clearly between *zoning for energy simulation* (few,
thermally-motivated zones) and *architectural floor-plan generation* (many program-motivated rooms) —
they are different problems that this project must bridge.

## Why this matters (so you scope correctly)

The method family determines everything downstream: its data needs, its failure modes, whether it
satisfies zero-fitted-parameters, and whether it can emit provenance. OpenUBEM's proposed method places a
corridor on the footprint spine and packs DOE-standard rooms onto edges/corners — that is a
*procedural-template method driven by a geometric decomposition*. This prompt must confirm that is a
recognized, defensible family (vs. pure rule-based core/perimeter, or vs. generative floorplan ML), and
must surface any family the manager has not considered that would handle L/U/O footprints more simply.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — The method families for footprint → thermal zones

| Method family | Core idea | Inputs required | Footprint shapes it handles well | Zones produced (few thermal vs. many program) | Fidelity tier | Representative source |
|---|---|---|---|---|---|---|
| Rule-based standards zoning (App-G core/perimeter) |  |  |  |  |  |  |
| Procedural template / prototype floorplate transplant |  |  |  |  |  |  |
| Corridor-spine + room-packing (the proposed method) |  |  |  |  |  |  |
| Geometric decomposition (skeleton / rectangular split, then zone each part) |  |  |  |  |  |  |
| Grid / raster subdivision |  |  |  |  |  |  |
| ML / generative floorplan synthesis |  |  |  |  |  |  |
| No-subdivision fallbacks (single-zone, one-zone-per-floor) |  |  |  |  |  |  |

### Table 2 — Fitness by footprint shape

Which families cope with which shapes. Mark ✓ / partial / ✗ and one-line why.

| Footprint shape | Rule-based core/perim | Procedural template | Corridor+packing | Geometric decomposition | ML/generative |
|---|---|---|---|---|---|
| Compact rectangle |  |  |  |  |  |
| L-shape |  |  |  |  |  |
| U-shape |  |  |  |  |  |
| T / cross |  |  |  |  |  |
| O-shape / courtyard (interior ring) |  |  |  |  |  |
| Thin ribbon (narrow) |  |  |  |  |  |
| Irregular / concave blob |  |  |  |  |  |

### Table 3 — Fit to OpenUBEM's constraints, per family

| Method family | Satisfies zero-fitted-parameters? (uses published dimensions, no target tuning) | Can emit provenance (which method / fallback touched a building)? | Expressible in `shapely`+`geomeppy`? | Verdict for OpenUBEM (adopt / adopt-as-fallback / skip) |
|---|---|---|---|---|
| Rule-based core/perimeter |  |  |  |  |
| Procedural template transplant |  |  |  |  |
| Corridor+packing |  |  |  |  |
| Geometric decomposition |  |  |  |  |
| ML/generative |  |  |  |  |

### Table 4 — The thermal-zoning vs. architectural-floorplan distinction

| Question | Answer + source |
|---|---|
| How many zones does BEM practice put on a typical floor (vs. an architectural plan's room count)? |  |
| Is the App-G "4 perimeter + 1 core" the field's default *thermal* zoning granularity? |  |
| When does a study go finer than core/perimeter (per-room), and what drives that (daylighting, HVAC zoning, load diversity)? |  |
| Does the corridor+DOE-module approach produce *thermal* zones or *architectural* rooms — and does that matter for EUI? |  |

---

## Part C — Synthesis (the family recommendation)

Give: (1) a one-paragraph verdict on **which method family OpenUBEM's proposed corridor+DOE-module method
belongs to**, and whether the field regards it as sound for UBEM-scale zoning; (2) the **recommended
primary family + fallback chain** for OpenUBEM (e.g. "core/perimeter where it works → geometric
decomposition into wings, each core/perimeter → single-zone-per-floor as last resort"); (3) an explicit
statement of **which families the downstream prompts should detail** (confirming the L02–L15 split or
proposing a change); (4) the single most important thing OpenUBEM's current one-method approach is
missing.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C synthesis.
3. Cite a standards/tool source for rule-based/procedural claims and a peer-reviewed / CS source for
   geometric/generative claims — keep the two kinds distinct.
4. **"Confidence and caveats":** which family's fitness for city-scale UBEM is least evidenced.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Cover all seven families in Table 1** — no "unknown" without saying what evidence would resolve it.
- **Explicitly locate the proposed corridor+packing method within the taxonomy.**
- **Respect the two hard constraints** (zero-fitted-parameters, provenance) when judging admissibility.
- **No fabricated precision;** flag GAPs. **Stay on topic** — the *taxonomy of methods and when each
  applies* only, not per-tool behaviour (`L02`), geometry algorithms (`L05`), or accuracy (`L14`).
