# RESULT V11 — SIMULATION-OUTPUT VISUALIZATION (mapping EnergyPlus results onto the scene)

> Scope: output-to-geometry mapping only. Colormap/legend logic → `V09` (not yet run). Time-slider UI
> mechanics → `V10` (not yet run). Grounded in the actual OpenUBEM results code (`openubem/results/`,
> `openubem/idf/outputs.py`, `openubem/geometry/zoning.py`) read directly 2026-07-02, and the real
> `fereshtehsabeghi/Torino-3d-heat-mapping` GitHub repo, fetched directly (not guessed).

---

## Table 1 — Output inventory

| OpenUBEM output | Source file/field | Granularity available | Best visual encoding | Source |
|---|---|---|---|---|
| Annual EUI (kWh/m²/yr) | `openubem/results/aggregator.py` `_STEP5_COLS` (`total_eui_kwh_m2` + 8 sub-EUI cols), written to `05_results.gpkg` / `.geojson` / `.csv` by `export_results()` — **note:** the prompt-set's assumed filename `eui_summary.json` does not exist in the codebase; see Confidence-and-caveats | Building (one row/polygon per building) | Extrude-height (real building height) + colour (sequential, `total_eui_kwh_m2`) — precedent already shipped: `openubem/results/visualization.py::plot_eui_choropleth` (2-D choropleth, `YlOrRd`, failed buildings hatched grey, "never invisible") | `aggregator.py:18-48,194-249`; `visualization.py:23-65` |
| Per-building end-use breakdown (heating/cooling/lighting/plug/DHW/fans/pumps/cooking/refrigeration) | Same `_STEP5_COLS`, sourced from `HVAC_METERS` — building-wide `OUTPUT:METER` objects at `RunPeriod` frequency (`Cooling:Electricity`, `Heating:NaturalGas`, `WaterSystems:*`, `Refrigeration:*`, `Cooking:*`, etc.) | Building (Facility/system-wide meters, not per-zone) | One end-use at a time via an attribute dropdown (cross-ref `V09`), reusing the EUI extrude+colour treatment; multi-series breakdown belongs in a docked per-building donut/stacked-bar (cross-ref `V10` linked chart), not a single always-on 3D encoding | `openubem/idf/outputs.py:28-42`; `aggregator.py:18-32` |
| Carbon (annual) | `openubem/results/carbon.py::compute_gwp` → `gwp_*_kgco2_m2` (per-building intensity) in `_STEP5_COLS`; absolute city total `neighbourhood_gwp_total_kgco2` in `05_neighbourhood_summary.json` | Building (intensity) **and** neighbourhood (single scalar, no spatial granularity) | Building: extrude-height+colour (sequential/diverging, cross-ref `V09`), same treatment as EUI. Neighbourhood total: **not a map** — a KPI/stat-tile outside the 3D scene | `carbon.py:32-113`; `aggregator.py:109-191,244-247` |
| Hourly demand (8760, whole-building) | `openubem/results/parser.py` parses hourly `Output:Variable`s from `eplusout.sql` per `openubem/idf/outputs.py::STANDARD_OUTPUTS` (11 Zone/Site-level hourly variables). **Conditional:** `write_outputs(trim_hourly=True)` — used for large `fast_zone`/many-zone fleets — skips ALL per-zone hourly `Output:Variable` objects; only annual RunPeriod meters survive | Building, hourly — **only when `trim_hourly=False` for that run**; when trimmed, no hourly data exists at all | Time-slider-driven colour animation over the EUI extrude+colour treatment (cross-ref `V10`); infeasible as an always-on full-8760 animation at neighbourhood scale (Table 3) | `outputs.py:10-23,45-52`; `parser.py:31,86` |
| Per-surface solar irradiance (if/where OpenUBEM's EnergyPlus runs request it) | **Not requested anywhere in the pipeline.** `STANDARD_OUTPUTS` (`outputs.py:11-23`) is the exhaustive, hard-coded output-variable list and contains zero `Surface`-level variables; a repo-wide grep found no `Output:Variable` request for `Surface Outside Face Incident Solar Radiation Rate per Area` (or any `Surface *` variable) anywhere in `openubem/idf/*` | **None today.** EnergyPlus can report this per-surface (confirmed real output variable, units W/m², `Key_Value="*"` applies it to every surface) — OpenUBEM simply never asks for it | N/A today (see Table 2 / "do not paint this way") | `outputs.py:11-23` (absence, verified by grep); EnergyPlus community corroboration (Unmet Hours threads, see References) — **primary NREL I/O-Reference page not fetched within budget, GAP** |
| Comfort metrics (if OpenUBEM computes any) | `iod` (Indoor Overheating Degrees): occupant-count-weighted mean zone-operative-temperature exceedance over an adaptive comfort threshold, occupied summer hours only, computed in `parser.py:340-399`; one scalar per building in `_STEP5_COLS`; aggregated as `mean_iod_c` / `p95_iod_c` in the neighbourhood summary | Building (one scalar per building; derived from zone-level data internally but exposed only at building grain) | Extrude-height+colour (sequential, cross-ref `V09`) — same single-value treatment as EUI | `parser.py:340-399`; `aggregator.py:161-165,176-189` |

## Table 2 — Per-surface vs. per-building mapping honesty

| Output | Honestly paintable per-surface today? | If not, honest fallback | Resolution-mode dependency | Source |
|---|---|---|---|---|
| EUI | **No.** `total_eui_kwh_m2`/sub-EUI are rolled up from building-wide `HVAC_METERS` and zone-hourly sums to one building total; EnergyPlus EUI is inherently a building/zone energy total, not a surface property | Per-building average (extrude+colour) — this is the honest ceiling, not a downgrade | **No.** EUI columns are building-aggregate in every resolution mode; `zone`/`floor` modes add internal zone detail during simulation but `aggregator.py` never exports per-zone EUI | `outputs.py:28-42`; `aggregator.py:18-48` |
| End-use breakdown | No, same reason (Facility/system meters, not per-surface) | Per-building | No | as above |
| Carbon | No — arithmetic on the EUI columns (`carbon.py:91-113`), inherits EUI's building granularity | Per-building | No | `carbon.py:91-113` |
| Solar/irradiance | **Not computed at any granularity today** (Table 1) | "Not available at this resolution" — a real current-capability gap, independent of resolution mode, because the `Output:Variable` is never requested regardless of mode | N/A for whether it's computed; **if** added, the number of paintable surfaces would scale with mode — `building` mode has few lumped envelope surfaces, `zone`/`floor` modes expose the true per-facade surface set from `zoning.py` | `outputs.py` (absence); `zoning.py:15-33` |
| Hourly demand | No — hourly data is Zone-level internally but the parser reduces it to a **building-level** hourly total; no per-surface or persisted per-zone hourly artifact exists today; also gated by `trim_hourly` | Per-building hourly (when not trimmed); annual-only (when trimmed) | **Partially yes.** `zone`/`floor` modes have real interior zone partitions, so a *future* per-zone hourly view would carry information; `building` mode has one lumped zone, so a "per-zone" curve would be identical to the whole-building curve. Per `RESULT_V04`'s LOD-Z gate, only ~5.8% of the AUTO-simulated fleet (470/8,152, `perimeter_core` strategy) currently qualifies for finer-than-building interior detail; new `fast_zone`/`zone`-mode runs qualify fully | `outputs.py:10-23,45-52`; `RESULT_V04_level_of_detail_model.md:98-99` |

## Table 3 — Temporal output handling

| Temporal view | What it shows | Feasibility at neighbourhood scale | Animation vs. static vs. slider | Source |
|---|---|---|---|---|
| Annual single value (default) | `total_eui_kwh_m2` / one end-use / carbon / IOD — one colour per building | Trivial — this is the existing `05_results.*` row; no extra data volume | **Static** (default view) | `aggregator.py` |
| Monthly aggregation | **Not computed or exported anywhere** — `_STEP5_COLS` has no monthly columns; `STANDARD_OUTPUTS` requests `Hourly` reporting frequency only, never `Monthly` | Would need a new `parser.py`/`aggregator.py` aggregation step (sum hourly → monthly); the raw data would exist in `eplusout.sql` for non-trimmed runs, but nothing surfaces it today | GAP — not built; if built, a 12-step month-selector (cross-ref `V10`) | `outputs.py:11-23` (Hourly-only); `aggregator.py` (no monthly cols) — confirmed absent, not merely undiscovered |
| Hourly animation (e.g. a summer week) | Would require a persistent per-building hourly export — today the hourly frame is consumed transiently by `parser.py` from `eplusout.sql` and reduced to annual scalars before anything is written to `05_results.*` | 8760 h × hundreds of buildings is a real payload concern; even a 168 h slice × ~500 buildings is non-trivial for browser-side JSON without a pre-aggregated array format — **GAP on concrete byte size**, needs a pilot (cross-ref `V12`) | **Slider-driven** (cross-ref `V10`), not full auto-animation, to bound data transfer | `parser.py` (SQL consumed then reduced, nothing persisted hourly) |
| Peak/extreme-hour snapshot (e.g. design day) | Not currently exported as a specific field; would require capturing one hour's value before the hourly frame is reduced to annual in `parser.py` | Cheapest temporal option — one value per building, same payload as the annual view | **Static snapshot**, same mechanics as the annual view | GAP — no current peak-hour field, but the hourly frame already passes through `parser.py` before reduction, so it is cheap to add later |

## Table 4 — Peer precedent and the MVP output view

| Question | Answer + source |
|---|---|
| Torino-3d-heat-mapping repo's actual metric and encoding (read directly, not guessed) | **Not an EnergyPlus/building-energy heat-map.** Fetched `github.com/fereshtehsabeghi/Torino-3d-heat-mapping` (repo page + raw `README.md`) directly, 2026-07-02. It maps **urban heat vulnerability**, not energy demand: a **200 m × 200 m grid-cell** density-based temperature *proxy* — README's own formula is "28 °C baseline + up to +6.5 °C from urban density" and the README explicitly labels this **"not measured temperature"** — overlaid with ISTAT population/elderly-share and OSM pedestrian routes. **Buildings themselves are not coloured by any metric** — the README states they are "extruded by height and coloured dark for contrast," serving only as 3D urban-canyon context. The heat proxy renders as a **translucent ground-plane layer per grid cell**, not per-building and not per-surface. Final rendering is by dragging generated GeoJSONs into **kepler.gl** (not a bespoke three.js/CesiumJS app); the Python pipeline uses OSMnx/GeoPandas. No mention of energy simulation, EUI, or EnergyPlus anywhere in the README. This **corrects** `RESULT_V03`'s earlier note ("Low certainty… could not be confirmed first-hand," `RESULT_V03_scene_geometry_interchange_formats.md:137`): the repo's format/stack is now confirmed first-hand, and it turns out to be a weaker direct analogue for an *energy* heat-map than the prompt set assumed. |
| What does CEA's radiation/demand map do differently | CEA runs `cea radiation` (DAYSIM ray-tracing, or the faster CRAX polygon-clipping model) to compute **solar irradiance per building surface** (roof + façade faces) as a distinct pipeline step from `cea demand`, which computes **energy demand per building** (whole-building end-use totals). The two are architecturally separate CEA outputs at different, correctly-matched granularities — CEA never conflates a per-surface physical quantity with a per-building aggregate. The exact dashboard colour-map/rendering mechanics were not stated in the fetched workflow-guide page — **GAP** on that specific rendering detail. |
| What does ubem.io's gallery show as its primary output encoding | Secondary/search-synthesized sources (the ubem.io site pages fetched directly did not state this explicitly — **GAP** on a primary-source confirmation) describe an "urban model visualizer module" that plots EUI/carbon-equivalent results "directly onto the 3D geometry in colour scales," i.e. **per-building colour-mapped 3D massing** — consistent with the extrude+colour approach OpenUBEM's own `plot_eui_choropleth` already does in 2D. No per-surface claim found for ubem.io. |
| Given OpenUBEM's actual output granularity, the single MVP output view | **Per-building total annual EUI (`total_eui_kwh_m2`), extruded to real building height, coloured on a sequential scale (cross-ref `V09`), static/annual (no time-slider in v1).** Justification: (1) the data already exists today, exported and in production use (`05_results.*`, `aggregator.py`); (2) it matches the field's actual convention — both CEA's demand map and ubem.io's gallery encode per-building demand/EUI this way, and it is a *closer* honest analogue to "a value-driven 3D colour map" than the Torino repo itself turns out to be; (3) zero granularity risk — no resolution-mode gate, no per-surface fabrication risk, no data-volume problem (unlike hourly); (4) it is a direct dimensional upgrade of an already-shipped, audited 2-D artifact (`plot_eui_choropleth`), not a new metric requiring new pipeline work. |

---

## Part C — Synthesis (the output-mapping spec + MVP)

### 1. Output-to-geometry mapping table (for `V09`/`V04` to consume)

| Output | Honest granularity | Visual encoding | Resolution-mode gate |
|---|---|---|---|
| Annual EUI | Building | Extrude-height + sequential colour | None — always available |
| End-use breakdown | Building | Extrude-height + colour, one end-use selected at a time (dropdown) + linked donut/bar panel | None |
| Carbon (building) | Building | Extrude-height + colour (sequential/diverging per `V09`) | None |
| Carbon (neighbourhood total) | Neighbourhood (scalar) | KPI stat-tile, not a map | N/A |
| Comfort (IOD) | Building | Extrude-height + colour (sequential) | None |
| Hourly demand | Building, hourly | Time-slider-driven colour animation (cross-ref `V10`) | **Gated on the run's `trim_hourly` flag** — must be read from run metadata before offering the slider |
| Per-surface solar irradiance | **None (not computed)** | N/A today | Blocked entirely until the pipeline requests the `Output:Variable`; if added, would additionally require `zone`/`floor`-mode-aware surface exposure |
| Monthly / peak-hour views | **None (not computed)** | N/A today | Blocked until `parser.py`/`aggregator.py` add the aggregation |

### 2. MVP output view

Ship **per-building total annual EUI**, extruded to real height, coloured sequentially (`V09`'s classification/colormap recipe, `total_eui_kwh_m2` as the bound attribute), static/annual only. It is the only output in Table 1 with zero granularity risk, it already exists end-to-end in the pipeline, and it is a direct 3-D upgrade of the already-shipped `plot_eui_choropleth`. Do not build the hourly time-slider, per-surface irradiance, or any end-use/carbon dropdown until the MVP EUI view is validated.

### 3. "Do not paint this way" list

- **Do not paint per-surface solar/irradiance heat-maps.** Not computed by OpenUBEM today at any resolution mode — this would fabricate spatial detail the simulation never produced (Table 1/2).
- **Do not paint per-zone EUI/end-use/carbon/IOD colouring**, even for `zone`-mode buildings whose simulation *internally* computed zone-level values. The exported `05_results.*` schema is building-aggregate in every mode — showing a "per-zone" colour would fabricate a spatial breakdown the export layer doesn't carry. (Note: `V04`'s LOD-Z gate governs whether *interior zone geometry* is shown at all — it does not, by itself, license per-zone *attribute* colouring, which is a separate, currently-unsupported binding. Flag to `V05`.)
- **Do not auto-animate a full 8760-hour loop for a `trim_hourly=True` run.** That run has zero hourly data; the viewer must check the run's `trim_hourly` metadata before even offering the time-slider control (cross-ref `V10`/`V14` provenance).
- **Do not present monthly aggregation or peak/extreme-hour snapshots as shipped features.** They are GAPs — not computed anywhere in `parser.py`/`aggregator.py` today — until a manager decides to add them.
- **Do not colour a `simulation_status != success` building as if it had a real value.** Carry over `plot_eui_choropleth`'s existing convention — hatched grey, "never invisible" — into the 3-D viewer (`visualization.py:53-58`).

### 4. Downstream note for `V10`

- **Static-only, no slider needed:** annual EUI, end-use breakdown, carbon (building + neighbourhood), IOD/comfort (Table 1 rows 1, 2, 3, 6).
- **Needs the time-slider, conditionally:** whole-building hourly demand — only for runs where `trim_hourly=False`. `V10` must gate the slider control on that per-run metadata flag, not assume it is always available fleet-wide.
- **Nothing currently needs a slider** for solar/irradiance or monthly/peak views because neither is computed — flag to `V10` as a future extension only if `parser.py`/`aggregator.py` are extended to produce them.

---

## Confidence and caveats

| Claim | Confidence | Caveat |
|---|---|---|
| `eui_summary.json` filename | **Low that it literally exists.** | The prompt set's shared facts assume a file named `eui_summary.json`; the actual code (`aggregator.py::export_results`) produces `05_results.gpkg` / `.geojson` / `.csv` / `.schema.json` and `05_neighbourhood_summary.json`. Every schema claim in this document cites the real files. Flag to manager: either correct the prompt-set's shared facts, or confirm an `eui_summary.json`-named artifact is planned but unbuilt. |
| Per-surface solar-irradiance `Output:Variable` is real and reportable per-surface | **High** on the variable's existence/units (multiple independent EnergyPlus community sources agree: W/m², `Key_Value="*"` applies per surface). | The **primary NREL Input/Output Reference** page was not fetched within the search budget — corroboration is from community forum threads (Unmet Hours), not the official EnergyPlus documentation. |
| OpenUBEM requests zero per-surface output variables | **High.** | Confirmed by direct read of `openubem/idf/outputs.py` (the exhaustive, hard-coded `STANDARD_OUTPUTS` list) plus a repo-wide grep for `Surface` output-variable requests — zero matches. |
| CEA's radiation/demand rendering mechanics (exact colour-map, dashboard UI) | **Medium-low.** | Confirmed CEA computes radiation (per-surface) and demand (per-building) as architecturally separate steps at correctly-differentiated granularities. The *exact* 3-D/dashboard rendering and colour-scale mechanics were not stated in the fetched workflow-guide page — GAP. |
| ubem.io's primary output encoding | **Low — GAP.** | No ubem.io-authored page fetched directly stated the exact visual encoding; the "per-building colour-mapped 3D massing" conclusion rests on search-synthesized secondary sources, not a primary ubem.io citation. A direct inspection of the ubem.io gallery/demo (if publicly accessible) is needed to firm this up. |
| Torino repo's actual metric/encoding | **High.** | Read directly (GitHub repo page fetched once, raw `README.md` fetched once, consistent details across both fetches). This supersedes `RESULT_V03`'s earlier "could not be confirmed" caveat. |
| Monthly / peak-hour temporal views are simply unbuilt (not hidden elsewhere in the codebase) | **High.** | Confirmed by direct read of `outputs.py` (Hourly-only reporting frequency, no Monthly request anywhere) and `aggregator.py` (`_STEP5_COLS` has no monthly/peak columns) — this is an absence-of-evidence claim backed by an exhaustive read of the two relevant files, not a search gap. |

---

## Reference list

1. OpenUBEM source code (internal, read directly 2026-07-02): `openubem/results/aggregator.py` (Step-5 Module 14, DESIGN §3F–§3G); `openubem/results/carbon.py` (Step-5 Module 14, DESIGN §3E); `openubem/results/parser.py`; `openubem/results/visualization.py` (Step-5 Module 16, DESIGN §3G); `openubem/idf/outputs.py` (DESIGN §3I, fact #26); `openubem/geometry/zoning.py`.
2. `docs/docs_ACTIVE/3D/deepResearch/RESULT_V04_level_of_detail_model.md` (internal, read 2026-07-02) — LOD-Z resolution-mode gate figures (470/8,152, 5.8%).
3. `docs/docs_ACTIVE/3D/deepResearch/RESULT_V03_scene_geometry_interchange_formats.md` (internal, read 2026-07-02) — prior (superseded) Torino-repo uncertainty note.
4. fereshtehsabeghi. "Torino-3d-heat-mapping." GitHub repository. https://github.com/fereshtehsabeghi/Torino-3d-heat-mapping — repo page and raw `README.md` fetched directly 2026-07-02.
5. City Energy Analyst (CEA) documentation. "How to do analyses with CEA?" https://city-energy-analyst.readthedocs.io/en/update_glossary_documentation/cea-workflow-guide.html — fetched 2026-07-02.
6. UBEM.IO. "Energy Modeler." https://www.ubem.io/energy-modeler — fetched 2026-07-02 (inconclusive on visualization specifics; see caveats).
7. Web-search synthesis (not a single primary citation, 2026-07-02) on UBEM.io's "urban model visualizer module" and 3-D colour-scale plotting of EUI/CO₂e — flagged low-confidence secondary source; see caveats.
8. EnergyPlus community corroboration of `Surface Outside Face Incident Solar Radiation Rate per Area` (units W/m², per-surface via `Key_Value="*"`): Unmet Hours forum, https://unmethours.com/question/43364/energy-plus-surface-outside-face-incident-solar-radiation-rate-per-area-of-tilted-surface/ and https://unmethours.com/question/29652/energyplus-how-to-calculate-incident-solar-radiation-rate-for-shading-surfaces/ — accessed via search synthesis 2026-07-02. Primary NREL Input/Output Reference not directly fetched (GAP, budget-bounded).

*Research budget used: 3 web searches, 4 web page fetches (2 to the Torino repo, 1 to CEA docs, 1 to ubem.io) — within the ≤6 search / ≤10 fetch cap. No sub-agents or skills invoked. Grounded additionally in direct reads of 6 OpenUBEM source files and 2 prior RESULT docs (not counted against the web budget).*
