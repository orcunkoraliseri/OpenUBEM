# EXAMPLE — dwelling-layout validation sheet (`EU-13B` sample execution)

**Arc:** European locations × Step 8 · **Work package:** `EU-13B` · **Date:** 2026-08-28 · **Author:** director session
**Status: PROTOTYPE EVIDENCE, NOT A RESULT.** No repository code was changed, no side-car was re-emitted, no viewer was
regenerated, nothing was submitted to Speed, and no EnergyPlus run stands behind any number in this document.

**What this document is for.** The owner asked to see what a correct floor plan looks like *before* `EU-13B` is
dispatched. This is that sample, kept as the worked example against which an executor's output is validated: the same
eight buildings the owner clicked in the Madrid, Lyon and London viewers, drawn as they are simulated today beside how
the ruled scheme draws them, with the acceptance quantities printed. An `EU-13B` deliverable is compared against this
sheet — §6 — not against a screenshot.

Interactive version of the same eight sheets: <https://claude.ai/code/artifact/3fe940e8-231d-459c-b46f-fb9daa1995ce>

---

## 1. The ruling this document carries

**`D-EU-36` — coverage bar, RULED 2026-08-28 by the owner: ≥ 95 % of buildings is sufficient; 100 % is not required.**

The consequence is that `EU-13B` may fail closed on the residual. A building the ruled grid cannot express
(`DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8`) is **refused**, keeps the already-ruled `one_zone_per_floor` fallback, and
is counted in a disclosed residual — it is never forced into a grid that does not fit it. What the bar does **not**
permit is silently *reducing* a building's dwelling count so that it fits, which is the defect `FINDING 201` records.

🔴 **Still open, and not settled by the coverage bar:** whether the unconditioned core is **carved** out of the observed
plate (the outline stays real, conditioned area falls by the circulation share, and every published EUI denominator
moves) or **added outside** it (`A_C_Ref` untouched, but the modelled building becomes larger than the measured
footprint, and `generate_external_unconditioned_core` refuses every non-rectangular plate —
`openubem/geometry/european_residential.py:377`). **Every drawing in this document was produced by carving.** The
recommendation on record is to carve, and to publish conditioned area beside gross footprint area on every building: a
denominator change is disclosable, a false footprint is not. `EU-13B` `T06` stays blocked until that half is ruled.

---

## 2. Method — what the sheets draw

Source of the method: `previous/MVP_european_locations.md` §4.2 (grid assignment), §4.3 (unconditioned staircase core),
§4.4 (habitability gate), and `IMP_step8/outputs/floor_layout_generation_report.md` §5–§9.

1. **Dwellings per storey come from the q/(q+1) stratification**, never from `ceil(total ÷ storeys)` applied to every
   storey. A 69-dwelling building over 17 storeys is 16 storeys of 4 plus 1 of 5 — not 17 storeys of 5.
2. **The ruled grids are `1×1`, `2×1`, `2×2`, `3×2`, `4×2`** — a ceiling of 8 dwellings per storey. Above 8 there is no
   ruled grid, so the building is refused, not approximated.
3. **Circulation is placed first, not last.** Five or more per storey → a 1.80 m double-loaded corridor spine on the
   long axis; two to four per storey → a centroidal unconditioned stair core at 6–12 % of the plate, 12.0–25.0 m².
4. **Dwellings are equal-AREA cuts of the real plate**, found by bisection, never equal-width strips of a bounding box.
   This is what keeps every cell non-empty on a concave or courtyard footprint and closes the area audit exactly.
5. **Habitability** (§4.4): every dwelling must hold ≥ 2.50 m of exterior facade contact. On failure the retry is a
   **90° rotation of the cutting frame at the same dwelling count** — never a reduction of the count.
6. **Area conservation:** dwellings + circulation = the observed plate, to 0.00 %.

---

## 3. Measured on the eight sample buildings

| | value | what it means |
|---|---:|---|
| Buildings drawn | 8 | 7 laid out, 1 correctly refused |
| Dwellings declared | 287 | across the 7 laid out — the number the sources state |
| Zones simulated today | **322** | +35 (+12.2 %) invented by `ceil()` on every storey |
| Zones, ruled scheme | **287** | exact — the q/(q+1) stratification, storey by storey |
| Plan area error | **0.00 %** | dwellings + circulation = the real plate, on every sheet |
| Circulation share | 5.0 – 11.7 % | inside the ruled 6–12 % band throughout |
| Refused by rule | 156 | 1 plate at 31–32 dwellings per storey, above the `4×2` ceiling — today it emits 160 overlapping slivers |

### 3.1 Per building

| # | building | district | plate m² | storeys | dwellings | per storey (ruled) | zones today | zones ruled | grid | scheme | circulation | min. facade | area error |
|---|---|---|---:|---:|---:|---|---:|---:|---|---|---:|---:|---:|
| 8 | `way/51781396` | London | 312.2 | 17 | 69 | 5 / 4 | 85 | **69** | `3×2` | corridor slab | 36.42 m² (11.7 %) | 6.74 m | 0.00 % |
| 9 | `relation/12704090` | Madrid | 666.1 | 5 | 30 | 6 | 30 | **30** | `3×2` | corridor slab | 48.17 m² (7.2 %) | 12.06 m | 0.00 % |
| 10 | `way/388485191` | Madrid | 475.8 | 7 | 38 | 6 / 5 | 42 | **38** | `3×2` | corridor slab | 41.80 m² (8.8 %) | 7.74 m | 0.00 % |
| 11 | `way/420409335` | Madrid | 361.5 | 3 | 20 | 7 / 6 | 21 | **20** | `4×2` | corridor slab | 20.05 m² (5.5 %) | 2.79 m | 0.00 % |
| 12 | `relation/3730743` | Madrid | 1868.7 | 5 | 156 | 32 / 31 | 160 | **0** | — | **REFUSED** | — | — | — |
| 13 | `way/391279229` | Madrid | 801.6 | 8 | 44 | 6 / 5 | 48 | **44** | `3×2` | corridor slab | 53.55 m² (6.7 %) | 9.80 m | 0.00 % |
| 14 | `BATIMENT0000000240879941_part0` | Lyon | 500.0 | 4 | 15 | 4 / 3 | 16 | **15** | `2×2` | point block | 25.00 m² (5.0 %) | 27.35 m | 0.00 % |
| 15 | `BATIMENT0000000240880045_part0` | Lyon | 954.3 | 10 | 71 | 8 / 7 | 80 | **71** | `4×2` | corridor slab | 97.91 m² (10.3 %) | 12.81 m | 0.00 % |

The `min. facade` column is the acceptance quantity for §4.4: the smallest exterior-wall contact any dwelling on that
plate holds. The lowest value in the sample is **2.79 m** on `way/420409335`, above the 2.50 m gate but not by much —
that building is the one to re-check first if the gate is ever retuned.

⚪ Buildings 14 and 15 are drawn but are **not simulated today**, for two different reasons that must not be conflated:
`BATIMENT0000000240879941_part0` is a genuine `FINDING 203` typology-table gap (15 dwellings over 4 storeys, which the
`D-EU-04-G` table has no row for), whereas `BATIMENT0000000240880045_part0` is one of Lyon's five
`MISSING_OBSERVED_YEAR_BUILT` exclusions. Its geometry is fully derivable; only its envelope is not.

---

## 4. Fleet coverage against the 95 % bar

Measured 2026-08-28 by replaying the ruled partitioner over every building each district actually prepared for the `S2`
campaign — the exact population `EU-13B` would re-partition. Measurement only: no IDF was built, nothing was simulated.

| district | prepared | ruled layout emits | coverage | refused `> 8`/storey | layout emitted **today** |
|---|---:|---:|---:|---:|---:|
| Madrid — Berruguete | 961 | 917 | **95.4 %** | 44 | 770 (80.1 %) |
| Lyon — Hauts de Croix-Rousse | 297 | 284 | **95.6 %** | 13 | 239 (80.5 %) |
| London — St Dunstan's | 82 | 64 | **78.0 %** | 18 | 69 (84.1 %) |
| Bologna — Galvani 2 | 1204 | 1204 | **100.0 %** | 0 | 796 (66.1 %) |
| **fleet** | **2544** | **2469** | **97.05 %** | **75** | **1874 (73.7 %)** |

**The bar is met at fleet level: 97.05 % ≥ 95 %.** The ruled scheme covers *more* of the fleet than the current
implementation does (73.7 %), while emitting the correct dwelling count where the current one over-counts — so meeting
the bar costs no coverage. The single failure mode across all four districts is the `> 8` per storey refusal; there is
no habitability failure and no area failure anywhere in the fleet.

🔴 **London is the exception and must be stated whenever this table is quoted: 78.0 %, below the bar.** Its 82 prepared
buildings carry 18 refusals at more than 8 dwellings per storey, the densest of the four districts. The bar the owner
ruled is a **fleet** bar, not a per-district one, and no London district-level result may be described as meeting it.

⚪ Bologna reaches 100 % because its dwelling counts are imputed from the archetype's `n_apartment` and never exceed the
`4×2` ceiling. That is a property of the imputation, not of the Bolognese stock, and it must not be read as evidence
that the ruled grid fits Italy better than it fits Spain.

### 4.1 `FINDING 204` — the two circulation criteria in MVP §4.3 conflict outside a narrow plate window

MVP §4.3 states communal circulation as **6–12 % of gross floor area** *and* **12.0–25.0 m² per floor**. Those two
conditions can hold together only for plates of **100.0 m² – 416.7 m²**: below 100 m², twelve percent of the plate is
under 12 m²; above 416.7 m², six percent of the plate is over 25 m².

Measured on the 2,544 prepared buildings: **1,602 (63.0 %) sit inside that window**, 542 plates are too small and 400
are too large. The sample in §3.1 shows the conflict directly — the percentage rule holds on all seven laid-out
buildings (5.0–11.7 %) while the absolute 25 m² ceiling is **exceeded on five of seven**, up to 97.91 m² on a 954 m²
plate. It is exceeded by construction: §4.2 requires a 1.80 m double-loaded spine for `3×2` and `4×2`, and 1.80 m across
a 55 m plate is 99 m² whatever §4.3 says.

The prototype resolves this by letting the **percentage** rule win and treating 12.0–25.0 m² as descriptive of the
Ankara plate sizes it was measured on (mean 18.4 m², a stock of mostly 150–350 m² plates). **That is a choice, it is not
in the MVP, and it is not this session's to make.** `EU-13B` must tag every building where the absolute band was
departed from rather than report a core inside a band it is not inside, and the owner must rule which of the two
criteria binds. It is recorded here because it is invisible on the sample of eight and unavoidable on the fleet.

---

## 5. The drawing sheets

Left panel = the zones EnergyPlus actually ran. Right panel = the ruled scheme. Hatched red = unconditioned circulation
(corridor spine or stair core). Both panels are at the same scale; the bar is 10 m.

### 5.8 — `way/51781396` · London — St Dunstan's · `GB.ENG.AB.04`

![Dwelling plan, as simulated beside as ruled, way/51781396](content/eu13b_sample_plan_8_way_51781396.svg)

- Footprint **312.2 m²**, **17** storeys, **69** dwellings declared.
- Today: `ceil(69 ÷ 17) = 5` on every storey → **85 zones**, +16 against the declared count, and no circulation zone.
- Ruled: 16 storeys at 4 plus 1 storey at 5 → **69 zones**, exact. Grid `3×2`, corridor slab, circulation 36.42 m²
  (11.7 % of plate), smallest facade contact 6.74 m, area error 0.00 %.

### 5.9 — `relation/12704090` · Madrid — Berruguete · `ES.ME.AB.04`

![Dwelling plan, as simulated beside as ruled, relation/12704090](content/eu13b_sample_plan_9_relation_12704090.svg)

- Footprint **666.1 m²**, **5** storeys, **30** dwellings declared.
- Today: `ceil(30 ÷ 5) = 6` on every storey → **30 zones**. The count is right here, but the plan is not: no corridor,
  and the six cells are equal-width strips of a bounding box rather than of the plate.
- Ruled: 6 on every storey → **30 zones**. Grid `3×2`, corridor slab, circulation 48.17 m² (7.2 %), smallest facade
  contact 12.06 m, area error 0.00 %. This building is the clean case: the count never moves, only the geometry does.

### 5.10 — `way/388485191` · Madrid — Berruguete · `ES.ME.AB.04`

![Dwelling plan, as simulated beside as ruled, way/388485191](content/eu13b_sample_plan_10_way_388485191.svg)

- Footprint **475.8 m²**, **7** storeys, **38** dwellings declared.
- Today: `ceil(38 ÷ 7) = 6` on every storey → **42 zones**, +4.
- Ruled: 3 storeys at 6 plus 4 at 5 → **38 zones**, exact. Grid `3×2`, corridor slab, circulation 41.80 m² (8.8 %),
  smallest facade contact 7.74 m, area error 0.00 %.

### 5.11 — `way/420409335` · Madrid — Berruguete · `ES.ME.AB.05`

![Dwelling plan, as simulated beside as ruled, way/420409335](content/eu13b_sample_plan_11_way_420409335.svg)

- Footprint **361.5 m²**, **3** storeys, **20** dwellings declared.
- Today: `ceil(20 ÷ 3) = 7` on every storey → **21 zones**, +1.
- Ruled: 2 storeys at 7 plus 1 at 6 → **20 zones**, exact. Grid `4×2`, corridor slab, circulation 20.05 m² (5.5 %),
  smallest facade contact **2.79 m** — the tightest in the sample — area error 0.00 %.

### 5.12 — `relation/3730743` · Madrid — Berruguete · `ES.ME.AB.04`

![Dwelling plan, as simulated beside the refusal, relation/3730743](content/eu13b_sample_plan_12_relation_3730743.svg)

- Footprint **1868.7 m²**, **5** storeys, **156** dwellings declared.
- Today: `ceil(156 ÷ 5) = 32` on every storey → **160 zones** of overlapping slivers on a plate that cannot carry them.
- Ruled: **refused**, `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` — 32 dwellings per storey is four times the `4×2`
  ceiling of 8. The building keeps `one_zone_per_floor` and is counted in the disclosed residual. This refusal is part
  of the acceptance test: an implementation that lays this building out has failed, however good the other seven look.

### 5.13 — `way/391279229` · Madrid — Berruguete · `ES.ME.AB.06`

![Dwelling plan, as simulated beside as ruled, way/391279229](content/eu13b_sample_plan_13_way_391279229.svg)

- Footprint **801.6 m²**, **8** storeys, **44** dwellings declared.
- Today: `ceil(44 ÷ 8) = 6` on every storey → **48 zones**, +4.
- Ruled: 4 storeys at 6 plus 4 at 5 → **44 zones**, exact. Grid `3×2`, corridor slab, circulation 53.55 m² (6.7 %),
  smallest facade contact 9.80 m, area error 0.00 %.

### 5.14 — `BATIMENT0000000240879941_part0` · Lyon — Hauts de Croix-Rousse

![Dwelling plan, as simulated beside as ruled, BATIMENT0000000240879941_part0](content/eu13b_sample_plan_14_batiment0000000240879941_part0.svg)

- Footprint **500.0 m²**, **4** storeys, **15** dwellings declared.
- Today: nothing. The building is excluded by `TYPOLOGY_SIGNALS_DISAGREE` — `FINDING 203`, the `D-EU-04-G` table has no
  row for 15 dwellings over 4 storeys. The left panel shows what the partitioner *would* emit: `ceil(15 ÷ 4) = 4` on
  every storey → 16 zones, +1.
- Ruled: 3 storeys at 4 plus 1 at 3 → **15 zones**, exact. Grid `2×2`, point block with a centroidal stair core,
  circulation 25.00 m² (5.0 %), smallest facade contact 27.35 m, area error 0.00 %. The geometry is not the obstacle
  here; the typology table is, and that is `D-EU-37`, not `EU-13B`.

### 5.15 — `BATIMENT0000000240880045_part0` · Lyon — Hauts de Croix-Rousse

![Dwelling plan, as simulated beside as ruled, BATIMENT0000000240880045_part0](content/eu13b_sample_plan_15_batiment0000000240880045_part0.svg)

- Footprint **954.3 m²**, **10** storeys, **71** dwellings declared.
- Today: nothing. This one is **not** a table gap — it is one of Lyon's five `MISSING_OBSERVED_YEAR_BUILT` exclusions,
  so it has no TABULA band and therefore no envelope. Left panel: `ceil(71 ÷ 10) = 8` on every storey → 80 zones, +9.
- Ruled: 9 storeys at 7 plus 1 at 8 → **71 zones**, exact. Grid `4×2`, corridor slab, circulation 97.91 m² (10.3 %) —
  the `FINDING 204` case, four times the 25 m² ceiling and still inside the 6–12 % band — smallest facade contact
  12.81 m, area error 0.00 %.

---

## 6. How an executor is validated against this sheet

For each of the eight buildings above, an `EU-13B` implementation is accepted only if it reproduces **all** of:

1. the **zones ruled** column exactly — not within a tolerance, exactly;
2. an area error of **0.00 %** between dwellings + circulation and the observed plate;
3. a **circulation zone present on every storey** carrying two or more dwellings, of the scheme named in §3.1;
4. a smallest facade contact **≥ 2.50 m**, with the reported value within 0.05 m of §3.1;
5. `relation/3730743` **refused** with `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` and zero zones emitted.

A run that matches 1–4 but silently lays out `relation/3730743` has failed. A run that reduces any building's dwelling
count in order to pass the habitability gate has failed, whatever else it matches. A run whose fleet coverage falls
below **95 %** has failed the `D-EU-36` bar; a run above it that does not print the per-district split, London included,
has failed the disclosure that goes with the bar.

---

## 7. What this document may and may not be quoted for

- ⚪ **May** be quoted as the worked example of the ruled subdivision scheme and as the acceptance target for `EU-13B`.
- ⚪ **May** be quoted for the coverage figures in §4, which are a geometric census and depend on no simulation.
- 🔴 **May not** be quoted for any energy quantity. Nothing here was simulated; these layouts exist in no IDF.
- 🔴 **May not** be read as `D-EU-36` being fully ruled. The coverage bar is ruled; carve-versus-add is not.
- 🔴 **May not** be described as the current state of the model. Every viewer and every published district EUI still
  carries the over-counted layouts shown in the left-hand panels.

---

## 8. Reproduction

| artefact | path |
|---|---|
| ruled partitioner prototype | `scratchpad/ruled_layout_sample.py` — outside the repository, deliberately |
| fleet coverage census | `scratchpad/coverage_census.py` → `coverage_census.json` |
| plan sheets | `openubem/outputs/eu13b_sample_plan_*.svg`, mirrored to `content/` |
| interactive board | <https://claude.ai/code/artifact/3fe940e8-231d-459c-b46f-fb9daa1995ce> |
| defects this addresses | `FINDING 200`–`FINDING 203`, `previous/STATE_european_locations_v2.md` §3; superseded by `STATE_european_locations_v3.md` §3 |
| execution plan | `prompts/PROMPT_EU-13B_dwelling_layout_scheme_conformance.md` |
| method of record | `previous/MVP_european_locations.md` §4.2–§4.4 |

⚪ One reproduction trap, hit once while producing §4. The census reads each footprint in its native UTM CRS and
translates it to its own centroid before cutting, because the bisection blades span ±10⁶ m. A footprint left in absolute
UTM coordinates silently produces empty cells, and the run then reports a fleet coverage near **16 %** instead of 97 %,
mis-attributed to the habitability gate. Any executor re-measuring §4 must translate first.
