# EXECUTOR PROMPT — EU-02/EU-04 acquisition adapters and the first European footprint manifest

**Slug:** `eu02-acquisition-adapters`
**Opened:** 2026-08-24
**Work packages:** `EU-02` (semantic crosswalk, residential filter) feeding `EU-04` (geometry)
**Slices covered:** `X-09`, `X-10`, `X-11` of the ledger in
[`DIRECTOR_PROMPT_european_locations.md`](DIRECTOR_PROMPT_european_locations.md) §19.5
**Governing specification:** [`../MVP_european_locations.md`](../MVP_european_locations.md) §9.7.2 (gates
`NS-01`–`NS-10`) and §10.4 (four-panel input audit)
**Selection record of authority:**
[`../outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md`](../outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md)
(Revision B, four sites SELECTED, boundaries checksummed). Do not re-open it. Every bbox, boundary
file, endpoint, field name and measured count quoted below comes from that document; where this plan
and that document disagree, **that document wins and this plan is wrong**.

**Why this plan exists.** EU-02 closed on 2026-08-24 with four selected neighbourhoods. Two of them
(`ES-MAD-BERRUGUETE`, `GB-LDN-STDUNSTANS`) can be acquired today through the existing OSM path. The
other two (`IT-BOL-GALVANI2`, `FR-LYO-HAUTCOEURPENTES`) cannot: gate `NS-02` is `NOT_MET` at those
sites for exactly one reason — **the repository has no IGN BD TOPO adapter and no Comune di Bologna
ODS adapter**. Nothing about those two sites is undecided; the sources are identified, licensed,
reachable, and already measured. This is missing code, and this plan writes it.

---

## 1. What "done" means

At the end of this plan the repository holds, for all four selected sites, a raw footprint manifest in
the frozen 23-column acquisition schema, a disjoint exclusion manifest, and a per-site gate report — so
that `NS-02` reads `MET` at all four sites and `EU-04` geometry can begin from real footprints.

Nothing in this plan generates geometry, IDF, or simulation results. Nothing in this plan touches
Speed.

---

## 2. Hard rules for the executor

1. **Do not re-open the selection.** The four sites, their boundaries and their checksums are fixed.
   If a boundary hash does not reproduce, stop and report — do not re-download and continue.
2. **No live network in the automated suite.** Every adapter needs two paths: an offline path over a
   small committed fixture (exercised by `pytest`) and a live path (never reached by `pytest`). This
   mirrors `openubem/acquisition/overture_fetcher.py:61`, whose live DuckDB leg is reached only by a
   manual LIVE_SMOKE driver. Mark any live test `@pytest.mark.slow` — the marker already exists at
   `pyproject.toml:56` — and keep it deselected by default.
3. **The 23-column schema is frozen.** `osm_fetcher._SCHEMA_COLUMNS` (`openubem/acquisition/osm_fetcher.py:518`)
   and its dtype contract in `_validate_schema` (`:531`) do not change. Adapters conform to it; they
   do not extend it. Source-specific richness goes into the `surplus_tags` JSON column.
4. **No behaviour change to the OSM path.** `tests/test_osm_fetcher.py` holds 56 tests. They must pass
   **unchanged, with no edits to the test file**, after T01. If a test needs editing, the refactor is
   wrong.
5. **The Bologna building unit is already ruled — do not re-open it.** One building = one
   `rifter_edif_pl` cadastral object (**1,372** in the unit); CTC volumetric bodies dissolve onto it.
   Ruling `D-EU-02-E`, §5.5. T07 still measures all three counts, as a cross-check, not as a question.
6. **No `.py` under `docs/`.** No figures anywhere except `openubem/outputs/`.
7. **No new third-party dependency.** See §4.
8. **Never run a git state-changing command.** Report; the user commits.
9. Evidence for each slice goes to `openubem/outputs/eu_evidence/X-09/`, `.../X-10/`, `.../X-11/`.
   Every artefact this plan names must exist and be non-empty before the slice is reported complete.
10. **Register any error you hit** in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` in the house
    format before closing the task — and search that file first, before debugging anything.

---

## 3. File layout

**New files**

| Path | Purpose |
|---|---|
| `openubem/acquisition/footprint_schema.py` | The source-agnostic tail of the acquisition pipeline, lifted out of `osm_fetcher.py` in T01. Owns `SCHEMA_COLUMNS`, `seven_step_clean`, `assign_provenance`, `build_quality_flag`, `validate_schema`, `serialize`. |
| `openubem/acquisition/boundary_clip.py` | Clip a footprint frame to a selected boundary GeoJSON, split residential from excluded, emit the `NS-08` exclusion manifest. |
| `openubem/acquisition/bdtopo_fetcher.py` | IGN BD TOPO V3 adapter (FR). |
| `openubem/acquisition/bologna_fetcher.py` | Comune di Bologna Opendatasoft adapter (IT). |
| `openubem/data/bdtopo_to_use_class.json` | `usage_1` / `usage_2` → OpenUBEM use class. |
| `openubem/data/bologna_ctc_to_use_class.json` | CTC `descrizion` → OpenUBEM use class (the 29 non-residential classes named in the report §3.3). |
| `openubem/data/fixtures/eu02/` | Committed offline slices: one small BD TOPO GeoJSON, one small Bologna CTC GeoJSON, one clipped boundary each. Keep each under ~200 kB. |
| `tests/test_bdtopo_fetcher.py`, `tests/test_bologna_fetcher.py`, `tests/test_boundary_clip.py` | Targeted tests. |

**Modified files**

| Path | Change |
|---|---|
| `openubem/acquisition/osm_fetcher.py` | Import the shared tail from `footprint_schema`; keep every public name importable from its current location (`ingest_buildings`, `fetch_buildings`) so no caller breaks. |
| `../MVP_european_locations.md` | `NS-02` row and the EU-02 status row, per the ruling in §5.4. |
| `../content/table_9_7_work_packages.csv`, `../content/walkthrough_progress_log.csv` | Status + one append-only row per completed task. |
| `DIRECTOR_PROMPT_european_locations.md` | Head box, §17, §19.5 ledger. |

**Do not touch:** anything under `docs/docs_main/`, root `main.py`, `openubem/idf/`, `openubem/geometry/`,
or any GSSCanada source. The four selected boundary GeoJSON files are read-only inputs.

---

## 4. Dependency decisions (pinned)

- **No new package.** BD TOPO and Bologna are both plain HTTP endpoints returning GeoJSON. Use
  `requests` (`pyproject.toml:19`) + `geopandas.read_file` on the response text. Do **not** add
  `owslib`, `duckdb`, `httpx`, or a WFS client library.
- `osmnx` stays pinned `>= 1.9, < 2.0` (`pyproject.toml:10`; the assertion at `osm_fetcher.py:15`
  enforces it at import).
- New JSON crosswalks are already covered by the packaging rule `"openubem.data" = ["*.json", "*.csv"]`
  (`pyproject.toml:43`) — no packaging change needed.
- Fixtures go under `openubem/data/fixtures/eu02/` following the `fusion/` precedent, and each fixture
  gets a line in a `LICENSES.md` beside it naming its source and licence, as
  `openubem/data/fixtures/fusion/LICENSES.md` does.

---

## 5. Specification facts, with citations

### 5.1 The gates this plan closes

| Gate | Text | Source |
|---|---|---|
| `NS-02` | "Use an existing OpenUBEM input mode: address, coordinate, bounding box, or OSM XML" — evidence is the acquisition configuration and raw footprint manifest | `../MVP_european_locations.md:734` |
| `NS-08` | "Show non-residential/unknown footprints only as excluded context" — evidence is an exclusion manifest **disjoint** from the layout/IDF/simulation manifests | `../MVP_european_locations.md:740` |
| `NS-09` | Audit construction period, energy-record availability, residential typology, construction material/set | `../MVP_european_locations.md:741` |
| `NS-10` | Keep multiple selected sites separate until independent acceptance — unique `neighbourhood_id`, per-site gate report | `../MVP_european_locations.md:742` |

The four-panel audit figure required before Q1/Q2 is `../MVP_european_locations.md:877`. This plan
produces the *inputs* for it (`NS-09` counts), not the figure.

### 5.2 The acquisition contract as it exists today

- `ingest_buildings(location=None, radius_m=1000.0, bbox=None, osm_path=None, tags=None, retry_policy=None, output_dir=None) -> gpd.GeoDataFrame` — `openubem/acquisition/osm_fetcher.py:26`.
- Exactly one of `{location, bbox, osm_path}` may be set; `_resolve_mode` raises otherwise — `:114`.
- **`bbox` order is `(north, south, east, west)`** because it is handed straight to
  `osmnx.features.features_from_bbox` in the pinned 1.9.3 — `:43`. The report's YAML packets carry
  both orders; use the `bbox_openubem_order` field, never `bbox_wgs84`.
- Pipeline stages after fetch, in order: `_flatten_tags` (OSM-specific, `:191`) → reproject to
  `estimate_utm_crs()` (`:55`) → `_seven_step_clean` (`:355`) → `_assign_provenance` (`:439`) →
  `_build_quality_flag` (`:489`) → column selection to `_SCHEMA_COLUMNS` (`:518`) → `_validate_schema`
  (`:531`) → `_serialize` (`:559`).
- `_serialize` writes exactly three artefacts into `output_dir`: `01_buildings_clean.gpkg` (layer
  `buildings`), `01_buildings_clean.schema.json` (per-column `provenance_role`), and a never-empty
  `01_buildings_clean.log` of JSON lines.
- `_validate_schema` enforces: 23 columns in exact order; `levels` / `year_built` / `underground` are
  `Int64`; `height_m` / `roof_height_m` / `footprint_area_m2` / `perimeter_m` are `float64`; `geometry`
  is a geometry dtype; **`osm_id` is unique**.
- The second-source precedent is `overture_fetcher.fetch_overture` — `openubem/acquisition/overture_fetcher.py:32`
  — which normalises to a 6-column frame for fusion. **That is not the pattern here.** BD TOPO and
  Bologna are *primary* footprint sources for their sites, so they must emit the full 23 columns and
  the same three artefacts, or downstream `EU-04` code would need a second code path.

### 5.3 The two sites that need new code

**`FR-LYO-HAUTCOEURPENTES`** — report §3.4, §4.2:

- Endpoint `https://data.geopf.fr/wfs/ows`, `SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=BDTOPO_V3:batiment&OUTPUTFORMAT=application/json`.
- **Axis-order trap, load-bearing:** `BBOX=<lon>,<lat>,<lon>,<lat>,CRS:84`. The same request written
  `,EPSG:4326` with lat/lon-ordered values returns **zero features and no error**. Encode this as an
  explicit constant and a test, not a comment.
- Page with `&COUNT=5000&STARTINDEX=<n>&SORTBY=cleabs`; `SORTBY` is what makes paging deterministic.
  `RESULTTYPE=hits` gives `numberMatched` for a pre-flight count.
- Stable id `cleabs` → `osm_id`. Fields consumed: `usage_1`, `usage_2` (use class),
  `nombre_d_etages` → `levels`, `hauteur` → `height_m`, `date_d_apparition` → `year_built`,
  `nombre_de_logements` and `materiaux_des_murs` → `surplus_tags`.
- Residential rule: include `usage_1 == 'Résidentiel' or usage_2 == 'Résidentiel'`; exclude
  `usage_1 in {Commercial et services, Industriel, Agricole, Religieux, Sportif}`; `Indifférencié` →
  **unknown, excluded, retained in the audit**; `usage_1 == 'Annexe'` and not residential → removed as
  non-modelable and **reported separately so the removal can be undone**.
- Expected on the retained boundary: 891 buildings, 23 annexes removed, of the remaining 868 →
  **544 residential, 278 unknown, 52 non-residential**. `nombre_de_logements` present for 100 % of the
  544 (6,387 dwellings); `nombre_d_etages` present for 100 % (mean 5.45).
- Licence: Licence Ouverte / Open Licence 2.0 (Etalab); the attribution string "IGN — BD TOPO" must be
  written into the manifest sidecar.

**`IT-BOL-GALVANI2`** — report §3.3, §4.4:

- Endpoint `https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets/{ds}/exports/geojson?limit=-1`,
  `ds = c_a944ctc_edifici_pl` (65,744 volumetric buildings). Optional server-side filter
  `&where=in_bbox(geo_shape, {min_lat}, {min_lon}, {max_lat}, {max_lon})`.
- Stable id `codice_ogg` → `osm_id`. Fields: `altezza_gronda` (or `quota_gronda − quota_piede`) →
  `height_m`, `volume` and `descrizion` → `surplus_tags`. **There is no per-object storey count and no
  per-object construction year** — Italian vintage/typology are ISTAT section-level aggregates, so
  `levels` and `year_built` are legitimately `<NA>` here and the four-panel audit for Italy is a
  choropleth over 66 census sections (report §3.3 `known_geometry_risks`).
- Residential rule: exclude the 29 explicitly non-residential `descrizion` classes (Stabilimento
  industriale, Edificio scolastico, Chiesa, Ospedale, Tettoia/pensilina, Baracca, Cabina ENEL, …);
  the remainder ("Edificio generico" and equivalents) are residential candidates. Enumerate all 29 in
  the crosswalk JSON — do not pattern-match on substrings.
- Expected on the retained boundary: **2,427 CTC objects, 239 excluded, 2,188 residential candidates**,
  397,592 m² footprint, median 96.5 m², height present for 100 %, mean eaves height 12.57 m.
- **The known unresolved relation:** ISTAT counts **1,010 residential buildings** in the same unit,
  and the cadastral layer `rifter_edif_pl` holds **1,372** objects there. The CTC decomposes one
  building into volumetric bodies, so 2,188 ≠ 1,010 is a representation difference, **not** a
  disagreement about how many buildings exist. This is what T07 measures and CP-C rules.
- Licence: CC BY 4.0, Comune di Bologna. ISTAT counts are CC BY 3.0 IT, vintage **2011**.

### 5.4 Ruling taken 2026-08-24 — `D-EU-02-D`, what satisfies `NS-02`

`NS-02` as written names four input modes and none of them is "a new adapter". Read literally, the two
sites could never pass. Read for its purpose — the gate exists so that a site is acquired through the
supported, schema-validated pipeline rather than a bespoke one-off script — a new adapter passes if it
is indistinguishable from the existing modes downstream.

**Ruled.** A source adapter satisfies `NS-02` when all four hold, and the gate report must assert all
four by test:

1. it lives in `openubem/acquisition/` and is reached through the documented `ingest_buildings`
   dispatch, not called ad hoc from a script;
2. it emits the frozen 23 columns in order and passes `validate_schema` untouched;
3. it writes the same three `_serialize` artefacts to `output_dir`;
4. its licence and endpoint are recorded in the manifest sidecar.

`../MVP_european_locations.md:734` is amended to name this route. **Reversible** by a later owner ruling
quoting this section; taken under the same delegation as `D-EU-02-A/B/C` (report §7).

**What this does not license:** changing the schema, weakening `validate_schema`, or treating a
hand-run notebook as an acquisition path.

---

### 5.5 Ruling taken 2026-08-24 — `D-EU-02-E`, what one building is at `IT-BOL-GALVANI2`

**One building = one `rifter_edif_pl` cadastral object.** On the retained boundary that is **1,372**.
The 2,188 residential CTC candidates are volumetric bodies and dissolve onto it; the ISTAT **1,010** is
a census aggregation carrying its own definitional rules and stays as the selection-time statistic and
a reported cross-check, not the acquisition unit.

**Reasoning.** The other three sites already fix the granularity: at Madrid and London one OSM building
polygon is one building, at Lyon one BD TOPO `batiment` is one building — in each case one footprint
polygon. The cadastral object is Bologna's footprint polygon. The CTC body is finer than a building
(the same building split by height), and ISTAT is coarser and produced by a different instrument.
Choosing 1,372 is therefore not a new judgement, it is the judgement already made at the other three
sites, applied consistently. Deciding it now also removes the only cross-country inconsistency that
would have made the four per-building EUIs incomparable.

**Reversible** by a later owner ruling quoting this section. T07 reports all three counts so any
reversal argues against measured numbers.

### 5.6 Ruling taken 2026-08-24 — `D-EU-02-F`, the Lyon boundary licence is a lookup, not a gate

Report §3.4 marks the Métropole de Lyon quartier boundary `NOT_VERIFIED`. That status came from the
selection session not having read the dataset page's licence field, **not** from any evidence the
licence is restrictive. It is therefore a lookup and it is folded into T05: record the exact licence
string and retrieval date in the slice evidence and flip the status.

Fallback, applied by the executor without asking: if the string is not an open licence, retain
IGN/INSEE CONTOURS-IRIS (Licence Ouverte / Etalab 2.0) clipped to the same quartier `7016` geometry as
the **publication** boundary, keep the Métropole geometry as the **acquisition** boundary, and report
the area delta. Either branch continues without a stop. This does **not** re-open `D-EU-02-A`: the
selected unit remains quartier `7016`, only the boundary artefact used for publication can change.

---

## 6. Task list

### Slice `X-09` — shared tail, boundary clip, and the two OSM sites

#### T01 — Extract the source-agnostic tail into `footprint_schema.py`

- **What.** Move `_SCHEMA_COLUMNS`, `_seven_step_clean`, `_assign_provenance`, `_build_quality_flag`,
  `_validate_schema`, `_serialize` and the `provenance_roles` map out of `osm_fetcher.py` into
  `openubem/acquisition/footprint_schema.py`, exported without the leading underscore. Re-import them
  into `osm_fetcher.py` under their existing private names so nothing else in the repository moves.
- **Why.** Three adapters must produce byte-identical schema and artefacts. Copying the tail three
  times guarantees they drift; the second copy would already be wrong.
- **How.** Pure move, no edits to logic. `_flatten_tags`, `_parse_height_to_m`, `_parse_year`,
  `_resolve_overlaps` and the `osmnx` assertion stay in `osm_fetcher.py` — they are OSM-specific.
  Keep `fetch_buildings = ingest_buildings` (`osm_fetcher.py:111`).
- **How to test.** `pytest -q tests/test_osm_fetcher.py` → **56 passed**, with the test file unedited.
  Then `pytest -q tests/` and compare to the recorded suite baseline; the delta must be zero.

#### T02 — `boundary_clip.py`: clip, split, and the `NS-08` exclusion manifest

- **What.** `clip_to_boundary(gdf, boundary_geojson, *, verify_sha256=None)` and
  `split_residential(gdf, crosswalk, *, unknown_policy="exclude_retain")`, plus a writer emitting
  `02_residential_manifest.gpkg`, `02_excluded_manifest.gpkg` and `02_exclusion_counts.json`.
- **Why.** `NS-08` requires the exclusion manifest to be **disjoint** from the modelled manifest —
  that is a property of the split, so it must be produced by one function and asserted once, not
  re-derived per site.
- **How.** Reproject the boundary to the frame's UTM CRS before the spatial predicate; retain a
  footprint whose **representative point** falls inside the boundary (not centroid — a concave
  L-shaped block can have its centroid outside itself). Re-hash the boundary file and compare to
  `verify_sha256` when given. `02_exclusion_counts.json` records, per site: total, residential,
  unknown, non-residential, annexes-removed, and the reason string for every exclusion.
- **How to test.** `tests/test_boundary_clip.py`: (a) union of the two manifests equals the clipped
  input and their intersection on `osm_id` is empty; (b) a footprint straddling the boundary edge is
  assigned deterministically; (c) an L-shaped polygon whose centroid lies outside itself is retained;
  (d) a wrong `verify_sha256` raises rather than warning.

#### T03 — Acquire `ES-MAD-BERRUGUETE` and `GB-LDN-STDUNSTANS`

- **What.** Run the existing OSM path for the two OSM-sourced sites, clip to their retained boundaries,
  split, and write per-site manifests under `openubem/outputs/eu02/<site_id>/`.
- **Why.** This is the arc's first real European footprint manifest, and it needs no new code — it is
  the control that proves T01/T02 did not break the working path before two new adapters are added.
- **How.** Use `bbox_openubem_order` from report §3.1 and §3.2 — Madrid
  `(40.463907, 40.453976, -3.698399, -3.711403)`, London from §3.2 — with `tags={"building": True}`.
  This is a **live network call**: run it as a script under `openubem/outputs/eu_evidence/X-09/`, never
  from `pytest`. Record `numberMatched`-equivalent row counts and the fetch timestamp.
- **How to test.** Assert the clipped residential counts land within a stated tolerance of the report's
  measured values (Madrid 1,195 residential of the barrio; London 1,241 on the **BFC** boundary — see
  the BGC/BFC note, report §2.6, and use BFC). A material disagreement is a **stop-and-report**, not a
  tolerance to widen.

### Slice `X-10` — IGN BD TOPO adapter (France)

#### T04 — `bdtopo_fetcher.fetch_bdtopo`

- **What.** `fetch_bdtopo(bbox=None, *, slice_path=None, endpoint=DEFAULT_WFS, page_size=5000) -> gpd.GeoDataFrame`
  returning the raw BD TOPO frame; and `ingest_bdtopo(...)` wrapping it through the T01 tail to the
  23-column schema and the three artefacts.
- **Why.** `NS-02` for `FR-LYO-HAUTCOEURPENTES`.
- **How.** Build the WFS query exactly as report §4.2. The `CRS:84` suffix and lon/lat ordering are a
  module-level constant with a comment naming the failure mode (zero features, no error). Page on
  `STARTINDEX` with `SORTBY=cleabs` until a short page returns. Map `cleabs → osm_id`,
  `nombre_d_etages → levels` (`Int64`), `hauteur → height_m`, `date_d_apparition → year_built`
  (parse the year out of the ISO date), `usage_1 → building_tag`, and put `usage_2`,
  `nombre_de_logements`, `materiaux_des_murs`, `appariement_fichiers_fonciers` into `surplus_tags`.
  Provenance values follow the OSM convention already in `_assign_provenance`.
- **How to test.** `tests/test_bdtopo_fetcher.py` against the committed offline slice: the axis-order
  constant is asserted against the literal expected query string; `cleabs` uniqueness; `usage_1`
  crosswalk covers every value present in the slice and raises on an unmapped one; `levels` and
  `year_built` are `Int64`; the full frame passes `validate_schema`. Live leg `@pytest.mark.slow`,
  deselected.

#### T05 — Acquire `FR-LYO-HAUTCOEURPENTES` and reconcile

- **What.** Run T04 live on the site bbox, clip, split, write manifests, and reconcile against the
  measured counts.
- **Why.** An adapter that runs is not an adapter that is right. The report gives four independently
  measured numbers to check it against.
- **How.** bbox `(45.774784, 45.768891, 4.837450, 4.823612)` in OpenUBEM order; boundary
  `eu02_boundary_FR-LYO-HAUTCOEURPENTES.geojson`, sha256
  `8832ec13e7bb96aff3cca4fee52b76d0f8644bffb9157a56c6eed2c77f4b0739`.
- **How to test.** Reconcile: 891 total, 23 annexes, 544 residential, 278 unknown, 52 non-residential,
  6,387 dwellings, mean 5.45 storeys. Report each as measured-vs-expected. **Also record the 278
  unknowns separately** — report §3.4 warns that BD TOPO assigns `Indifférencié` where the match
  against the *fichiers fonciers* failed, so some are dwellings; if they were resolved the site grows
  toward 800. That number must be visible, not folded into "excluded".

### Slice `X-11` — Comune di Bologna adapter (Italy)

#### T06 — `bologna_fetcher.fetch_bologna`

- **What.** `fetch_bologna(dataset, bbox=None, *, slice_path=None) -> gpd.GeoDataFrame` plus
  `ingest_bologna(...)` through the T01 tail.
- **Why.** `NS-02` for `IT-BOL-GALVANI2`.
- **How.** Opendatasoft Explore v2.1 export endpoint as report §4.4, `limit=-1`, optional
  `in_bbox(geo_shape, min_lat, min_lon, max_lat, max_lon)` — note this filter takes **lat first**,
  the opposite of BD TOPO; both orders live in the same package, so name them explicitly in each
  module. `codice_ogg → osm_id`, `altezza_gronda → height_m` with
  `quota_gronda − quota_piede` as the fallback, `descrizion → building_tag`, `volume` and the CTC
  attributes to `surplus_tags`. `levels` and `year_built` stay `<NA>` — do **not** derive storeys from
  height here.
- **How to test.** `tests/test_bologna_fetcher.py` on the committed slice: all 29 non-residential
  classes are present in the crosswalk and an unlisted `descrizion` raises; `codice_ogg` uniqueness;
  height fallback fires when `altezza_gronda` is null and both quotas exist; `validate_schema` passes
  with `levels`/`year_built` entirely `<NA>`; the aggregation ratio is **not** silently applied.

#### T07 — Measure the CTC-to-building relation (cross-check of ruling `D-EU-02-E`)

- **What.** For the 2,188 residential CTC candidates inside the boundary, report: (a) the number of
  connected components after dissolving touching/overlapping polygons; (b) the count after a spatial
  join onto `rifter_edif_pl` cadastral objects (1,372 in the unit); (c) the ISTAT figure (1,010); and
  the per-component footprint-area and volume distributions for each.
- **Why.** The unit is ruled (`D-EU-02-E`, §5.5): the manifest is built on (b), the **1,372** cadastral
  objects. (a) and (c) are reported alongside it so the ratio to the CTC bodies and to the ISTAT count
  is on the record and the ruling can be reversed later against measured numbers rather than argued.
- **How.** One script under `openubem/outputs/eu_evidence/X-11/`, writing a single JSON plus a table.
  The manifest itself is built on the cadastral object per `D-EU-02-E`.
- **How to test.** The three counts are reported with the exact query used for each, and the manifest
  row count equals the cadastral-join count. **No stop — continue to T08.**

#### T08 — Per-site gate report and surface updates

- **What.** A per-site `NS-01`–`NS-10` gate report (`NS-10` requires per-site separation and a unique
  `neighbourhood_id`), the `NS-09` attribute-coverage counts from the report §2.7 columns, and the
  four bookkeeping surfaces updated in the same change set.
- **Why.** §19.1 of the director prompt requires all four surfaces updated per material result, and the
  gate report is the evidence `NS-02` is finally `MET`.
- **How.** Update: (1) the head box and §19.5 ledger of the director prompt; (2) MVP §9.7 and
  `../content/table_9_7_work_packages.csv`; (3) walkthrough Table 4 and one append-only UTC row per
  task in `../content/walkthrough_progress_log.csv`; (4) a decision record under `../debugs/docs/`
  for the CP-C ruling.
- **How to test.** `NS-02` reads `MET` for four sites with a manifest path each; the exclusion manifests
  are disjoint; every cited artefact exists and is non-empty.

---

## 7. Stop-and-report points

**CP-A — after T03.** Report the two OSM manifests with measured-vs-expected counts and confirm the
56 OSM tests still pass unedited. Do not start T04 if either count disagrees materially — a
disagreement means the boundary, the bbox order, or the clip predicate is wrong, and it would be
inherited by both new adapters.

**CP-B — after T05.** Report the France reconciliation, including the 278 unknowns as their own line.
Also carry out the **Métropole de Lyon boundary licence check** — ruling `D-EU-02-F`, §5.6. This is a
lookup, not a decision and not a stop: read the licence field on the source dataset page, record the
exact string and the retrieval date in the slice evidence, and flip report §3.4 from `NOT_VERIFIED`.
If and only if the string is not an open licence, retain IGN/INSEE CONTOURS-IRIS (Licence Ouverte /
Etalab 2.0) clipped to the same quartier `7016` geometry as the publication boundary, keep the
Métropole geometry as the acquisition boundary, and report the area delta. Continue either way.

**CP-C — after T07.** Report the three counts (dissolved components / cadastral join **1,372** /
ISTAT 1,010) and the resulting dwellings-per-building, against the ruled unit `D-EU-02-E`. **This is a
report, not a gate — do not wait for a reply.** Continue to T08 in the same session. Stop only if the
cadastral join lands outside 1,200–1,550, which would mean the join predicate or the clip is wrong.

---

## 8. Progress log

*One entry per completed task, appended by the executor. Format:*
`#### TXX — <title> — completed YYYY-MM-DD` *then* **Artifacts** / **Deviations** / **Test status** /
**Notes**.

<!-- executor appends below this line -->
