# I02 — Candidate external height data source survey

Desk research only (`WebSearch`/`WebFetch` against public documentation/catalog pages). No dataset
downloaded, no API called, no code written. Findings are cited per-claim to the page read.

## Target tracts (from `scripts/validation/v12_cell_pipeline.py::CELL_CONFIGS`, lines 45-106)

| cell | lat | lon | radius_m | state | `height_m` NaN (I01) | Geographic location (from coordinates) |
|---|---|---|---|---|---|---|
| `nyc_suburban` | 40.7052 | -73.5985 | 500 | NY | 100.0% (1589/1589) | **Not inside NYC's five boroughs** — this point sits east of Queens' eastern edge (~‑73.70°), i.e. in Suffolk County, Long Island (West Islip/Bay Shore area) |
| `nyc_rural` | 42.0396 | -74.1143 | 1000 | NY | 100.0% (198/198) | **Far outside NYC** — ~130 km north of the five boroughs, in the Catskills/Delaware County area |
| `austin_rural` | 30.5788 | -98.2700 | 1000 | TX | 100.0% (245/245) | Texas Hill Country west of Austin (Burnet/Blanco County area, near Marble Falls/Spicewood), well outside Austin city limits |
| `austin_centre` | 30.2672 | -97.7431 | 500 | TX | 84.5% (349/413) | Downtown Austin (Texas State Capitol coordinates) — inside Austin city limits |

**This geographic fact is load-bearing for the whole survey**: two of the four tracts are named
`nyc_*` for case-study/cluster-taxonomy reasons (Stage-6 UTCI arc naming), not because they are
administratively inside New York City. Any candidate scoped to "NYC" or "City of Austin" open-data
portals only covers the tracts that are *actually* inside those municipal boundaries — `austin_centre`
qualifies, `nyc_suburban`/`nyc_rural`/`austin_rural` do not.

## Findings table

| dataset | covers which of the 4 tracts | resolution / height semantics | license | access | integration effort | key caveat |
|---|---|---|---|---|---|---|
| **USGS 3DEP** (LiDAR point cloud + derived DEMs) | Nominally all 4 (99% of the U.S. has baseline 3DEP data available-or-in-progress as of end of FY25); **exact QL/vintage at these 4 specific points not confirmed** — would require querying the live LidarExplorer/National Map coverage index, which this task does not do | Raw point cloud (LAZ), QL2-or-better under current baseline spec; height is *not* a direct product — building height requires classifying first/last returns and differencing a DSM against a bare-earth DTM | U.S. Government Public Domain (USGS terms of use) | Bulk download only: AWS S3 `usgs-lidar-public` (free, Entwine Point Tiles) or `usgs-lidar` (Requester Pays, raw LAZ, "not a complete 3DEP mirror") | **New ingestion module** — point-cloud classification + DSM/DTM differencing + footprint join is a non-trivial new processing pipeline, not a one-off script | 8-year-old-or-newer baseline spec means vintage varies tile-to-tile; national coverage stat is a *availability* claim, not proof these 4 specific rural/suburban points have processed, downloadable QL2 data today |
| **NYC Open Data — Building Footprints** (`HEIGHT_ROOF`/`GROUND_ELEVATION` fields) | **None of the 4** — dataset scope is the five NYC boroughs only; `nyc_suburban` and `nyc_rural` are geographically outside that boundary (see table above) despite the cell name | Per-building `HEIGHT_ROOF` field, sourced from a mix of as-built DOB plan drawings, EagleView oblique imagery measurement, and Cyclomedia street-level imagery (for structures <60 ft) — a genuine roof-height-above-ground field, not a raster/DSM proxy | NYC Open Data terms (`opendata.cityofnewyork.us`) — permissive, open-source compatible | REST API, NYC Open Data portal (shapefile/GeoJSON, EPSG:4326), or NYCMapHub bulk download; updates weekly | Would be a **one-off enrichment script** (spatial join) *if* it covered the target tracts — it does not | High-quality per-building field, but geographically irrelevant to all 4 gap tracts as scoped |
| **NYS Building Footprints** (statewide, `data.gis.ny.gov`) | Geographically covers `nyc_suburban` (Long Island) and `nyc_rural` (Catskills) — statewide dataset | Aggregates footprints from four source feeds: Microsoft ML footprints, NYC Open Data, NYSERDA, and NYS Geospatial Services; **whether a populated height field survives into the merged statewide layer outside the NYC-sourced portion is not established from the documentation read** | Presumed NY State open-data terms (not separately confirmed) | NYS GIS Clearinghouse (`data.gis.ny.gov`), map/dataset download | Cannot rank confidently — **needs direct field-level inspection of a downloaded sample before ruling in or out** (out of scope for this desk-research task) | Flagged, not resolved: this is the one candidate where "does it actually have height for these two tracts" could not be answered from documentation alone |
| **City of Austin Open Data — Building Footprints (2013)** | Geographically covers `austin_centre` only (inside city limits); does **not** cover `austin_rural` (outside city limits, unincorporated Hill Country) | 2D footprint geometry only — no height attribute in the schema. Footprints were digitized from 2012/2013 orthoimagery, with 2012 LiDAR used only where imagery was unavailable (i.e. LiDAR was an input to footprint *tracing*, not a carried-through height value) | City of Austin Open Data terms | REST API / bulk download, `data.austintexas.gov` | **Not feasible as a height source** — no height field exists in this layer at all, regardless of geographic coverage | Even where it geographically applies (`austin_centre`), this dataset cannot plug the gap; it is a footprint-only layer |
| **TNRIS / Texas StratMap LiDAR** (Texas Natural Resources Information System, TxGIO) | Both Texas tracts — TxGIO states LiDAR now covers the entire state of Texas | Raw LiDAR point cloud (LAS/LAZ) plus derived bare-earth DEM products; per-building height again requires a DSM (first-return surface) minus bare-earth DTM workflow, then a footprint join — not a direct output | Public domain / free (final deliverables placed in the public domain per TNRIS) | Free bulk download via the TNRIS DataHub (`data.tnris.org`), discoverable per-project via the "Lidar Selector" index tool; no API, no account required for download itself | **New ingestion module** (same class of effort as 3DEP: point-cloud processing pipeline), not a one-off script | Statewide "full coverage" claim read from the TNRIS landing page did not resolve to project-level vintage/QL for the specific `austin_rural`/`austin_centre` coordinates — that would require using the Lidar Selector index interactively, not done here |
| **Microsoft Global ML Building Footprints** (height estimates) | Nominally all 4 (nationwide U.S. coverage, independent of municipal boundaries) — but height *estimates* are a named subset ("tens of millions" of height estimates out of ~1.4B total footprints, with continuing additions, e.g. +1.2M height estimates from Vexcel imagery added Feb 2026 for the U.S.), so per-tract height-attribute presence is not guaranteed even though footprint presence likely is | Per-building polygon with an ML-estimated height attribute derived from satellite/aerial imagery (Bing/Maxar/Airbus/IGN/Vexcel) — a modeled estimate, not a direct survey measurement; no stated systematic accuracy figure in what was read | **CDLA Permissive 2.0** — clearly open-source compatible | Bulk download only (no API): country/quadkey-partitioned `.csv.gz` files (line-delimited GeoJSON despite the extension) linked from a central `dataset-links.csv` on Microsoft's Azure storage, or via Microsoft Planetary Computer | **One-off enrichment script**: download the relevant quadkey tile(s) for each tract's bounding box, spatial-join MS footprint polygons to the platform's existing OSM footprints (geometry overlap, not shared IDs), carry over height where present | Coverage is nationwide by construction (not tied to any city/county boundary), which is the main reason this is the most broadly promising candidate for exactly this kind of "OSM gap in specific tracts" problem — but the height *sub*-layer's actual density at these 4 specific points is unverified without downloading (forbidden here) |
| **GHS-BUILT-H** (JRC Global Human Settlement Layer, R2023A) | All 4 trivially (global raster grid, no municipal-boundary dependency) | 100 m grid cells, two layers: Average Net Building Height (ANBH) and Average Gross Building Height (AGBH) — **a neighbourhood-average, not a per-building value**; 2018 epoch, derived from AW3D30/SRTM30 DSMs filtered against Sentinel-2 composite | Free/open, JRC European Commission, attribution requested | Direct raster download (GeoTIFF) from the GHSL data page, or via Earth Engine / awesome-gee-community-catalog mirrors | **One-off enrichment script** (raster sample at cell/tract centroid) if used as a *regional statistical fallback* rather than a per-building fix — this maps directly onto I04 candidate (c), not candidate (b) | 100 m resolution is coarser than a typical building footprint (all 4 tracts' footprint areas run tens to low-thousands of m² per building per I01) — usable only as an area-level prior, not a per-building height assignment |
| **Copernicus DEM GLO-30** | All 4 trivially (global, free-license instance) | 30 m Digital *Surface* Model (buildings/vegetation included, from TanDEM-X 2011-2015 radar) — again a coarse raster, and it is a DSM with **no bundled bare-earth DTM**, so a second elevation product would be needed just to derive a height-above-ground value | Free for general public under the Copernicus DEM license (per the published license PDF) | Copernicus Browser / API, or AWS Registry of Open Data mirror, or OpenTopography | **Not feasible** at building-footprint granularity for this platform's use case | 30 m pixels are frequently larger than a single building footprint in these tracts (I01 footprint-area minimums are ~20-35 m²) — same class of problem as GHS-BUILT-H but without even a purpose-built "building height" semantic |
| **Google Open Buildings 2.5D Temporal** | **None** | 4 m effective resolution, per-building-ish height with a stated ~1.5 m mean absolute error (Google's own research blog) | Documented as open on the project page (not independently re-verified here since it's inapplicable) | GEE catalog / HDX bulk download | **Not feasible — out of scope entirely** | Explicitly does not cover the USA; its stated coverage is Africa, South Asia, South-East Asia, and Latin America/Caribbean only |
| **ALOS World 3D (AW3D30)** — noted in passing, one of GHS-BUILT-H's own DSM inputs | All 4 trivially (global) | 30 m DSM (JAXA), same class of product as Copernicus DEM GLO-30 | Free, but requires user registration via JAXA's G-Portal | Registration-gated bulk download | **Not feasible** at building granularity, same reasoning as GLO-30 | Could not be assessed beyond its documented existence without creating an account — flagged per the "no account/paid access" rule rather than guessed at |

## Per-candidate notes and documentation read

**USGS 3DEP.** Read: `https://registry.opendata.aws/usgs-lidar/` (license, S3 bucket structure, "not a
complete 3DEP mirror" caveat); `https://www.usgs.gov/faqs/what-coverage-3d-elevation-program-3dep-dems`
and search-result summaries of `https://www.usgs.gov/3d-elevation-program/what-3dep` and the FY25/FY26
3DEP status-map announcement pages (99%-of-Nation baseline-or-in-progress claim, QL2-or-better/8-years-
or-newer baseline spec definition). Did not query the live LidarExplorer/National Map interactive
coverage index for the 4 specific coordinate pairs — that would be closer to a live geodata query than
reading a documentation page, and was treated as out of scope for a desk-research task.

**NYC Open Data Building Footprints.** Read:
`https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_BuildingFootprints.md`
(field definitions for `HEIGHT_ROOF`/`GROUND_ELEVATION`, source provenance, access channels, update
cadence).

**NYS Building Footprints.** Read search-result summaries only (no single metadata page fetched in
full) of `https://data.gis.ny.gov/maps/a6bbc64e38f04c1c9dfa3c2399f536c4` and
`https://data.gis.ny.gov/datasets/sharegisny::nys-building-footprints-2/about` (four-source aggregation
claim: Microsoft, NYC Open Data, NYSERDA, NYS Geospatial Services). Field-level height-attribute
completeness for the non-NYC portion of the state was not confirmed and is explicitly flagged as
unresolved above.

**City of Austin Building Footprints (2013).** Read search-result summary of
`https://data.austintexas.gov/Locations-and-Maps/Building-Footprints-2013/7bns-7teg/about` (digitizing
method: 2012/2013 orthoimagery, with 2012 LiDAR used only where imagery was unavailable; no height
field mentioned in the schema description).

**TNRIS / Texas StratMap LiDAR.** Read: `https://tnris.org/stratmap/elevation-lidar` directly (full-page
fetch: statewide coverage claim, point-cloud vs. bare-earth-DEM product distinction, free DataHub
download + Lidar Selector index tool, Research and Distribution Center for physical copies). Also saw,
but did not fetch in full, `https://cdn.tnris.org/documents/state_of_texas_stratmap_lidar_specification_ver_XIII.pdf`.

**Microsoft Global ML Building Footprints.** Read:
`https://github.com/microsoft/GlobalMLBuildingFootprints/blob/main/README.md` directly (CDLA Permissive
2.0 license, ~1.4B footprints / ~174M with height attributes, US/Western-Europe/Australia/Turkey height
coverage, `.csv.gz`-named line-delimited GeoJSON format, `dataset-links.csv` + quadkey partitioning,
Planetary Computer alternative access). Also saw, but did not fetch in full,
`https://tech.marksblogg.com/ms-buildings-2026.html` (Feb 2026 update: +1.2M footprints / +1.2M height
estimates from Vexcel imagery, U.S.-only contribution).

**GHS-BUILT-H.** Read search-result summaries of `https://human-settlement.emergency.copernicus.eu/ghs_buH2023.php`
and `https://human-settlement.emergency.copernicus.eu/datasets.php` (100 m grid, ANBH/AGBH layers, 2018
epoch, AW3D30/SRTM30/Sentinel-2-composite derivation, JRC European Commission open/free license with
attribution).

**Copernicus DEM GLO-30.** Read search-result summaries of
`https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM`,
`https://portal.opentopography.org/raster?opentopoID=OTSDEM.032021.4326.3`, and the license PDF at
`https://docs.sentinel-hub.com/api/latest/static/files/data/dem/resources/license/License-COPDEM-30.pdf`
(free-for-general-public license terms, 30 m/1 arc-second resolution, TanDEM-X 2011-2015 source, DSM —
not bare-earth — semantics).

**Google Open Buildings 2.5D Temporal.** Read search-result summaries of
`https://sites.research.google/gr/open-buildings/temporal/` and
`https://research.google/blog/open-buildings-25d-temporal-dataset-tracks-building-changes-across-the-global-south/`
(4 m effective resolution, ~1.5 m MAE height accuracy claim, explicit Africa/South-Asia/South-East-Asia/
Latin-America-and-Caribbean-only coverage — USA not included).

**ALOS World 3D (AW3D30).** Identified only as a component input cited in the GHS-BUILT-H search
results; not independently fetched. Flagged as requiring JAXA G-Portal account registration, which is
exactly the "cannot be assessed without an account" case the plan asks to state plainly rather than
guess at.

## Which candidate(s) look most viable, and why

**Microsoft Global ML Building Footprints** is the strongest single candidate for all 4 tracts
specifically *because* its coverage is nationwide-by-construction and independent of any municipal
open-data boundary — unlike the NYC/Austin city portals, it does not care that `nyc_suburban`,
`nyc_rural`, and `austin_rural` sit outside their respective cities' administrative footprints. Its
license (CDLA Permissive 2.0) is unambiguously open-source compatible, and access is a plain bulk
download with no account gate. The main open question — how much of the height *sub*-layer (not just
footprint presence) actually lands inside these 4 specific bounding boxes — could not be resolved
without downloading a tile, which this task is barred from doing; that is the natural first check for
whichever future plan picks this candidate up.

**USGS 3DEP and TNRIS StratMap** (the LiDAR-first-principles route) are the most rigorous in principle
— actual measured surface data, both nationally/statewide "fully" flown per their own landing-page
claims — but both require a materially heavier integration effort (a new point-cloud-processing
ingestion module: classify returns, build a DSM, difference against a DTM, join to footprints) versus
Microsoft's already-tabular per-building estimate. They are a plausible *second-choice* or
cross-validation source, not the first thing to reach for given the effort delta.

**GHS-BUILT-H** is a credible fallback specifically for I04's "regional/cell-level statistical fallback"
option (candidate (c) in the plan's I04 framing) rather than a real fix for individual buildings — its
100 m grid is coarser than most footprints in these tracts, so it would smear a single averaged height
across many buildings, not assign per-building values.

## What could not be assessed, and why

- **NYS Building Footprints' actual height-field completeness outside the NYC-sourced portion** — the
  documentation read confirms the dataset aggregates four source feeds including Microsoft (which does
  carry height) but does not state, at the field/schema level, whether a usable height value survives
  into the merged layer for Long Island (`nyc_suburban`) or the Catskills (`nyc_rural`) specifically.
  This would need a downloaded sample to confirm, which is out of scope here.
- **USGS 3DEP and TNRIS StratMap's exact QL/vintage at the 4 specific coordinate pairs** — both sources'
  landing pages make nationwide/statewide "fully covered" claims, but resolving that to a specific
  point requires querying the live interactive coverage-index tools (LidarExplorer / National Map /
  Lidar Selector), which was treated as beyond "reading a documentation page" and was not done.
- **ALOS World 3D (AW3D30)** — requires a JAXA G-Portal account to access; per the plan's instruction,
  this is stated plainly as unassessed rather than guessed at.
- **Google Open Buildings 2.5D Temporal** was assessed only far enough to establish it excludes the USA
  entirely — no further depth was needed once that was confirmed.
