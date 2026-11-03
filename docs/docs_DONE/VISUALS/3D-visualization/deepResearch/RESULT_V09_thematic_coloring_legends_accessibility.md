# RESULT V09 — Thematic Coloring, Legends & Accessibility

*Executed as a bounded single-pass deep-research run. Budget used: **6 web searches, 3 page fetches**
(cap was ≤6 searches / ≤10 fetches). No sub-agents or skills were invoked for the research itself.*

**Note on the `dataviz` skill / `references/palette.md` requirement:** per instructions, I did not invoke
the `dataviz` skill. I searched the repository (`OpenUBEM/`) and the local Claude Code configuration
(`~/.claude/`, including `~/.claude/plugins/**/skills/`) for an on-disk `palette.md` or a `dataviz` skill
directory and found neither — the skill is listed as an available capability in this environment but its
`references/palette.md` is not present anywhere I could read as a plain file. **Marked `GAP`** in Table 3;
Part C uses the closest defensible default (ColorBrewer + viridis/cividis + Okabe-Ito) pending reconciliation
by whoever can actually invoke the skill and inspect its palette file.

---

## Table 1 — Coloring recipe per attribute type

| Attribute (OpenUBEM field) | Data type | Recommended colormap family | Classification method | Legend type | Source |
|---|---|---|---|---|---|
| Function / archetype (DOE prototype name) | categorical (nominal) | Qualitative palette — ColorBrewer "Set2"/"Paired" or, if colorblind-robustness must be guaranteed at up to 8 classes, the Okabe-Ito 8-color CUD set | None (one hue per distinct archetype; no binning) | Discrete swatch list, one swatch + label per archetype present in the current scene | Brewer & Harrower, *ColorBrewer.org* (2002); Okabe, M. & Ito, K., *Color Universal Design (CUD)* (2002, rev. 2008) |
| Vintage / `year_built` | ordinal / interval | Sequential single-hue, perceptually uniform (viridis, or a ColorBrewer sequential like "YlOrBr") | Manual/fixed breaks aligned to the DOE-prototype vintage bands the classifier already uses (reuse existing cut-points rather than inventing new ones) — equivalent to equal-interval only if those bands happen to be equal-width | Classed swatches (one per vintage band) with a continuous color-bar as an alternate view | Slocum, McMaster, Kessler & Howard, *Thematic Cartography and Geovisualization* (3rd ed., 2009) — ordinal-data classification guidance; Smith, N.J. & van der Walt, S., "A Better Default Colormap for Matplotlib" (SciPy 2015) for viridis |
| Population (per building) | sequential (count) | Sequential, single-hue (ColorBrewer "Blues"/"Greens") or viridis if consistency with the EUI ramp is preferred | Quantile (equal-count) default — building-count/population data is right-skewed (few very large buildings) and quantile prevents one outlier from washing out the rest; unclassed continuous as an exploratory alternate | Continuous color-bar (ratio data with a true zero) | Slocum et al. (2009) — quantile fitness for skewed data; ColorBrewer sequential family |
| EUI (kWh/m²/yr) | sequential (ratio) | Perceptually uniform sequential — **viridis default**, **cividis as the CVD-optimized alternate** | Quantile default (this is the prompt's own stated intended default), with an unclassed/continuous toggle for the "honest alternative" view | Continuous color-bar with quantile break ticks marked — this is the primary heat-map | Smith & van der Walt (2015); Nuñez, J.R., Anderton, C.R. & Renslow, R.S., "Optimizing colormaps with consideration for color vision deficiency...", *PLOS ONE* 13(7):e0199239 (2018) |
| Energy end-use share / carbon | sequential or diverging | Sequential — reuse the same perceptually-uniform family as EUI but a **visually distinct hue** (e.g. viridis for EUI, a warm sequential like ColorBrewer "OrRd"/plasma for carbon) so two simultaneously-relevant heat-maps are never confused | Equal-interval for bounded percentage shares (0–100%, roughly evenly distributed); quantile for unbounded carbon totals (kgCO2e/yr), matching the EUI logic | Continuous color-bar (share/ratio); optional classed swatches if end-use share is shown as a stacked/donut side panel rather than 3-D surface color | Slocum et al. (2009) — equal-interval fitness for bounded/evenly distributed data; ColorBrewer sequential family |
| Deviation from a baseline (e.g. vs. median EUI) | diverging (has a meaningful midpoint) | ColorBrewer diverging, CVD-safe pick — **"PRGn" or "PuOr"** (avoid "RdBu"/"RdGn" — red-green pairs are the one CVD failure mode diverging maps must dodge) | Standard-deviation classification, centered at zero/median, symmetric ±σ bins | Diverging color-bar with the baseline/zero point explicitly marked and labelled ("−2σ … 0 … +2σ") | Slocum et al. (2009) — standard-deviation classification for diverging data; Brewer & Harrower ColorBrewer colorblind-safe filter |
| Per-surface solar irradiance | sequential (continuous field) | Sequential perceptually-uniform continuous ramp — viridis, or plasma/inferno (same matplotlib perceptually-uniform family) for an intuitively "warm = high irradiance" read | Continuous/unclassed only — classing a dense per-vertex/per-texel field on curved or faceted 3-D geometry introduces visible banding artifacts | Continuous color-bar only, no discrete swatches | Smith & van der Walt (2015); general scientific-visualization convention for dense continuous scalar fields on 3-D surfaces (synthesis — no single dated source for the 3-D-specific banding claim, flagged in Confidence section) |

## Table 2 — Classification method fitness

| Classification method | What it's good for | Distortion risk | When to use in this viewer | Source |
|---|---|---|---|---|
| Equal-interval | Evenly-distributed, bounded data with intuitive round-number breaks (percentages, ratios with a known physical range) | If data is skewed, most features pile into one or two classes and the map looks flat | End-use share (%, bounded 0–100), and vintage bands if the DOE bands happen to be equal-width | Slocum et al. (2009); GISGeography, "Choropleth Maps – A Guide to Data Classification" |
| Quantile | Guarantees equal count per class — keeps every class visually represented regardless of skew | Can force dissimilar values into one class or split near-identical values across two classes; on carbon/EUI this is exactly the failure the prompt itself warns about ("a quantile map on carbon can make everything look average") | Default for population and EUI heat-maps, precisely because the building stock is heterogeneous (many small buildings + few large towers) | Slocum et al. (2009); GISGeography classification guide |
| Jenks natural-breaks | Data with genuine natural clusters/gaps (multi-modal distributions) — minimizes within-class variance, maximizes between-class variance | Breaks are recomputed from whatever dataset is loaded — adding one new city/cell shifts every break, breaking comparability across runs and violating OpenUBEM's reproducible-artifact goal unless the breaks are pinned/frozen | One-off exploratory analysis of a single neighbourhood/cell's EUI distribution to surface real "high-consumer" clusters — **not** the cross-city/cross-run default | Slocum et al. (2009); GISGeography classification guide |
| Standard-deviation | Diverging data centered on a mean/median — communicates "how many σ from typical" directly | Assumes roughly-normal distribution; a few extreme high-carbon buildings pile into the outer bins and the middle bins can be near-empty | Table 1's "deviation from baseline" row only | Slocum et al. (2009) |
| Continuous (unclassed) ramp | True gradient with no arbitrary bin edges — best for dense fields and for an "honest" exploratory view that doesn't hide the real spread | Harder to read an exact bucket for a building without a hover tooltip; less legible in a static screenshot/export than a classed map | Solar irradiance (always); the "honest alternative" toggle for EUI/carbon per this prompt's own Part-C requirement | Datawrapper, "When to use classed and when to use unclassed color scales" (blog, accessed 2026-07); Tobler, W.R. (1973) — first unclassed (grey-tone) map, cited via the missing-data cartography search |

## Table 3 — Accessibility & legibility on 3D geometry

| Concern | Convention / rule | Source |
|---|---|---|
| Colour-blind safety (deuteranopia/protanopia/tritanopia) | Use CVD-tested families only: viridis/cividis for sequential (cividis is *explicitly* optimized to look near-identical to CVD and non-CVD viewers), ColorBrewer's built-in "colorblind safe" filter for classed schemes, PRGn/PuOr (not RdBu/RdGn) for diverging, Okabe-Ito for categorical | Nuñez, Anderton & Renslow (2018); Brewer & Harrower ColorBrewer; Okabe & Ito (2002/2008) |
| Max distinguishable categorical classes (before needing patterns/labels) | ~8 with the Okabe-Ito set; general HCI/cartography consensus is that beyond 8 categories, colour alone stops being reliably distinguishable and needs supplementary labels/patterns/hover. A generic ColorBrewer "colorblind safe" qualitative scheme is more conservative (reported around 4 fully-safe classes in some renderings) | Okabe & Ito (2002/2008); secondary source: rgblind.com, "Color Blind Friendly Chart Colors & Palettes" (blog, lower-confidence, flagged) |
| Legibility on shaded 3D surfaces (colour shifts under lighting/ambient occlusion) | Data-driven colour should be applied as an **unlit/emissive or vertex-colour material**, not a physically-lit PBR material, so directional light and ambient occlusion don't shift the encoded hue/lightness away from the legend's true value — matches how glTF `EXT_mesh_features`/`EXT_structural_metadata` and 3D-Tiles styling pipelines typically separate "data colour" from "shading" | Synthesis from general 3D-Tiles/glTF styling practice (see `00_README` roster); **not independently verified with a dated citation within this budget — flag as GAP-adjacent, high confidence but uncited** |
| Light-mode vs dark-mode scene (does the palette hold on both backgrounds?) | Sequential/diverging ColorBrewer and viridis-family ramps sit in a mid-lightness band and are broadly background-agnostic, but their palest end (pale yellow in viridis, pale "Yl-" hues in ColorBrewer sequentials) washes out on a light/white background, and the palest end of a reversed ramp washes out on black — test both backgrounds explicitly, don't assume | GAP for a named source specific to 3-D/dark-mode; general inference from the colormap literature above |
| Distinguishing "no data" / imputed / low-confidence buildings from real low values | Reserve one **neutral light-grey** as the dedicated "no data" colour, kept clearly outside the active data ramp (never the palest end of the sequential scale, which could be misread as "low value"); for imputed-but-present values, layer a **pattern/hatch or outline treatment** on top of the true-value colour rather than substituting a flat grey, so imputed data stays visually distinguishable from missing data (ties to `V14`) | General cartographic convention (light grey for missing, found via search on choropleth missing-data handling); Tobler (1973) on hatching as the historical pattern-based alternative to colour |
| Consistency with the repo `dataviz` palette (`references/palette.md`) | **GAP** — could not locate this file or a `dataviz` skill directory anywhere on disk in this environment (repo search and `~/.claude` search both empty); did not invoke the skill per instructions. Closest defensible default: adopt the ColorBrewer + viridis/cividis + Okabe-Ito combination specified in Table 1 as a placeholder, and have whoever can invoke `dataviz` reconcile hex values against `references/palette.md` before implementation | GAP |

## Table 4 — Legend & interaction

| Question | Answer + source |
|---|---|
| Continuous colour-bar vs classed swatches — when each, for a 3D scene? | Classed swatches for categorical function/archetype and for the diverging baseline-deviation map (needs the zero point marked); continuous colour-bar for dense per-surface fields (solar irradiance); for the primary EUI/carbon heat-map, default to a small number of quantile classes (~5) with a toggle to continuous — Datawrapper's guidance is that classed maps have a "statistically significant advantage" for readers estimating a specific value, while unclassed maps better reveal outliers and general pattern. Source: Datawrapper, "When to use classed and when to use unclassed color scales." |
| Should the legend show the classification breaks + counts (histogram legend)? | Yes, recommended for the EUI/carbon/deviation heat-maps: a mini-histogram legend (bar height = building count in that bin, bar colour = the bin's map colour) lets the user see the palette **and** the underlying distribution's skew simultaneously — directly addresses this prompt's own risk statement ("a quantile map on carbon can make everything look average"). This is a synthesis recommendation grounded in general statistical-graphics/legend-design practice (Slocum et al., legend-design chapter) rather than a single dated citation for "histogram legend" specifically — flagged as synthesis, not a verified peer convention. |
| How do peer UBEM viewers (ubem.io, CEA, Torino heat-map) present their energy legend? (cite `V02`) | **GAP within this prompt's budget.** My one search targeting the Torino-3d-heat-mapping repo and ubem.io's legend/colormap specifics did not surface legend-UI details (ubem.io's public pages describe the framework, not its legend widget; the Torino repo did not appear in indexed results). This question is explicitly owned by `V02` (peer-tool teardown) — defer to that RESULT file as the source of record rather than re-researching it here. |
| How to keep colour comparable across buildings when the user switches attribute (fixed vs auto-rescaled domain)? | Recommend a **fixed/pinned domain per attribute type**, not a domain that silently re-normalizes to whatever subset is currently in view/filtered — colour must stay comparable across buildings and across camera moves, which is a direct consequence of the "faithful to the model" constraint (`V14`): a silently-rescaled colour changes what the same hue *means* without the user asking for it. Only rescale when the user explicitly changes the underlying dataset (e.g. switches city/cell), and always show the active domain (min/max or break values) in the legend so a rescale is never silent. This is Part-C-level synthesis from the two hard constraints in `00_README`, not a single named source. |

---

## Part C — Synthesis (the coloring spec)

**(1) The concrete coloring spec, per user-named mode:**

- **Function / categorical mode:** ColorBrewer qualitative palette (or the Okabe-Ito 8-colour CUD set when
  guaranteed CVD-safety at up to 8 classes matters more than palette familiarity), **no classification**
  (one hue per distinct DOE archetype), **discrete swatch-list legend** — one swatch + label per archetype
  actually present in the current scene (not the full possible roster, to avoid a legend longer than the
  building count justifies).
- **Population / sequential mode:** single-hue sequential (ColorBrewer "Blues" or viridis, for consistency
  with the output heat-map family), **quantile classification default** (population/building-count data is
  right-skewed), **continuous colour-bar legend** since it is ratio data with a true zero.
- **Output / heat-map mode (EUI, carbon, end-use share):** perceptually-uniform sequential — **viridis as
  the default, cividis as the CVD-optimized swap-in** — **quantile classification default with an unclassed
  continuous toggle** (the "honest alternative"), **continuous colour-bar legend with break ticks marked**,
  reserving **diverging (PRGn/PuOr, standard-deviation classed, zero marked)** exclusively for the case where
  a value has a real baseline/midpoint (deviation from median EUI), never for a plain magnitude.

**(2) Default and honest-alternative for the energy heat-map:** default = **sequential viridis, quantile
classification (~5 classes), with an unclassed continuous-ramp toggle** so a user can verify the classed view
isn't hiding real spread; **diverging only when a meaningful baseline midpoint exists** (e.g. vs. city median
EUI), using a CVD-safe diverging pair (PRGn/PuOr, not RdBu) with standard-deviation classing centered at zero.

**(3) Accessibility rule:** (a) every colormap family used must be CVD-tested — viridis/cividis for
sequential, PRGn/PuOr for diverging, Okabe-Ito (max 8) for categorical, with pattern/label fallback beyond 8
categories; (b) reserve one dedicated **neutral light-grey**, kept outside the active data ramp, for true
"no data," and a **pattern/hatch or outline overlay** (not a flat colour swap) for imputed/low-confidence
values so they never masquerade as a genuine low reading — this is the direct coloring-side implementation
of the faithful-to-model constraint and the `V14` provenance tie; (c) apply data colour as an
unlit/emissive/vertex-colour material so ambient occlusion and directional lighting on the 3-D scene do not
distort the encoded value away from what the legend promises.

**(4) GAP — needs manager decision:**
- **Population data source** — not resolved by this prompt (owned by `V05`); this prompt only fixes *how*
  population would be coloured once a source exists (sequential, quantile default).
- **The exact baseline for the diverging "deviation from median EUI" map** — city median? cell median?
  archetype-cohort median? Closest defensible default: **archetype-cohort median within the current scene**
  (comparing an office to the office median, not to a mixed-use citywide median), pending a manager decision.
- **The repo `dataviz` skill's `references/palette.md`** — not located on disk in this environment; this
  spec's hex/family choices (ColorBrewer + viridis/cividis + Okabe-Ito) are the closest defensible default
  and must be reconciled against the actual palette file by whoever can invoke the skill.
- **Exact count of DOE archetypes in the current OpenUBEM classifier roster** — needed to confirm whether the
  8-class Okabe-Ito ceiling is sufficient for the function/categorical legend or whether hue-family grouping
  (e.g. group by sector: commercial hues vs. residential hues) plus text labels is required from day one.

---

## Confidence and caveats

- **High confidence, well-sourced:** the three-family split (qualitative/sequential/diverging), viridis and
  cividis as the CVD-safe sequential choices, Okabe-Ito as the CVD-safe categorical ceiling, and the
  classification-method fitness table (equal-interval/quantile/Jenks/std-dev) — all trace to named,
  peer-reviewed or standard-reference sources (Brewer & Harrower; Smith & van der Walt; Nuñez et al.; Okabe
  & Ito; Slocum et al.).
- **Matter of taste, not evidence:** the specific choice of *which* ColorBrewer diverging pair (PRGn vs.
  PuOr), the exact quantile class count (5 is a common default, not a law), and whether end-use share should
  visually differ in hue from the EUI ramp — these are defensible design choices, not settled science.
- **Weakest citations in this RESULT:** the "3-D shaded-surface legibility" row (Table 3) and the
  "histogram legend" recommendation (Table 4) are synthesis from general 3-D-rendering and
  statistical-graphics practice, not a single dated, peer-reviewed source found within the search budget —
  flagged inline, treat as a reasonable default pending a deeper look if it becomes contentious.
- **Genuine GAP, not just under-cited:** the `dataviz` skill / `references/palette.md` reconciliation (could
  not be read as a file in this environment), the peer-viewer legend teardown (owned by `V02`, not
  re-researched here), and the population baseline/data-source questions (owned by `V05` / a manager
  decision).

---

## Reference list

1. Brewer, C.A. & Harrower, M. *ColorBrewer: Color Advice for Maps* (colorbrewer2.org). Also: Brewer, C.A.
   "ColorBrewer in Print: A Catalog of Color Schemes for Maps," *Cartography and Geographic Information
   Science*, 30(1), 2003. https://colorbrewer2.org/ ; https://www.tandfonline.com/doi/abs/10.1559/152304003100010929
2. Smith, N.J. & van der Walt, S. "A Better Default Colormap for Matplotlib" (viridis), SciPy 2015 /
   `matplotlib` project documentation. https://cran.r-project.org/web/packages/viridis/vignettes/intro-to-viridis.html
3. Nuñez, J.R., Anderton, C.R. & Renslow, R.S. "Optimizing colormaps with consideration for color vision
   deficiency to enable accurate interpretation of scientific data" (cividis), *PLOS ONE*, 13(7): e0199239,
   2018. https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0199239 ; preprint
   https://arxiv.org/abs/1712.01662
4. Okabe, M. & Ito, K. *Color Universal Design (CUD) — How to Make Figures and Presentations That Are
   Friendly to Colorblind People*, 2002 (revised 2008). https://jfly.uni-koeln.de/color/
5. Slocum, T.A., McMaster, R.B., Kessler, F.C. & Howard, H.H. *Thematic Cartography and Geovisualization*,
   3rd ed., Pearson Prentice Hall, 2009. (Classification-method fitness: equal-interval, quantile, Jenks
   natural-breaks, standard-deviation.)
6. GISGeography. "Choropleth Maps – A Guide to Data Classification." https://gisgeography.com/choropleth-maps-data-classification/
7. Datawrapper (Lisa Charlotte Muth / Datawrapper Blog). "When to use classed and when to use unclassed
   color scales." https://www.datawrapper.de/blog/classed-vs-unclassed-color-scales
8. Tobler, W.R. (1973), cited via search as the originator of the first unclassed (continuous grey-tone)
   choropleth map — used here for the classed-vs-unclassed and no-data/hatching discussion in Tables 2–3.
   (Secondary citation only; primary Tobler 1973 paper not directly fetched within budget.)
9. rgblind.com. "Color Blind Friendly Chart Colors & Palettes" (blog, 2026) — secondary/lower-confidence
   source for the "ColorBrewer colorblind-safe qualitative maxes around 4 classes" claim in Table 3.
   https://rgblind.com/blog/color-blindness-friendly-chart-colors
10. `00_README_3dviz_prompt_set.md` (this repo, `docs/docs_ACTIVE/3D/deepResearch/`) — OpenUBEM shared
    facts, roster, and the two hard constraints (faithful-to-model; reproducible/self-contained) that this
    RESULT's Part C synthesis is bound by.
11. `V09_thematic_coloring_legends_accessibility_prompt.md` (this repo) — the prompt executed.

*GAP items in this RESULT (repeated for visibility): the `dataviz` skill's `references/palette.md` (not
found on disk in this environment); peer-viewer legend teardown detail (deferred to `V02`); population data
source (deferred to `V05`); exact archetype-roster count for the categorical-legend ceiling check; the
diverging map's baseline choice (needs manager decision).*
