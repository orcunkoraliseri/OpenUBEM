# Layout-Mapping — Deep-Research Prompt Set (INDEX)

> READ FIRST. This is a **focused follow-on** to the main resolution-mode research set
> (`../00_README_resolution_prompt_set.md`, `../RESULT_01..16`). Those answered *what* zoning each mode
> should use. This sub-set answers the **one open question they left**: in `zone` mode, how do you take a
> building type's **standardized internal zone layout** (e.g. the DOE/PNNL prototype's "8 apartments + 1
> hallway" per floor, or an office's "core + 4 perimeter") and **apply it to a real, irregular GIS
> footprint** — when real buildings are L-/U-/T-shaped, many-sided, or oddly proportioned and the DOE
> prototype was drawn on a clean rectangle. Run each prompt in your deep-research tool; save the answer
> beside it as `RESULT_<id>_<slug>.md`. The manager audits and folds the method into the plan.

---

## The exact decision this set must inform

OpenUBEM builds **one EnergyPlus IDF per building** on the building's **real OpenStreetMap footprint**
(this is fixed — we do NOT swap in a resized DOE rectangle). In `zone` mode we want each floor divided
into the archetype's **DOE-defined zones**, all in that single IDF. Worked example, MidriseApartment:
DOE layout = **8 apartments (around the perimeter) + 1 central hallway = 9 zones/floor**; a 4-storey
building → 9 × 4 = 36 zones, simulated together. Offices → core + perimeter ring; warehouse → 1 zone;
etc. **The problem:** the DOE "8 apartments + hallway" is drawn for the DOE's own rectangle. On a real,
arbitrary footprint we must decide how to reproduce that layout. Two candidate philosophies frame every
prompt below:

- **Option 1 — Match the DOE zone count/type as closely as possible.** Always aim for the prototype's
  zone makeup (≈8 apartment zones + 1 corridor), subdividing the perimeter to hit the target count even
  on odd shapes. Most faithful; needs a real layout-generation algorithm; can be fragile.
- **Option 2 — Robust generic scheme.** Core/perimeter where the perimeter ring is split by the
  building's own wall edges (a 4-sided footprint → ~4 perimeter zones, a 6-sided → ~6) + 1 core
  mapped to the prototype's interior space (hallway/back-of-house). Simpler, robust on any shape, but the
  zone *count* won't equal the prototype's.

**We are not asking you to pick for us blindly — we are asking how peer UBEM tools and the literature
actually do this, with sources, so the manager can choose.** Every prompt must surface real, cited
practice, not invented schemes.

---

## The prompts

| # | File | What it learns |
|---|------|----------------|
| L01 | `L01_footprint_to_zone_layout_algorithms_prompt.md` | The master comparison: the actual auto-zoning algorithms tools use to turn an arbitrary footprint into prototype-like zones (straight-skeleton/offset, raster/pixel, shoebox, CEA), with perimeter-split rule, core formation, zone-count control, residential handling, irregular-shape robustness. |
| L02 | `L02_perimeter_subdivision_rule_prompt.md` | The apartment-count crux: how the perimeter ring is divided into rooms/units — by wall edge, by target width/area, or by orientation — i.e. what makes "8 apartments" happen, and the Option 1 vs Option 2 trade. |
| L03 | `L03_double_loaded_corridor_residential_prompt.md` | How residential / hotel **double-loaded-corridor** layouts (units along a central hallway) are generated or approximated on real polygons, where the corridor/core is placed, and code constraints (egress, daylight). |
| L04 | `L04_irregular_footprint_handling_prompt.md` | How tools adapt a prototype layout to non-rectangular shapes (L/U/T/courtyard/sliver): simplification, decomposition, fallbacks, and when to abandon the detailed layout for core/perimeter or single-zone. |
| L05 | `L05_zone_count_fidelity_vs_robustness_prompt.md` | Does reproducing the exact prototype zone count actually change energy results vs a simplified core/perimeter? The accuracy-vs-robustness evidence that says whether Option 1 is worth its complexity. |
| L06 | `L06_per_archetype_doe_layout_catalog_prompt.md` | The reference catalog: each DOE/PNNL prototype's actual per-floor zone layout — zone count, zone types, corridor presence, adjacency — i.e. the *target* layout OpenUBEM is trying to reproduce for every archetype. |

> Load-bearing core: **L01 + L02 + L06** (what others do, the perimeter-split rule, and the target
> layouts). L03 is critical specifically for residential/lodging; L04 makes it survive real geometry;
> L05 tells us whether the whole effort changes the answer enough to justify Option 1.

---

## Shared facts (all prompts assume these — same as the parent set)

- **Engine / geometry:** EnergyPlus 23.1, one IDF per building, annual 8760-hour run, **geomeppy**
  (`add_block`; native `core/perim` splits the perimeter ring into **one zone per exterior wall edge**
  and forms the core by inward offset).
- **Footprint is REAL and FIXED:** the building's true OSM polygon, never a resized DOE rectangle (the
  earlier "B1 over B2" decision stands). Neighbour shading depends on the true shape.
- **Perimeter depth:** 4.57 m (15 ft), ASHRAE 90.1-2019 Normative Appendix G Table G3.1 — do not re-derive.
- **Floor-to-floor:** 3.5 m. **EUI denominator:** `footprint_area_m2 × num_floors`, all modes.
- **Existing hard fallbacks (must be preserved):** core empties / core < 10 m² → `one_zone_per_floor`;
  interior courtyard (donut) → `one_zone_per_floor` (geomeppy donut core → vertex mismatch → E+ Fatal).
- **Zero-fitted-parameters:** any layout rule must be a published convention, not a tuned knob. The
  validated `auto` baseline (city EUI within ±9 % measured) stays the default and is not moved by this work.
- **Prior findings to build on (do not re-answer):** `../RESULT_03` gave a one-line per-archetype zoning
  verdict (incl. the residential **Core-as-Corridor** rule) and `../RESULT_04` gave core-vs-perimeter
  load/OA/WWR deltas. This sub-set goes deeper on the **geometry/layout** half they did not fully solve.

## Conventions for every answer (enforced by each prompt)

1. **Lead with the filled tables**; prose after. Empty / "TBD" cells are failures.
2. Every method/value carries a **named, dated source** — a peer-reviewed UBEM paper (author, venue,
   year), tool documentation (URBANopt, CityBES, AutoBEM, UMI, CEA), the DOE/PNNL prototype docs, or the
   EnergyPlus / geomeppy references. Blogs/vendor pages last resort, labelled.
3. Geometry in **SI** (m, m²); note any IP the source uses + conversion.
4. **No fabricated precision.** If a rule is your synthesis, say so. If unpublished, write
   **"GAP — needs manager decision"** + the closest defensible default and its source.
5. **Map onto OpenUBEM's exact archetype IDs** (roster in `../00_README_resolution_prompt_set.md`).
6. Frame everything against **Option 1 (match DOE count) vs Option 2 (robust edge-split + mapped core)**;
   say which each tool/method effectively chooses.

---

*OpenUBEM resolution-mode — layout-mapping sub-set. Markdown only; binding specs remain `docs/docs_main/`. 2026-06-29.*
