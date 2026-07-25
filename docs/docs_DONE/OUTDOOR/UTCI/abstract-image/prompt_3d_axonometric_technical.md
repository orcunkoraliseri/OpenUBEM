# UTCI / Stage-6 — Graphic Summary Prompt (Style §2.3 — Hybrid Annotated Axonometric)

**Style reference:** `docs/docs_EXPLANATION/OpenUBEM_graphic_summary_prompt_styles.md` §2.3 + §3.
**Intended use:** paste the block below **verbatim** into Gemini web (or a comparable image model).
**Scope note:** this graphic presents the Stage-6 UTCI pipeline **as a process** — it deliberately does
not encode which tasks are complete; completion status lives in `docs/docs_DONE/OUTDOOR/UTCI/UTCI_CHECKLIST.md`.

**Step content sourced from** `implementation/PLAN_utci_microclimate_implementation.md` §2 ("What we are
building", lines 128-160) — the real module chain, in real execution order. Do not edit the quoted
strings when iterating; per style-guide §4.4, iterate on layout/legibility only.

---

## PROMPT — copy everything below this line

Create a single wide landscape **technical illustration** in the style of a premium engineering
brochure exploded-diagram: a **photorealistic 3D axonometric render with a precise technical
annotation layer on top**. It must work simultaneously as a slide hero image and as a documentation
figure.

**Fix these visual constants once — they must be identical across every vignette:**
- **Camera:** a single isometric/axonometric angle, held exactly the same for all eight vignettes. No perspective changes, no camera drift.
- **Lighting:** soft studio lighting, gentle contact shadows, neutral pale off-white background. No sky, no landscape, no environment context.
- **Materials:** realistic matte concrete, brushed metal, and frosted glass. Physically plausible, restrained.
- **Palette:** cool neutral greys and off-whites for all geometry, plus **exactly one accent colour — a warm amber-orange (#E8833A)**. The accent appears only on: the connector arrows between vignettes, the annotation leader-lines, the annotation card borders, and one small glowing highlight per vignette. It is never used decoratively anywhere else.
- **Annotations as physical set-dressing:** each label is a small white rectangular card with a thin amber border and small clean sans-serif text, standing in the 3D scene and joined to its element by a thin amber leader-line. They are physical objects inside the render, not flat overlay text.

**Layout:** eight vignettes in a **horizontal left-to-right sequence**, each on its own small floating
rectangular ground plane, linked by a thin amber connector arrow pointing rightward. One continuous
spine, no second row.

**Render these eight vignettes, in exactly this order. Do not reorder, merge, add, or omit any of them.**

1. **Inputs.** Two thin translucent glass data-slabs floating side by side above the ground plane, one showing a faint weather-timeseries curve, the other a faint building-footprint map.
   Card text: **"INPUTS"** · sub-text: **"EPW hourly weather + 01_buildings_clean.gpkg"** · second sub-line: **"Ta, RH, v10, DNI, DHI, GHI, IR_sky"**

2. **Raster domain.** A small city block extruded upward out of a fine raster grid, the grid cells visibly quantising the building bases — a digital surface model taking shape.
   Card text: **"domain.py"** · sub-text: **"DSM / DEM / CDSM / building mask / land-cover"**

3. **Sky view factor & shadows.** The same city block under a translucent hemispherical dome scored with radial azimuth lines, with sharp dark building shadows cast across the ground plane.
   Card text: **"svf.py + shadow.py"** · sub-text: **"sky view factor Ψsky + 32-azimuth horizon angles"** · second sub-line: **"per-hour building + vegetation shadow rasters"**

4. **Surface temperatures.** The same block with its ground plane and its wall faces tinted by a thermal gradient, warm on sunlit faces, cool in shade.
   Card text: **"surfaces.py"** · sub-text: **"ground temp T_grd, wall temp T_wall"**

5. **Mean radiant temperature.** A small stylised standing human figure at street level inside the block, enclosed in a translucent cube with six glowing amber arrows striking it from all six directions — up, down, and the four sides.
   Card text: **"mrt.py"** · sub-text: **"6-directional flux balance → Tmrt field"**

6. **Wind & air temperature.** The same block with smooth flowing streamline ribbons threading between the buildings, descending from a high reference marker down to pedestrian level.
   Card text: **"wind.py + airtemp.py"** · sub-text: **"v10 → v(1.1 m) pedestrian field"** · second sub-line: **"Ta field + UHI / anthropogenic offset"**

7. **UTCI kernel.** A precision-machined metal instrument block with four thin input pipes feeding into it, emitting a horizontal colour-graded strip below the block.
   Card text: **"utci.py"** · sub-text: **"Bröde 210-term polynomial → UTCI field"** · second sub-line: **"inputs: Ta, Tmrt, v, e"** · third sub-line: **"10-class official thermal-stress palette"**

8. **Outputs.** A neat stack of rendered map plates and a small chart plate on the ground plane, with one plate lifted and floating slightly above the others.
   Card text: **"exposure.py + raster_io.py"** · sub-text: **"PHEH / CTSI / parcel aggregation"** · second sub-line: **"GeoTIFF + COG + figures + 3D viewer"**

**Decision point — render as a physical object, not an abstract shape.** Between vignette 2 and
vignette 3, place a small upright **engraved frosted-acrylic diamond plaque** standing on its own
tiny plinth, lit from within by the amber accent.
Engraved text: **"height_m present?"** · smaller engraved sub-line: **"no → building excluded from DSM"**

**Caveat plaque — visually distinct, deliberately different material.** Along the bottom edge of the
image, spanning its full width, place a single low **matte dark-slate plaque** — clearly a different
material from the bright white annotation cards, and separated from the vignette row by a thin
horizontal divider line.
Engraved light-grey text, in three short lines:
**"KNOWN LIMITATION — E-UTCI-09"**
**"3 of 12 validated cells have height_m = NaN for 100% of buildings; a 4th at 84.5%"**
**"those cells compute as a flat open field (svf_mean = 1.0000), not an urban canyon"**

**Text fidelity — critical.** Reproduce every quoted string above **exactly as written**, including
lowercase module filenames with their `.py` extensions, the underscores, the arrows, and the Greek
letter Ψ. Do not paraphrase, translate, shorten, re-capitalise, or "tidy" any of them. This
illustration's value depends on the technical text surviving generation legibly and verbatim.

**Exclude:** no logos, no watermarks, no signatures, no people other than the single small figure in
vignette 5, no background landscape or sky, no decorative flourishes, no extra colours beyond the
stated palette, no additional labels beyond those specified.

**Orientation and legibility fallback:** the composition is **horizontal, one single row of eight
vignettes**, on a wide landscape canvas. If the content does not fit, **shrink the vignettes and the
card text rather than wrapping to a second row, reordering the vignettes, or dropping any annotation
card**. Legibility of the quoted text takes priority over rendering detail.
