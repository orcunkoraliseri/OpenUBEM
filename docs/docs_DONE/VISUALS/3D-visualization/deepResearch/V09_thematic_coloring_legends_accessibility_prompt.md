# Deep-Research Prompt V09 — THEMATIC COLORING, LEGENDS & ACCESSIBILITY (how the scene recolours by attribute)

> SCOPE GUARD — READ FIRST. This prompt owns the **coloring system** of the viewer: how the 3D scene is
> recoloured by an attribute, what colormap + classification each attribute *type* needs, how the legend is
> built, and how it stays colour-blind-safe and legible in light & dark. It is NOT about *which* outputs to
> show or how to fetch them onto surfaces (that is `V11`), NOT about the UI controls that trigger a recolour
> (that is `V10`), and NOT about the rendering library's styling API internals (that is `V06`). See
> `00_README_3dviz_prompt_set.md` for shared facts, roster, conventions. **Align with the repo `dataviz`
> skill and its `references/palette.md`** — this prompt should produce a coloring spec consistent with that
> design system, not a competing one.

> RESEARCH BUDGET — KEEP IT BOUNDED. Run this cheaply, in a SINGLE pass. Hard caps: **≤6 web searches and
> ≤10 page fetches, total.** After that pass, fill the required tables + Part C and STOP — do not iterate
> toward "comprehensive." Deliverable is the tables + Part C only: no preamble, no literature review beyond
> what the cells and synthesis need. Any cell you cannot fill within budget = mark it `GAP`; do not spend
> extra searches chasing one cell. **Do NOT spawn sub-agents or invoke skills to do this research** — run
> the searches yourself with plain web-search/fetch only; delegating to agents or skills multiplies token
> spend. If run by a Sonnet employee: model Sonnet, effort medium.

---

## What this document is

The coloring rulebook for the viewer. The user named three coloring modes: **function-based** (categorical
— DOE archetype / building use), **population-based** (sequential — a per-building count), and
**output-based** (the energy heat-map — EUI / demand / carbon, sequential or diverging). Each attribute
*type* demands a different colormap family, classification method, and legend. OpenUBEM today has only
**fixed per-category material colours** (wall/roof/floor/window) — no data-driven, no legend, no
accessibility story. This prompt establishes the field's conventions so the viewer's coloring is
defensible, readable, and honest about the data.

## Role

Geospatial thematic-cartography + data-visualization analyst. Ground colormap and classification choices in
recognized sources: **ColorBrewer** (Brewer/Harrower) for categorical/sequential/diverging schemes, the
**perceptually-uniform colormap literature** (viridis/cividis — Smith & van der Walt; cividis for CVD —
Nuñez et al.), **choropleth classification** methods (equal-interval, quantile, Jenks natural-breaks,
standard-deviation — Slocum et al., *Thematic Cartography*), and **accessibility** guidance (CVD-safe
palettes, WCAG contrast). Reconcile every recommendation with the repo's own `dataviz` skill /
`references/palette.md` so the viewer matches OpenUBEM's chart design language.

## Why this matters (so you scope correctly)

Coloring is where a UBEM viewer most easily **lies** — a rainbow colormap invents structure, a bad
classification hides the spread, a quantile map on carbon can make everything look average. The
faithful-to-model constraint applies to colour, not just geometry: the legend must let a user read the real
value, and imputed/low-confidence buildings must be distinguishable (ties to `V14`). This prompt keeps the
heat-map honest and readable.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Coloring recipe per attribute type

| Attribute (OpenUBEM field) | Data type | Recommended colormap family | Classification method | Legend type | Source |
|---|---|---|---|---|---|
| Function / archetype (DOE prototype name) | categorical (nominal) |  |  |  |  |
| Vintage / `year_built` | ordinal / interval |  |  |  |  |
| Population (per building) | sequential (count) |  |  |  |  |
| EUI (kWh/m²/yr) | sequential (ratio) |  |  |  |  |
| Energy end-use share / carbon | sequential or diverging |  |  |  |  |
| Deviation from a baseline (e.g. vs. median EUI) | diverging (has a meaningful midpoint) |  |  |  |  |
| Per-surface solar irradiance | sequential (continuous field) |  |  |  |  |

### Table 2 — Classification method fitness

| Classification method | What it's good for | Distortion risk | When to use in this viewer | Source |
|---|---|---|---|---|
| Equal-interval |  |  |  |  |
| Quantile |  |  |  |  |
| Jenks natural-breaks |  |  |  |  |
| Standard-deviation |  |  |  |  |
| Continuous (unclassed) ramp |  |  |  |  |

### Table 3 — Accessibility & legibility on 3D geometry

| Concern | Convention / rule | Source |
|---|---|---|
| Colour-blind safety (deuteranopia/protanopia/tritanopia) | (which colormap families are CVD-safe; how many categorical classes stay distinguishable) |  |
| Max distinguishable categorical classes (before needing patterns/labels) |  |  |
| Legibility on shaded 3D surfaces (colour shifts under lighting/ambient occlusion) |  |  |
| Light-mode vs dark-mode scene (does the palette hold on both backgrounds?) |  |  |
| Distinguishing "no data" / imputed / low-confidence buildings from real low values |  |  |
| Consistency with the repo `dataviz` palette (`references/palette.md`) |  |  |

### Table 4 — Legend & interaction

| Question | Answer + source |
|---|---|
| Continuous colour-bar vs classed swatches — when each, for a 3D scene? |  |
| Should the legend show the classification breaks + counts (histogram legend)? |  |
| How do peer UBEM viewers (ubem.io, CEA, Torino heat-map) present their energy legend? (cite `V02`) |  |
| How to keep colour comparable across buildings when the user switches attribute (fixed vs auto-rescaled domain)? |  |

---

## Part C — Synthesis (the coloring spec)

Give: (1) the **concrete coloring spec** OpenUBEM should encode — for each of the three user-named modes
(function/categorical, population/sequential, output/heat-map) the exact colormap family, default
classification, and legend type, expressed to be consistent with the repo `dataviz` system; (2) the
**default and the honest-alternative** for the energy heat-map (e.g. "sequential viridis, quantile default,
with an unclassed continuous option; diverging only when a meaningful baseline midpoint exists"); (3) an
explicit **accessibility rule** (CVD-safe families, max categorical classes, the no-data/imputed
treatment); (4) any **GAP — needs manager decision** (e.g. the population data source, the baseline for a
diverging map) with the closest defensible default.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C spec.
3. Cite ColorBrewer / the colormap literature / a cartography text / the `dataviz` skill for every
   colormap + classification claim.
4. **"Confidence and caveats":** which coloring choice is most a matter of taste vs. evidence.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Give a specific colormap family + classification for every attribute type in Table 1** — no "pick any
  sequential map."
- **Reconcile explicitly with the repo `dataviz` skill / `references/palette.md`** — the viewer must match
  OpenUBEM's chart design language, not introduce a rival palette.
- **Address CVD-safety and the no-data/imputed case** — coloring is subject to the faithful-to-model
  constraint (`V14`).
- **No fabricated precision;** flag GAPs (esp. the population source). **Stay on topic** — the *coloring +
  legend + accessibility* system only, not which outputs to fetch (`V11`) or the UI controls (`V10`).
