# Graphical Abstract Prompt — Step 5: EnergyPlus Work Directories → EUI / GWP / IOD Results GeoDataFrame

> **Slug:** `step-5-parse-energyplus-outputs-into-eui-gwp-iod-and-aggregate-results-back-to-th` &nbsp;•&nbsp; **Companion to:** `DESIGN_step-5-parse-energyplus-outputs-into-eui-gwp-iod-and-aggregate-results-back-to-th.md` &nbsp;•&nbsp; **Generated:** `2026-06-09`

---

## Concept

The figure must communicate the convergence that closes the pipeline: thousands of per-building SQL files are parsed, distilled into three metric families (EUI, GWP, IOD), and re-attached to the city map they came from. The single most important takeaway in 5 seconds: **raw simulation databases become a coloured building-level energy map — every building gets five EUI values, five GWP values, and an overheating index, and buildings that failed remain visible as grey, never deleted.** The visual story is "from file forest back to the map."

## Suggested Structure

4-panel left-to-right horizontal flowchart, with a small "convention chip" inset under Panel 3 (the GWP factor logic) and a metric-legend strip under Panel 4.

Reasoning: the pipeline is a funnel (many files → one table → one map), so the panels should physically narrow left-to-right and then bloom into the choropleth; the GWP factor routing (gas vs electricity) is the one non-obvious computation and earns the only inset.

## Key Elements to Show

- **Panel 1 — Input file forest**: a grid of small database-file icons labelled `eplusout.sql` (5–6 visible, ellipsis implies hundreds), each tagged with a tiny folder caption `results/<osm_id>/`, plus one table icon `04_simulation_manifest.parquet` with a filter chip `status ∈ {success, success_cached}`. One file icon greyed with a chip `failed → NaN, kept`.
- **Panel 2 — Parse & distil** (Module 13): a funnel shape receiving the SQL icons; inside the funnel three stacked operation labels: `sqlite3 bulk query (ReportData × Time)`, `J → kWh once`, `zone regex {osm_id}_F{n}_{label}`. Output: a small tidy table sketch with row chips `heating · cooling · lighting · equipment · total EUI` and `IOD (occupied summer hours)`.
- **Panel 3 — Carbon attribution** (Module 15): two parallel factor arrows entering the metric table: an orange arrow labelled `heating × 0.181 kg CO₂e/kWh (natural gas)` and a blue arrow labelled `cooling + lighting + equipment × eGRID 2022 (state → subregion)`. **Inset chip below**: a small tag icon reading `convention: load_referenced_v1` — visually styled like a version badge.
- **Panel 4 — Back to the map** (Modules 14 + 16): a building-footprint choropleth (10–15 small polygons in a street-grid arrangement) coloured on a yellow→red ramp labelled `total EUI kWh/m²·yr`, with 2 polygons hatched grey and a mini-legend entry `failed (kept, NaN)`. Beside it, three small export-file icons: `05_results.gpkg (UTM · canonical)`, `.geojson (EPSG:4326)`, `.csv`, and a small JSON icon `neighbourhood_summary` with the chip `pct_floor_area_simulated`.
- **Flow arrows** between panels labelled with the module decomposition: `Module 13 (parser)` → `Module 15 (carbon)` → `Module 14 (aggregator)` → `Module 16 (figures)`.
- **Bottom strip — validation gates**: 4 small chips: `CV(RMSE) < 30%`, `NMBE ±10%`, `R² > 0.6`, `KS D < 0.10 — vs CBECS 2018`.
- Key numbers: `70-column GeoDataFrame (57 + 13)`, `J→kWh once`, `Tcomf = 0.31·Tave + 20.3`, `8760 h`.
- What to **NOT** show: EnergyPlus solver internals or the simulation stage (Step 4 territory); zoning/geometry diagrams (Step 3); imputation/classification (Step 2); detailed SQL schema tables; matplotlib figure thumbnails (the choropleth in Panel 4 already stands for them).

## Visual Metaphors

- A **funnel** narrowing from a forest of identical database files into one tidy table — parsing as distillation.
- **Two coloured factor arrows** (orange gas / blue grid electricity) merging into the table — per-end-use carbon attribution at a glance.
- The **choropleth bloom** at the end — the entire pipeline's purpose realized: data returns to the map it came from, and grey hatched buildings encode scientific honesty (flag-don't-drop).

## Style Guidance

- **Palette:** muted slate-blue for file icons and arrows; warm orange reserved for the natural-gas factor arrow and the EUI hot end of the choropleth ramp; cool blue for the electricity factor arrow; yellow→red sequential ramp inside the choropleth only; neutral grey for failed buildings and module labels.
- **Typography:** clean technical sans-serif (Inter / IBM Plex / Helvetica). Labels are short tokens (`J→kWh`, `eGRID 2022`, `load_referenced_v1`) — never sentences.
- **Background:** clean white. The choropleth panel may sit on a very faint street-grid texture.
- **Target width:** journal double-column (≤ 180 mm). 4 panels + 1 inset chip + 1 legend strip; readable at quarter-page without zoom.
- **Density:** ≤ 7 visible top-level labels (one per panel, convention chip, validation strip). All other detail lives in the figure caption.

## Generation Prompt

> Paste directly into Midjourney, DALL-E, or Ideogram.

```
Clean technical scientific diagram, four-panel horizontal flowchart on a white background, illustrating the results-aggregation stage of an urban building energy modeling pipeline. Panel 1 (left): a grid of six small database-file icons labelled "eplusout.sql" each with a tiny folder caption "results/<osm_id>/", one icon greyed out with a chip "failed → NaN, kept", beside a table icon "04_simulation_manifest.parquet" with a filter chip "status ∈ success". Panel 2: a large funnel receiving the file icons, containing three stacked operation labels "sqlite3 bulk query", "J → kWh once", "zone regex {osm_id}_F{n}_{label}", emitting a small tidy metrics table with row chips "heating · cooling · lighting · equipment · total EUI" and "IOD". Panel 3: two factor arrows entering the metrics table — a warm-orange arrow labelled "heating × 0.181 kg CO2e/kWh natural gas" and a cool-blue arrow labelled "cooling + lighting + equipment × eGRID 2022 electricity"; below, a small version-badge chip reading "convention: load_referenced_v1". Panel 4 (right): a building-footprint choropleth map of about twelve small street-grid polygons coloured on a yellow-to-red ramp labelled "total EUI kWh/m²·yr", two polygons hatched grey with legend "failed (kept, NaN)"; beside the map three export-file icons "05_results.gpkg UTM canonical", ".geojson EPSG:4326", ".csv" and a small JSON icon "neighbourhood_summary · pct_floor_area_simulated". Slate-blue arrows between panels carry module labels "Module 13 parser → Module 15 carbon → Module 14 aggregator → Module 16 figures". Bottom strip of four small grey chips: "CV(RMSE) < 30%", "NMBE ±10%", "R² > 0.6", "KS D < 0.10 vs CBECS 2018". Palette: muted slate-blue, warm orange and cool blue factor arrows, yellow-to-red ramp confined to the map, neutral grey, white background. Typography: clean technical sans-serif (Inter or IBM Plex), short token labels, no sentences. Style: precise CAD-inspired technical illustration, vector-clean lines, no photorealism, no clutter, journal double-column width (180 mm). Publication quality.
```

## Alternative Prompt — schematic / technical variant

```
Schematic boxes-and-arrows diagram for a technical report figure, white background, four sequential modules left-to-right: [Module 13: SQL extraction — stdlib sqlite3 read-only bulk query over ReportData/ReportDataDictionary/Time, single J→kWh conversion at the parse boundary, zone-name regex resolving {osm_id}_F{n}_{WHOLE|CORE|PERIM}, CSV fallback flagged RESULTS_CSV_FALLBACK] arrow to [Module 13 metrics: five EUI columns (heating, cooling, lighting, equipment, total kWh/m²/yr, denominator = footprint_area × derive_num_floors imported from Step 3) plus IOD = mean excess of operative temperature over Tcomf = 0.31·Tave + 20.3 across occupied summer hours, occupant-weighted] arrow to [Module 15: GWP — gwp_heating = heating EUI × 0.181 kg CO2e/kWh natural gas; gwp_cooling, gwp_lighting, gwp_equipment = EUI × eGRID 2022 state→subregion electricity factor; convention badge load_referenced_v1] arrow to [Module 14 + 16: LEFT join on osm_id appending exactly 13 columns onto the byte-identical 57-column GeoDataFrame → (N, 70); flag-don't-drop with simulation_status; floor-area-weighted neighbourhood EUI and pct_floor_area_simulated; exports 05_results.gpkg (UTM canonical) / .geojson (EPSG:4326) / .csv + neighbourhood_summary.json; observability-only matplotlib choropleth with failed buildings hatched grey]. Bottom annotation strip lists validation gates CV(RMSE)<30%, NMBE ±10%, R²>0.6, KS D<0.10 versus CBECS 2018 New England. Monochrome blue-grey line art with one orange accent on the GWP module and a small yellow-to-red ramp on the output map; clean technical sans-serif labels (Inter / IBM Plex); no shadows, no gradients, vector-precise; suitable for a methods-section figure of an energy-modeling journal article.
```
