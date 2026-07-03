# PLAN — Interactive 3D Web-Visualization (Arc I, MVP)

- **Slug:** `3dviz-implementation`
- **Date:** 2026-07-02
- **Status:** DRAFT — awaiting manager-of-manager approval before any executor kickoff.
- **Binding contract:** this arc has **no `docs_main/` DESIGN** (it is research-driven, not spec-driven).
  The **15 audited `RESULT_V*.md` files** under `docs/docs_ACTIVE/3D/deepResearch/` are the binding
  source-of-truth in the same way a DESIGN would be. Every load-bearing decision below cites the RESULT
  that fixed it (§5). If a RESULT and this PLAN disagree, **STOP and quote the conflict** — do not invent.
- **Related arcs (do not re-litigate here):** [[project_input_imputation_arc]] (provenance fields we render),
  [[project_layoutgenerator_arc]] / simulation-Resolution (the `resolution_mode`/`zoning_strategy` we gate on),
  [[project_archetype_threshold_E-R3-3]] (`archetype_confidence` we render).

---

## 0. What this task is (read first)

**The goal.** OpenUBEM today can render its simulated neighbourhoods only as **static matplotlib PNGs and
desktop-CAD files** (`.dae`/`.obj`/`.skp`), all living in the sibling `idf_reader` ancestor codebase. None of
it is interactive, web-deliverable, or driven by simulation *outputs*. This arc builds the missing capability:
an **interactive, browser-based 3D viewer** — the OpenUBEM analogue of the Torino heat-map and the ubem.io
gallery — that lets a user open a neighbourhood, orbit/navigate it as 3D masses, click into one building to
see its windows, and **recolour the whole scene by a simulation result** (annual EUI first).

**The shape we are building (locked by the research).** A new **Step-5 post-processing exporter**, pure
Python, that turns each simulated neighbourhood (per-building IDF geometry + `05_results.*` attributes +
provenance fields) into a **self-contained single HTML file** at `openubem/outputs/<run_id>_viewer.html`,
opened by double-click with no server, no paid tiles, no internet. Inside it: a **frozen, vendored three.js
shell** renders a **CityJSON** scene with two levels of detail —

- **LOD-N (neighbourhood):** surfaces/masses only (walls + roofs, no windows) — for 3D navigation.
- **LOD-B (building):** surfaces + sub-surfaces (windows/doors) — revealed on click-to-drill-down.
- **LOD-Z (zone):** interior zone partitions — **conditionally available**, gated by the building's
  `zoning_strategy`; never fabricated for buildings that were not simulated with real zones.

**The two hard constraints (every task obeys both — the whole point of the arc):**

1. **Faithful-to-model.** Render *exactly* what the pipeline produced. No fabricated geometry, no interpolated
   values presented as real, no per-zone colouring the export layer doesn't carry, no "measurement" implying
   survey precision the model never had. Where an input was **imputed** or the **resolution was degraded**, the
   viewer must **visibly flag it**. A pretty view that lies about the model is a non-starter.
2. **Reproducible / self-contained / open-source.** Deterministically generatable from the Python pipeline;
   deliverable as one artifact openable offline; **no** Mapbox token, Cesium Ion, proprietary engine, or paid
   host baked into the delivered file.

**The MVP boundary (ship this, defer the rest).** MVP = the two real LODs + orbit/select/drill-down +
**one output view: per-building annual EUI, extruded to height, sequential-coloured, static/annual** + the
provenance badges + the self-contained HTML delivery + the six validation checkpoints. Explicitly **deferred**
to post-MVP: the hourly time-slider, per-surface solar heat-maps, population colouring, first-person
walkthrough, section planes, measurement, per-surface selection, the MapLibre-hybrid geo-referenced basemap,
and 3D-Tiles streaming. Each is deferred for a *reason recorded in the research* (data doesn't exist yet, or
scale doesn't require it, or it risks false precision) — not for lack of ambition.

---

## 1. High-level checklist (manager monitoring surface)

Tick as each lands. Phases are sequential; tasks inside a phase are mostly parallelizable. CP-# are the
stop-and-report gates (§7).

- [x] **Phase 0 — Foundations & de-risk spike**
  - [x] T01 Port `collect_geometry` into `openubem/viz/` as a standalone module + add stable per-surface IDs — completed 2026-07-02
  - [x] T02 Pilot spike: real neighbourhood IDF → CityJSON, measure size, confirm browser earcut load + per-surface identity — completed 2026-07-02
  - [x] **CP-0 — spike go/no-go** — ✅ MANAGER GREENLIGHT 2026-07-02 (PROCEED with CityJSON+three.js+earcut; 3 measurements all in-band; 3 judgment calls ratified — see §8 CP-0-AUDIT)
- [x] **Phase A — Geometry emitter & LOD ladder**
  - [x] T03 `cityjson_emitter.py` emitter (LOD-N + LOD-B, semantic surfaces, deterministic order) — completed 2026-07-02
  - [x] T04 Extruded-footprint LOD-0 placeholders (REQUIRED for failed/no-IDF buildings) + optional context layer — completed 2026-07-02
- [x] **Phase B — Attribute & provenance binding**
  - [x] T05 Attribute binding (EUI/end-uses/carbon/`iod` + `archetype_id`/`year_built`/`levels`) — completed 2026-07-02
  - [x] T06 Provenance binding (per-field source map + absent-field graceful degrade; population OMITTED) — completed 2026-07-02
  - [x] T07 Embedded reproducibility metadata block (commit/seed/run-id/spec-versions) — completed 2026-07-02
  - [x] **CP-1 — data layer complete** — ✅ MANAGER RATIFIED 2026-07-02 (all four assertable checkpoints PASS on the live pilot: CP-Geometry max 0.499 mm, CP-Value 0 mismatches/738, CP-Provenance 11 present/5 absent, CP-Reproducibility hash-stable; five judgment calls accepted)
- [x] **Phase C — Viewer shell, interaction, coloring**
  - [x] T08 Frozen three.js viewer shell scaffold (vendored libs, loads CityJSON, renders LOD-N) — completed 2026-07-02
  - [x] T09 MVP interaction (orbit/pan/zoom + select/highlight + click drill-down + back) — completed 2026-07-02
  - [x] T10 Coloring system (categorical + sequential, fixed domain, legend, no-data grey, imputed hatch) — completed 2026-07-02
  - [x] T11 MVP output view (per-building EUI extruded + sequential; failed = hatched, never invisible) — completed 2026-07-02
  - [x] T12 Provenance surfacing UI (mode border + trust badge + LOD-Z gate + detail pane) — completed 2026-07-02
  - [ ] **CP-2 — viewer feature-complete** — AWAITING MANAGER AUDIT; live pilot walkthrough evidence captured (CP-Value exact match 1562.8947…/1562.8947…, 0 http requests from file://, 0 console errors, 13-value node test suite green, dormant failed/no-data paths exercised via synthetic fixture)
- [x] **Phase D — Delivery & validation**
  - [x] T13 `viewer_export.py` Step-5 exporter → self-contained `<run_id>_viewer.html` — completed 2026-07-02
  - [x] T14 Six validation checkpoints as tests (Geometry/Value/Provenance/LOD/Reproducibility + a11y walkthrough) — completed 2026-07-02
  - [x] T15 LIVE_SMOKE: real Step-5 data → real viewer.html, evidence captured for manager — completed 2026-07-02
  - [ ] **CP-3 — MVP acceptance** (USER-SIGN-OFF: the viewer is faithful, reproducible, self-contained) — T13–T15 done + **MANAGER-AUDITED CLEAN 2026-07-02** (see §8 audit entry); STAGED and PARKED for manager-of-manager sign-off

---

## 2. Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** The geometry-extraction source you port lives in the
   sibling repo `C:\Users\o_iseri\Desktop\idf_reader\` — you may **read** it, but all new code lands under
   `openubem/`, and the viewer artifact lands under `openubem/outputs/`.
2. **You execute this plan; you do not rewrite it.** If a RESULT is ambiguous or contradicts the plan, STOP and
   quote the conflict. Do not propose alternative stacks/formats — the stack (three.js), format (CityJSON), and
   delivery (single-file HTML) are **already decided** (§4). Re-debating them is out of scope.
3. **No scope creep past the MVP boundary (§0).** Do not build the time-slider, population colouring,
   per-surface heat-maps, walkthrough, section planes, or the MapLibre hybrid. They are deferred *by the
   research*; adding them now violates the plan.
4. **Faithful-to-model is not optional and not a polish step.** Any task that would render geometry or a value
   the pipeline did not produce (procedural zones, interpolated colour across a gap, a measurement to mm) is a
   STOP-and-ask, not a judgment call.
5. **Default to no comments.** One short line only where the WHY is non-obvious (e.g. a determinism sort key, a
   provenance gate). No `.py` under `docs/`. Never edit `main.py` at the project root, or any OVERVIEW/DESIGN doc.
6. **Progress log is binding.** Append one §8 entry per completed task (format in §8). Git is handled
   externally — never commit or offer to.
7. **Match the model to the job.** Bulk/mechanical work (the emitter loops, the JS shell scaffold, the tests)
   is Sonnet's. The formerly-open design decisions are now all resolved in §9 (pilot cell, legend grouping,
   diverging baseline, footprint source, room_layout gate, legacy provenance) — escalate to the manager only
   a genuine faithful-to-model ambiguity or a RESULT-vs-plan conflict.

---

## 3. File layout to create

New geometry/viz package under `openubem/`, plus the frozen JS shell and its vendored libraries. **All new.**

```
openubem/
├── viz/
│   ├── __init__.py
│   ├── geometry_extract.py     # T01 — ported collect_geometry + stable per-surface IDs (standalone)
│   ├── cityjson_emitter.py     # T03 — IDF(s) → neighbourhood.city.json (LOD-N + LOD-B, semantic surfaces)
│   ├── geojson_context.py      # T04 — OSM footprints → extruded-GeoJSON LOD-0 context (labelled approx.)
│   ├── attribute_binding.py    # T05/T06 — join 05_results.* + provenance into CityObjects.attributes
│   ├── metadata_block.py       # T07 — commit/seed/run-id/spec-version provenance block
│   ├── viewer_export.py        # T13 — Step-5 post-processor: inject scene into shell → single HTML
│   └── shell/                  # the frozen, vendored three.js viewer (built ONCE, then version-pinned)
│       ├── viewer.html.template     # T08 — HTML shell with a scene-payload injection point
│       ├── viewer.js                # T08/T09/T10/T11/T12 — three.js app (bundled, vendored)
│       ├── viewer.css               # UI chrome (legend, badges, detail pane)
│       └── vendor/                  # three.min.js, OrbitControls, cityjson-threejs-loader, earcut — pinned
└── outputs/
    └── <run_id>_viewer.html    # T13 — the delivered self-contained artifact (double-click, offline)

tests/
├── test_viz_geometry_extract.py    # T01
├── test_viz_cityjson_emitter.py    # T03/T04
├── test_viz_attribute_binding.py   # T05/T06/T07
└── test_viz_validation.py          # T14 — the six checkpoints as automatable assertions
```

> **Note:** `openubem/viz/` is a new sub-package; confirm it does not collide with any existing import before
> creating it (the current package has no `viz/` — verified 2026-07-02 against the package tree).

---

## 4. Dependency decisions (pinned — do not re-debate)

| Concern | Decision | RESULT that fixed it |
|---|---|---|
| **Render stack** | **Standalone three.js** (MIT), vendored offline. MapLibre+three.js hybrid is a *documented future fallback* only, for a geo-referenced basemap — **not** built in the MVP. | V06 §2.1–2.3 |
| **Do-not-use** | Mapbox GL JS (proprietary/token), CesiumJS-as-primary (heavy + Ion coupling), any game engine (WASM bloat, no headless Python build). | V06 §2.3 |
| **Interchange format** | **CityJSON v2.0** as primary (lossless polygons, native dual-LOD via `"lod"`, native attributes, first-class `Window`/`Door` semantic surfaces). Emit with stdlib `json` (optionally `cjio` for validation). | V03 Part C §1 |
| **Context layer** | **Extruded GeoJSON** from OSM footprints, **LOD-0 approximation only**, clearly labelled in-UI, never where fidelity is claimed. Optional; MVP can ship without it. | V03 Part C §2 |
| **Browser geometry loader** | `cityjson-threejs-loader` + `earcut` (triangulation happens **in the browser at load**, source polygons stay lossless in the file). Vendored. | V03 Part C caveat; V08 T3 Q3 |
| **Python geometry libs** | none heavy — CityJSON is plain JSON. Reuse the **ported `collect_geometry`** for extraction; port `idf_to_collada._triangulate` **only if** a server-side triangulation is ever needed (not needed for CityJSON emit). | V15 Part C §2 |
| **Attribute binding** | CityJSON `CityObjects[<osm_id>].attributes` (per-building) + semantic-surface properties (per-surface); provenance as `provenance_<field>`/`confidence_<field>` siblings + `data_quality_flag`. `osm_id` is the stable object key. | V05 Part C §1 |
| **LOD switching** | **Discrete swap** (pre-built LOD-N + LOD-B geometry per building in one `.city.json`; client filters on `"lod"`). No tile streaming in MVP. | V04 Table 3, Part C §1 |
| **Delivery** | **Self-contained single HTML** at `openubem/outputs/<run_id>_viewer.html`. Frozen JS shell built once + vendored; per-run pipeline stays **pure Python** injecting data only. | V13 Part C |
| **Colormaps** | EUI/sequential → **viridis** (default) / **cividis** (CVD swap); categorical/archetype → **Okabe-Ito** (≤8) ; diverging (only w/ real baseline) → **PRGn/PuOr**, never RdBu. Quantile (~5) default + **unclassed continuous toggle**. Fixed/pinned domain per attribute. | V09 Part C |
| **Population** | **OMITTED from MVP** — OpenUBEM stores no per-building population; do not synthesize one. New data dependency, deferred. | V05 Part C §2 |
| **Per-surface solar** | **OMITTED** — not requested by any `Output:Variable` today; painting it would fabricate detail. | V11 Table 1, "do-not-paint" list |

---

## 5. Source-of-truth verified facts (cited, so the executor does not re-derive)

**Geometry & reuse (V15, verified against `idf_reader` code 2026-07-02):**
- `collect_geometry` lives **inside** `idf_reader/idf_to_sketchup.py:726-1069` (not a standalone module); it is
  imported by `idf_to_collada.py:34` and `idf_to_obj.py:28`. It returns a dict `faces:[(building_key, zone_name,
  category, verts)]`, `subwin:[...]`, `shade_faces:[...]`, `counts`. **It already** honours
  `GlobalGeometryRules` relative/absolute coords + per-zone origins, separates opaque `faces` from `subwin`
  (the exact LOD-N vs LOD-B split), groups by building+zone, and carries hard-won fixes (neighbour-aware window
  push-out clamp; merged-neighbourhood sub-surface repair).
- **Gap to close in T01:** it **discards the per-surface EnergyPlus name** (`surf_name` is read at
  `idf_to_sketchup.py:953` but not retained in the tuple). Add it as a 5th tuple element → the stable
  per-surface feature ID for V05 binding. Also: it returns Python tuples (fine for CityJSON vertex lists).
- The per-category colour convention is **triplicated with drift** (window α 0.70 in
  `visualizer_adapter._WIN_ALPHA` vs 0.55 in `idf_to_sketchup._MATERIALS`). Consolidate to **one** source of
  truth in `openubem/viz/` and re-validate CVD-safety (T10). Seed hexes: wall `#d4a574`, roof `#8b5e3c`, floor
  `#c0c0c0`, window `#5dade2`, shading `#a7f3d0` α0.40.
- Matplotlib painter's-order/z-fight workarounds are **matplotlib-only** — do NOT port them; WebGL depth-buffer
  handles transparency natively.

**Outputs available to colour (V11 + V05, verified against `openubem/results/` AND against the real pinned-pilot
`05_results.csv` header 2026-07-02):**
- **There is no `eui_summary.json`.** Real Step-5 exports: per-building `05_results.gpkg`/`.geojson`/`.csv`
  (written by `aggregator.py::export_results` at `aggregator.py:194`, columns = `_STEP5_COLS` at
  `aggregator.py:18-48`) + `05_neighbourhood_summary.json`.
- **EUI field = `total_eui_kwh_m2`** + **11 sub-EUI end-use cols** (not 8): 4 core (`heating`/`cooling`/
  `lighting`/`equipment`) + 7 Phase-E service (`fans`/`pumps`/`dhw_gas`/`dhw_elec`/`dhw`/`cooking`/
  `refrigeration`), all `*_eui_kwh_m2`. Carbon = 9 end-use `gwp_*_kgco2_m2` + `gwp_total_kgco2_m2`. Comfort =
  per-building **`iod`** column in `05_results.*` (`mean_iod_c`/`p95_iod_c` are *neighbourhood-level*, in the
  summary JSON only — do not look for them per building). All **per-building, annual**.
- **Actual `05_results.csv` header (pilot, verified):** `osm_id, footprint_area_m2, levels, height_m,
  archetype_id, zoning_strategy, data_quality_flag, <12 EUI cols>, <10 GWP cols>, iod, simulation_status,
  error_summary, centroid_lon, centroid_lat`. Note the real names: **`archetype_id`** (not `archetype`),
  **`levels`** (not `num_floors`). **`year_built` is NOT in `05_results.*`** — it lives in the per-run
  `01_buildings.gpkg` (join by `osm_id`). `05_results.*` contains **success rows only** (pilot: 738/738
  `simulation_status == "success"`) — failed/skipped buildings are entirely absent, not present-with-status.
- Hourly (8760) exists **only when `trim_hourly=False`** for that run — must be read from run metadata before
  any slider is offered. (Deferred anyway.) End-uses/carbon/IOD are all **building-aggregate in every
  resolution mode** — the export carries **no per-zone attribute breakdown**; do not paint per-zone values.
- **MVP output = `total_eui_kwh_m2`**, extruded to real height, sequential-coloured, static/annual — it already
  exists end-to-end and is a 3D upgrade of the shipped 2D `visualization.py::plot_eui_choropleth` (whose
  "failed buildings hatched grey, never invisible" convention we carry forward).

**Provenance fields to render (V14 + V05, re-verified in code AND against the pinned pilot's real artifacts
2026-07-02):**
- `resolution_mode` ∈ {`building`,`floor`,`fast_zone`,`zone`,`auto`} — **`zone` IS now implemented**
  (`zoning.py:23-31`, post-layoutgenerator-arc): units+corridor archetypes get `room_layout`, all others
  degrade to `perimeter_core`; requesting `zone` never raises. (The earlier "`zone` raises
  `NotImplementedError`" research claim is **stale** — superseded by code.)
- `zoning_strategy` ∈ {`single_zone`, `one_zone_per_floor`, `perimeter_core`, **`room_layout`**} — the 4th
  value is new (`zoning.py:83-96`); `num_zones` — all per-building.
- `mean_imputation_confidence` (float; HIGH=1.0/MED=0.5/LOW=0.1, observed=1.0) + `imputed_fields_count` (int)
  + `data_quality_flag` (`|`-joined tokens, `_FLAG_SEP="|"`) — computed by
  `provenance.py::add_lineage_summary` (`provenance.py:175-181`, wired at `semantic/__init__.py:427-430`);
  spec at `PLAN_input_imputation_implementation.md:309-322`.
- `archetype_confidence` ∈ {HIGH,MEDIUM,LOW} + `archetype_source` (rule token) — from
  `building_classifier.py::_assign_confidence` (`:337`), schema-gated at `:483-508`.
- `generation_status` ∈ {`success`, `skipped_invalid_geometry`, `failed_interzone_vertex_mismatch`,
  `failed_no_extruded_zones`, `failed_worker_exception`} — `builder.py:387-537`, consumed by
  `parallel.py:41-42`. Buildings absent from `05_results.*` **never ran** → render hatched no-data, never dropped.
- **Trust badge = the *lower* of** `mean_imputation_confidence` and `archetype_confidence` (a LOW archetype
  guess must dominate even with fully-observed inputs). V14 Part C §1. **If either side is absent from the
  run's artifacts (see availability map below), the badge shows a distinct "not recorded" state — never a
  defaulted min().**

**Where each field actually lives — per-run artifact source map (verified on the pinned pilot 2026-07-02):**

| Field(s) | Source file (per run) | In pinned phaseE pilot? |
|---|---|---|
| values (EUI/GWP/`iod`) + `footprint_area_m2`/`levels`/`height_m`/`archetype_id`/`zoning_strategy`/`data_quality_flag` | `05_results.csv/.gpkg/.geojson` | ✅ |
| `year_built`, footprint geometry, per-field `provenance_*` cols (`provenance_levels`, `provenance_height_m`, `provenance_year_built`, …) | `01_buildings.gpkg` | ✅ |
| `generation_status`, `zoning_strategy`, `num_zones`, `idf_path` | `step3/03_idf_manifest.parquet` | ✅ |
| `resolution_mode` | Step-3 manifest rows (`builder.py:526`) — **newer runs only** | ❌ (pre-resolution-switch run; column absent) |
| `archetype_confidence`, `archetype_source` | Step-2 enriched gdf — **not persisted** in phaseE artifacts | ❌ |
| `mean_imputation_confidence`, `imputed_fields_count` | imputation-arc lineage summary — **newer runs only** | ❌ (run predates the arc) |

**Binding graceful-degrade rule (faithful-to-model applied to provenance itself):** a provenance field absent
from the source run's artifacts is **omitted** from the CityObject attributes (never defaulted, never inferred
— e.g. do NOT write `resolution_mode="auto"` just because that was the era's implicit default), the metadata
block records it in a `provenance_coverage` list (T07), and the viewer badge shows "not recorded" (T12).

**LOD-Z gate (V04 — Rule V04-RMG-01, binding, extended by manager ruling §9.6):**
- LOD-N = CityGML **LOD1**; LOD-B = CityGML **LOD3**; LOD-Z ≈ **LOD4**. LOD-Z is fully offerable when
  `zoning_strategy ∈ {"perimeter_core", "room_layout"}` (room_layout carries *real room-level* zone geometry —
  §9.6); **`one_zone_per_floor`** → per-floor fills only, no core/perimeter;
  **`single_zone`** → refuse all interior subdivision, show disclosure badge. **Procedural synthesis of zone
  boundaries in the viewer is strictly prohibited.** Only ~5.8% (470/8,152) of the current AUTO fleet qualifies
  for LOD-Z — the rest correctly show the disclosure badge.

**Determinism & reproducibility (V14 + V13):**
- Upstream is already deterministic (`np.random.default_rng(config.RANDOM_SEED)`, default 42; E+ deterministic
  given IDF+EPW+version). The **export is a new code path** and must be made deterministic: **fixed iteration
  order (sort by `osm_id`)**, and **no wall-clock timestamp inside the content-hashed region** (timestamp lives
  in a separate un-hashed metadata field). Embedded metadata block: git commit hash, `RANDOM_SEED`, run id,
  per-mode building-count summary, `viewer_spec_version` + `lod_spec_version`, source-table refs.

**Interaction MVP (V08):** orbit/pan/zoom (`OrbitControls`) + `Raycaster` select/highlight + **click-driven**
drill-down (bundled with select — one click loads LOD-B, hides LOD-N for that building) + explicit
"back-to-neighbourhood". Drill-down trigger is a **click**, not a zoom threshold. Everything else deferred.

---

## 6. Task list

Each task: **What / Why / How / How to test.** Executor appends a §8 progress-log entry per completed task.

### Phase 0 — Foundations & de-risk spike

---

**T01 — Port `collect_geometry` into a standalone `openubem/viz/geometry_extract.py` + add stable per-surface IDs**
- **What.** Lift the geometry-extraction logic (`collect_geometry` and the low-level IDF-vertex parsers it
  depends on) out of `idf_reader/idf_to_sketchup.py` into a new standalone module `openubem/viz/geometry_extract.py`.
  Preserve behaviour exactly, then make **one** additive change: retain the per-surface EnergyPlus name as a
  stable feature ID on every face/sub-surface record.
- **Why.** V15 Part C §2 names `collect_geometry` the single most valuable reuse asset (honours
  `GlobalGeometryRules` + zone origins, separates surfaces from sub-surfaces = the LOD split, carries
  production correctness fixes), and V15 Discrepancy #1 says to extract it to a standalone module **before**
  adding a 4th consumer. The per-surface ID is required for V05 attribute binding and V08 per-surface picking.
- **How.** Copy `collect_geometry` (`idf_to_sketchup.py:726-1069`) and its imported parsing helpers from
  `visualizer_adapter.py` (`_parse_bsd_vertices`, `_parse_fen_vertices`, `_parse_window_relative`,
  `_parse_shading_vertices`, `_bsd_offsets`, `_is_relative_coords`, `_build_zone_origins`). Append `surf_name`
  (available at `idf_to_sketchup.py:953`) as a 5th element of each `faces`/`subwin` tuple. **Do not** port the
  matplotlib painter's-order workarounds or the SketchUp Ruby emitter. Keep the neighbour-aware window
  push-out clamp and the merged-neighbourhood sub-surface repair. Keep the recentring behaviour **but** record
  the discarded XY offset (needed later for V07 geo-referencing — store it, don't apply it) — flag as a note,
  not a feature, for MVP.
- **How to test.** `tests/test_viz_geometry_extract.py`: on a fixture IDF (reuse an existing `tests/` IDF
  fixture or a small DOE prototype), assert (a) `faces` and `subwin` are non-empty and disjoint; (b) every
  record carries a non-empty `surf_name`; (c) surface + sub-surface **counts** match the source IDF's
  `BuildingSurface:Detailed` / `FenestrationSurface:Detailed` object counts; (d) relative-coord and per-zone-
  origin handling reproduces the same vertices as `visualizer_adapter` for one known surface (golden values).

---

**T02 — Pilot spike: real neighbourhood IDF set → CityJSON → browser load (de-risk the 3 flagged GAPs)**
- **What.** A throwaway spike (kept under `openubem/viz/` behind a `_spike_` prefix or in a scratch script) that
  takes **one real OpenUBEM neighbourhood's** per-building IDFs, emits a minimal CityJSON (geometry only, both
  LODs, no attributes yet), and loads it in a browser via `cityjson-threejs-loader`. Measure and record:
  (1) `.city.json` file size for a real neighbourhood; (2) client-side earcut load time; (3) whether per-surface
  identity survives the loader (does a wall stay individually pickable, or are all walls merged into one mesh?).
- **Why.** Three research GAPs must be closed **before** committing to the full emitter build: V03 flagged "no
  published IDF→CityJSON neighbourhood size benchmark" (Low confidence); V08 T3 Q3 flagged per-surface identity
  through the loader as unconfirmed; V04 flagged client-side triangulation performance as untested at
  neighbourhood scale. Cheaper to learn now than after T03–T12.
- **How.** Pilot cell = `nyc_centre`, pinned (§9.1); its 738 per-building IDFs live at
  `%LOCALAPPDATA%\Temp\ubem_validation\phaseE\nyc_centre\step3\idfs\` (verified present 2026-07-02; paths in
  `step3/03_idf_manifest.parquet`). **First action of T02: archive that IDF set + the `03_idf_manifest.parquet`
  as a zip next to the durable validation results**
  (`docs/docs_VALIDATION/validations/overAll/results/phaseE/nyc_centre/`) — it sits in a Temp directory and a
  cleanup would delete the only local copy (zip = one file, no `.py`-under-`docs` violation). Then loop the
  ported `geometry_extract` over the IDFs, hand-assemble a CityJSON dict (LOD1 = walls+roof, LOD3 = +windows),
  write one `.city.json`. Open the stock `cityjson-threejs-loader` example pointed at the file (no bespoke UI).
  Record the three numbers in the progress log.
- **How to test.** Not a unit test — a measured spike. **Pass bar:** the neighbourhood loads and orbits at
  interactive frame-rate in a desktop browser, file size is within the single-file-HTML ceiling (V13: comfortable
  ≤ low-tens of MB, warning > 100 MB), and per-surface picking either works or the merging behaviour is
  documented so T09/T10 can plan around it. **This is CP-0's evidence.**

> **CP-0 — spike go/no-go.** STOP. Report the three measurements + a recommendation: proceed with
> CityJSON+three.js as planned, or escalate a format/loader concern to the manager. Do not start T03 until the
> manager greenlights.

### Phase A — Geometry emitter & LOD ladder

---

**T03 — `cityjson_emitter.py`: neighbourhood IDFs → one `.city.json` with LOD-N + LOD-B**
- **What.** The production emitter. For a neighbourhood, loop over per-building IDFs via `geometry_extract`,
  build a single CityJSON v2.0 dict: one `Building` CityObject per building (keyed by `osm_id`), each with two
  geometry entries — `"lod": "1"` (walls + roof only) and `"lod": "3"` (walls + roof + `Window`/`Door` semantic
  surfaces). Deterministic: sort buildings by `osm_id`, sort surfaces within a building by `surf_name`. Write
  `neighbourhood.city.json` (attributes added in T05/T06, not here).
- **Why.** V03 Part C §1 (CityJSON primary, native dual-LOD in one file) + V04 Part C §1 (LOD-N=LOD1,
  LOD-B=LOD3, discrete swap) + V14 Table 2 (deterministic iteration order for reproducibility).
- **How.** Use stdlib `json` (V03: emitter is ~20–50 lines of dict construction; `cjio` optional for
  validation only). Windows/doors → first-class `"Window"`/`"Door"` semantic surface types nested under their
  parent `WallSurface` (V03 Table 2). **No triangulation at emit time** — store exact polygon vertex lists;
  the browser earcut-triangulates on load. Preserve `surf_name` as the CityObject/surface identity. One
  CityObject per building, `"children"` per zone where zones exist.
- **Positioning — MANAGER RULING 2026-07-02 (Option A, true relative frame).** All buildings share ONE
  neighbourhood coordinate frame (a standards-valid CityJSON city model — NOT 738 masses stacked at the
  origin). Coordinate chain (verified in code): call `geometry_extract.collect_geometry(recentre=False)` so
  each building's vertices are the exact builder-local frame `IDF = UTM − footprint_centroid` (footprint.py:53
  `translate_to_origin`, and that centroid IS the `01_buildings.gpkg` polygon centroid — exact inverse, no
  live OSM). **Force `recentre=False`** — do not trust T01's conditional recentre to be zero. Then emit each
  vertex as `IDF + footprint_centroid_UTM − common_origin`, Z untouched. `footprint_centroid_UTM` is read per
  building from the archived `01_buildings.gpkg`. `common_origin = (floor(min cx), floor(min cy), 0)` over ALL
  footprint centroids, computed deterministically (buildings land in small, WebGL-float32-friendly metres).
  Record CRS `EPSG:32618` in `metadata.referenceSystem`; store `common_origin` in the T07 metadata block and
  each building's `footprint_centroid_UTM` as a CityObject attribute — so V07 absolute geo-ref recovers exactly
  as `UTM = vertex + common_origin` (relative positioning is in-MVP; absolute lat/lon geo-referencing stays
  V07/post-MVP). Z-up throughout (matches source).
- **How to test.** `tests/test_viz_cityjson_emitter.py`: (a) emitted JSON validates as CityJSON v2.0 (via `cjio`
  or a schema check); (b) each building has both a `"lod":"1"` and a `"lod":"3"` geometry; (c) LOD-1 geometry
  contains **zero** `Window`/`Door` surfaces, LOD-3 contains them; (d) **byte-identical** output on two runs
  over the same input (determinism); (e) vertex round-trip **through the stored offsets** (per Option A
  positioning) — for a sampled surface, `(CityJSON_vertex + common_origin) − building.footprint_centroid_UTM`
  equals the source IDF (`recentre=False`) vertex within ≤1 cm. This is the exact faithfulness assertion (T14
  CP-Geometry); it proves the emitter applied only a known rigid translation, no geometry corruption.

---

**T04 — `geojson_context.py`: extruded-footprint LOD-0 placeholders (REQUIRED for failed/absent buildings; full-cell context layer optional)**
- **What.** Emit a lightweight `FeatureCollection` from the per-run **footprints** (not IDF geometry): one
  `Feature` per building, `properties.height = levels × 3.5 m`, `properties.osm_id`, tagged
  `is_approximation: true`. Two uses: (a) **required** — hatched placeholder geometry for buildings that have
  **no IDF** (generation failed/skipped) or no results row, so the "never invisible" convention (T11) is
  satisfiable at all; (b) *optional* — a full-cell zoomed-out navigational scaffold.
- **Why.** V03 Part C §2 (LOD-0 footprint background) **plus a structural necessity found 2026-07-02:** the
  CityJSON emitter (T03) loops over IDFs, and a failed-generation building **has no IDF** — without a
  footprint-sourced placeholder there is literally no geometry to hatch, and the carried-forward
  `plot_eui_choropleth` convention ("failed = hatched grey, never invisible") would be silently violated.
  **Explicitly a non-faithful approximation:** must be visibly labelled in-UI and must never be shown where IDF
  fidelity is claimed (the moment a building is selected or a heat-map is on, CityJSON geometry is used).
- **How.** Footprint source **confirmed and pinned (§9.5): the per-run `01_buildings.gpkg`** (has geometry,
  `levels`, `osm_id`, and real UTM coords) — do NOT re-fetch from live OSM (network rule + the run's snapshot
  is the faithful source). Failed/absent set = `01_buildings` osm_ids minus the T03 CityJSON osm_ids. Trivial
  `json` emission. The optional full-cell scaffold is built only if T02 shows the full CityJSON is too heavy to
  show all masses at once.
- **How to test.** `tests/test_viz_cityjson_emitter.py` (shared file): placeholder feature set == (buildings in
  `01_buildings.gpkg`) − (buildings with IDF geometry), exercised with a synthetic fixture where one building
  lacks an IDF (the pilot has zero failures — 738/738 success — so the live path won't exercise this); every
  feature carries `height` and `osm_id`; the layer is tagged `is_approximation: true` and the UI renders the
  "LOD-0 context, not model geometry" label.

### Phase B — Attribute & provenance binding

---

**T05 — `attribute_binding.py`: bind simulation outputs + building attributes into CityObjects**
- **What.** Join the Step-5 result tables and building attributes onto the CityJSON objects by `osm_id`, writing
  them into `CityObjects[<osm_id>].attributes`: `total_eui_kwh_m2`, the **11** sub-EUI end-uses, the 9 per-end-use
  `gwp_*_kgco2_m2` + `gwp_total_kgco2_m2`, per-building `iod`, and `archetype_id`/`levels`/`height_m`/
  `footprint_area_m2` (from `05_results.*`) + `year_built` (joined from the per-run `01_buildings.gpkg` — it is
  **not** in `05_results.*`; see §5 source map).
- **Why.** V05 Part C §1 (CityJSON `attributes` dict is the traceable binding; raw field names unchanged) + V11
  Table 1 + the §5 verified header (real column names: `archetype_id`, `levels`, `iod` — never rename to
  `archetype`/`num_floors`). MVP colours `total_eui_kwh_m2`; the others ride along for the deferred dropdown but
  are **not** wired to colour yet.
- **How.** Read `05_results.csv`/`.geojson` (the real files — **not** `eui_summary.json`). Key join on `osm_id`.
  Store raw OpenUBEM field names verbatim as attribute keys (traceability). **Population: do not add** (V05 §2 —
  no source). **Per-surface solar: do not add** (V11 — not computed). `05_results.*` contains **success rows
  only** (§5) — buildings present in the CityJSON or `01_buildings.gpkg` but absent from `05_results.*` get
  **no** EUI attribute (they never ran) — T11/T12 render them as no-data.
- **How to test.** `tests/test_viz_attribute_binding.py`: (a) for every building in `05_results.csv`, its
  `total_eui_kwh_m2` in the CityJSON equals the CSV cell exactly (float-tolerance) — this **is** T14 CP-Value;
  (b) no `population` key exists anywhere; (c) a building absent from the results table has no EUI attribute and
  is not dropped from the CityJSON.

---

**T06 — Provenance binding: mode, trust confidence, generation status → attributes**
- **What.** Add the provenance fields to each CityObject's `attributes`, in the **same attribute table** as the
  values (never a side-channel): `resolution_mode`, `zoning_strategy`, `num_zones`, `mean_imputation_confidence`,
  `imputed_fields_count`, `archetype_confidence`, `archetype_source`, `data_quality_flag` (raw `|`-joined),
  `generation_status`, and a derived `trust_confidence = min(mean_imputation_confidence, confidence_rank(archetype_confidence))`.
- **Why.** V14 Part C §1 (two badges + border, all bound to already-existing fields; the trust badge takes the
  *lower* of imputation and archetype confidence; provenance MUST ride the same binding as values or they drift
  silently) + V05 Part C §3 (field-level provenance siblings + row-level `data_quality_flag`).
- **How.** Read each field from its pinned source file per the **§5 source map**: `zoning_strategy`/`num_zones`/
  `generation_status` ← `step3/03_idf_manifest.parquet`; `data_quality_flag` ← `05_results.*`; per-field
  `provenance_*` cols ← `01_buildings.gpkg`; `resolution_mode` / `archetype_confidence` / `archetype_source` /
  `mean_imputation_confidence` / `imputed_fields_count` ← manifest / enriched-gdf columns **where the run's
  artifacts carry them**. Store **raw tokens verbatim** — never re-worded, never defaulted, never approximated
  by the export (V14 CP-Provenance). **Graceful degrade is binding (§5):** a field absent from the run's
  artifacts is omitted + listed in the metadata `provenance_coverage` (T07) — the pinned phaseE pilot lacks
  `resolution_mode`, `archetype_confidence`/`archetype_source`, and both imputation-lineage fields, so this
  path runs live from day one, it is not an edge case. `trust_confidence` maps `HIGH→1.0 / MEDIUM→0.5 /
  LOW→0.1` for the archetype side, then takes the min with the float imputation confidence; **if either side is
  absent, `trust_confidence` is omitted** (T12 shows "not recorded"), never computed one-sided.
  *Optional (manager-approved) backfill for the pilot:* `archetype_confidence`/`archetype_source` may be
  regenerated by re-running the Step-2 classifier offline on the archived `01_buildings.gpkg` (deterministic,
  no network, no simulation) — but **only** usable where the regenerated `archetype_id` equals the manifest's
  `archetype_id` for that building (the classifier changed post-run, E-R3-3); on mismatch, treat as absent.
- **How to test.** `tests/test_viz_attribute_binding.py`: (a) every provenance field **present in the source
  artifacts** round-trips exactly (T14 CP-Provenance, 100% coverage of available fields); (b) negative case — a
  zero-imputation, HIGH-archetype building shows `trust_confidence == 1.0` and an empty/`observed`
  `data_quality_flag`, never ambiguous; (c) a `generation_status != "success"` building keeps its literal
  status string (synthetic fixture — the pilot has none); (d) absent-field case — a source table missing
  `resolution_mode` yields CityObjects with **no** `resolution_mode` key and a `provenance_coverage` entry,
  never a default value.

---

**T07 — `metadata_block.py`: embedded reproducibility metadata**
- **What.** Build the CityJSON `metadata` block: git commit hash of the OpenUBEM checkout, `config.RANDOM_SEED`
  (=42, `config.py:52`), pipeline run id, per-`resolution_mode` building-count summary (or per-`zoning_strategy`
  when `resolution_mode` is not recorded — §5), a **`provenance_coverage`** list naming which provenance fields
  the run's artifacts carried vs. lacked (feeds T06/T12 graceful degrade), `viewer_spec_version` +
  `lod_spec_version` strings, and references to the source `05_results.*` / manifest files. The build timestamp
  goes in a **separate, un-hashed** field.
- **Why.** V14 Table 2 + Part C §2 — makes the artifact self-describing and content-addressable; the timestamp
  must be outside the hashed region or byte-identity breaks. FAIR Reusable principle applied to a generated
  artifact.
- **How.** Read commit hash via a lightweight subprocess `git rev-parse HEAD` (read-only; not a commit).
  `viewer_spec_version`/`lod_spec_version` are literal constants bumped by hand when T10's colour spec or T03's
  LOD ladder changes. Place in CityJSON `metadata`.
- **How to test.** `tests/test_viz_attribute_binding.py`: (a) the block carries all seven required keys
  (commit, seed, run id, count summary, `provenance_coverage`, spec versions, source refs); (b) two
  builds over the same pipeline state produce byte-identical **content hashes** when the timestamp field is
  excluded (T14 CP-Reproducibility); (c) the timestamp field is not inside the hashed region.

> **CP-1 — data layer complete.** STOP. The `.city.json` now carries faithful geometry (both LODs) + all value
> attributes + all provenance fields + the metadata block, all deterministic. Report: the CP-Geometry,
> CP-Value, CP-Provenance, CP-Reproducibility test results (four of the six checkpoints are already assertable
> here, before any browser code). Manager audits faithfulness before Phase C.

### Phase C — Viewer shell, interaction, coloring

---

**T08 — Frozen three.js viewer shell scaffold**
- **What.** The vendored, offline browser app skeleton: `viewer.html.template` + `viewer.js` + `viewer.css` +
  `vendor/` (three.min.js, OrbitControls, cityjson-threejs-loader, earcut — all pinned). It loads an injected
  CityJSON payload and renders **LOD-N** (masses) with a default camera framed on the neighbourhood centroid.
- **Why.** V06 §2.1 (standalone three.js, 100% offline, glTF/CityJSON handoff) + V13 Part C (frozen shell built
  once, vendored, version-pinned; per-run pipeline injects data only, stays pure Python).
- **How.** Build the JS bundle **once** as a developer step (esbuild/Vite — a one-time dev dependency, NOT a
  per-run pipeline dependency), then commit the vendored output. The template has a single scene-payload
  injection point (a `<script>` slot) that T13 fills. Render LOD-N by filtering the loaded CityJSON on
  `"lod":"1"`. Apply data colour as **unlit/emissive/vertex-colour** material, not lit PBR (V09 Table 3 — so
  lighting doesn't distort encoded values). Add a simple in-scene North compass + metre scale bar (V06 §2.4 —
  standalone three.js has no map grid).
- **How to test.** Manual: open `viewer.html.template` with a T02 sample payload inlined; the neighbourhood
  renders as masses, orbits smoothly, no console errors, loads from `file://` with no network requests
  (check the browser network tab is empty — the self-contained constraint).

---

**T09 — MVP interaction: orbit / select / drill-down / back**
- **What.** Wire the four MVP interactions: `OrbitControls` (target = neighbourhood centroid, clamped
  min/max distance); `Raycaster` click-select with an emissive/outline highlight; **click-driven drill-down**
  (on select, reveal the building's LOD-B geometry and hide its LOD-N mass — the discrete swap); explicit
  "back to neighbourhood" button/Esc that reverses the swap and re-frames the camera.
- **Why.** V08 Part C §1–§2 (this is the field's minimum bar — ubem.io/CEA ship exactly this set; drill-down
  is a **click**, not a zoom threshold, because our LOD is discrete-swap not tile-streamed; select and
  drill-down are **bundled** into one click per V04 §4).
- **How.** `raycaster.intersectObjects(buildingGroups, true)` on click. Selection + drill-down are the same
  action. LOD-B geometry is already in the loaded CityJSON (`"lod":"3"`) — the "swap" is a visibility toggle,
  not a fetch (single-file build has everything resident). Back = restore LOD-N visibility, unload/hide LOD-B,
  recentre `OrbitControls.target`. **Defer** walkthrough, isolate-as-separate-action, section planes,
  measurement, per-surface selection (V08 deferred list — false-precision + low-value + unconfirmed-granularity
  reasons).
- **How to test.** Manual walkthrough on a T02 sample: click a building → it highlights and shows windows while
  its neighbours stay as masses; back → returns to all-masses; picking stays responsive across the pilot
  neighbourhood's full building count (T02's picking measurement is the evidence).

---

**T10 — Coloring system: categorical + sequential, fixed domain, legend, no-data, imputed hatch**
- **What.** The data-driven recolouring engine + legend. Categorical (archetype → Okabe-Ito, ≤8, discrete
  swatch legend of archetypes present); sequential (EUI → viridis default / cividis CVD-toggle, **quantile ~5
  classes** default + **unclassed-continuous toggle**, continuous colour-bar with break ticks + a mini
  histogram legend). **Fixed/pinned domain per attribute** (never silently rescale to the in-view subset).
  Reserve **one neutral light-grey** for no-data (kept off the ramp); render imputed/low-confidence buildings
  with a **hatch/outline overlay on top of their true colour**, never a flat grey swap.
- **Why.** V09 Part C §1–§3 (the full coloring spec: families, classification, fixed domain, no-data grey,
  imputed-hatch = the coloring-side of faithful-to-model) + V14 Table 3 (non-colour-only: every colour value
  also has a tooltip/label).
- **How.** Consolidate the triplicated colour dicts (§5) into one module-level palette in `viewer.js`; seed
  categorical defaults from the existing hexes, then **verify CVD-safety** (fail → Okabe-Ito). **Categorical
  archetype legend: the vocab is 30 (§9.3) — exceeds the 8-colour ceiling — so group archetypes into sector
  hue-families (Office / Education / Lodging / Residential / Retail / Healthcare / Food-service / Warehouse / …)
  with text labels; never rely on colour alone. Show one labelled swatch per archetype present in the current
  scene.** Quantile breaks computed **once from the full neighbourhood**, pinned, and shown in the legend (never
  recomputed per camera move). Continuous toggle = unclassed ramp. Diverging (PRGn/PuOr) is scaffolded but only
  used if a real-baseline attribute is added later (baseline = archetype-cohort median, §9.4) — **not** for
  plain EUI magnitude.
- **How to test.** Manual + a small unit check on the classification function: quantile breaks are stable across
  runs (determinism); no-data grey is distinct from the palest ramp colour; every coloured building exposes its
  numeric value in a tooltip (non-colour-only). CVD check via a simulator over the shipped palette (T14
  CP-Accessibility, manual).

---

**T11 — MVP output view: per-building EUI extruded + sequential-coloured**
- **What.** The headline deliverable: colour every building by `total_eui_kwh_m2` on the sequential scale
  (T10), buildings extruded to their real height (they already are — it's real geometry). Static/annual, no
  slider. Buildings with `generation_status != "success"` or absent from `05_results.*` render **hatched grey,
  never invisible** (carry forward `plot_eui_choropleth`'s convention) — their geometry comes from **T04's
  extruded-footprint placeholders** (they have no IDF, so no CityJSON geometry exists), visibly tagged as
  approximation.
- **Why.** V11 Part C §2 (the single MVP output view — zero granularity risk, already exists end-to-end, a 3D
  upgrade of the shipped 2D choropleth) + V11 "do-not-paint" list (no per-zone, no per-surface, no failed-as-real).
- **How.** Bind `total_eui_kwh_m2` from the CityObject attributes to the sequential colormap; default view on
  load. Attribute selector UI may list end-uses/carbon/IOD but MVP only wires EUI to colour (others are
  deferred dropdown targets). **Do not** auto-animate; **do not** offer a slider (no hourly in MVP).
- **How to test.** Manual: the neighbourhood recolours by EUI with a correct legend; a known high-EUI building
  reads high on the ramp; a failed building is visibly hatched, not missing; the displayed value in its tooltip
  matches `05_results.csv` (T14 CP-Value, live).

---

**T12 — Provenance surfacing UI: mode border + trust badge + LOD-Z gate + detail pane**
- **What.** Render the trust affordances from the bound provenance attributes: a **resolution-mode border
  treatment** on footprints at LOD-N (thin `building` / medium `floor` / heavy `fast_zone`/`zone`; **no border
  + "not recorded" hover text when `resolution_mode` is absent** — legacy runs, §5) + a text badge on
  hover/select; a **merged trust badge** (shape glyph — solid/half/hollow for HIGH/MED/LOW `trust_confidence`,
  plus a distinct **"not recorded"** state when the field is absent — not colour-only); **no-data hatch** for
  failed/absent buildings; a **detail pane** on select listing raw `data_quality_flag` tokens +
  `archetype_source` + `imputed_fields_count` verbatim (absent fields shown as "not recorded", never blank);
  and the **LOD-Z gate (Rule V04-RMG-01 + §9.6)** — the "Zone breakdown" control is enabled for
  `perimeter_core` **and `room_layout`**, "Floor-level" for `one_zone_per_floor`, and
  disabled-with-disclosure for `single_zone`.
- **Why.** V14 Part C §1 + V04 Rule V04-RMG-01 (both binding). This is the faithful-to-model constraint made
  visible — and V14 flags it as **novel UX** (no UBEM peer ships per-building provenance), so budget design
  care here.
- **How.** All fields already resident in the CityObject attributes (T06). Badges use shape/fill, never hue
  alone (WCAG non-colour-only; keeps clear of T10's data colours). Detail pane shows literal tokens — no
  re-interpretation. LOD-Z gate reads `zoning_strategy` before enabling any interior view; **procedural zone
  synthesis is prohibited** — if no real zone geometry exists, the control is disabled, full stop.
- **How to test.** Manual: a `single_zone` building shows the disclosure badge and cannot open a zone view; a
  LOW-confidence building shows a half/hollow trust glyph and its raw flags in the detail pane; a failed
  building is hatched with its literal status on hover; a legacy-run building shows "not recorded" for
  `resolution_mode`/trust, never a fabricated default. Automated: the gate logic is unit-tested against all
  **four** `zoning_strategy` values (`single_zone`, `one_zone_per_floor`, `perimeter_core`, `room_layout`).

> **CP-2 — viewer feature-complete.** STOP. A faithful, interactive, EUI-coloured viewer with provenance
> surfacing now runs on the pilot neighbourhood. Report: a manager screen-share / screenshots + the CP-Value
> and CP-LOD live results. Manager audits faithfulness (does anything on screen misrepresent the model?) before
> delivery hardening.

### Phase D — Delivery & validation

---

**T13 — `viewer_export.py`: Step-5 exporter → self-contained single HTML**
- **What.** The pipeline entry point. A Step-5 post-processor (after `05_results.*` + summary exist) that calls
  the emitter + binding + metadata, then **injects** the CityJSON scene payload into the frozen shell and writes
  one self-contained file: `openubem/outputs/<run_id>_viewer.html`. Everything inlined — no runtime fetches.
- **Why.** V13 Part C (self-contained single HTML is the only delivery model matching OpenUBEM's outputs
  discipline + offline + open-source constraints; new exporter adjacent to `openubem/results/visualization.py`;
  pure-Python per run, frozen JS shell).
- **How.** Serialize the scene + attribute tables into the shell's injection slot (data-URI or inline
  `<script type="application/json">`). Inline `vendor/` JS/CSS. Deterministic serialization (sort by `osm_id`,
  stable float formatting). Write to `openubem/outputs/` (flat, per the outputs rule). Wire it as an optional
  Step-5 stage (flag-gated) so it doesn't slow every run.
- **How to test.** `tests/test_viz_validation.py`: the emitted HTML has **zero** external URLs (regex/parse
  check — the self-contained constraint); it opens from `file://` and renders (manual); two exports of the same
  run are byte-identical modulo the un-hashed timestamp (T14 CP-Reproducibility).

---

**T14 — The six validation checkpoints as automatable tests**
- **What.** Encode V14's six faithfulness checkpoints as `tests/test_viz_validation.py` (five automatable + one
  documented manual procedure): **CP-Geometry** (sampled vertex round-trip vs source IDF **through the stored
  Option-A offsets** — `(CityJSON_vertex + common_origin) − footprint_centroid_UTM == source IDF`, ≤1 cm),
  **CP-Value** (100% of displayed EUI/carbon/end-use == `05_results.csv`, float-tolerance), **CP-Provenance**
  (100% of badge-driving fields == source tables + the zero-imputation negative case), **CP-LOD** (per-mode
  sub-surface/zone count check + `single_zone`-never-shows-zones), **CP-Reproducibility** (two builds → identical
  content hash excluding timestamp). **CP-Accessibility** is a documented manual procedure (WCAG 1.4.3 4.5:1
  text / 1.4.11 3:1 non-text contrast on legend+badges; keyboard-operable chrome per 2.1.1; CVD-simulation pass
  on the shipped palette).
- **Why.** V14 Part C §4 — these six are the enforcement mechanism the faithful-to-model constraint needs; each
  is "fail = block ship."
- **How.** Reuse `visualizer_adapter`'s IDF parser (via T01's ported module) for the geometry round-trip. Diff
  against the **real** `05_results.csv`, not a cached copy. Stratify the geometry sample ≥1 building per
  (archetype × zoning_strategy) present (`resolution_mode` is absent from the pilot's artifacts — §5).
  CP-Provenance asserts 100% round-trip of the **available** fields *plus* that every absent field appears in
  `provenance_coverage` (§9.7).
- **How to test.** The tests are themselves the deliverable; CI-run them green on the pilot cell. Manual
  CP-Accessibility documented with the tool used + results.

---

**T15 — LIVE_SMOKE: full pipeline run → real viewer.html → manager opens + confirms faithful**
- **What.** Run the whole pipeline (or resume from existing Step-5 outputs) on **one real cell**, produce a real
  `openubem/outputs/<run_id>_viewer.html`, and have the manager open it and walk the CP-Accessibility + a visual
  faithfulness spot-check (one building per resolution mode: does the mass/window detail match what
  `resolution_mode` claims?).
- **Why.** [[feedback_synthetic_test_blind_spots]] — 100% synthetic-fixture green ≠ live-path green. A LIVE_SMOKE
  on real Step-5 data before CP-3 catches integration gaps (missing columns, real `osm_id` join misses, a real
  neighbourhood that's too heavy for the single-file ceiling) that fixtures hide.
- **How.** Use the pilot's already-simulated Step-5 outputs + archived IDFs (no need to re-simulate — dispatch
  a Sonnet employee for any cluster/harvest step per [[feedback_sonnet_for_cluster_harvest]]). Manager opens
  the file locally. **Expected on this legacy run (§9.7):** `resolution_mode`/trust badges read "not recorded"
  — that is correct behaviour, not a bug; verify the badges say so rather than showing defaults.
- **How to test.** The manager's sign-off **is** the test. Record: file size, load time, which cell, the
  per-mode visual spot-check result, and the CP-Accessibility outcome in the progress log.

> **CP-3 — MVP acceptance (USER-SIGN-OFF ONLY).** STOP. The viewer is faithful (six checkpoints pass),
> reproducible (byte-identical rebuild), and self-contained (offline, no external URLs). Manager-of-manager
> signs off before the arc is declared MVP-complete and before any post-MVP feature (slider, population,
> per-surface, hybrid basemap) is scoped.

---

## 7. Stop-and-report checkpoints

Four gates, at the integration points where a silent bug would compound:

- **CP-0 (after T02)** — spike go/no-go. Confirms CityJSON+three.js+earcut actually works at OpenUBEM's real
  neighbourhood size/identity **before** the emitter is built. Reports 3 measurements.
- **CP-1 (after T07)** — data layer complete. Four of the six faithfulness checkpoints (Geometry, Value,
  Provenance, Reproducibility) are already assertable on the `.city.json` **before** any browser code exists.
  Cheapest place to catch a fidelity bug.
- **CP-2 (after T12)** — viewer feature-complete. A faithful interactive EUI view with provenance runs. Manager
  eyeballs for any on-screen misrepresentation before delivery hardening.
- **CP-3 (after T15)** — MVP acceptance, **USER-SIGN-OFF ONLY**. Faithful + reproducible + self-contained,
  confirmed on live data.

---

## 8. Progress log

*(Executor appends one entry per completed task, in this format. Empty until work begins.)*

#### PLAN-REVIEW — manager audit pass against real artifacts — completed 2026-07-02
- Artifacts: this doc (corrections in place; no code touched).
- Deviations from the draft, all verified against code + the pinned pilot's real files:
  (1) §5 outputs corrected — 11 sub-EUI cols not 8; per-building IOD col is `iod`; real names `archetype_id`/`levels`; `year_built` only in `01_buildings.gpkg`; `05_results.*` = success rows only.
  (2) §5 provenance corrected — `zone` mode now implemented (stale NotImplementedError claim removed); `zoning_strategy` has a 4th value `room_layout`; added per-field artifact source map + binding graceful-degrade rule (pilot lacks `resolution_mode`, `archetype_confidence/_source`, imputation-lineage fields).
  (3) T04 upgraded from optional to required-for-failed-buildings — IDF-less buildings have no CityJSON geometry, so "hatched, never invisible" needs footprint placeholders; source pinned to archived `01_buildings.gpkg`.
  (4) T02 gains a first-action archive step — pilot IDFs live in a Temp dir.
  (5) T06/T07/T12/T14/T15 wired for provenance graceful-degrade + "not recorded" badge; T12 gate extended to `room_layout` (§9.6).
  (6) §9 gains rulings 6 (room_layout LOD-Z) and 7 (legacy provenance coverage).
- Test status: n/a (plan doc only).
- Notes: still DRAFT pending manager-of-manager sign-off; MVP scope unchanged.

```
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + RESULT cite>
- Test status: <pytest summary / manual result>
- Notes: <auditor-relevant>
```

#### T01 — Port `collect_geometry` into a standalone `openubem/viz/geometry_extract.py` + add stable per-surface IDs — completed 2026-07-02
- Artifacts: `openubem/viz/__init__.py`, `openubem/viz/geometry_extract.py` (new standalone module — `collect_geometry`, `parse_idf`, and every low-level vertex-parsing helper it needs, ported from `idf_reader/idf_to_sketchup.py:726-1069` + `idf_reader/visualizer_adapter.py`); `tests/fixtures/viz/Restaurant_QuickServiceRestaurant_90.1-2013.idf` (small real DOE-prototype fixture, copied verbatim from `docs/docs_DONE/scheduleDigitization/sources/`, 18 `BuildingSurface:Detailed` + 4 `FenestrationSurface:Detailed`, no windows/doors in the existing `tests/fixtures/sim/1zone_with_sql.idf`, which made it unusable for the "faces/subwin non-empty" assertion); `tests/test_viz_geometry_extract.py`.
- Deviations:
  1. The plan's How-section names 7 helpers to port "from `visualizer_adapter.py`" (`_bsd_offsets`, `_build_zone_origins`, `_is_relative_coords`, `_parse_bsd_vertices`, `_parse_fen_vertices`, `_parse_shading_vertices`, `_parse_window_relative`). `collect_geometry` also calls 5 more helpers that in fact live in `idf_to_sketchup.py` itself, not `visualizer_adapter.py` (`_surface_normal`, `_snap_subsurface_to_parent`, `_door_to_window_fields`, `_classify`, `_building_key`), plus `idf_parser.parse_idf` (the tokenizer). All were ported too — "preserve behaviour exactly" requires it; the plan's "How" undercounts the dependency list but does not contradict it (T01 "What" says "collect_geometry and the low-level IDF-vertex parsers it depends on", which is the broader, correct scope).
  2. `expand_multipliers` parameter dropped entirely (not ported). Source `_expand_floor_multipliers` (~300 lines, `idf_to_sketchup.py:417-720`) stacks multiplied floor bands to make every floor visually appear — a "pure visual post-process" per its own docstring, i.e. it synthesizes geometry not literally present as separate IDF surfaces. Default in source is `expand_multipliers=False`; no T01/T02 consumer needs `True`. Porting it would also cut against the plan's own faithful-to-model rule (Sec 2.4: never render geometry the pipeline did not produce) for a module whose whole purpose is feeding a faithful CityJSON emitter. Not requested by T01's How section either. Flagging for manager awareness in case a later task (T04 context layer?) turns out to need it — it does not appear to (T04 uses footprint-derived `levels x 3.5m` extrusion, not IDF floor geometry).
  3. Per-surface ID interpretation: plan text says append "`surf_name`, read at `idf_to_sketchup.py:953`" as the 5th tuple element "on every faces/subwin record". Line 953's `surf_name` is literally the *parent wall's* name. Implemented as: `faces` records get the surface's own `Name` field (matches plan literally); `subwin` records get the *sub-surface's own* `Name` field (`fen[0]`/`win[0]`/`door[0]`), not the repeated parent-wall name. Rationale: the plan's own "Why" states the ID is "required for V05 attribute binding and V08 per-surface picking" — reusing the parent wall's name for every window on that wall would make individual windows indistinguishable, defeating both stated purposes. Verified live: fixture's `Dining_Wall_East` hosts one window (`Dining_Wall_East_Window`) so this fixture alone doesn't exercise multi-window-per-wall collision, but the two-lines-different-name choice is the only one consistent with "stable **per-surface** feature ID". Flagging for manager review since it is a literal-text vs. evident-intent judgment call, not a RESULT citation.
- Test status: `pytest tests/test_viz_geometry_extract.py -v` — 4 passed (faces/subwin non-empty+disjoint; every record has non-empty `surf_name`; counts 18 faces / 4 subwin match raw IDF `BuildingSurface:Detailed`/`FenestrationSurface:Detailed` object counts exactly; golden vertex round-trip for `Dining_Wall_East` matches the raw IDF vertex block to 1e-6, confirming the ported `_parse_bsd_vertices` reproduces `visualizer_adapter`'s algorithm — zone `Dining` has a zero origin and the building never crosses the 50 m recentre threshold, so `recentre_offset == (0,0,0)` and world coords equal raw IDF coords exactly, making this a clean golden case). Full `pytest tests/ -q` run afterward to check for collisions (result below, this same log entry covers both T01 and the collision check since the plan's task list treats T01 as a single stop-tested unit).
- Notes: `openubem/viz/` did not previously exist — confirmed no import collision (per the plan's Sec 3 note). Colour/style dicts (`_MATERIALS` in the source) were intentionally NOT ported — replaced with a bare `_CATEGORY_KEYS` tuple for the `counts` dict vocabulary, since colour consolidation is explicitly T10's job (Sec 5: "Consolidate to one source of truth ... T10"). numpy confirmed present in `.venv` (2.4.4) — `_parse_window_relative`/`_surface_normal`/`_snap_subsurface_to_parent` all guard on `_HAS_NUMPY` exactly as the source does. **Addendum after T02's real-pilot run (same day): a genuine bug was found and fixed in `_parse_fen_vertices`'s fallback branch — see T02 entry below and the updated module docstring/inline comment in `geometry_extract.py`.** Full-suite `pytest tests/ -q`: 1208 passed, 12 failed, 13 skipped (915.71s). All 12 failures are in `test_outputs.py`, `test_r6_gwp_subregion.py`, `test_r6_rescore.py`, `test_results_parser.py`, `test_v19_rescore.py` — confirmed via grep that none of these files reference `openubem.viz`/`geometry_extract`, and all of them touch unrelated pre-existing arcs (R6 GWP subregion, V19 rescore, results parser) whose modified/untracked files (`openubem/config.py`, `zoning.py`, `builder.py`, `semantic/*`, `layoutGenerator.py`, etc.) predate this session per `git status`. Pre-existing failures, not caused by T01.

#### T02 — Pilot spike: real neighbourhood IDF set -> CityJSON -> browser load — completed 2026-07-02
- Artifacts: `docs/docs_VALIDATION/validations/overAll/results/phaseE/nyc_centre/nyc_centre_step3_idfs_archive.zip` (durable archive, first action of T02 — 738 IDFs + `03_idf_manifest.parquet` zipped from the Temp path, 14.1 MB, `zipfile.testzip()` clean, entry count verified 739 = 738 `.idf` + 1 manifest). All spike code/outputs are throwaway per the plan's own framing ("kept ... in a scratch script") and live outside the repo in the session scratchpad (`.../scratchpad/spike_3dviz/`: `build_cityjson.py`, `nyc_centre.city.json`, `entry.js`/`bundle.js`, `harness.html`, `run_puppeteer.js`, plus the render/screenshot variants) — confirmed via `git status` that nothing under `node_modules/`, no `.city.json`, and no bundle landed inside the OpenUBEM repo; only the T01 bug-fix diff, this doc, and the durable zip are new/changed in-repo.
- Deviations: none from the plan's T02 scope. One in-flight T01 deviation surfaced and fixed during T02 (documented in T01's addendum above and in Notes below) — cited here because T02's own measurements would have been unrepresentative (0 windows) without it.
- Test status: not a unit test (per plan, T02 is a measured spike). Evidence below.
- **Measurement 1 — file size.** 738/738 pilot buildings processed with zero failures. Raw (pre-filter) totals across the fleet: 121,720 `faces` + 66,022 `subwin` records (after the T01 fix; **0 subwin before the fix**, see Notes). Emitted `nyc_centre.city.json` (LOD "1" = wall+roof `MultiSurface`, LOD "3" = LOD-1 + window/door `MultiSurface`, geometry only, no attributes, vertices deduped by rounded-coordinate to 300,956 global vertices): **16,296,172 bytes = 15.54 MB**. Comfortably inside V13's "comfortable <= low tens of MB" band, nowhere near the 100 MB warning line — for the pilot cell, which the plan's own §9.2 table places at 738 buildings, mid-upper of the 12-cell range (4 cells exceed 1,000 and would scale roughly linearly, e.g. nyc_urban at 1,779 ~ extrapolates to ~37 MB, still comfortable).
- **Measurement 2 — client-side earcut load time.** Real headless Chromium (Puppeteer), not a Node-only proxy: `cityjson-threejs-loader`'s stock `CityJSONParser`+`CityJSONLoader` (its earcut-based triangulation path, `TriangleParser.js`) loaded the actual 15.54 MB file over `fetch()` from a local static server. `fetch`+`JSON.parse`: **~124 ms**. `CityJSONParser.parse()` (this **is** the earcut load time — triangulates all faces across both LODs into one `BufferGeometry`): **~324 ms**, yielding 404,900 triangles. Total page-ready wall time (navigation start to fully parsed): **~1.16 s**. Zero console errors from the loader/earcut path (one benign `favicon.ico` 404, isolated and confirmed unrelated). This is well inside "interactive load" territory for a 738-building neighbourhood.
- **Measurement 3 — per-surface identity through the loader.** CONFIRMED SURVIVES, via attributes rather than mesh separation. `cityjson-threejs-loader`'s default `chunkSize` is 2000 CityObjects; our 738 buildings fit in one chunk, so **all 738 buildings across both LODs collapse into a single `THREE.Mesh` (one WebGL draw call for the whole neighbourhood)** — walls do NOT stay as individually separate mesh objects. However every vertex carries `objectid` (source building), `boundaryid` (source face/surface index within that building+geometry), `geometryid`, `surfacetype`, `lodid` buffer attributes; the loader's own `CityObjectsMesh.resolveIntersectionInfo()` reads these off a `Raycaster` hit to recover exact per-building **and** per-source-surface identity. Empirically verified live: sampling the merged mesh's attributes for building `way/42496314` alone found **817 distinct `boundaryid` values** and confirmed >1 distinct `boundaryid` co-occurring with the same `objectid` (i.e., multiple individually-identifiable surfaces belonging to one building, inside the one merged mesh). **Implication for T09:** click-to-pick/highlight of an individual wall is fully supported, implemented as an attribute lookup on a merged mesh rather than "one mesh per wall" — and a single draw call per LOD-chunk for the whole neighbourhood is a *better* real-time-performance outcome than many small meshes, not a compromise.
- **Recommendation: PROCEED with CityJSON + three.js + `cityjson-threejs-loader` + earcut as planned.** All three measurements land comfortably inside acceptable territory; no format/loader concern to escalate to the manager as a go/no-go blocker. Two secondary items for manager awareness (neither blocks CP-0):
  1. **`cityjson-threejs-loader@0.4.0` (published 2023-07-20, latest release) is stale against current `three@0.185.1`** — it imports removed three.js exports directly (`sRGBEncoding`, removed after r152) and uses extensionless `three/examples/jsm/...` import paths that current `three`'s strict `package.json` `exports` map rejects. Worked around here by pinning `three@0.155.0` (roughly contemporaneous with the loader's last release) and bundling with esbuild + explicit `--alias` flags for the extensionless paths. **T08 ("frozen, vendored three.js shell") needs to pin a specific compatible `three` version deliberately** (not "latest") when it vendors — `0.155.0` is a working starting point, or patch/fork the two-line loader import if a newer `three` is preferred. Flagging now so T08 doesn't rediscover this from scratch.
  2. **The spike's CityJSON does not apply real inter-building neighbourhood positioning** — `collect_geometry` recentres each building independently around its own local IDF coordinates (by design, for single-building CAD export; T01 preserved this behaviour exactly and additionally stores-but-does-not-apply the discarded offset per the plan's instruction). Verified empirically: the spike's 300,956 deduped vertices span only |x| <= 245 m, |y| <= 369 m around the origin — i.e. all 738 real buildings are overlapping/stacked near the origin rather than spread across the true multi-block neighbourhood footprint. This is a **known, already-anticipated** gap, not a new finding: plan §9 ruling 5 already assigns true relative positioning to **T04**, sourced from the per-run `01_buildings.gpkg` (real UTM coordinates), not from `collect_geometry`'s IDF-local output. It does not affect any of the three required CP-0 measurements (all position-independent) but does mean a real "does the neighbourhood look right" visual walkthrough isn't meaningful until T04 wires in true positions — noting this so the manager doesn't expect a geographically-correct screenshot from this spike.
- Notes (real bug found and fixed, T01 addendum): while building this spike, **0 of 738 buildings produced any `subwin` (window/door) geometry** on the first run. Root cause: `_parse_fen_vertices`'s fallback branch (taken when the primary "Number of Vertices" integer scan finds nothing) skipped only *blank* tokens before this fix, not the literal string `"autocalculate"`. This pipeline's real IDF builder writes `"autocalculate"` as literal text for `FenestrationSurface:Detailed`'s Number-of-Vertices field (not blank), so the fallback's `for v in fields[8:]` hit that token first and `break` before ever reaching the real coordinate floats — silently discarding every fenestration surface fleet-wide. This bug is inherited unchanged from `idf_reader/visualizer_adapter.py` (i.e. the *original* source has the same latent bug on this kind of real-world IDF; T01's port did not introduce it, "preserve behaviour exactly" faithfully carried it forward). Fixed with a minimal one-line-condition change (`openubem/viz/geometry_extract.py`, `_parse_fen_vertices`): also skip `v.lower() == "autocalculate"` in the fallback scan, mirroring how the primary integer scan already skips it. Added a regression test reproducing the exact real-world field shape (`tests/test_viz_geometry_extract.py::test_parse_fen_vertices_literal_autocalculate_num_vertices`); full T01 suite re-run green (5 passed) after the fix. **Flagging this prominently for manager review**, since it is a second change to T01's module beyond the plan's explicitly-authorized "one additive change" (the `surf_name` field) — the plan's own faithful-to-model rule (Sec 2.4: "any task that would render ... a value the pipeline did not produce ... is a STOP-and-ask") cuts the other way here (a value the pipeline *did* produce, a real window, was being silently dropped), and leaving it unfixed would have made every one of T02's measurements — and, if uncorrected, all of T03's future production output — unrepresentative (buildings appearing glassless network-wide). Also verified `_door_to_window_fields`/`Door` (standalone `Door,` object type, separate from `FenestrationSurface:Detailed`) is unaffected — this pilot's IDFs use only `FenestrationSurface:Detailed` for openings (0 standalone `Window,`/`Door,` objects fleet-wide, consistent with the T01 fixture finding). No npm packages, `node_modules/`, or JS bundle output were added to the OpenUBEM repo — all under the session scratchpad, confirmed via `git status`.

#### CP-0-AUDIT — manager audit + greenlight — completed 2026-07-02
- Artifacts: this doc (§1 CP-0 ticked). Verified live: bug-fix diff (`geometry_extract.py:184,228,249`), `surf_name` binding (`:638,651,669,677`), both §8 progress-log entries.
- **Verdict: CP-0 PASS — PROCEED with CityJSON + three.js + `cityjson-threejs-loader` + earcut.** All three spike measurements land in-band: 15.54 MB / 738 bldgs (V13 comfortable band; ~37 MB extrapolated for heaviest cell nyc_urban 1779, still fine); ~324 ms earcut parse / ~1.16 s page-ready (interactive); per-surface identity survives via `objectid`/`boundaryid` vertex attributes (single draw call — a *better* perf outcome, not a compromise).
- **Three executor judgment calls — all RATIFIED:**
  1. **`surf_name` per-surface interpretation** (faces = own name; subwin = sub-surface's own `Name`, not the repeated parent-wall name). CORRECT — the only reading consistent with the plan's stated purpose ("stable **per-surface** feature ID … for V05 binding and V08 picking"); parent-wall reuse would make windows on one wall indistinguishable. Evident-intent over literal-text; ratified.
  2. **`_parse_fen_vertices` "autocalculate" fix** (second change beyond the authorized one). RATIFIED — **faithful-to-model (§2.4) outranks preserve-behaviour-exactly**: the ported behaviour silently dropped 100% of real windows fleet-wide (a value the pipeline *did* produce). Fix is minimal, mirrors the primary-scan branch that already skipped the token, and is regression-tested. Executor correctly STOPPED and flagged rather than silently applying. Note: the bug is latent in sibling `idf_reader` too — NOT our repo to fix.
  3. **`expand_multipliers`/`_expand_floor_multipliers` NOT ported** (~300 lines). RATIFIED — it synthesizes floor geometry not literally in the IDF (cuts against faithful-to-model), default False, no T01/T02 consumer. **Forward-watch → T03:** first-check the pilot IDFs for `Zone` Multiplier > 1; if any building uses zone multipliers the dropped logic becomes height-faithfulness-relevant and T03 must STOP-and-decide. Expected: none (OpenUBEM models floors explicitly via `one_zone_per_floor`).
- **Forward-carry notes (no CP-0 action):** (a) T09 picking = attribute lookup (`resolveIntersectionInfo` on `objectid`/`boundaryid`), not mesh-per-wall; (b) T04 owns true inter-building positioning from `01_buildings.gpkg` (spike stacks buildings at origin, as designed); (c) T08 must pin a `three` version compatible with `cityjson-threejs-loader@0.4.0` (working: `three@0.155.0`), never "latest".
- Test status: n/a (audit). Executor's suite: T01 5/5 green; full suite 1208 passed / 12 pre-existing unrelated failures (none reference `openubem.viz`).
- Notes: T03–T07 greenlit to the same executor (context continuity — it holds the loader internals + field-source map + autocalculate quirk), STOP at CP-1.

#### T03 — `cityjson_emitter.py`: neighbourhood IDFs → one `.city.json` (LOD-N + LOD-B) — completed 2026-07-02
- Artifacts: `openubem/viz/cityjson_emitter.py` (`build_cityjson`, `footprint_centroids_utm`, `dumps`, `_window_parent_map`); `tests/test_viz_cityjson_emitter.py` (7 emitter tests + 3 T04 tests share the file).
- **First-action faithfulness gate (mandated) — PASSED:** scanned all 738 pilot IDFs for `Zone` objects with `Multiplier > 1` → **0 found**. OpenUBEM models every floor explicitly (`one_zone_per_floor`), so the T01-dropped `expand_multipliers` logic is correctly NOT height-faithfulness-relevant for this pilot. No STOP required; recorded and proceeded per manager instruction.
- Positioning: **Option A (manager ruling 2026-07-02, PLAN §9 ruling 8)** implemented exactly. `collect_geometry(recentre=False)` (forced, not trusted-zero); vertex = `IDF + footprint_centroid_UTM − common_origin`, Z untouched; `footprint_centroid_UTM` read from `01_buildings.gpkg` (EPSG:32618, the exact inverse of `footprint.py:53` centroid subtraction — verified: the builder subtracts `poly.centroid`, which IS the `01_buildings` polygon centroid); `common_origin = (floor(min cx), floor(min cy), 0)` over all emitted buildings' centroids. CRS in `metadata.referenceSystem` (`.../EPSG/0/32618`), `common_origin` in `metadata["+common_origin_utm"]`, per-building `footprint_centroid_utm` as a CityObject attribute → V07 recovers `UTM = decoded_vertex + common_origin`. Live pilot: coherent 1545 m × 1390 m neighbourhood (matches the ~1.2 km UTM centroid spread + building extents), no origin-stacking.
- Deviations (three, all flagged for audit):
  1. **Vertex encoding = integer millimetres + CityJSON `transform`** (`scale=[0.001,0.001,0.001]`, `translate=[0,0,0]`), not raw floats. Rationale: this is the canonical, compact, perfectly-deterministic CityJSON form; max rounding error 0.5 mm ≪ the 1 cm CP-Geometry tolerance (live max observed 0.499 mm). The manager's CP-Geometry formula ("CityJSON_vertex + common_origin − footprint_centroid_UTM") is applied to the **decoded** vertex (`v_int × scale`); the test decodes first. Not a plan contradiction (plan left encoding open); flagged because it's a concrete choice the plan didn't spell out.
  2. **Window→parent-wall linkage re-derived in T03 from the IDF** (`_window_parent_map`, reads `FenestrationSurface` field[3] / `Window` field[2] / `Door` field[2]) rather than adding a 6th element to T01's tuple. `collect_geometry` does not carry the parent linkage on `subwin` records, and the plan requires windows "nested under their parent `WallSurface`". Chose re-derivation to keep the ratified T01 module untouched (one extra `parse_idf` per building, ~cheap). Verified live: every window/door nests under a `WallSurface` parent with `parent`/`children` indices.
  3. **Per-zone `children` CityObjects NOT emitted** (plan T03 How: "children per zone where zones exist"). Emitted one `Building` CityObject per `osm_id` with LOD-1/LOD-3 `MultiSurface` covering all its surfaces; the real `zone_name` is preserved on each face record inside `geometry_extract` but is not turned into child CityObjects. Rationale: (a) none of the four CP-1 checkpoints need zone children; (b) per-zone/LOD-Z is an explicitly separate, gated feature (T12 + PLAN §5 "the export carries no per-zone attribute breakdown; do not paint per-zone values"); (c) fabricating child zone-objects now for `one_zone_per_floor`/`perimeter_core` buildings could imply a zone-level view the MVP does not offer. This is the *conservative* (do-not-fabricate) direction, never a faithfulness violation — but flagging since it declines a literal "How" note. Recommend revisiting when T12/LOD-Z is built.
- Test status: `pytest tests/test_viz_cityjson_emitter.py -q` — 10 passed (T03: valid CityJSON-v2 structure incl. semantic/vertex-index range checks; both LODs present per building; LOD-1 zero openings / LOD-3 has them; windows nested under parent walls; byte-identical across two runs [determinism]; **vertex round-trip through offsets ≤1 cm** [CP-Geometry]; buildings-not-stacked positioning). Live pilot (738): byte-identical rebuild TRUE, CP-Geometry max 0.499 mm over 24 strata/7709 vertices, 30.42 MB.
- Notes: **file size 30.42 MB** for the pilot (vs the T02 spike's 15.54 MB) — true positioning cuts cross-building vertex dedup AND every surface now carries its verbatim `surf_name` semantic ID (the stable per-surface feature key). Still inside V13's "comfortable ≤ low-tens-of-MB" band; extrapolating to the heaviest cell (nyc_urban 1779) ≈ 73 MB — under the 100 MB warning but worth watching; a post-MVP option is `surf_name` interning if size becomes a constraint. Pilot `zoning_strategy` mix (from the run): `one_zone_per_floor` 467, `perimeter_core` 149, `single_zone` 122 (738 total) — so the pilot does exercise `perimeter_core`, relevant to T12's LOD-Z gate later.

#### T04 — `geojson_context.py`: extruded-footprint LOD-0 placeholders — completed 2026-07-02
- Artifacts: `openubem/viz/geojson_context.py` (`build_context_geojson`, `_height_m`, `_footprint_to_scene`); tests in `tests/test_viz_cityjson_emitter.py::TestContextPlaceholders` (3 tests).
- Scope (narrowed by manager ruling): T04 does **not** position the CityJSON buildings (Option A moved that into T03). T04 owns only the **required** hatched placeholders for IDF-less/failed/absent buildings (footprint-extruded, `is_approximation: true`) + the optional context scaffold. Placeholder set = `01_buildings` osm_ids − emitted-CityJSON osm_ids. The pilot has 0 failures (738/738), so the live path emits an **empty** placeholder collection; the path is exercised by a synthetic fixture (building `way/C` with a footprint but no IDF → exactly one placeholder feature).
- Deviations: **placeholder coordinate frame** — emitted in the SAME scene frame as the T03 CityJSON (`UTM − common_origin` metres, footprint translated by `−common_origin`), with the CRS + `common_origin` recorded on the collection (`openubem:frame`). The plan didn't state the placeholder frame explicitly, but placeholders must render coherently *among* the real buildings, so the shared scene frame is the only consistent choice; it fabricates no model data (features are already flagged `is_approximation`). This is viewer scene-space, not RFC-7946 geographic GeoJSON — noted on the collection. `height = levels × 3.5 m` (falls back to `ceil(height_m/3.5)×3.5`, then 1 floor), mirroring the pipeline's own `derive_num_floors` logic (faithful).
- Test status: `pytest tests/test_viz_cityjson_emitter.py -q` — the 3 T04 tests pass (placeholder set == absent-buildings only; every feature carries `osm_id` + `height` + `is_approximation:true` + a Polygon/MultiPolygon geometry; zero-absent → empty FeatureCollection).
- Notes: `build_context_geojson(buildings_gdf, emitted_osm_ids, common_origin)` takes `common_origin` from T03 so the two layers share one frame. Deterministic (features sorted by `osm_id`).

#### T05 — `attribute_binding.py::bind_values`: bind simulation outputs + building attributes — completed 2026-07-02
- Artifacts: `openubem/viz/attribute_binding.py` (`bind_values` + shared helpers); `tests/test_viz_attribute_binding.py::TestBindValues` (4 tests).
- Bound verbatim into `CityObjects[osm_id].attributes` by `osm_id` join: `total_eui_kwh_m2` + the **11** sub-EUI end-uses + the **10** GWP columns (9 end-use + `gwp_total_kgco2_m2`) + `iod` + `footprint_area_m2`/`levels`/`height_m`/`archetype_id` (from `05_results.csv`) + `year_built` (from `01_buildings.gpkg`, per §5 — it is not in `05_results`). Raw OpenUBEM field names kept verbatim (never `archetype`/`num_floors`). Population NOT added (V05 §2 — no source); per-surface solar NOT added (V11). `05_results` has success rows only — a building absent from it gets no EUI key and is NOT dropped (T05 test c).
- Deviations: none. (NaN cells are omitted rather than written as JSON-invalid `NaN` — a correctness necessity, not a scope change.)
- Test status: `pytest tests/test_viz_attribute_binding.py -q` — TestBindValues 4/4 (CP-Value: `total_eui_kwh_m2` == source exactly; `year_built` joined from 01_buildings; no `population` key anywhere; absent-from-results building has no EUI + not dropped). **Live pilot CP-Value: 4,428 cell comparisons across 738 buildings × 6 value columns → 0 mismatches; 738/738 have `total_eui_kwh_m2` bound.**

#### T06 — `attribute_binding.py::bind_provenance`: mode/trust/status + graceful degrade — completed 2026-07-02
- Artifacts: `openubem/viz/attribute_binding.py` (`bind_provenance`, `_coverage`, `_ARCHETYPE_CONFIDENCE_RANK`); `tests/test_viz_attribute_binding.py::TestBindProvenanceGracefulDegrade` (4) + `::TestBindProvenanceFullArtifacts` (3).
- Provenance rides the **same** `attributes` table as values (never a side-channel). Per §5 source map: `zoning_strategy`/`num_zones`/`generation_status`(+`resolution_mode`/`archetype_confidence`/`archetype_source`/`mean_imputation_confidence`/`imputed_fields_count` *where present*) ← manifest; `data_quality_flag` ← `05_results`; per-field `provenance_*` (7) ← `01_buildings`. Raw tokens verbatim. **Graceful degrade (binding):** a field whose source **column** is absent is omitted (never defaulted — no `resolution_mode="auto"`) and recorded in the returned `provenance_coverage = {present, absent}`. `trust_confidence = min(mean_imputation_confidence, rank(archetype_confidence))` with `HIGH→1.0/MEDIUM→0.5/LOW→0.1`; **omitted entirely** unless BOTH sides are present+non-missing (never one-sided).
- Deviations: **optional Step-2-classifier backfill NOT performed.** The plan marks it "optional (manager-approved)"; the manager's ruling did not mandate it, and the faithful graceful-degrade path (which the plan says "runs live from day one") is the honest default for this legacy run. So the pilot's `archetype_confidence`/`archetype_source` stay in `coverage.absent` and `trust_confidence` is omitted fleet-wide — deferred, easily added later behind the `archetype_id`-equality guard if the manager wants it. Flagging as an explicit deferral of an optional step.
- Test status: `pytest tests/test_viz_attribute_binding.py -q` — 7/7 provenance tests (absent `resolution_mode` omitted + in coverage.absent; present fields round-trip verbatim; `trust_confidence` omitted when sides absent; coverage lists present fields; WITH full artifacts: `trust_confidence` = min of sides [A HIGH+1.0→1.0, B LOW+0.5→0.1]; literal `failed_worker_exception` preserved; `resolution_mode` present when the run carries it). **Live pilot CP-Provenance: present = 11 fields** [`data_quality_flag, generation_status, num_zones, provenance_{building_tag,function_tag,geometry,height_m,levels,postcode,year_built}, zoning_strategy`], **absent = 5** [`archetype_confidence, archetype_source, imputed_fields_count, mean_imputation_confidence, resolution_mode`] — exactly matching the §5 legacy-run source map; `trust_confidence_computable=False` (both sides absent), so it is correctly omitted for all 738.
- Notes: `coverage` also carries `trust_confidence_computable` / `trust_confidence_computed_any` booleans for T12's "not recorded" badge logic + T07's block.

#### T07 — `metadata_block.py`: embedded reproducibility metadata — completed 2026-07-02
- Artifacts: `openubem/viz/metadata_block.py` (`add_metadata_block`, `content_hash`, `_git_commit`, `_building_counts`); `tests/test_viz_attribute_binding.py::TestMetadataBlock` (4).
- `cityjson["metadata"]["+openubem_reproducibility"]` carries all seven required keys: `git_commit` (read-only `git rev-parse HEAD` subprocess — never a commit), `random_seed` (=42, `config.py:52`), `run_id`, `building_counts` (grouped by `resolution_mode` if the run carries it, else by `zoning_strategy` — the pilot lacks `resolution_mode` so it groups by zoning: single_zone 122 / one_zone_per_floor 467 / perimeter_core 149), `provenance_coverage` (from T06), `viewer_spec_version` + `lod_spec_version` (module constants), `source_refs`. The build timestamp lives in a **separate** `metadata["+openubem_build_timestamp"]` key; `content_hash()` deep-copies and pops that key before hashing → two builds hash identically while the files differ.
- Deviations: none. (Custom metadata keys are `+`-prefixed per CityJSON's extension convention.)
- Test status: `pytest tests/test_viz_attribute_binding.py -q` — TestMetadataBlock 4/4 (seven required keys present + seed==42; **CP-Reproducibility: two builds with different timestamps → different files but identical `content_hash`**; timestamp not inside the hashed region; counts group by `zoning_strategy` absent `resolution_mode`). **Live pilot CP-Reproducibility: full pipeline built twice (different timestamps) → identical content hash, files differ. Full 15/15 attribute+metadata suite green; 30/30 across all three viz test files; full-suite collection 1259 tests, no import collisions.**

---

#### T08 — Frozen three.js viewer shell scaffold (vendored, LOD-N render, compass + scale bar) — completed 2026-07-02
- Artifacts: `openubem/viz/shell/viewer_app.mjs` (three.js app source), `viewer.css` (UI chrome), `viewer.html.template` (single scene-payload injection slot `__SCENE_PAYLOAD__` + `__VIEWER_JS__`/`__VIEWER_CSS__`/`__RUN_ID__`), `viewer.js` (esbuild IIFE bundle, 1.0 MB — three@0.155.0 + cityjson-threejs-loader@0.4.0 + OrbitControls all inlined), `BUILD.md` (one-time build command + pinned toolchain).
- The shell parses the injected `#scene-data` JSON (no fetch), loads CityJSON via `CityJSONLoader`/`CityJSONParser` with `parser.lods=["1","3"]` (lodid 0 = LOD-N masses, 1 = LOD-B), and renders LOD-N by a per-mesh draw-index over triangles with `lodid==0`. Material is an **unlit `MeshBasicMaterial` + per-vertex `color`** (vertex colours written sRGB→working-linear via `Color.setRGB(...,SRGBColorSpace)`), NOT the loader's default lambert material (V09 Table 3 — no lit PBR to distort encoded values). In-scene North compass (SVG needle tracking camera azimuth in the Z-up XY plane) + a metre scale bar (nice-number metres per fixed 80 px at target distance).
- Deviations: (1) **`vendor/` subfolder collapsed into the single `viewer.js` bundle.** The plan's §3 tree lists `vendor/three.min.js + OrbitControls + loader + earcut`; I bundled all of them into one committed `viewer.js` instead. Rationale: the plan's own §4/T13 mandate is a *self-contained single HTML* with "everything inlined — no runtime fetches"; a single pre-bundled artifact is the vendored output ("build the JS bundle ONCE as a dev step, then commit the vendored output" — T08 How) and is strictly simpler for T13 to inline than N separate vendored files. Version-pinning is preserved and documented in `BUILD.md`. (2) Loader's `computeMatrix` recenter is kept (not forced to identity); the same bbox-centre shift is applied to T04 context placeholders so both frames align. No faithfulness impact (a known rigid translation, same as §9.8's chain).
- Test status: rendered live on the 738-building nyc_centre pilot (screenshot `cp2_neighbourhood.png`); orbits; **0 console errors; 0 http(s) requests when opened from `file://`** (puppeteer request-interception, self-contained constraint MET).
- Notes: bundle built with `esbuild --bundle --format=iife` + three `--alias` flags for the loader's extensionless `three/examples/jsm/lines/*` imports (see `BUILD.md`); `three@0.155.0` pin is load-bearing (loader imports `sRGBEncoding`, removed in three ≥ 0.157).

#### T09 — MVP interaction: orbit / select / drill-down / back — completed 2026-07-02
- Artifacts: `viewer_app.mjs` (`_onPointerDown`/`_onPointerUp`, `_selectBuilding`, `_backToNeighbourhood`, `_setLodIndex`).
- `OrbitControls` (target = neighbourhood centroid, damping, min/max distance clamped to scene radius). Click-select uses `Raycaster.intersectObjects([mesh])` then the loader's **`mesh.resolveIntersectionInfo(hit)`** to recover `objectIndex`→`osm_id` from the merged mesh (NOT mesh-per-wall). Select + drill-down are **one action** (V04 §4): the selected building's draw-index swaps to its `lodid==1` triangles (walls+roof+**windows**), every other building stays at `lodid==0` — a resident-buffer visibility swap, no fetch. Highlight = amber vertex-colour override on the selected object. Back = button + **Esc**, restores all-LOD-N index, clears selection, re-frames target. Drags (>5 px) are ignored so orbit doesn't fire selection.
- Deviations: none. (Walkthrough/isolate/section-planes/measurement/per-surface-select deferred per V08 list.)
- Test status: live puppeteer — programmatic select of the max-EUI building resolved the correct `objectIndex`→`osm_id way/266149324` and swapped it to LOD-B (windows shown), neighbours stayed masses (`cp2_drilldown.png`); back restores. Picking responsive across all 738.
- Notes: windows/doors (loader `surfacetype` 5/6, from `defaults/colors.js` key order) get a fixed glass colour in drill-down so openings read as openings, not EUI.

#### T10 — Colouring system: categorical + sequential, pinned domain, legend, no-data, imputed overlay — completed 2026-07-02
- Artifacts: `openubem/viz/shell/colormaps.mjs` (viridis/cividis 10-stop ramps, `sampleRamp`/`classColor`, 13-sector `SECTOR_COLOR`, 30-archetype→sector `ARCHETYPE_SECTOR`, `NO_DATA_GREY` off-ramp), `viewer_logic.mjs` (`quantileBreaks`/`classifyQuantile`/`normalizeContinuous`), legend rendering in `viewer_app.mjs`; `tests/viz_js/viewer_logic.test.mjs`.
- Sequential EUI: **quantile ~5 classes, breaks computed ONCE from the full 738-building scene and pinned** (never rescaled to the in-view subset), viridis default + cividis CVD toggle + unclassed-continuous toggle over a fixed [min,max] domain. Categorical archetype: 30-vocab grouped into **sector hue-families with always-shown text labels** (§9.3 mandatory — colour never the sole channel); legend shows one labelled swatch per archetype *present in the scene* (13 on the pilot) with its sector name. One reserved neutral grey for no-data, kept off both ramps. Imputed/low-confidence buildings get an outline/edge overlay (never a grey swap).
- Deviations: none. (Diverging PRGn/PuOr scaffolding intentionally not shipped — deferred per §9.4, no diverging attribute in the EUI-magnitude MVP.)
- Test status: `node --test tests/viz_js/viewer_logic.test.mjs` — **13/13 pass**: quantile determinism (order-independent + repeat-stable + monotone), bins in 0..4, NaN/null→−1, **no-data grey distinct from every ramp class colour**, continuous clamp, ramp endpoints, 30-archetype→sector mapping. Live pilot: pinned breaks `[138.2, 168.7, 188.8, 207.2]`, legend + colour-by switch verified (`cp2_neighbourhood.png` EUI, `cp2_archetype.png` sector).
- Notes: sibling archetypes in a sector render identical hue by design (30 > 8-colour ceiling); per-archetype identity is recovered via the detail pane/tooltip, satisfying WCAG non-colour-only.

#### T11 — MVP output view: per-building EUI, sequential-coloured, failed = hatched — completed 2026-07-02
- Artifacts: `viewer_app.mjs` (`_colorForBuilding` EUI path is the default `mode="eui"` on boot; `_buildContext` extrudes T04 placeholders).
- Default load view colours every building by `total_eui_kwh_m2` on the pinned sequential ramp; buildings are already extruded to real height (real IDF geometry). No slider, no auto-animate. Absent-from-results / no-EUI buildings fall to the reserved no-data grey; **failed/IDF-less buildings render as hatched grey extruded-footprint placeholders from T04's context GeoJSON (extrude + wireframe edge overlay), never invisible.**
- Deviations: none.
- Test status: **CP-Value MET live** — the viewer's bound EUI for the selected building equals `05_results.csv` **exactly** (1562.8947094858167 == 1562.8947094858167; detail-pane tooltip == CSV). The pilot has **0 failed and 0 no-EUI buildings** (0 context placeholders), so — per the plan's T11 instruction ("pilot has 0 failures so exercise via synthetic fixture and SAY SO") — the failed/no-data paths were exercised on a **synthetic derivative** (`make_synth.py`: add one `is_approximation` context feature + drop one building's EUI): puppeteer confirmed `contextGroup.children == 2` (placeholder extrusion + hatch overlay both render) and the EUI-dropped building has no EUI attribute → no-data grey, 0 pageerrors.
- Notes: max-EUI building is a `QuickServiceRestaurant` (1563 kWh/m², reads at the top of the ramp) — plausible; high-EUI reads high.

#### T12 — Provenance surfacing UI: mode border + trust badge + LOD-Z gate + detail pane — completed 2026-07-02
- Artifacts: `viewer_logic.mjs` (`lodZGate`, `trustBadge`, `resolutionBorder`, `displayToken`), detail pane in `viewer_app.mjs` (`_showDetail`); `tests/viz_js/viewer_logic.test.mjs` gate tests.
- On select, the detail pane shows: a **resolution-mode border badge** (thin/medium/heavy for building/floor/zone; **dashed "not recorded" with no border when `resolution_mode` absent**), a **merged trust badge** (shape glyph ●/◐/○ for HIGH/MED/LOW + a distinct "—/not recorded" state, never hue-only), a **verbatim field table** (`data_quality_flag`, `archetype_source`, `imputed_fields_count`, etc. — absent ⇒ "not recorded", never blank/fabricated), and the **LOD-Z gate**: "Zone breakdown" enabled for `perimeter_core` AND `room_layout`, "Floor-level" for `one_zone_per_floor`, disabled-with-disclosure for `single_zone`, and "not recorded" for legacy/unknown. Procedural zone synthesis is prohibited (enabled controls only surface a "per-zone rendering deferred in MVP — no synthetic zones drawn" note).
- Deviations: none.
- Test status: **gate unit-tested against all FOUR `zoning_strategy` values** (`node --test` — perimeter_core/room_layout→zoneBreakdown, one_zone_per_floor→floorLevel, single_zone→disclosure, unknown→"not recorded"), plus trustBadge/resolutionBorder/displayToken absent-state tests. Live pilot (a legacy run): selected building shows "resolution: not recorded" + "trust: — not recorded" + verbatim `data_quality_flag = no_year|VINTAGE_NAN_PERMISSIVE_DEFAULT`, `zoning_strategy = one_zone_per_floor` → Floor-level enabled / Zone breakdown disabled (`cp2_drilldown.png`).
- Notes: pilot carries no `room_layout`/`perimeter_core`+`single_zone` building selected in the screenshot, but the gate's four branches are proven by the node suite; the live legacy-run path (all-"not recorded") is the faithful behaviour §9.7 mandates.

#### CP-2 — viewer feature-complete — evidence captured 2026-07-02 (awaiting manager audit)
- **Walkthrough evidence** (headless Chromium + SwiftShader, `verify_cp2.js`): 738 buildings render as EUI-coloured LOD-N masses with pinned quantile legend + compass + 200 m scale bar (`cp2_neighbourhood.png`); select+drill-down of the max-EUI building shows windows + full detail pane (`cp2_drilldown.png`); colour-by → Archetype recolours to sector hue-families with a 13-archetype labelled legend (`cp2_archetype.png`).
- **CP-Value (live):** viewer bound EUI == `05_results.csv` exactly for the checked building (1562.8947094858167).
- **Self-contained (live):** opened from `file://`, **0 http(s) network requests**, 0 console errors.
- **Automated:** `tests/viz_js/viewer_logic.test.mjs` 13/13 (T10 determinism + T12 four-value gate). Python viz suites unchanged (30/30).
- **Dormant paths:** failed-placeholder + no-data-grey exercised on a synthetic derivative (pilot has 0 of each), stated in the T11 entry.
- **Optional nyc_urban (1779) scale stress-check:** not run this pass; the pilot at 738 (31 MB scene, 32 MB HTML) renders + picks smoothly under SwiftShader (a software floor, not a GPU) — flagged as available if the manager wants it before CP-2 sign-off.

#### CP-2 FIX — Fallback / no-data de-conflation (colormaps) — completed 2026-07-02
- **Trigger:** manager CP-2 audit flagged a faithfulness conflation — the large flat footprints render yellow (top EUI band) in EUI mode but no-data grey in archetype mode. Diagnostic (read-only) confirmed **case #1**: `SECTOR_COLOR["Fallback"]` was `NO_DATA_GREY.slice()` (`[176,176,176]`), so a **present** classification `archetype_id == "OpenUBEMUnknown"` rendered byte-identical to true absence. Counts on the pilot: **35 buildings are `OpenUBEMUnknown`** (present, → Fallback), 30 of them in the top EUI band; the two giant 3.5 m / ~130–157k m² OSM-relation slabs are `relation/11171793` (EUI 265) and `relation/11171765` (EUI 88). **0 buildings have an absent `archetype_id`** (case #2 ruled out — no emitter drop; every grey building was a real Unknown).
- **Fix.** `colormaps.mjs`: `SECTOR_COLOR["Fallback"]` = **`[108, 96, 128]`** (muted dark slate-violet), its own constant, no longer aliasing `NO_DATA_GREY`. Chosen against three constraints (verified numerically incl. a deuteranopia sim): distance **115** from `NO_DATA_GREY` and much darker (luminance 101 vs 176); min **34** from every sequential ramp class (viridis+cividis, 5 each); min **36** from every other sector colour; holds under CVD (122 / 22). `viewer_app.mjs::_colorForBuilding` archetype branch made explicit + commented — `archetype_id === undefined → NO_DATA_GREY`; any **present** id (incl. `OpenUBEMUnknown`/unmapped) → `archetypeColor` → distinct Fallback swatch. Both legend rows stay labelled and are now visibly different swatches ("OpenUBEMUnknown / Fallback" vs "no data").
- **Regression guard.** `tests/viz_js/viewer_logic.test.mjs` extended by **4 tests**: `SECTOR_COLOR.Fallback` byte-distinct from `NO_DATA_GREY`, from every ramp class, and from every other sector colour; plus `archetypeColor("OpenUBEMUnknown")` and an unmapped id both route to Fallback and NOT to no-data grey.
- **Deviations:** none. (Final RGB differs from the manager's `[110,110,128]` starting suggestion — nudged to `[108,96,128]` because `[110,110,128]` sat only 23 from a cividis mid-class and 24 from the Industrial sector grey; the chosen value widens both margins to 34/36 while staying muted-neutral. Reported per instruction.)
- **Test status:** `node --test tests/viz_js/viewer_logic.test.mjs` — **17/17 pass** (was 13, +4 distinctness). Bundle rebuilt (esbuild). Live re-render `cp2_archetype_fixed.png`: the 35 `OpenUBEMUnknown` buildings (incl. both giant slabs, introspected as `[108,96,128]`) shifted OFF no-data grey onto the Fallback slate-violet; office/high-rise/etc. unchanged; 0 pageerrors. Genuine no-data (0 on this pilot) would still map to the reserved grey.

---

#### T13 — `viewer_export.py`: Step-5 exporter → self-contained single HTML — completed 2026-07-02
- Artifacts: `openubem/viz/viewer_export.py` (`build_scene`, `export_viewer`, `export_viewer_from_run`, `_inject`, `_scene_json`); optional flag-gated wiring in `openubem/results/__init__.py` (`aggregate_results` gained `export_html: bool = False` + an env toggle `OPENUBEM_EXPORT_HTML=1`, gated after `export_results` in a non-fatal `try/except`, mirroring the `make_figures` precedent at lines 199–204). Delivered artifact: `openubem/outputs/nyc_centre_viewer.html`.
- The exporter calls the T03 emitter + T05/T06 binding + T07 metadata + T04 context, then injects the CityJSON scene payload + the vendored esbuild IIFE (`shell/viewer.js`) + `shell/viewer.css` into the frozen `shell/viewer.html.template` slots, writing ONE offline file to `openubem/outputs/` (flat, outputs rule). Everything inlined; scene is an inline `<script type="application/json">` island (never a fetch). Determinism: `json.dumps(scene, sort_keys=True, separators=(",",":"))` over the emitter's already-sorted vertices/surfaces + osm_id-sorted context; `</`→`<\/` escape so no string can close the host `<script>`.
- Deviations: (1) **`vendor/` collapsed into the single bundle** — the injector inlines the one `viewer.js` (all deps bundled, per the CP-2/T08 decision) rather than N vendored files; the delivery model is a single self-contained HTML (V13 Part C, T13 "everything inlined"). (2) **Wired at the `aggregate_results` library seam + env toggle rather than threading a new CLI flag through `v12_cell_pipeline.py`** — the boolean kwarg IS the flag (matches the `make_figures` idiom the Explore audit found at `results/__init__.py:70`), default-off so it never slows a normal run, and the env toggle lets it be enabled without editing any driver. No DESIGN conflict; §3 lists the exporter "adjacent to `visualization.py`" and this is the same seam `render_all_figures` uses.
- Test status: ran live on the pilot — `export_viewer_from_run(run_id="nyc_centre", …)` produced `openubem/outputs/nyc_centre_viewer.html` = **32.43 MB (34,008,796 bytes), 738 buildings, 0 context placeholders, build 9.3 s**, `content_hash 77dc3329…`. `aggregate_results` import + signature verified (`export_html: bool = False` present). Self-contained + reproducibility assertions covered by T14 (below).
- Notes: the `aggregate_results` scope passes `idf_manifest` (has `idf_path`) as manifest, `enriched_gdf` as buildings, `results_gdf` as results; `run_id` derived from `output_dir.parent.name`. The exporter also accepts explicit paths (`export_viewer_from_run`) for out-of-pipeline runs like this LIVE_SMOKE.

#### T14 — the six V14 faithfulness checkpoints as tests — completed 2026-07-02
- Artifacts: `tests/test_viz_validation.py` (11 tests). Fixture builds the scene once from the pilot; IDFs come from the live Step-3 run if present, else the durable archive zip is extracted and `idf_path` rewritten (survives a Temp wipe).
- **CP-Geometry:** stratified sample (≥1 per archetype×zoning present) round-trips every LOD-1 vertex THROUGH the stored Option-A offsets — `(CityJSON_vertex + common_origin) − footprint_centroid_UTM == source IDF (recentre=False)`, max error ≤ 1 cm (mm-rounding only). **CP-Value:** re-reads the REAL `05_results.csv` and asserts 100% of bound EUI/carbon/end-use/`iod` == source (>1000 bindings, 0 mismatches). **CP-Provenance:** every `coverage["present"]` field has a live round-trip witness; the five legacy-absent fields (`resolution_mode`, `archetype_confidence`, `archetype_source`, `mean_imputation_confidence`, `imputed_fields_count`) are in `coverage["absent"]` AND bound on no building; zero-imputation negative case (`trust_confidence_computable=False`, no `trust_confidence`/`imputed_fields_count` attribute). **CP-LOD:** every CityObject is a `Building` with LODs exactly `["1","3"]` and no zone geometry (single_zone can never show zones); per-building LOD-B sub-surface count == the IDF's window/door count on the sample; `single_zone` present in the pilot. **CP-Reproducibility:** two independent builds with different timestamps → identical `content_hash` and byte-identical `dumps()` after popping the timestamp (which differs), proving the timestamp is outside the hashed region. **T13 self-contained:** the emitted HTML has no `<link>`, no `<script src>`, no external/protocol-relative `src`/`href`, no `@import`/`url(http…)` in the inlined `<style>` — only the inline JSON + inline bundle. **CP-Accessibility:** documented MANUAL procedure (WCAG 1.4.3 / 1.4.11 / 2.1.1 + CVD-sim, tool recorded) plus an automatable contrast sanity (primary text 4.5:1, subtext 3:1 on the panel).
- Deviations: none. (CP-Accessibility is the one documented-manual checkpoint per PLAN §T14; its automatable slice is included.)
- Test status: `pytest tests/test_viz_validation.py -v` — **11 passed in 28.9 s**.
- Notes: CP-Accessibility's CVD-sim leans on the always-shown text labels (colour never the sole channel) + the CP-2 Fallback/no-data de-conflation; the JS-side LOD-Z gate over all four `zoning_strategy` values remains covered by the 17-test node suite.

#### T15 — LIVE_SMOKE: real Step-5 data → real viewer.html → evidence for manager — completed 2026-07-02
- Artifacts: the delivered `openubem/outputs/nyc_centre_viewer.html` (T13 output on the pilot's real Step-5 artifacts — not re-simulated); manager spot-check screenshots in scratchpad: `t15_a_eui.png`, `t15_b_archetype.png`, `t15_c_drilldown_windows.png`, `t15_d_provenance.png`.
- Opened the REAL delivered file from `file://` in headless Chromium: **0 http(s) requests, 0 console errors** (self-contained confirmed on the shipped artifact, not a re-assembly). (a) EUI headline renders 738 buildings on the pinned quantile ramp + compass + 200 m scale bar; (b) archetype view shows sector hue-families with the CP-2 Fallback slate-violet (de-conflation present on the delivered file); (c) drilled `way/487519790` (SuperTallBuilding, 245 m, 70 levels, real `year_built 1933`) to LOD-B — window mullions visible, neighbours stay masses; (d) provenance pane reads **"resolution: not recorded" + "trust: — not recorded"** with verbatim tokens (`data_quality_flag`, `zoning_strategy`) and absent fields as "not recorded" — the CORRECT legacy-run behaviour (§9.7), not fabricated defaults.
- Deviations: none. (Per [[feedback_sonnet_for_cluster_harvest]] no cluster step was needed — the pilot was already simulated; used the archived Step-5 outputs + live/archived IDFs.)
- Test status: manager sign-off IS the test — evidence captured for the Opus manager's faithfulness spot-check (user asleep, per instruction). **File: `openubem/outputs/nyc_centre_viewer.html`, 32.43 MB, opens + interactive within a few seconds under SwiftShader (software floor); comfortably within the V13 single-file band (32 MB ≪ 100 MB warning).** Per-mode visual spot-check: EUI/archetype/drill-down/provenance all faithful; legacy "not recorded" badges verified to say so.
- Notes: the delivered file's content reflects the fixed bundle (CP-2 Fallback fix). CP-3 (USER-SIGN-OFF) stays PARKED for the manager-of-manager.

#### MANAGER AUDIT of T13–T15 — completed 2026-07-02 (Opus)
- **Verdict: CLEAN. No corrections needed. CP-3 staged, NOT signed (USER-SIGN-OFF gate).**
- Ran `tests/test_viz_validation.py` myself: **11 passed** (all six V14 checkpoints + the zero-external-URL assertion).
- Self-contained re-verified on the delivered `openubem/outputs/nyc_centre_viewer.html` (34,008,796 B) independently of the employee's headless check: scanned for active-load patterns (`src=`/`href=`/`fetch(`/`import…from "http`/`@import`/`url(http`) → **zero**. The only two `http(s)://` literals are inert — one inside a `console.warn` string, one a code comment — both in the vendored three.js r155 bundle, no network effect.
- Reproducibility: covered by CP-Reproducibility (identical content_hash excl. timestamp) in the passing suite.
- Eyeballed all 4 renders: (a) EUI viridis quantile + compass + 200 m bar + "no data" grey legend; (b) archetype sector hue-families — **CP-2 Fallback slate-violet holds on the delivered file** (`OpenUBEMUnknown` visibly distinct from "no data" grey); (c) `way/487519790` drilled to LOD-B, window mullions present, neighbours stay masses, `one_zone_per_floor` ⇒ Zone-breakdown DISABLED + "no synthetic zones drawn"; (d) `way/162977896` provenance pane faithfully shows a **populated** `data_quality_flag` (`no_year|VINTAGE_NAN_PERMISSIVE_DEFAULT`) alongside absent fields as "not recorded" — present-vs-absent rendered honestly, no fabricated defaults.
- One non-blocking data-quality **observation** for the user (faithful-to-model, NOT a viewer bug): the large flat top-bucket polygon + thin sliver at the neighbourhood's SE/W edges are un-extruded large-footprint OSM slabs (Fallback archetype) the pipeline itself produced; the viewer renders them exactly. Worth an eyeball at the source-data level someday, not a delivery blocker.
- Employee deviation (wired the exporter at the `aggregate_results` library seam + `OPENUBEM_EXPORT_HTML=1` env toggle rather than a new `--export-html` CLI flag on `v12_cell_pipeline.py`): **RATIFIED** — matches the existing `make_figures` idiom at the same seam, default-off, no DESIGN conflict. An explicit CLI flag remains an easy post-sign-off follow-up if the user wants it.

---

## 9. Manager decisions — RESOLVED 2026-07-02

All §9 items (1–5 original + 6–7 added on plan review) are resolved against the codebase (grepped/verified
2026-07-02, incl. the pilot's real artifacts). Recorded here as binding inputs to the tasks that reference them.

1. **Pilot cell for T02/T15 = `nyc_centre` (738 successful buildings, phaseE baseline).** Use the *same* cell
   for the T02 spike and the T15 LIVE_SMOKE for continuity. **Rationale:** it is the best-characterized cell
   (already the imputation-arc pilot — "flattest 5-vintage spread", [[project_input_imputation_arc]]), the
   densest urban-core mix so it exercises the categorical archetype legend and the vintage/EUI ramps hardest,
   and sits at mid-upper scale (738) so it meaningfully stresses CityJSON file-size + picking **without** being
   the heaviest cell. Real `05_results.*` + `05_neighbourhood_summary.json` + `01_buildings.gpkg` +
   `04_simulation_manifest.parquet` exist at
   `docs/docs_VALIDATION/validations/overAll/results/phaseE/nyc_centre/`. **The 738 per-building IDFs +
   `step3/03_idf_manifest.parquet` exist (verified 2026-07-02) at
   `%LOCALAPPDATA%\Temp\ubem_validation\phaseE\nyc_centre\` — a Temp path; T02's first action archives them
   (zip) into the durable validation folder before anything else.** *(Feeds T02, T15.)*

2. **Per-cell building counts (phaseE baseline, `n_buildings_by_status.success`):** la_rural 149 · nyc_rural
   198 · la_centre 226 · austin_rural 245 · austin_centre 413 · austin_urban 425 · austin_suburban 437 ·
   la_urban 618 · **nyc_centre 738** · la_suburban 1343 · nyc_suburban 1589 · nyc_urban 1779. **Regime verdict:**
   all 12 cells are in V12's hundreds-to-low-thousands regime; LOD-N masses are feasible everywhere (V04:
   1k–10k+ at LOD1). Discrete-swap (MVP) is correctly sized for the pilot and for 8 of 12 cells. **Four cells
   exceed 1,000** (la_suburban 1343, nyc_suburban 1589, nyc_urban 1779) and sit near the discrete-swap ceiling —
   the camera-elevation batch-downgrade (V12) becomes a real need **only for these, and only post-MVP**. Add
   **`nyc_urban` (1779)** as an *optional* CP-2 scale stress-check (if the pilot holds and nyc_urban holds, every
   cell holds). *(Feeds CP-2; no MVP scope change.)*

3. **DOE-archetype roster = 30** (`openubem/data/openstudio_archetypes.json`; enforced as `_VALID_30` /
   "30-element vocab" in `building_classifier.py:31,423,477`, plus the `OpenUBEMUnknown` fallback). **30 far
   exceeds the Okabe-Ito 8-colour ceiling → the categorical legend MUST group archetypes into sector hue-families
   (Office / Education / Lodging / Residential / Retail / Healthcare / Food-service / Warehouse / …) with text
   labels, from day one — not colour alone.** V09's "one swatch per archetype *present in the current scene*"
   mitigation still applies (a single cell rarely shows all 30) but a dense pilot like nyc_centre will exceed 8
   present archetypes, so hue-grouping + labels is **mandatory in T10, not optional.** *(Feeds T10 — updates the
   V09 GAP: resolved, grouping required.)*

4. **Diverging-map baseline = archetype-cohort median within the current scene** (compare an office to the office
   median, not a mixed citywide median) — V09's defensible default, locked as the default for **if/when** the
   deviation map is built. **Deferred: not MVP** (no diverging attribute ships in the EUI-magnitude MVP). *(Feeds
   a post-MVP task only.)*

5. **Footprint source = CONFIRMED real-coordinate-bearing, and pinned to the per-run snapshot.**
   `openubem/acquisition/osm_fetcher.py` fetches OSM footprints via osmnx, projects to a **projected UTM CRS**
   (`estimate_utm_crs()`, asserts `crs.is_projected`, stores the `crs_utm` string), and retains WGS84
   convertibility (`to_crs("EPSG:4326")`). Real coordinates are carried **at the footprint source**; the
   recentring that discards them happens **downstream** in the matplotlib/CAD renderers (`visualizer_adapter` /
   `collect_geometry`), not upstream. **Resolves the V15 GAP.** For T04, the concrete source is the run's
   **archived `01_buildings.gpkg`** (geometry + `levels` + `crs_utm`, per-run snapshot) — never a live OSM
   re-fetch, which could disagree with what was simulated. V07 geo-referencing (post-MVP) is recoverable from
   the same file + T01's stored recentre offset. *(Feeds T04, and V07 post-MVP.)*

6. **`room_layout` extends the LOD-Z gate (ruling, extends V04-RMG-01).** The research predates the
   layoutgenerator arc: `resolution_mode="zone"` is now implemented (`zoning.py:23-31`) and introduces a 4th
   `zoning_strategy` value, **`room_layout`** (`zoning.py:83-96`), carrying *real room-level zone geometry*
   from `layoutGenerator.generate_layout`. Ruling: buildings with `zoning_strategy == "room_layout"` qualify
   for **full LOD-Z** exactly like `perimeter_core` (their zones are real, not procedural viewer synthesis —
   the prohibition targets *viewer-side* fabrication, which stays absolute). The phaseE pilot predates `zone`
   mode, so no pilot building carries it — cover with unit tests (T12). *(Feeds T12, §5 gate.)*

7. **Legacy-run provenance coverage (ruling).** The pinned pilot's artifacts (pre-resolution-switch,
   pre-imputation-arc) do **not** carry `resolution_mode`, `archetype_confidence`/`archetype_source`, or the
   imputation-lineage fields (§5 source map, verified 2026-07-02). Ruling: the viewer handles this via the
   binding graceful-degrade rule — absent field ⇒ attribute omitted + `provenance_coverage` entry (T07) +
   "not recorded" badge (T12) — **never a default**. This is a feature, not a blocker: rendering a legacy run
   honestly is itself the faithful-to-model behaviour, and it exercises the degrade path live from day one.
   T06's optional deterministic Step-2 re-classification backfill (with the `archetype_id`-equality guard) is
   the only sanctioned enrichment. *(Feeds T06, T07, T12, T15.)*

8. **Inter-building positioning applied in T03, NOT T04 — Option A (true relative frame). RULING 2026-07-02**
   (resolves the T03 STOP; supersedes ruling 5's "V07 recoverable ... Feeds T04" only as to *where relative
   positioning happens* — T04's role narrows to failed/absent placeholders + optional context scaffold, it does
   NOT position the CityJSON buildings). **The `.city.json` must be a standards-valid city model: all buildings
   in ONE shared neighbourhood frame, not 738 masses stacked at the origin** (a stacked file is malformed
   CityJSON and breaks any external consumer — cuts against the self-contained/interoperable constraint §2).
   Verified coordinate chain: `translate_to_origin` (footprint.py:53) makes builder-local = `UTM −
   footprint_centroid`, that centroid is exactly the `01_buildings.gpkg` polygon centroid (exact inverse, no
   live OSM); T01's `recentre` is a *conditional* second shift (`geometry_extract.py:704-710`, fires only past a
   50 m threshold) so the emitter **forces `recentre=False`** rather than trusting it to be zero. Emit each
   vertex as `IDF + footprint_centroid_UTM − common_origin`, `common_origin = (floor(min cx), floor(min cy), 0)`
   over all footprint centroids (deterministic; keeps metres WebGL-float32-friendly), Z untouched. Store CRS
   `EPSG:32618` (`metadata.referenceSystem`), `common_origin` (T07 metadata block), and per-building
   `footprint_centroid_UTM` (CityObject attribute) → V07 absolute geo-ref recovers exactly as `UTM = vertex +
   common_origin`. **CP-Geometry reframed** (T03 test e, T14) to the exact round-trip *through the stored
   offsets*: `(CityJSON_vertex + common_origin) − footprint_centroid_UTM == source IDF (recentre=False) vertex`,
   ≤1 cm — still an exact faithfulness assertion, proving only a known rigid translation was applied. **Why A
   over B (per-building-local + render-time offset):** A is the standards-correct representation *and* delivers
   the coherent navigable neighbourhood §0 promises with faithfulness intact; B trades CityJSON interoperability
   for a more literal test phrasing — the wrong trade. *(Feeds T03, T07, T14; narrows T04.)*

> **Net effect on the plan:** no MVP scope change. Firm requirements gained: **T10's categorical legend must use
> sector hue-grouping + labels (30-archetype vocab)**; **T04's failed-building placeholder path is required**
> (the CityJSON emitter cannot render IDF-less buildings, and "never invisible" is binding); **T06/T07/T12 must
> implement provenance graceful-degrade** (the pilot itself is a legacy run). T04's footprint source is pinned
> to the archived `01_buildings.gpkg`. CP-2 gains an optional nyc_urban stress-check. Pilot = nyc_centre,
> pinned; its Temp-resident IDFs get archived first thing in T02.

---

*PLAN — OpenUBEM 3D interactive-visualization arc, MVP. Binding source-of-truth: the 15 `RESULT_V*.md` files
under `docs/docs_ACTIVE/3D/deepResearch/`. Markdown only; no `.py` under `docs/`. 2026-07-02.*
