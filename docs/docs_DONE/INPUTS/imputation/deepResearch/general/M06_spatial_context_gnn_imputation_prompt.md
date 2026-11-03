# Deep-Research Prompt M06 — SPATIAL / URBAN-CONTEXT / GNN IMPUTATION (exploiting that neighbours correlate)

> SCOPE GUARD — READ FIRST. This is the **spatial-context tier** of the advanced-model track. Its
> distinguishing feature is the *information used*, not the model class: methods here exploit that
> buildings near each other share attributes (same block, parcel, era, use). Cover spatial
> autocorrelation / kriging, spatial-lag & geographically-weighted regression, neighbour-voting /
> dominant-context fill, and graph neural networks over building-adjacency graphs. Do NOT cover
> aspatial tabular methods (statistics `M03`, ML `M04`, neural `M05`) except to contrast; do NOT cover
> external-data joins (that's `M07`, fetching truth rather than inferring from neighbours). See
> `00_README_imputation_prompt_set.md`.

---

## What this document is

An appraisal of imputation methods that use OpenUBEM's *geography* — which every OpenUBEM building has,
for free, because footprints come with coordinates. A missing floor count in a block of otherwise-9-storey
apartments, or a missing use-type surrounded by retail, is far more predictable from spatial context than
from the building's own attributes. The manager needs to know whether the UBEM/GIS literature confirms
this signal is strong and stable enough to build on, and which method extracts it most defensibly.

## Role

Spatial-statistics / GIS-ML research analyst. Ground methods in their sources: spatial-statistics
canon (Tobler's first law; kriging; Anselin on spatial regression; geographically-weighted regression),
GNN literature applied to urban/building graphs, and any UBEM/urban-morphology study that imputes
building attributes from spatial context or block/parcel homogeneity (the İşeri paper and the
building-stock-characterization literature it cites are relevant).

## Why this matters (so you scope correctly)

Spatial context is OpenUBEM's cheapest strong predictor — it needs no external join and no extra data,
only the coordinates already present. If the literature shows neighbour-based fills materially beat
aspatial imputation for height/use/vintage (the plausible expectation), a spatial method may be the
single highest-value addition regardless of which aspatial tier it sits beside. But spatial methods have
their own failure mode — heterogeneous blocks, edges of the study area, and MNAR clustering (a whole
informal district missing `year_built` together) — that the manager must weigh.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Spatial-context imputer catalogue

| Method | What spatial structure it uses (distance, adjacency, block/parcel, network) | Best-suited OpenUBEM input(s) | Handles heterogeneous neighbourhoods / edges? | Reference impl | Source |
|---|---|---|---|---|---|
| Spatial autocorrelation / kriging |  | height, continuous |  | `pykrige`, `gstat` |  |
| Spatial-lag / GWR regression |  | continuous |  | `spreg`, `mgwr` |  |
| Neighbour-voting / dominant-context fill |  | use, vintage (categorical) |  | (custom / `libpysal`) |  |
| Graph neural network (adjacency graph) |  | mixed |  | `pytorch-geometric` |  |

### Table 2 — Evidence the spatial signal is real for building attributes

| Study | Attribute | Strength of spatial signal reported (e.g. Moran's I, neighbour-fill accuracy) | Where it broke down (heterogeneity, edges) | Source |
|---|---|---|---|---|
|  |  |  |  |  |

### Table 3 — Spatial vs. aspatial head-to-head

| Study | Attribute | Spatial method vs. aspatial baseline result | Net verdict | Source |
|---|---|---|---|---|
|  |  |  |  |  |

### Table 4 — Constraint & operability fit

| Method | Complexity vs. payoff (needs a graph build? tuning?) | Zero-fitted-params posture | Provenance/confidence story (e.g. neighbour-agreement as confidence) | MNAR-clustering risk (whole district missing together) | Verdict | Source |
|---|---|---|---|---|---|---|
| Kriging |  |  |  |  |  |  |
| Spatial regression / GWR |  |  |  |  |  |  |
| Neighbour-voting |  |  |  |  |  |  |
| GNN |  |  |  |  |  |  |

---

## Part C — Synthesis (spatial verdict)

Give: (1) whether the spatial signal is strong enough that a **neighbour-based fill should be a first-
class part of OpenUBEM's imputer** rather than an afterthought — and for which inputs specifically;
(2) the simplest method that captures most of the payoff (the İşeri paper favours simplicity; is a GNN
ever worth it over neighbour-voting/kriging for this data?); (3) how spatial context should *combine*
with the aspatial tiers — as a standalone imputer, a feature fed into `M04`/`M05`, or a confidence
booster; (4) the explicit MNAR-clustering caveat: when spatial fill is *dangerous* (whole
block/district missing the same field for a shared reason) and how to detect it.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C spatial verdict.
3. Cite the spatial-statistics source and, separately, any building-attribute application.
4. **"Confidence and caveats":** where spatial homogeneity is weakest (mixed-use dense cores).
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Judge "simple neighbour-fill vs. GNN" explicitly** — do not assume the fancier method wins on this
  data scale.
- **Address the MNAR-clustering failure mode** — spatial fill's signature risk.
- **Give a "how it combines with aspatial tiers" recommendation** — spatial context rarely stands alone.
- **No fabricated precision;** flag GAPs. **Stay on topic** — spatial-context inference only, not
  external-data joins (`M07`).
