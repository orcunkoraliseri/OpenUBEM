# Image-generation prompt — LayoutAssigner technical flowchart

**Purpose:** a single clean engineering flowchart of the `layout_assign` resolution-mode pipeline, for use in documentation/presentations. Paste the prompt below into Gemini (or any image model) as-is.

**Tool:** Gemini web · **Style:** technical/vector flowchart, not photorealistic · **Orientation: horizontal (left-to-right).**

---

## Prompt to paste

Create a clean, single-page technical flowchart diagram, **left-to-right horizontal flow**, engineering/software-architecture documentation style (think a well-designed AWS or Google Cloud architecture diagram — flat vector shapes, no photorealism, no 3D, generous whitespace, crisp small sans-serif labels, muted professional color palette of navy blue / slate gray / white background, one accent color — teal or amber — used only for the decision branch and the two warning callouts). Wide landscape canvas; the main chain reads strictly left to right along one horizontal spine.

Title at the top-left, bold: **"LayoutAssigner — resolution_mode = 'layout_assign'"**. Small subtitle underneath in gray: "Archetype prototype-substitution pipeline (OpenUBEM)".

Render this exact sequence of labeled rectangular process boxes along a single horizontal spine, connected by rightward arrows, in this order:

1. **"Real building record"** — sub-label in smaller text inside the box: "footprint_area_m², num_floors, archetype_id (from semantic enrichment)". Draw this as a rounded rectangle, slightly different fill (light gray) to mark it as an input, not a processing step.
2. Arrow right to **"Archetype → baseline lookup"** — sub-label: "match archetype_id against 28 DOE / ASHRAE 90.1 prototype IDFs (BaselineIDFRegistry)".
3. From that box, draw a **diamond decision shape**: **"Baseline found?"**
   - A branch labeled **"No"** dropping straight **down** (the only vertical deviation from the horizontal spine) to a smaller box below: **"Fallback to adaptive auto zoning"** with sub-label "single_zone / one_zone_per_floor / perimeter_core + dq_flag tagged". Give this branch a dashed border and the amber accent color, to visually mark it as the exception path.
   - A branch labeled **"Yes"** continuing straight along the horizontal spine to the next box.
4. **"Compute scaling factor"** — sub-label: "S = real_area ÷ baseline_area · planar factor = √S".
5. **"Scale geometry + absolute loads"** — sub-label: "vertices × √S (walls, windows, shading) · lights / equipment / people / infiltration / OA / DHW × S · per-area density fields untouched".
6. **"Purge outputs + patch location/weather"** — sub-label: "strip baseline Output:* objects · replace Buffalo-CZ6A Site:Location/RunPeriod with the target city's real EPW".
7. **"Parse real zone list"** — sub-label: "read back the DOE-native zone names for provenance/QA (e.g. \"G SW APARTMENT\")".
8. **"Hand off to standard IDF builder"** — sub-label: "manifest tagged zoning_strategy = layout_assign — merges into the same pipeline as every other resolution mode from here on".
9. Final box, rightmost, visually distinct (bold border, darker fill): **"EnergyPlus 23.1 annual simulation → results & carbon"**.

Below the entire horizontal spine, add a small full-width footnote strip with a thin border, smaller gray text, titled "Known limitations (flagged, not hidden)": two short bullet lines inside it — "• fixed-capacity equipment (transformers, DHW tanks, HVAC coils) not yet scaled" and "• baseline's native Buffalo CZ 6A envelope still used (climate-specific envelope patching not yet applied)". This footnote strip should look like a documentation caveat, not part of the main flow — separate it with a horizontal divider line, positioned under the whole 9-box chain, not under any single box.

Keep every piece of text short, legible, and exactly as given above — do not invent additional steps or relabel the boxes. Wide landscape orientation, one single horizontal row for the 9 main boxes (shrink box width/font slightly rather than wrapping the chain onto a second row); the only permitted deviation from the single horizontal line is the one downward decision branch described in step 3.
