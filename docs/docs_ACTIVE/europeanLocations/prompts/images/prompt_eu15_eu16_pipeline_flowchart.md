# Image prompt — `EU-15` + `EU-16` pipeline (horizontal technical flowchart)

**Shows:** the order of operations, from a GIS footprint to one simulated building surrounded by its context.
**Style:** §2.1 technical flowchart, horizontal (`docs/docs_EXPLANATION/OpenUBEM_graphic_summary_prompt_styles.md`).
**Source of the steps:** `implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md` §6 T01–T09 ·
`rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md` §2 · `rules/RULES_context_geometry_simulation_2026-08-30.md`.

**Revision 2026-08-30** — the circulation branch (corridor spine vs stair core) is now an explicit decision, sub-labels
are shortened, and label duplication is forbidden explicitly.

---

## Prompt to paste

Create a clean single-page technical flowchart diagram, **left-to-right horizontal flow**, engineering documentation
style — flat vector shapes only, no photorealism, no 3D, generous whitespace, crisp small sans-serif labels, muted
palette of slate gray / navy on a white background, with **one teal accent** used only for the decision diamonds and the
exception branches. Wide landscape canvas; the main chain reads strictly left to right along one horizontal spine.

Title top-left, bold: **"EU-15 ruled zoning + EU-16 context — one building, one run"**. Small gray subtitle underneath:
"OpenUBEM · Madrid · Lyon · London · Bologna".

Render this exact sequence of labelled rectangular process boxes along a single horizontal spine, connected by rightward
arrows, in this order:

1. **"GIS footprint + storeys"** — sub-label: "footprint · dwellings declared · storeys". Rounded rectangle, light-gray
   fill, to mark it as an input rather than a step.
2. **"Regularise the plate"** — sub-label: "tolerance 0.15 m · refuse if area moves > 2 %".
3. **"Classify morphology"** — sub-label: "point block · L-shape · I-shape slab · courtyard".
4. **"Stratify dwellings"** — sub-label: "q / (q+1) per storey · never reduce the count".
5. A **teal diamond**: **"Dwellings on this storey?"**
   - Branch labelled **"2 to 4"** rising to a box: **"Centroidal stair core"**, sub-label: "12–25 m² · 6–12 % of plate".
   - Branch labelled **"5 to 8"** dropping to a box: **"Corridor spine"**, sub-label: "1.80 m double-loaded, long axis".
   - Branch labelled **"more than 8"** dropping to a dashed-teal box: **"Refused — FALLBACK_PENDING_LAYOUT"**,
     sub-label: "keeps one_zone_per_floor · reason recorded".
   The first two branches rejoin the spine at the next box.
6. **"Cut the dwellings"** — sub-label: "equal-area cuts of the real plate, by bisection · facade ≥ 2.50 m".
7. **"Check the plate closes"** — sub-label: "dwellings + circulation = plate · 0.00 % area error".
8. **"Query 20 m context"** — sub-label: "every neighbour in 01_buildings_clean.gpkg · height_m → levels × 3.0 m →
   district median".
9. A second **teal diamond**: **"Neighbour touching?"**
   - Branch labelled **"Yes, within 0.30 m"** to a small box: **"Shared wall → Adiabatic"**, sub-label: "ground slab at
     z = 0 stays Ground".
   - Branch labelled **"No"** rejoining the spine.
10. **"Assemble the IDF"** — sub-label: "zones → intersect_match → shading blocks · context is geometry only ·
    Solar Distribution = FullExterior".
11. Final box, rightmost, bold border and darker fill: **"EnergyPlus 23.1.0 on Speed — one annual run per building"**.

Below the whole spine, separated by one horizontal divider line running the full width, add a small footnote strip in
smaller gray text titled "Measured before this work": three short lines — "• 57.81 % of buildings (1,469 of 2,541) on a
ruled grid; the bar is 95 %", "• 0 of 2,541 buildings carry an unconditioned zone", "• 0 of 2,516 IDFs carry a shading
or adiabatic surface".

**Rendering hygiene, obey strictly.** Every box, label and sub-label listed above appears exactly ONCE; never repeat the
same label twice in the diagram. Do not add any box, arrow, title or word that is not written above. Spell every string
exactly as given — no invented words, no word repeated twice in a row, no truncation, no placeholder text. Keep the main
chain on one single horizontal row: if it does not fit, shrink the box width and the font rather than wrapping onto a
second row; the only permitted departures from the spine are the branches described in steps 5 and 9.
