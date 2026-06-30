# Graphical Abstract Prompt — Step 2.1: Classified Buildings → Climate Zone, State, and EPW Weather File

> **Slug:** `step-2-1-assign-ashrae-climate-zone-us-state-and-epw-weather-file-to-every-build` &nbsp;•&nbsp; **Companion to:** `DESIGN_step-2-1-assign-ashrae-climate-zone-us-state-and-epw-weather-file-to-every-build.md` &nbsp;•&nbsp; **Generated:** `2026-06-09` &nbsp;•&nbsp; **Revised:** `2026-06-10` (ASHRAE 169-2013 edition tag per OQ-1 resolution; downstream arrow added)

---

## Concept

The figure must communicate the *location-to-context* resolution that unblocks the whole pipeline: building footprints drop onto a county-coloured climate-zone map, each picks up its zone and state, and one weather file is pulled from the nearest station into the run directory. The single most important takeaway in 5 seconds: **every building learns its ASHRAE climate zone and US state from a county map, and the run gets exactly one validated EPW weather file — the two facts every later stage assumes.** The visual story is "pins on a zoned map, one weather file in the box."

## Suggested Structure

3-panel left-to-right horizontal flowchart, with a small "fallback chip" inset under Panel 2 (the nearest-fallback rule) and a resolution-chain strip under Panel 3 (the four EPW sources in priority order).

Reasoning: the step is two parallel resolutions (zone join; EPW fetch) converging on one appended-columns table, so two mid-panels feeding a single output panel reads naturally; the EPW priority chain is the one protocol-like element and earns the only strip.

## Key Elements to Show

- **Panel 1 — Input pins**: a small cluster of building-footprint polygons (8–10) with map pins at their representative points, captioned `02_buildings_classified.gpkg (N, 26)`; one pin highlighted with a tag `representative_point — always inside the footprint`.
- **Panel 2 — County climate-zone map** (climate_zone.py): a stylized US-northeast county patchwork (small caption `ASHRAE 169-2013 county assignments`) coloured in 4–5 zone bands with large zone labels `4A`, `5A`, `6A`; the pins from Panel 1 landing on one county; a callout chip on the matched county reading `5A · MA · FIPS 25025`; **inset chip below**: a small dashed-circle icon labelled `no match → nearest ≤ 5 km → HEURISTIC`, and a tiny stop-sign icon `no coverage ⇒ abort run`.
- **Panel 3 — Weather resolution** (epw_manager.py): a radio-tower icon labelled `WMO 725090 · Boston Logan` with a geodesic arc to the neighbourhood, distance tag `epw_distance_km`; a file icon `USA_MA_Boston-Logan...TMYx.epw` passing through a checklist gate (`LOCATION header ✓`, `8760 rows ✓`) into a folder icon `<output_dir>/weather/` ; **strip below**: four small source chips in priority order `user epw_dir → ~/.openubem cache → onebuilding.org → energyplus.net`, with a padlock chip `offline mode: cache only`.
- **Output block (right edge)**: a slim table icon `02a_buildings_climate.gpkg (N, 29)` with three highlighted new column chips `climate_zone · epw_path · provenance_climate_zone`, plus a second small table `02a_climate_epw.parquet` with a chip `state → Stage 5 eGRID`; exit arrow labelled "→ Step 2.2 enrichment".
- Key numbers: `26 → 29 columns`, `16-token zone vocabulary`, `1 EPW per run`, `≤ 5 km fallback`, `300 km far-station warn`.
- What to **NOT** show: archetype classification (Step 2); construction/loads tables (Step 2.2); IDF or simulation imagery (Steps 3–4); EUI choropleths (Step 5); any real meteorological plots — the EPW is a file artifact here, not data to visualize.

## Visual Metaphors

- **Pins on a zoned county patchwork** — the building inherits context from where it stands.
- A **geodesic arc** from radio tower to neighbourhood — "nearest station" made literal.
- A **checklist gate** in front of the run folder — only validated weather enters; the stop-sign abort encodes fail-loud.

## Style Guidance

- **Palette:** muted slate-blue for file icons and arrows; a 4-step warm-to-cool band palette (sand → amber → teal → steel-blue) reserved for the climate-zone counties; neutral grey for chips and labels; one red accent only on the abort stop-sign.
- **Typography:** clean technical sans-serif (Inter / IBM Plex / Helvetica). Labels are short tokens (`5A · MA`, `TMYx`, `≤ 5 km`) — never sentences.
- **Background:** clean white; the county map panel may sit on a very faint graticule.
- **Target width:** journal double-column (≤ 180 mm). 3 panels + 1 inset chip + 1 source strip; readable at quarter-page without zoom.
- **Density:** ≤ 7 visible top-level labels (one per panel, fallback chip, source strip, two output tables). All other detail lives in the figure caption.

## Generation Prompt

> Paste directly into Midjourney, DALL-E, or Ideogram.

```
Clean technical scientific diagram, three-panel horizontal flowchart on a white background, illustrating climate-zone and weather-file assignment in an urban building energy modeling pipeline. Panel 1 (left): a cluster of nine small building-footprint polygons with map pins at their centers, captioned "02_buildings_classified.gpkg (N, 26)", one pin tagged "representative_point — inside footprint". Panel 2 (center): a stylized county patchwork map with a small caption "ASHRAE 169-2013" colored in four climate-zone bands labelled "4A", "5A", "6A", the pins landing on one county with a callout chip "5A · MA · FIPS 25025"; below the map a small dashed-circle chip "no match → nearest ≤ 5 km → HEURISTIC" and a tiny stop-sign chip "no coverage ⇒ abort run". Panel 3 (right): a radio-tower icon labelled "WMO 725090 Boston Logan" with a curved geodesic arc to the neighbourhood and a distance tag "epw_distance_km"; a weather-file icon "USA_MA_Boston-Logan...TMYx.epw" passing through a checklist gate with ticks "LOCATION header ✓" and "8760 rows ✓" into a folder icon "<output_dir>/weather/"; beneath, four small source chips in order "user epw_dir → cache → onebuilding.org → energyplus.net" with a padlock chip "offline: cache only". Right edge: a slim output table icon "02a_buildings_climate.gpkg (N, 29)" with three highlighted column chips "climate_zone", "epw_path", "provenance_climate_zone", and a second small table icon "02a_climate_epw.parquet" with chip "state → Stage 5 eGRID", plus an exit arrow "→ Step 2.2 enrichment". Palette: muted slate-blue icons and arrows, sand-amber-teal-steel band colors confined to the county map, neutral grey chips, single red accent on the stop-sign. Typography: clean technical sans-serif (Inter or IBM Plex), short token labels, no sentences. Style: precise CAD-inspired technical illustration, vector-clean lines, no photorealism, no clutter, journal double-column width (180 mm). Publication quality.
```

## Alternative Prompt — schematic / technical variant

```
Schematic boxes-and-arrows diagram for a technical report figure, white background, three sequential modules left-to-right: [Module 02a: climate_zone.py — representative_point() per building, one vectorized UTM→EPSG:4326 reprojection, gpd.sjoin predicate='within' against bundled ashrae_climate_zones.gpkg (ASHRAE 169-2013 assignments, ~3,100 US county polygons carrying county_geoid, state_abbrev, climate_zone); unmatched points routed to sjoin_nearest ≤ 5 km in metric CRS with provenance HEURISTIC; zero coverage aborts the run; closed 16-token US zone vocabulary] arrow to [Module 02b: epw_manager.py — one station per run via pyproj.Geod geodesic argmin over bundled epw_stations.csv; resolution order user epw_dir → ~/.openubem/epw cache → climate.onebuilding.org → energyplus.net/weather; atomic .tmp → os.replace download; validation gate: LOCATION header parses, 8760 or 8784 data rows, header-to-index distance ≤ 10 km; epw_distance_km recorded, > 300 km warns epw_far_station; accepted file copied to <output_dir>/weather/] arrow to [Emit: append exactly three columns climate_zone, epw_path, provenance_climate_zone (26 → 29, upstream byte-identical) → 02a_buildings_climate.gpkg + 29-entry schema.json + sidecar 02a_climate_epw.parquet (N × 9) carrying state and county_geoid to the Stage 5 eGRID lookup]. Bottom annotation strip lists validation gates: 8/8 known-city zone fixture, nearest_fallback ≤ 1% on Boston 500 m, truncated-EPW fixture rejected, byte-identical re-run determinism. Monochrome blue-grey line art with one amber accent band on the climate-zone map module; clean technical sans-serif labels (Inter / IBM Plex); no shadows, no gradients, vector-precise; suitable for a methods-section figure of an energy-modeling journal article.
```
