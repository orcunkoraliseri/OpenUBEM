# Deep-Research Prompt M07 — EXTERNAL-DATA FUSION for gap-filling (fetch the truth instead of guessing)

> SCOPE GUARD — READ FIRST. This is the **fetch-the-truth** alternative to statistical/ML imputation:
> when an OSM field is missing, is there an authoritative external dataset that simply *contains* the
> real value, joinable by geometry/location? Cover global building-footprint+attribute datasets,
> height-from-remote-sensing, national/municipal registries and assessor data, and imagery-derived
> attribute inference. Do NOT cover inferring a value from the building's own attributes or neighbours
> (that's `M03`–`M06`). The boundary: this prompt is about *joining to an external source of the actual
> value*; the others are about *inferring* it. See `00_README_imputation_prompt_set.md`.

---

## What this document is

A survey of external datasets that could replace an imputed guess with a measured value, plus their
coverage, licence, accuracy, and joinability to OSM footprints. A guessed floor count is a liability; a
LiDAR-derived height or a Google/Microsoft/EUBUCCO attribute join is ground truth. For an open-source
tool this is often the *highest-quality and most defensible* form of "imputation" — it is data
acquisition, not estimation, and sidesteps the zero-fitted-parameters question entirely. OpenUBEM already
fetches OSM footprints and EPW weather at runtime, so a fusion step is architecturally natural.

## Role

Geospatial data-sources research analyst. Catalogue authoritative, ideally-open datasets with
building-level attributes, prioritising global/US coverage (OpenUBEM's validation cities are US;
İşeri's case study is Turkey, so note ex-US coverage too). For each: what attribute it supplies, spatial
coverage, update cadence, licence, accuracy vs. ground truth, and how it joins to an OSM footprint.

## Why this matters (so you scope correctly)

Every gap fillable by a reliable external join is a gap OpenUBEM should *not* be statistically imputing.
The implementation plan needs a clear precedence rule — "join to authoritative source first, impute only
what remains" — and that requires knowing which sources are trustworthy and joinable at scale. This
prompt also surfaces licensing landmines (a dataset that can't ship in the pip wheel or be redistributed
changes the architecture) before the plan commits to them.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — External building-attribute datasets

| Dataset | Attribute(s) supplied (height, footprint, use, year) | Spatial coverage | Licence (redistributable? bundle-able?) | Reported accuracy vs. ground truth | Join key to OSM | Source |
|---|---|---|---|---|---|---|
| Microsoft Global Building Footprints |  |  |  |  |  |  |
| Google Open Buildings |  |  |  |  |  |  |
| Overture Maps buildings |  |  |  |  |  |  |
| EUBUCCO |  |  |  |  |  |  |
| GHSL (built-up / height) |  |  |  |  |  |  |
| National/municipal registry or assessor (name examples) |  |  |  |  |  |  |
| 3D city models (CityGML/CityJSON LoD1/2) |  |  |  |  |  |  |

### Table 2 — Height from remote sensing

| Source | Product (DSM/nDSM, LiDAR, radar, ML-from-imagery) | Resolution / vertical accuracy | Coverage | Licence | Source |
|---|---|---|---|---|---|
| National LiDAR (e.g. USGS 3DEP) |  |  |  |  |  |
| Global DSM (Copernicus/ALOS) |  |  |  |  |  |
| ML height-from-footprint / imagery |  |  |  |  |  |

### Table 3 — Imagery-derived attribute inference (use / stories / retrofit)

| Approach | Attribute inferred | Reported accuracy | Data + compute cost | Source |
|---|---|---|---|---|
| Street-view / façade classification |  |  |  |  |
| Satellite / aerial use classification |  |  |  |  |

### Table 4 — Fusion precedence & OpenUBEM fit

| OpenUBEM missing input | Best external source to join *before* imputing | Realistic fill rate from that join | Fallback if join misses (which imputation tier) | Source |
|---|---|---|---|---|
| `height` / `levels` |  |  |  |  |
| `year_built` |  |  |  |  |
| `use` / function |  |  |  |  |
| `footprint` completeness |  |  |  |  |

---

## Part C — Synthesis (the fusion-first recommendation)

Give: (1) a proposed **precedence rule** — the ordered list of external joins OpenUBEM should attempt
before falling back to statistical/ML imputation, per input; (2) the licence/architecture verdict —
which sources can be *bundled* (frozen in the wheel like existing `openubem/data/`), which must be
*runtime-fetched* (like OSM/EPW), and which are unusable for licensing reasons; (3) the accuracy case —
where an external join is clearly better than the best `M03`–`M06` guess, and where the external source
is *itself* so uncertain that imputation is comparable; (4) the ex-US coverage caveat (İşeri's Turkey
case) — which sources degrade outside the US and where imputation must carry more load.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C fusion-first recommendation.
3. Cite each dataset's official documentation/paper; state the licence exactly.
4. **"Confidence and caveats":** which accuracy figure is least independently verified.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **State licence and bundle-ability for every dataset** — this drives the architecture, not just
  accuracy.
- **Give the join key and realistic fill rate** — a source that can't be joined to an OSM footprint at
  scale is not usable.
- **Provide the fusion→imputation precedence rule** — the single most actionable output.
- **No fabricated precision;** flag GAPs. **Stay on topic** — external sources of the actual value only,
  not inference from the building's own attributes/neighbours.
