# European locations — the brief (v3)

**2026-08-30.** One page: what we are trying to do, what is wrong, how it gets fixed, in what order.
Detail lives in `STATE_european_locations_v3.md`; this is the plain version.

---

## 1. The goal

Take four real European residential neighbourhoods — **Madrid Berruguete, Lyon Hauts de Croix-Rousse,
London St Dunstan's, Bologna Galvani 2** — and model every residential building the way the published
Ankara method models one: real footprint, real storey count, **each floor divided into residential thermal
zones plus an unconditioned circulation core**, each building simulated on its own but **surrounded by its
real neighbours** so shading is right.

The output is a set of IDFs that GSSCanada can later inject occupants into, and four 3D viewers where a
click shows the actual floor plan that was simulated.

Method of record: MVP §4.2–§4.4, `IMP_step8/outputs/floor_layout_generation_report.md` §5–§9, and
*Energy & Buildings* 337 (2025) 115620 Fig. 4.

---

## 2. What is done

The pipeline exists and runs end to end. All fourteen `EU-01`–`EU-14` packages plus `EU-13B` and `EU-14B`
are complete. 2,516 buildings across four districts were prepared, simulated on Speed, harvested, and bound
into the viewers. Dwelling counts are now conserved exactly — 28,189 declared, 28,189 zones, zero errors.

---

## 3. What is wrong — two things, both visible in the viewer

### Problem 1 — most floors are not zoned by the ruled scheme

The rule says: cut each floor into a `1×1`, `2×1`, `2×2`, `3×2` or `4×2` grid of dwellings around a
**centroidal unconditioned stair core**, with a **1.80 m corridor spine** on long plates. Refuse anything
above 8 dwellings per floor.

What is actually on disk:

- **Only 57.81 % of buildings (1,469 of 2,541) use a ruled grid.** The bar is ≥ 95 %.
- **33.2 % (843) still use the old strip cutter** — parallel bands sliced across the plate, no corridor.
  That is what the screenshots show, and the published coverage figures (93.6 %, 88.1 %) hide it, because
  the strip cutter is counted as a success.
- **0 of 2,541 buildings have the unconditioned core.** Circulation is measured but never cut out, because
  the owner had not ruled whether to carve it from the plate or add it outside.

Worst district is Bologna at 49.6 %, then London at 54.9 %.

### Problem 2 — every building was simulated alone in an empty field

The rule says: simulate each building separately, but with **every building within 20 m** present as
shading geometry, and with **shared walls between attached buildings set to adiabatic**.

What is actually on disk:

- **0 of 2,516 IDFs contain a single shading surface.** One line does it —
  `scripts/run_eu_s2_campaign.py:227` passes an empty context list.
- **0 of 2,516 contain an adiabatic surface.** Terraced European stock is losing heat through walls it
  shares with the neighbour.
- Each building is missing **11–12 neighbours** on average, and **88.5–99.1 %** of buildings touch at least
  one other building.

**Consequence: none of the four district EUIs can be quoted.** They are the state of the model, not results.

---

## 4. How it gets fixed

Two owner rulings were taken on 2026-08-30, and they unblock everything:

- **`D-EU-39`** — the ruled scheme is mandatory on ≥ 95 % of buildings **in every district** (not a fleet
  average); the strip cutter is retired; and circulation is **carved** out of the real plate. The footprint
  stays real, conditioned area drops, and conditioned area is published beside gross footprint area.
- **`D-EU-40`** — every building is simulated with its 20 m context as shading, and attached walls are
  adiabatic. Written up as `rules/RULES_context_geometry_simulation_2026-08-30.md`.

The code needed already exists on the North-American side (`discover_context`, `extrude_geometry`,
`set_adiabatic_surfaces`) — it was simply never wired into the European path.

---

## 5. How it is planned

One plan, two work packages, executed by fresh Sonnet sessions, never by this session:
`implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`.

| | Package | Tasks | Ends at |
|---|---|---|---|
| 1 | **`EU-15`** — zoning | Courtyard unfolding, harden the L-shape and gallery routes, retire the strip cutter, carve the core and corridor | ≥ 95 % ruled coverage per district, core present, conditioned area published |
| 2 | **`EU-16`** — context | 20 m context shading, adiabatic party walls, `ShadowCalculation`, rebuild IDFs, resimulate all four districts on Speed, re-emit side-cars and viewers | Four fresh district EUIs, with the shading/adiabatic census |
| 3 | validation | Independent audit against both rule documents' acceptance tests | `validation/VALIDATION_EU-15_EU-16_*.md` — PASS or a named defect list |

Three stop-and-report points: after the geometry census, after the local IDF rebuild (before any `sbatch`),
and after the harvest. Nothing goes to Speed without an explicit instruction at the second point.

Walltime: every `sbatch` requests `--time=7-00:00:00` minimum, never a shorter hours guess — new
2026-08-31 after a Lyon resubmit timed out twice at 3h. Detail: `STATE_european_locations_v3.md`.

**What is deliberately not in scope:** `D-EU-37` (extending the typology table, which would recover Lyon's
226 and London's 345 excluded buildings) stays an unruled owner decision, and the DR16 Bologna and DR15
London verdicts are reported, never tuned into a band.
