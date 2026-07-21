# PLAN — Phase D: External-Data Fusion Precedence Layer (`_fusion_tier` / T12)

**Slug:** `input-imputation-phaseD-fusion`
**Date:** 2026-07-13
**Arc:** Input-Parameter Imputation ("OpenUBEM AI"). This is the **detailed execution plan for
task T12** of the parent plan
`docs/docs_ACTIVE/input/imputation/PLAN_input_imputation_implementation.md` (§6 T12, §7 CP-4). The
parent plan's §0 tracker + §8 progress log remain the binding arc record; this doc decomposes T12
into executable sub-tasks T12.1–T12.7 and pins the load-bearing decisions. Structurally symmetric to
the Phase-C plan `docs_Done/PLAN_phaseC_ml_imputer.md`.
**Binding contract:** OpenUBEM Stage-2.2 DESIGN §3E (imputation tier) + the M07 external-data-fusion
research report (`deepResearch/RESULT_M07_external_data_fusion.md`, Part C precedence rules).
**This plan may not contradict the DESIGN; on any conflict the executor STOPS and quotes the exact
lines.**

**Scope decision (user, 2026-07-13):** build **Overture first** as the primary global, runtime-fetchable
source (one new dependency: `duckdb`), **plus** local-file **LiDAR (nDSM zonal)** and **assessor**
adapters behind user-config paths, all in one pluggable source registry. **EUBUCCO / GHSL / street-view
imagery are documented-deferred** (Europe-only / raster-zonal / GPU lifts — the registry leaves room to
add them later without rework). **CP-4 gate = join-correctness + fill-rate + license/bundle guard**
(one manually-run real Overture LIVE_SMOKE against a committed real slice; **no cluster / no EnergyPlus
EUI leg** — fused values are authoritative ground truth, not a guess to be EUI-validated). **Ships
opt-in only** until the T12-ship user-sign-off.

---

## 0. Status at a glance

> Legend: `[x]` done · `[~]` in progress · `[ ]` not started · `[!]` blocked/needs decision.
> **Last updated:** 2026-07-13 (**🔒 PHASE D CLOSED — manager-audited + self-signed.** T12.1–T12.6 +
> CP-4a + CP-4 (real Overture LIVE_SMOKE, release `2026-06-17.0`, 1,667 buildings via anonymous DuckDB/S3;
> `height_m` 87.6% ground-truth fill) + T12-ship all done. `fusion` is now an enabled-by-default tier that
> is byte-identical for any run without a configured source (proven by two byte-identity tests). Gate suite
> **171 passed / 0 failed**. `enrich_semantics` reroute deferred to a future arc. The input-imputation
> arc's scoped work (Phase A–D) is COMPLETE — ready to file to `docs_DONE`.)

- [x] **T12.1** — fusion source-adapter protocol + registry + per-attribute precedence chains (no live network)
- [x] **T12.2** — Overture adapter (runtime DuckDB spatial query; committed-slice path for offline test)
- [x] **T12.3** — LiDAR nDSM zonal adapter + assessor join adapter (user-config paths, optional)
- [x] **T12.4** — wire `_fusion_tier` to the tier contract + `FUSED_<SOURCE>_<TIER>` tokens + opt-in config
- [x] **T12.5** — license/bundle guard (no restricted dataset vendored; allowlist + size cap)
- [x] **CP-4a** *(stop-checkpoint)* — **MET 2026-07-13** — fusion tier built + wired + unit-green (mock + committed synthetic fixtures, no live net) + no-fusion path byte-identical (`assert_frame_equal` + spy) + license guard green. Suite 170/0. Manager read `_fusion_tier`/`fuse`/the rewritten routing test directly (not trusted).
- [x] **T12.6** — CP-4 gate: real Overture LIVE_SMOKE — **MET 2026-07-13** (release `2026-06-17.0`, 1,667 buildings, anonymous DuckDB/S3; `height_m` fusion 87.6% ground-truth fill, all `FUSED_OVERTURE_HIGH`; misses fell through to hotdeck/groupmode; surfaced + fixed a real `year_built`-absent-from-Overture schema bug; `use_class` crosswalk 73.6% mapped)
- [x] **CP-4** *(gate)* — **MET 2026-07-13** — LIVE_SMOKE join correct + fill-rate reported + license/bundle guard green (real 279 KB CDLA-Permissive slice). Manager-audited (code read, no Opus pytest re-run).
- [x] **T12-ship** — **DONE + SIGNED 2026-07-13** (user-delegated decision). `IMPUTE_ENABLED_TIERS` → `("fusion","spatial","statistical")`; byte-identical for any unconfigured run (two byte-identity tests); gate suite **171/0**. `enrich_semantics` reroute kept OUT of Phase-D scope (future arc).
- [x] **🔒 PHASE D CLOSED** — 2026-07-13. Fusion tier shipped enabled-by-default; arc Phase A–D complete, ready to file to `docs_DONE`.
- [ ] **T13 (Phase E)** — frontier documentation (deep-generative/GNN/LLM out of scope) + optional isolated TabPFN note. Documented-deferred; not part of Phase D.

---

## 1. What Phase D delivers (and why it is different from A/B/C)

Phases A/B/C all **guess** a missing value from the observed stock (statistics, spatial neighbours, ML).
Phase D does the opposite: **fetch the truth first.** Every gap fillable by a reliable external join
(Overture, LiDAR, municipal assessor) is a gap OpenUBEM should **not** be statistically imputing at all —
it is a **data-acquisition** step, and it **sidesteps zero-fitted-params entirely** because a joined
value is an observation, not a fitted quantity (M07 Part C §3; parent §1 "External-data fusion" row).

The routing subsystem already reserves the slot: `_CANONICAL_TIER_ORDER = ("fusion", "spatial", "ml",
"statistical")` puts **fusion first**, so a join hit wins over every imputation tier, and a join **miss**
falls through to the existing spatial/ml/statistical fills. Phase D's whole job is to replace the
skeleton `_fusion_tier` (which today just raises `NotImplementedError("fusion tier is Phase D")`) with a
real per-attribute source-precedence layer, **without changing the default run** (fusion stays out of
`IMPUTE_ENABLED_TIERS` until the T12-ship user-sign-off).

> **The Phase-D question CP-4 answers:**
> *Does a real external join (Overture primary; LiDAR/assessor where the user supplies paths) fill
> morphology/semantic gaps (`height`/`levels`/`year_built`/`use_class`) with an authoritative value +
> a `FUSED_<SOURCE>` provenance token, correctly falling through to imputation on a join miss — proven
> once on a real external slice (not synthetic)?*

**Targets = morphology/semantic only** (identical to the Phase-C ML exclusion set): `height`, `levels`,
`year_built`, `use_class`. **Footprint completeness is explicitly OUT of scope** — geometry is never
imputed; missing/invalid footprints are dropped at Stage-1 acquisition (M07 Table 4 "do not impute
geometry"; `openubem/geometry/footprint.py` Tier-A drop convention). Envelope U-values / SHGC / COP /
load densities / setpoints stay on the PDE-from-standards path — fusion never touches them (same rule 7
as Phase C).

**Honest coverage caveat the plan builds in (M07 §4, the Ankara/Turkey case):** external coverage
degrades sharply outside the US/EU. USGS 3DEP LiDAR = zero coverage in Turkey; TKGM assessor data is
legally restricted. So Phase D is **US-first**, and imputation (A/B/C) **must still carry the load** on
a join miss — Phase D is additive precedence, never a replacement for the imputation tiers. This is why
the fusion tier falls through cleanly to spatial/statistical rather than hard-failing on a miss.

---

## 2. Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** Execute this plan; do not rewrite it. On DESIGN
   ambiguity **STOP and quote**.
2. **Never edit `main.py` (root), OVERVIEW, or DESIGN docs. No `.py` under `docs/`.**
3. **Zero-fitted-params is preserved *by construction* here** — a fused value is an observation, not a
   fitted quantity. But the discipline still binds: **no fusion source-selection, precedence order,
   join radius, or confidence cut-point may EVER be tuned to make simulated EUI match a validation
   anchor.** Precedence order = M07 Part C (cited, fixed); join tolerances = published/geometry
   conventions (cited, never swept). **No EUI column may appear in any join or adapter code path.**
   Enforce structurally where feasible (a test asserting no `*_eui*` column is read by the adapters).
4. **Mandatory provenance.** Every fused value carries a `FUSED_<SOURCE>_<TIER>` token **and** a
   confidence tier. **Directly-joined attribute → HIGH; a value *derived* from a joined one
   (e.g. `levels = max(1, LiDAR_height // 3.5)`) → MED.** Extend the parent §5G registry — do not invent
   a parallel vocabulary; record the exact token strings in the T12.4 progress-log entry for manager
   ratification into parent §5G (the Phase-C T11.2 protocol).
5. **Additive & opt-in — do NOT reroute `enrich_semantics` in T12.1–T12.6.** The fusion tier is reached
   only through `impute_missing` when a caller explicitly enables `fusion` for an attribute. The default
   `config.IMPUTE_ENABLED_TIERS = ("spatial", "statistical")` is **unchanged** — `fusion` is never in the
   default. The production enrichment path is untouched until T12-ship, which is USER-SIGN-OFF-gated.
6. **NO live network in the automated test suite** (project hard rule: no live-network integration tests
   until §5.3 is unblocked). Every unit test uses either a **mock adapter** or a **small committed real
   Overture slice fixture** (M07 §2 sanctions city-scale slices as bundled *test* fixtures). The single
   real live query is the **CP-4 LIVE_SMOKE only** — run **manually, once**, recorded in §8, and **never
   wired into the pytest suite** (satisfies both the no-live-network rule and the synthetic≠live
   blind-spot rule).
7. **Nothing large or license-restricted is bundled in the wheel** (M07 §2). Only small allowlisted
   city-slice test fixtures under an allowlisted path. T12.5 enforces this with a guard test.
8. **New dependencies: `duckdb` (Overture query) + `rasterio` (LiDAR nDSM zonal) only.** No `rasterstats`
   (do zonal stats manually with `rasterio.mask` + numpy — keeps the dep surface minimal, mirrors the
   Phase-C "sklearn only, no xgboost" discipline). Assessor join reuses the existing `geopandas`. Pin
   exact versions in `pyproject.toml` and record them in §8 (as Phase-C did for scikit-learn 1.9.0).
9. **Fusion is a data step, not a compute step — no cluster, no EnergyPlus in Phase D.** CP-4 is a join /
   fill-rate / license gate, evaluated locally. (If a future user ever wants an EUI-improvement study of
   fusion, it is a *separate* arc, not CP-4.)
10. **Default to no comments.** One short line only where the WHY is non-obvious.

---

## 3. File layout

```
openubem/
├── acquisition/
│   └── overture_fetcher.py   (NEW — T12.2: runtime DuckDB spatial query against Overture GeoParquet
│                                       (cloud endpoint OR a local committed slice path); mirrors
│                                       osm_fetcher.py's fetch-and-normalize shape)
├── semantic/
│   ├── fusion.py             (NEW — T12.1 FusionSource protocol + registry + per-attribute precedence;
│   │                                 T12.2 OvertureSource (wraps overture_fetcher); T12.3 LidarSource +
│   │                                 AssessorSource; T12.4 `fuse(gdf, attr, cfg) -> (value, token)`)
│   └── imputation.py         (MODIFY — T12.4: rewrite `_fusion_tier` to call `fusion.fuse(...)` and
│                                       return the (value, token) tier contract; NO other tier touched)
└── config.py                 (MODIFY — T12.4: fusion opt-in surface — FUSION_SOURCES_BY_TARGET,
                                        FUSION_OVERTURE_SLICE_PATH/ENDPOINT, FUSION_LIDAR_NDSM_PATH,
                                        FUSION_ASSESSOR_PATH + assessor field-map;
                                        `fusion` NOT added to IMPUTE_ENABLED_TIERS)

tests/
├── test_fusion.py            (NEW — T12.1–T12.4: protocol/registry, mock-adapter precedence, Overture
│                                     against a committed slice, LiDAR/assessor adapters, `_fusion_tier`
│                                     contract + no-fusion byte-identity + no-EUI structural guard)
└── test_fusion_license_guard.py (NEW — T12.5: bundle allowlist + size cap + license allowlist)

openubem/data/fixtures/fusion/   (NEW — small committed real slices for offline test ONLY; allowlisted)
└── overture_<cell>_slice.parquet + (optional) lidar/assessor mini-fixtures

docs/docs_ACTIVE/input/imputation/
├── PLAN_phaseD_fusion.md                     (this file — §8 progress log appended by executor)
└── PLAN_input_imputation_implementation.md   (parent — §0/§8 T12 lines updated by manager only)

scratchpad/  (throwaway — CP-4 LIVE_SMOKE driver; NEVER under docs/)
└── t12_cp4_live_smoke.py   (one real Overture query + join-rate/fill-rate report — run manually once)
```

**No files outside this list without a plan update.** Any figures → `results/phase_D/` (this arc's
figures live ONLY under the results folder, per the standing user constraint — never `openubem/outputs/`).

---

## 4. Dependency decisions (pre-decided — do not re-debate)

| Concern | Decision | Rationale |
|---|---|---|
| Overture access | **Runtime DuckDB spatial query** against Overture GeoParquet (cloud S3/Azure endpoint OR a local committed slice path); **new dep `duckdb`** + its `spatial` extension (`INSTALL spatial; LOAD spatial;`). **Nothing bundled** beyond small test slices. | Parent §4; M07 §2 — Overture ~150GB, only targeted spatial queries are viable; mirrors `osm_fetcher`. |
| LiDAR nDSM | **`rasterio` only**, zonal stats computed manually (`rasterio.mask.mask` per footprint → numpy mean/max), **no `rasterstats`.** nDSM raster path is a user-config path, runtime-read. | M07 Table 2 (USGS 3DEP nDSM); minimal dep surface (Phase-C "no extra libs" discipline). |
| Assessor / 3D-model | **Local file via existing `geopandas`** (vector/CSV with parcel geometry or PIN/BBL); spatial-overlap OR PIN join; a per-municipality **field-map** in config (PLUTO/MassGIS column names differ). No new dep. | M07 Table 1 (assessor = administrative ground truth); geopandas already present. |
| EUBUCCO / GHSL / street-view | **Documented-deferred — NOT built in Phase D.** The registry protocol leaves room to add them; a short note in §6 T13/Phase-E records the deferral with the M07 evidence. | Scope decision (user 2026-07-13): Europe-only / raster-zonal / GPU lifts, lower priority than Overture+LiDAR+assessor. |
| Bundling | **Only small allowlisted city-slice test fixtures** under `openubem/data/fixtures/fusion/`. No global footprint/raster dataset in the wheel. T12.5 guard enforces it. | M07 §2 licence/size verdict. |
| Confidence tiering | **Direct join → HIGH; derived value (levels-from-LiDAR-height) → MED.** Fixed, cited (M07 accuracy table); never swept. | Rule 4; matches the "authoritative observation = HIGH, heuristic derivation = MED" grade used across the arc. |
| Join geometry tolerance | **Centroid-within-polygon primary, else nearest-within-fixed-tolerance** (a published geometry convention, e.g. matching footprint centroid to the external polygon; tolerance cited, never EUI-swept). | M07 Table 1 join keys; zero-fitted-params (rule 3). |
| Cluster / EnergyPlus | **None in Phase D.** CP-4 is join/fill-rate/license, evaluated locally. | Rule 9; fused values are ground truth, not an EUI hypothesis. |

---

## 5. Source-of-truth verified facts (manager-grepped — executor does not re-derive)

**A. The T12 hook is live and already reachable.**
- `imputation.py:616-620` — `_fusion_tier(gdf, attr, mask, rng)` currently just
  `raise NotImplementedError("fusion tier is Phase D")` (labelled a Phase-D skeleton hook, never called
  by default because `fusion ∉ config.IMPUTE_ENABLED_TIERS`). **This is what T12.4 rewrites.**
- `imputation.py:543` — `_CANONICAL_TIER_ORDER = ("fusion", "spatial", "ml", "statistical")`. **fusion is
  FIRST**, so a join hit wins over spatial/ml/statistical; a join miss returns null and falls through.
  T12 changes **no** tier order — the slot is already correct.
- `imputation.py:836-841` — `_TIER_HANDLER_NAMES = {"fusion": "_fusion_tier", ...}`; `impute_missing`
  (`:844`) resolves handlers via `globals()` at call time (`:907-910`), so tests may monkeypatch
  `_fusion_tier` directly.

**B. The tier-handler contract every tier obeys** (parent §5D / Phase-C §5D): a handler
`f(gdf, attr, mask, rng)` returns **`(value, token)`** — two `pd.Series` aligned to `gdf.index`; `value`
is `NaN`/`None` for rows it declines; `token` is the provenance token for filled rows. `impute_missing`
fills `remaining & value.notna()`, stamps `provenance_{attr}`, appends flags via `prov.append_flag`, and
shrinks `remaining`. **`_fusion_tier` must return exactly this shape** — it is the first handler in the
loop, so any deviation corrupts every downstream tier. `_spatial_tier`/`_ml_tier` are the precedents to
copy (both accept HIGH/MED and discard LOW → fall through); **fusion never emits LOW** (a join either
hits, giving HIGH/MED, or misses, giving null).

**C. Config surface + opt-in discipline.**
- `config.py:84-86` — `# fusion/ml stay OUT of the default tuple until Phase D/C ship` +
  `IMPUTE_ENABLED_TIERS: tuple = ("spatial", "statistical")`. **T12.4 adds the fusion config constants
  but does NOT add `fusion` to this tuple** (opt-in only — mirrors how Phase C added
  `IMPUTE_ML_METHOD_BY_TARGET`/`IMPUTE_ML_FLOORS` without touching `IMPUTE_ENABLED_TIERS`).
- Config constants are read at **call time** (not import-time), so a test may monkeypatch them (the
  Phase-B/C pattern).

**D. The acquisition-fetcher precedent to mirror.** `openubem/acquisition/osm_fetcher.py::ingest_buildings`
fetches → normalizes → cleans → reprojects to an estimated UTM CRS → returns a `gpd.GeoDataFrame`. The
Overture fetcher (T12.2) mirrors this shape: a targeted spatial query (DuckDB against GeoParquet)
returns a normalized `gpd.GeoDataFrame` in a known CRS, ready for the spatial join. `openubem/acquisition/`
currently holds `osm_fetcher.py`, `epw_manager.py`, `climate_zone.py` — `overture_fetcher.py` joins them.

**E. M07 fusion precedence (Part C §1) — the fixed, cited order T12.1 encodes (trimmed to Phase-D scope:
Overture + LiDAR + assessor; EUBUCCO/GHSL deferred).** Per attribute, try sources in decreasing
confidence, then fall through to imputation:

| OpenUBEM attribute | Phase-D source precedence (built now) | Fall-through (existing tiers) |
|---|---|---|
| `height` / `levels` | LiDAR nDSM zonal → assessor/3D-model → Overture `height`/`num_floors` | spatial → statistical (levels-from-height heuristic / group median) |
| `year_built` | assessor (PIN/BBL) → Overture `year_built` (where populated) | ml (if enabled) → statistical (group mode) |
| `use_class` | assessor land-use code → Overture `primary_use` | statistical (stratified mode / size-cascade) |
| footprint | **OUT OF SCOPE** — geometry is dropped, never imputed (M07 Table 4) | — |

**F. M07 licence / bundle verdict (Part C §2) — the T12.5 guard encodes this.**
- **Redistributable & allowlisted for small test slices:** Overture (CDLA-Permissive-2.0 IDs / CC-BY-4.0
  data), Microsoft Footprints (ODbL-1.0), Google Open Buildings (CC-BY-4.0 / ODbL), EUBUCCO (ODbL-1.0),
  GHSL (CC-BY-4.0), USGS 3DEP (US-Gov public domain), most US assessor (public-domain / CC-BY).
- **BARRED from the wheel & from default runtime targets:** proprietary aggregators (CoStar, Zillow
  ZTRAX); CC-BY-**NC** / restrictive-ShareAlike sub-datasets (some EUBUCCO country slices); legally-
  restricted assessor (Turkey TKGM). The guard test asserts none of these classes is vendored.
- **Existing legit bundles to allowlist (do NOT flag):** `openubem/data/` already ships
  `construction/`, `schedules/`, `loads/`, `service_loads/`, `carbon/`, `climate_zones/`,
  `refrigeration/`, `epw_stations.csv`, `cbecs_pba_map.json`, `openstudio_archetypes.json`,
  `osm_to_use_class.json` — these are OpenUBEM's own reference tables, not external building datasets;
  the guard's scope is **new external-building/raster datasets**, not these.

**G. CP-4 definition (parent §7, lines 873-874, verbatim):** *"CP-4 — before T12 ships (Phase D).
External-data path requires a LIVE_SMOKE join against a real Overture/assessor slice + the license/bundle
guard, before it is allowed into a default run."* — i.e. join-correctness + license, **not** an EUI gate.
Consistent with the user's 2026-07-13 CP-4 scope decision.

**H. New deps confirmed absent** (grep of `pyproject.toml`, 2026-07-13): `duckdb` and `rasterio` are NOT
present; `geopandas >= 0.14` and `shapely >= 2.0` ARE. So T12.2 adds `duckdb`, T12.3 adds `rasterio`;
assessor reuses geopandas. (Phase-C precedent: scikit-learn was added to `[project] dependencies` + the
version recorded in §8.)

**I. Zero-fitted-params is structurally satisfied but still test-guarded.** A fused value is an
observation, so it cannot be "fitted to EUI." The residual risk is an adapter accidentally *reading* an
EUI column as a join feature — guard it with a `test_fusion.py` structural check mirroring
`eui_impact.TestNoImputerFeedback` (assert no `*_eui*`/`total_eui` column name appears in the adapters'
read paths).

---

## 6. Task list

> Each task: **What / Why / How / How to test.** All fusion logic lands in `semantic/fusion.py` (+ the
> Overture fetch in `acquisition/overture_fetcher.py`); all tests in `test_fusion.py` /
> `test_fusion_license_guard.py`. Sub-tasks are ordered; stop at CP-4a after T12.5.

### T12.1 — Fusion source-adapter protocol + registry + per-attribute precedence
- **What:** In `semantic/fusion.py`, define a `FusionSource` protocol/ABC with:
  `name: str`, `source_token: str` (e.g. `"OVERTURE"`), `available(cfg) -> bool` (config path/endpoint
  present), and `join(gdf, attr) -> pd.Series` (value aligned to `gdf.index`, `NaN` where no join, plus a
  parallel per-row `derived: bool` signal — or a 2nd Series — so T12.4 can grade direct=HIGH /
  derived=MED). A registry `{name → factory}` and a `precedence_for(attr, cfg) -> list[FusionSource]`
  returning the M07-ordered, *available* sources for that attribute (§5E table).
- **Why:** M07 Part C §1 — fusion is a precedence chain, not a single source; centralizing it keeps
  adding EUBUCCO/GHSL later a one-line registry entry. Parent §5D tier contract needs a clean producer.
- **How:** Pure interface + registry, **no live network, no new heavy dep yet.** `precedence_for` reads
  `config.FUSION_SOURCES_BY_TARGET` (per-attr ordered source-name list) intersected with `available()`.
  A `MockSource` for tests. **No EUI column ever read** (rule 3 / §5I).
- **How to test:** `test_fusion.py::TestRegistry` — registry round-trips; `precedence_for("year_built")`
  returns the configured order filtered to available; two mock sources chain (first-hit wins, second not
  called for a hit row, called for a miss row); a mock source that reads an EUI column trips the
  structural guard.

### T12.2 — Overture adapter (runtime DuckDB spatial query)
- **What:** `acquisition/overture_fetcher.py::fetch_overture(bbox|gdf_bounds, *, endpoint|slice_path)` →
  normalized `gpd.GeoDataFrame` of Overture buildings (columns → `height`, `num_floors`→`levels`,
  `class`/`subtype`→`use_class` raw, `year_built` where present, geometry). Then
  `fusion.OvertureSource.join(gdf, attr)` spatially joins the target `gdf` to the fetched Overture layer
  (centroid-within-polygon primary; nearest-within-tolerance fallback, §4) and returns the attribute
  Series (direct join → HIGH).
- **Why:** M07 Table 1 — Overture is the only global, deduplicated, runtime-fetchable, license-clean
  source; parent §4 pins DuckDB. It is the Phase-D primary.
- **How:** DuckDB + `INSTALL spatial; LOAD spatial;`; targeted bbox spatial query (mirror `osm_fetcher`'s
  fetch-normalize-reproject shape, §5D). **Offline-testable:** if `cfg.FUSION_OVERTURE_SLICE_PATH` is set,
  read that committed GeoParquet slice instead of the cloud endpoint — this is the ONLY path exercised by
  the automated suite (rule 6). Add `duckdb` to `pyproject.toml`, record the pinned version in §8.
- **How to test:** `test_fusion.py::TestOverture` — against a small committed real Overture slice fixture
  (`openubem/data/fixtures/fusion/overture_<cell>_slice.parquet`): a building overlapping an Overture
  polygon gets that polygon's `height`/`levels`/`use_class`; a building outside all polygons gets `NaN`
  (miss → fall-through); CRS mismatch is handled; **no live network call in the test.**

### T12.3 — LiDAR nDSM zonal adapter + assessor join adapter (user-config paths)
- **What:** `fusion.LidarSource` — reads a user-config nDSM raster (`cfg.FUSION_LIDAR_NDSM_PATH`),
  computes per-footprint zonal mean/max height (`rasterio.mask` + numpy), returns `height` (direct →
  HIGH) and, when the target is `levels`, the derived `max(1, height // 3.5)` (derived → MED).
  `fusion.AssessorSource` — reads a user-config assessor file (`cfg.FUSION_ASSESSOR_PATH`) + a field-map
  (`cfg.FUSION_ASSESSOR_FIELDS`, e.g. PLUTO `YearBuilt`/`BldgClass`/`NumFloors`), joins by PIN/BBL if
  present else spatial-overlap, returns `year_built`/`use_class`/`levels` (direct → HIGH).
- **Why:** M07 Table 4 — LiDAR/assessor are the *highest-accuracy* sources for height/year in the US
  (LiDAR <10 cm RMSEz; assessor = administrative ground truth), ranked ABOVE Overture in §5E. Optional
  because coverage is US/EU-centric (M07 §4).
- **How:** Both are **optional** — `available()` returns False when the config path is unset, so the
  source is silently skipped (no error). LiDAR: add `rasterio` to `pyproject.toml` (pin, record in §8);
  zonal stats manual (no `rasterstats`, rule 8). Assessor: reuse `geopandas`. The assessor field-map is a
  plain dict so a new municipality is a config edit, not a code change. **No bundled LiDAR/assessor data**
  (only a tiny synthetic/clipped mini-fixture for the test).
- **How to test:** `test_fusion.py::TestLidar`/`TestAssessor` — a footprint over a mini nDSM raster gets
  the zonal-mean height (direct HIGH) + derived levels (MED); an unset path → `available()` False →
  source skipped; an assessor mini-frame joins `year_built` by PIN and by spatial overlap; field-map
  remaps municipality-specific column names.

### T12.4 — wire `_fusion_tier` + `FUSED_<SOURCE>_<TIER>` tokens + opt-in config
- **What:** Rewrite `imputation.py::_fusion_tier(gdf, attr, mask, rng)` to call
  `fusion.fuse(gdf, attr, cfg)` which walks `precedence_for(attr, cfg)`, first available source with a
  non-null join wins per row, and returns the `(value, token)` two-Series contract (§5B). Emit
  `FUSED_<SOURCE>_<TIER>` (direct → `_HIGH`, derived → `_MED`; **never `_LOW`**). Add the `config.py`
  opt-in surface: `FUSION_SOURCES_BY_TARGET`, `FUSION_OVERTURE_SLICE_PATH`/`_ENDPOINT`,
  `FUSION_LIDAR_NDSM_PATH`, `FUSION_ASSESSOR_PATH`, `FUSION_ASSESSOR_FIELDS` — **do NOT add `fusion` to
  `IMPUTE_ENABLED_TIERS`.**
- **Why:** Parent §5D contract + rule 5 (opt-in). Without the wiring the tier stays a stub; the opt-in
  keeps the default run + CP-1 byte-identity intact.
- **How:** Keep the return-contract byte-identical to `_spatial_tier`. **Prove no-fusion path is
  byte-identical** (default `impute_missing()` never calls `_fusion_tier`; a monkeypatched spy confirms).
  Register the new tokens by **requesting a manager edit** to parent §5G (record exact strings +
  HIGH/MED cut-points in this task's §8 entry — the Phase-C T11.2 ratification protocol; executor does
  not edit parent §5G directly).
- **How to test:** `test_fusion.py::TestFusionTier` — with `per_input_tiers={"year_built":("fusion",
  "spatial","statistical")}` + a slice fixture, fusion fills overlapping rows with `FUSED_OVERTURE_HIGH`
  and misses fall to spatial/statistical; a LiDAR-derived `levels` row stamps `FUSED_LIDAR_MED`; default
  `impute_missing()` (fusion disabled) is byte-identical to pre-T12 (`assert_frame_equal`); the full CP-1
  + `test_imputation_routing` + `test_mask_recover` suites stay green unchanged.

### T12.5 — license/bundle guard
- **What:** `test_fusion_license_guard.py` — assert the wheel/repo vendors **no** restricted external
  building/raster dataset: (a) an **allowlist** of bundled fixture paths under
  `openubem/data/fixtures/fusion/` + a per-file **size cap** (e.g. ≤ a few MB — a slice, never a
  city-wide raster); (b) a **license allowlist** (ODbL / CC-BY / CDLA-Permissive / US-public-domain OK;
  CC-BY-NC / restrictive-ShareAlike / proprietary BARRED) checked against a small `LICENSES.md` /
  manifest the executor writes alongside the fixtures; (c) assert none of the existing legit
  `openubem/data/` reference tables (§5F) is flagged (scope = new external datasets only).
- **Why:** M07 §2 + rule 7 — license contamination of the open-source core is the one irreversible
  Phase-D risk; a joined runtime value is fine, a vendored restricted dataset is not.
- **How:** A pure filesystem/manifest test (no network). The manifest lists each bundled fixture with its
  source + license + size; the guard cross-checks the filesystem against the manifest and the license
  allowlist. Any fixture not in the manifest, over the cap, or under a barred license → test fails.
- **How to test:** the test IS the guard; add a negative case (a synthetic "restricted" fixture entry
  makes the guard fail) to prove it bites.

> ### 🛑 CP-4a — stop-and-report (after T12.5)
> The fusion tier is built, wired, and unit-green **before** any live query is run. **Gate:**
> `test_fusion.py` + `test_fusion_license_guard.py` fully green (mock adapters + committed slice, **no
> live network**); `test_imputation_routing` + `test_mask_recover` + the CP-1 gate suite green
> **unchanged** (no-fusion path byte-identical); the `FUSED_<SOURCE>_<TIER>` tokens recorded for manager
> §5G ratification; `duckdb`+`rasterio` pinned + recorded. Executor appends §8 entries and **waits for
> manager audit** before T12.6.

### T12.6 — CP-4 gate: real Overture LIVE_SMOKE + fill-rate + license
- **What:** ONE **manually-run** real Overture query (NOT in the pytest suite — rule 6) via
  `scratchpad/t12_cp4_live_smoke.py` on a real fixture cell: fetch the real Overture layer for the cell's
  bbox (live cloud endpoint), run `fuse(...)` for each target attribute, and report: (a) **join hit-rate**
  per attribute (% of buildings that got a fused value); (b) that hits carry the correct
  `FUSED_<SOURCE>_HIGH/MED` token; (c) that **misses fall through to imputation** (spatial/statistical
  fill, correct token); (d) **fill-rate lift** vs pure imputation (how many gaps fusion closed with
  ground truth); (e) a spot-check that ≥1 fused value matches the external source. Re-confirm the
  license/bundle guard is green. **No cluster / no EnergyPlus.**
- **Why:** CP-4 (parent §7 / §5G): the external-data path must be proven on a **real** slice before any
  default-run consideration — synthetic-fixture green ≠ live-path green (memory blind-spot rule). Fill-
  rate is the honest headline (how much ground truth fusion actually recovers); EUI is out of scope
  (fused = truth, rule 9).
- **How:** The driver commits the fetched slice as a fixture (so the flow becomes reproducible offline
  afterward), reports the metrics to §8, and **STOPS** for the user's ship decision. Record the Overture
  release/version queried. If the live endpoint is unreachable at run time, report that + run the smoke
  against the committed slice as a graceful fallback, flagging that the live leg is owed.
- **How to test:** the LIVE_SMOKE **is** the gate (report-only); the offline reproduction is covered by
  `test_fusion.py`.

> ### 🛑 CP-4 — the gate (after T12.6)
> **Ships (opt-in) if** the LIVE_SMOKE join is correct (hits→FUSED value+token, misses→imputation
> fallback), the fill-rate is reported, and the license/bundle guard passes. **Report the join/fill-rate
> result + license status to the user and STOP.** The fusion tier stays **opt-in** (`fusion ∉
> IMPUTE_ENABLED_TIERS`) regardless — promoting it to the default run is the separate T12-ship decision,
> which is the user's.

### T12-ship — promote `fusion` into the default run — 🔴 USER-SIGN-OFF ONLY
- **What:** *(Only after CP-4 passes AND the user accepts.)* Turn fusion from opt-in into a selectable/
  default tier: add `fusion` to `config.IMPUTE_ENABLED_TIERS` (or wire the fusion precedence into
  `enrich_semantics` ahead of the imputation tiers) and **re-establish the CP-1 byte-identity guarantee**
  for the enrichment path (a join that changes a value legitimately changes downstream EUI — that is the
  *point* of fusion, but it must be a deliberate, field-diffed, user-approved change, not a silent one).
- **Why:** Promoting a default-run behaviour is load-bearing and hard to reverse (mirrors the Phase-C
  T11.7 and E-R3-3 baseline-promotion gates: producing the comparison is authorized; changing the shipped
  default is not).
- **How:** Deferred design — scope T12-ship's exact tasks **after** CP-4, when the fill-rate numbers and
  the user's intent (US-only default? require explicit source paths? Overture-on-by-default?) are known.
  Options range from "ship opt-in only, `enrich_semantics` untouched" (zero risk) to "fusion-first by
  default where sources are configured" (requires a fresh byte-identity + coverage-degradation review,
  M07 §4). **Do not start T12-ship without the user's explicit go.**
- **How to test:** defined at T12-ship scoping; minimally a CP-1-style IDF field-diff if the production
  path changes, plus an ex-US graceful-degradation test (join miss everywhere → imputation still carries).

### T13 (Phase E) — frontier documentation (out of Phase-D scope, recorded for completeness)
- **What:** A short in-repo note (this arc dir) recording, with the M05/M06/M10 evidence, that
  deep-generative / GNN / LLM are **out of scope** (scale + zero-fitted-params + hallucination/
  provenance), plus the deferred EUBUCCO/GHSL/street-view fusion sources and the optional isolated
  TabPFN experimental track (never default). **Documented-deferred — not built.**
- **Why:** Ruling options out *with evidence* is a first-class deliverable (parent §6 T13); keeps "all
  data-driven" represented without letting an unvalidated method into results.
- **How / test:** markdown only; if ever built, it reuses the T08/T09 harness and must clear the same
  gates as T11/T12 before any promotion.

---

## 7. Stop-and-report checkpoints

- **CP-4a — after T12.5.** Fusion tier built + wired + unit-green + no-fusion path byte-identical +
  license guard green, **before** any live query is spent. (Catches a broken tier contract / a
  non-byte-identical default path / a license leak before the LIVE_SMOKE.)
- **CP-4 — after T12.6.** The gate. Report the real-slice join-correctness + fill-rate + license status;
  manager decides the ship question on these numbers (user delegated 2026-07-13).
- **T12-ship — manager decision (user-delegated 2026-07-13).** The user delegated the ship decision to the
  manager ("tu decides tu progress tu finis phase d"), so no user-sign-off is owed. Manager stance:
  enable `fusion` in the `impute_missing` router default tiers (byte-identical for any unconfigured run),
  and keep the `enrich_semantics` production reroute OUT of Phase-D scope (§5D-quarantined,
  CP-1-byte-identity-breaking — a separate future arc). Any change is still executed by a Sonnet employee
  + manager-audited, and must keep the unconfigured-run byte-identity proof green.

---

## 8. Progress log

*(Executor appends one entry per completed sub-task — format per CLAUDE.md §"Plan doc structure". Manager
may append audit notes. The binding arc record remains the parent plan §8; cross-reference entries there.)*

#### Manager — Phase-D plan authored — 2026-07-13
- Artifacts: `PLAN_phaseD_fusion.md` (this doc); parent `PLAN_input_imputation_implementation.md` §0
  "Progress" checklist updated (Phase D → PLANNING); `PROJECT_CHECKLIST.md` reconciled (imputation arc
  kept in `docs_ACTIVE` — the 2026-07-13 premature move to `docs_DONE` reverted, since Phase D is real
  remaining scoped work).
- Deviations: none (planning only). Scope set by user 2026-07-13: **Overture-first + LiDAR/assessor
  config-path adapters** in one registry (EUBUCCO/GHSL/imagery documented-deferred); **CP-4 =
  join-correctness + fill-rate + license/bundle guard**, no cluster/EUI leg.
- Test status: n/a (plan doc).
- Notes: Decomposed parent T12 into T12.1–T12.7 + CP-4a (build-complete) + CP-4 (gate) + the T12-ship
  user-sign-off gate, symmetric to the Phase-C plan. Pinned the load-bearing architecture: (1) the
  `fusion` slot is already first in `_CANONICAL_TIER_ORDER` and `_fusion_tier` is a live stub — T12 only
  fills it in, no tier-order change; (2) fusion sidesteps zero-fitted-params by construction (a join =
  observation), still test-guarded against EUI-column reads; (3) direct join → HIGH, derived value → MED,
  never LOW (miss → null → fall through to imputation); (4) NO live network in the automated suite (mock
  + committed real slice), the ONE live query is the CP-4 LIVE_SMOKE run manually once (satisfies both
  the no-live-network rule and the synthetic≠live blind-spot rule); (5) new deps `duckdb`+`rasterio`
  only, nothing large/restricted bundled (T12.5 license guard); (6) US-first with honest ex-US
  degradation (M07 §4) — imputation always carries a join miss. Opt-in only; `enrich_semantics`/default
  run untouched until the T12-ship user-sign-off.

#### T12.1 — Fusion source-adapter protocol + registry + per-attribute precedence — completed 2026-07-13
- Artifacts: `openubem/semantic/fusion.py` (`FusionSource` protocol, `_REGISTRY`/`register_source`/
  `get_source`, `precedence_for`, `_assert_no_eui_columns`, `_empty_value`). Tests:
  `tests/test_fusion.py::TestRegistry` (mock sources `_MockSource`/`_MockMissSource`/
  `_MockUnavailableSource`/`_MockEuiReaderSource` defined in the test file, registered/unregistered via
  an autouse fixture).
- Deviations: none. Mock adapters live in `tests/test_fusion.py` rather than `fusion.py` — test-only
  scaffolding, keeps the production module free of test fixtures; the plan's §3 file list has no separate
  test-support module.
- Test status: `pytest tests/test_fusion.py::TestRegistry -q` — 5 passed.
- Notes: `precedence_for(attr, cfg)` resolves `cfg` lazily (defaults to `openubem.config` at call time),
  mirroring `_ml_method_for`/`ImputeConfig.tiers_for` (rule/fact C) — tests may pass either a
  monkeypatched `config` module or an explicit fake `SimpleNamespace` cfg without global monkeypatching.

#### T12.2 — Overture adapter (runtime DuckDB spatial query) — completed 2026-07-13
- Artifacts: `openubem/acquisition/overture_fetcher.py` (`fetch_overture`, `_fetch_live`, `_normalize`);
  `openubem/semantic/fusion.py::OvertureSource` + `_spatial_join_positions`/`_crosswalk_use_class`/
  `_load_use_class_crosswalk`; fixture `openubem/data/fixtures/fusion/overture_testcell_slice.parquet`
  (2-row synthetic GeoParquet, EPSG:32618, columns id/height/num_floors/class/subtype/year_built/geometry
  mimicking the real Overture Buildings schema). Tests: `tests/test_fusion.py::TestOvertureFetch` (2),
  `TestOvertureSource` (7).
- Deviations (flagged, within the rule-4 chicken-and-egg sanction):
  1. The committed synthetic fixture uses a **projected CRS (EPSG:32618)**, not Overture's real
     EPSG:4326 — keeps the offline join-tolerance arithmetic in plain metres, no degree/metre
     conversion. `test_crs_mismatch_is_handled` separately proves the reprojection code path by
     constructing a target gdf in EPSG:4326 against the EPSG:32618 fixture and asserting the join still
     hits — so CRS-mismatch handling is genuinely exercised even though the fixture itself is projected.
     Real EPSG:4326 Overture data is exercised end-to-end only at T12.6 (not this task).
  2. `duckdb`'s `spatial`/`httpfs` extensions load ONLY inside `_fetch_live` (the live-endpoint branch,
     reached exclusively by the future manual T12.6 driver) — the `slice_path` branch (the only one any
     test calls) reads the fixture via `gpd.read_parquet`, no `duckdb` import at all. Rationale:
     `INSTALL spatial`/`INSTALL httpfs` require a network download on a machine without a pre-cached
     extension (verified network access exists in THIS dev sandbox, but a clean CI checkout is not
     guaranteed to have the extension cached) — confining DuckDB to the untested live leg keeps the
     automated suite genuinely, robustly network-free (rule 6), not merely network-free-by-luck. `duckdb`
     is still a real, exercised dependency: `_fetch_live` uses it for the live Overture cloud query,
     following Overture's own `bbox` struct-column pushdown convention (no `ST_` function needed even
     there).
  3. `use_class` crosswalk reuses the existing `openubem/data/osm_to_use_class.json::tag_to_use_class`
     table (Overture's `class`/`subtype` vocabulary overlaps OSM's — Overture ingests OSM as a source)
     rather than inventing a new Overture-specific crosswalk — a fixed, already-pinned, non-invented
     resource.
- Test status: `pytest tests/test_fusion.py -k Overture -q` — 9 passed.
- Notes: nearest-within-tolerance matches are graded HIGH, same as centroid-within-polygon — both are
  *direct* field joins (no computed transformation), only the geometric matching rule differs; only a
  value *derived from* a joined field (LiDAR height→levels, T12.3) is graded MED, per plan §2 rule 4's
  binary direct/derived split.

#### T12.3 — LiDAR nDSM zonal adapter + assessor join adapter — completed 2026-07-13
- Artifacts: `openubem/semantic/fusion.py::LidarSource`, `_zonal_mean_height` (manual `rasterio.mask` +
  numpy, no `rasterstats`), `AssessorSource`, `_load_assessor`. Fixtures:
  `openubem/data/fixtures/fusion/lidar_testcell_ndsm.tif` (50×50 px synthetic nDSM, one footprint at a
  uniform 24.5 m, nodata=-9999 elsewhere), `assessor_testcell.gpkg` (2-parcel synthetic vector,
  BBL/YearBuilt/BldgClass/NumFloors columns). Tests: `tests/test_fusion.py::TestLidarSource` (4),
  `TestAssessorSource` (4).
- Deviations: none beyond the T12.2 synthetic-fixture note (rule 4). Derived-levels uses the existing
  pinned `config.FLOOR_TO_FLOOR_M` (3.5 m) rather than a new hardcoded constant, matching the plan's own
  worked example (`levels = max(1, LiDAR_height // 3.5)`).
- Test status: `pytest tests/test_fusion.py -k "Lidar or Assessor" -q` — 8 passed.
- Notes: `AssessorSource` does NOT crosswalk its `use_class` field (unlike Overture) — per plan §6 T12.3
  ("a new municipality is a config edit, not a code change"), the raw assessor field value is assumed
  already in OpenUBEM's canonical vocabulary via the user's own field-map; no crosswalk logic exists for
  assessor by design.

#### T12.4 — wire `_fusion_tier` + `FUSED_<SOURCE>_<TIER>` tokens + opt-in config — completed 2026-07-13
- Artifacts: `openubem/semantic/fusion.py::fuse`; `openubem/semantic/imputation.py::_fusion_tier`
  (rewritten — ONLY this function touched, no other tier code changed); `openubem/config.py`
  (`FUSION_SOURCES_BY_TARGET`, `FUSION_OVERTURE_SLICE_PATH`, `FUSION_OVERTURE_ENDPOINT`,
  `FUSION_LIDAR_NDSM_PATH`, `FUSION_ASSESSOR_PATH`, `FUSION_ASSESSOR_FIELDS` — `fusion` NOT added to
  `IMPUTE_ENABLED_TIERS`). Tests: `tests/test_fusion.py::TestFusionTier` (5), `TestNoEuiColumnEverRead`
  (2).
- **`FUSED_<SOURCE>_<TIER>` tokens for manager §5G ratification** (exact strings the code emits):
  - `FUSED_OVERTURE_HIGH` — direct Overture field join (height/levels/year_built/use_class-crosswalked).
  - `FUSED_LIDAR_HIGH` — direct LiDAR nDSM zonal-mean height join.
  - `FUSED_LIDAR_MED` — derived `levels = max(1, floor(height / config.FLOOR_TO_FLOOR_M))` from a
    LiDAR-joined height.
  - `FUSED_ASSESSOR_HIGH` — direct assessor field join (PIN/BBL, or spatial-overlap when no PIN).
  - `FUSED_OVERTURE_MED` / `FUSED_ASSESSOR_MED` — reserved by the grammar (no derived-value code path
    exists for Overture or assessor in this Phase-D scope; never emitted today).
  - Cut-point: direct field join → HIGH; a value *computed from* a joined field → MED; fusion never emits
    `_LOW` (a miss returns null and falls through to spatial/ml/statistical) — structurally enforced in
    `fuse()` (only two possible suffixes, gated by each source's `derived: bool` return).
  - All tokens parse cleanly under the existing `provenance.parse_token` grammar (`{METHOD}_{SOURCE}_
    {TIER}`), e.g. `FUSED_LIDAR_MED` → `("FUSED", "LIDAR", "MEDIUM")`; `provenance.CONFIDENCE_WEIGHT`
    already grades it correctly (method="FUSED" ≠ "OBSERVED" → imputed, weighted by tier) — no
    `provenance.py` change needed. No parent §5G edit made by this executor (per protocol); recording
    here for manager ratification.
- Deviations (flagged — **requires manager attention**): `tests/test_imputation_routing.py` was touched,
  outside the plan §3 file list. `TestForceEnabledSkeletonStubs::test_fusion_force_enabled_raises_
  not_implemented` pinned the PRE-T12 stub behaviour (`_fusion_tier` raises `NotImplementedError`) —
  definitionally superseded once T12.4 replaces the stub with a real tier: with no source configured for
  the attribute (the test's own scenario), `fuse()` now correctly returns an all-null result and the row
  falls through unfilled, exactly mirroring the EXISTING `test_ml_force_enabled_below_floor_falls_through`
  test in the same file/class — Phase C's T11.3 already established this precedent (rewriting a
  stub-pinning test when its stub becomes real, in this same class). Renamed/rewrote the one stale test
  to `test_fusion_force_enabled_no_source_configured_falls_through` (asserts the new correct
  fall-through, no exception) and updated the class/module docstring's point (5) to match. No other test
  in the file was touched; the file's other 18 tests are byte-unchanged and pass. Flagging explicitly
  because the plan's CP-4a gate text says this file stays green "unchanged" and it is not in the §3 list —
  judged a necessary, precedented consequence of building T12.4 as specified, not a scope violation, but
  exactly the kind of deviation the plan's own protocol asks to be surfaced rather than silently made.
- Test status: full CP-4a gate run — `pytest tests/test_fusion.py tests/test_fusion_license_guard.py
  tests/test_imputation_routing.py tests/test_mask_recover.py tests/test_imputation.py
  tests/test_tierB_provenance.py tests/test_vintage_donor.py tests/test_levels_groupwise.py
  tests/test_spatial_impute.py tests/test_provenance.py -q` → **170 passed, 0 failed**.
- Notes: `test_default_impute_missing_never_calls_fusion_tier_byte_identical` proves the no-fusion path
  never calls `_fusion_tier` (monkeypatched spy, zero calls) AND that the input `gdf` is left untouched —
  the byte-identity requirement (rule 5) is met.

#### T12.5 — license/bundle guard — completed 2026-07-13
- Artifacts: `tests/test_fusion_license_guard.py` (manifest parser + `check_manifest` pure checker — all
  guard logic lives in the test file per plan §6 T12.5 "the test IS the guard", no separate production
  module, consistent with §3's file list); `openubem/data/fixtures/fusion/LICENSES.md` (3-row manifest:
  file / source / license / declared size); `openubem/data/fixtures/__init__.py` +
  `openubem/data/fixtures/fusion/__init__.py` (setuptools package discovery) + a
  `pyproject.toml` package-data entry `"openubem.data.fixtures.fusion"`.
- Deviations: none. Negative-case tests (`TestGuardBites`) call `check_manifest` directly on synthetic
  bad rows (barred license, oversized entry) rather than mutating the real fixture directory — proves the
  checker bites without touching the real, already-passing manifest.
- Test status: `pytest tests/test_fusion_license_guard.py -q` — 10 passed.
- Notes: fixture sizes are 15,647 / 10,386 / 98,304 bytes — all well under the 5 MB cap; licensed
  `CDLA-Permissive-2.0` (Overture-mimicking slice) / `public-domain` (LiDAR/assessor mimicking USGS
  3DEP / a US municipal assessor extract) — both allowlisted per M07 §2 / plan §5F. The guard explicitly
  never scans `openubem/data/{construction,schedules,loads,...}` (existing legit OpenUBEM reference
  tables) — verified by `test_existing_legit_data_reference_tables_are_out_of_scope`.

#### Manager — CP-4a AUDIT: MET — greenlit T12.6 — 2026-07-13
- Artifacts audited (read directly, not trusted from the report): `openubem/semantic/fusion.py`
  (`fuse`, `precedence_for`, `_assert_no_eui_columns`, all four sources), `openubem/semantic/imputation.py::_fusion_tier`
  (rewritten), `openubem/acquisition/overture_fetcher.py`, `openubem/config.py` fusion block, the rewritten
  `tests/test_imputation_routing.py::test_fusion_force_enabled_no_source_configured_falls_through`, and the
  fixtures + `LICENSES.md`.
- **Verdict: CP-4a MET.** All gate conditions confirmed: (1) full imputation-relevant suite
  `pytest test_fusion + test_fusion_license_guard + test_imputation_routing + test_mask_recover + test_imputation
  + the CP-1 gate suite` → **170 passed / 0 failed** (manager re-ran, 3.22s). (2) `_fusion_tier` obeys the
  `(value, token)` two-Series contract exactly (dtype-aware, no-op on empty mask, delegates to `fuse`, fills
  only masked rows — mirrors `_ml_tier`); NO other tier code touched. (3) `fuse()` walks `precedence_for`,
  first-hit-wins per row, emits `FUSED_<SOURCE>_HIGH` (direct) / `_MED` (derived), never `_LOW`; remaining-shrink
  correct. (4) No-EUI structural guard (`_assert_no_eui_columns`) present in every adapter AND in `fuse()` —
  zero-fitted-params structurally enforced. (5) No-fusion path byte-identical (spy proves default `impute_missing`
  never calls `_fusion_tier` + `assert_frame_equal`). (6) License guard bites (negative cases fail on barred
  license / oversized), existing legit `openubem/data/` tables out of scope.
- **Deviations ratified:**
  1. **`FUSED_<SOURCE>_<TIER>` tokens → ADDED to parent §5G** (manager edit): `FUSED_OVERTURE_HIGH`,
     `FUSED_LIDAR_HIGH`, `FUSED_LIDAR_MED` (levels-from-height derived), `FUSED_ASSESSOR_HIGH`; grammar reserves
     `FUSED_OVERTURE_MED`/`FUSED_ASSESSOR_MED` (no derived path today). Cut-point = direct join→HIGH,
     computed-from-a-join→MED, miss→null (never LOW). Parses under existing `provenance.parse_token`; no
     `provenance.py` change needed. Ratified into parent §5G registry.
  2. **`tests/test_imputation_routing.py` touched** (outside §3 file list) — the one pre-T12 stub-pinning test
     `test_fusion_force_enabled_raises_not_implemented` rewritten to `..._no_source_configured_falls_through`.
     Read directly: the new test HONESTLY asserts the correct fall-through (force-enabled fusion with no source
     configured returns null, no exception), not a weakened assertion. Exactly the Phase-C T11.3/T11.6-STEP-0
     precedent (rewrite a stub-pinning test when the stub becomes real). **Ratified.**
  3. **DuckDB confined to the live `_fetch_live` branch** (offline `slice_path` uses `gpd.read_parquet`) —
     sound (keeps the automated suite robustly network-free per rule 6). **CARRY-FORWARD to T12.6/CP-4:** the
     live DuckDB `INSTALL spatial`/`httpfs` + real Overture cloud query path is therefore UNEXERCISED by any
     test — the CP-4 LIVE_SMOKE is its first real run; the executor must confirm DuckDB actually loads its
     extensions + returns a real slice (or gracefully fall back + flag the live leg owed).
  4. Synthetic fixtures use EPSG:32618 (with a dedicated CRS-mismatch test) + reuse `osm_to_use_class.json`
     for the Overture `use_class` crosswalk. **CARRY-FORWARD to T12.6:** the LIVE_SMOKE must report the real
     EPSG:4326 Overture `use_class` crosswalk hit-rate (the OSM crosswalk may miss Overture-specific class
     values — an accuracy caveat, not a blocker).
  5. Mock adapters + guard logic live in the test files (test-only scaffolding) — clean, ratified.
- Test status: manager re-ran the CP-4a gate suite → 170 passed / 0 failed.
- Notes: **CP-4a GREENLIT → T12.6 DISPATCHED** (fresh Sonnet: the manual real-Overture LIVE_SMOKE +
  join/fill-rate/license report). Hard-STOP at CP-4 for the user's ship decision; T12-ship stays
  user-sign-off-only — NOT to be started autonomously.

#### T12.6 — CP-4 gate: real Overture LIVE_SMOKE + fill-rate + license — completed 2026-07-13
- Artifacts: `scratchpad/t12_cp4_live_smoke.py` (manual driver, NOT wired into pytest, per rule 6) +
  `scratchpad/t12_cp4_live_smoke_output.log` (full run transcript). Committed fixture:
  `openubem/data/fixtures/fusion/overture_nyc_centre_slice.parquet` (279,284 bytes; RAW Overture schema
  — `id/height/num_floors/class/subtype/geometry`, EPSG:4326, bbox-clipped to the `nyc_centre` fixture
  cell — same raw-schema convention as the T12.2 synthetic fixture, so `fetch_overture(slice_path=...)`
  applies `_normalize` identically on replay). `LICENSES.md` manifest row added (`CDLA-Permissive-2.0`,
  279284 bytes, well under the 5MB cap). Code fix (see Deviations):
  `openubem/acquisition/overture_fetcher.py::_fetch_live`.
- **Overture release queried: `2026-06-17.0`** — the latest of only two release folders that exist under
  `s3://overturemaps-us-west-2/release/` at run time (`2026-05-20.0`, `2026-06-17.0`; confirmed via a
  direct S3 `ListBucketResult` query, not guessed).
- **DuckDB live path: CONFIRMED WORKING (carry-forward item #3 CLOSED).** `duckdb==1.5.4`,
  `INSTALL httpfs; LOAD httpfs;` (~0.03-0.05s) and `INSTALL spatial; LOAD spatial;` (~0.06-0.08s) both
  succeeded; `SET s3_region='us-west-2';` + a bbox-pushdown query against
  `s3://overturemaps-us-west-2/release/2026-06-17.0/theme=buildings/type=building/*` returned **1,667 real
  Overture buildings** for the `nyc_centre` bbox in 67-74s (two full runs). Access is genuinely anonymous/
  unsigned (no AWS credentials present anywhere on this machine — `env | grep -i aws` and `~/.aws` both
  empty) — reproducible by any user with no AWS account, confirming Overture's public-bucket claim.
- **Real fixture cell: `nyc_centre`** (`docs/docs_VALIDATION/validations/overAll/results/phaseE/nyc_centre/01_buildings.gpkg`,
  738 real OSM buildings, EPSG:32618, bbox reprojected to EPSG:4326 = `(-73.9911, 40.7475, -73.9725,
  40.7600)` — Manhattan Midtown). `use_class` was derived in the driver via
  `building_classifier._normalise_use_class` with the genuine self-consistency fix that a `score==0.0`
  ("unknown", no OSM tag matched at all — 608/738 rows) is NaN'd out as a real semantic gap, not
  pre-filled with the literal string `"unknown"` (which would have made `missing_before==0` and defeated
  the point of the exercise).
- **Per-attribute report (N=738):**

  | attr | missing_before | join hit-rate (all 738) | fusion-only fill of the real gaps | fill-rate lift | combined (fusion+spatial+statistical) fill |
  |---|---|---|---|---|---|
  | `height_m` | 121 (16.4%) | 721/738 = 97.7% | **106/121 = 87.6%** (`FUSED_OVERTURE_HIGH`) | 106 gaps closed with ground truth | 121/121 (106 FUSED + 8 `HOTDECK_NEIGHBOR_MED` + 7 `GROUPMODE_MED`) |
  | `levels` | 602 (81.6%) | 134/738 = 18.2% | **0/602 = 0%** | 0 (see note) | 602/602, 100% fallback (565 `GROUPMODE_MED`, 35 `HOTDECK_NEIGHBOR_MED`, 2 `HOTDECK_NEIGHBOR_HIGH`) |
  | `year_built` | 580 (78.6%) | **0/738 = 0.0% (structural, see Deviations)** | 0/580 = 0% | 0 (structural) | 580/580, 100% fallback (542 `GROUPMODE_MED`, 31 `HOTDECK_NEIGHBOR_HIGH`, 7 `HOTDECK_NEIGHBOR_MED`) |
  | `use_class` | 608 (82.4%) | 128/738 = 17.3% | **2/608 = 0.3%** (`FUSED_OVERTURE_HIGH`) | 2 gaps closed with ground truth | 608/608 (2 FUSED + 606 `GROUPMODE_MED`) |

  `levels`/`use_class` note: the 134/128 overall Overture hits are NOT independent of which target rows
  already had an observed value — in this dense already-well-mapped Manhattan tile, Overture's
  `num_floors`/`class` coverage overlaps almost entirely with buildings OSM *already* had a level/tag
  for, leaving near-zero overlap with the genuinely missing rows. This is an honest, non-cherry-picked
  finding (not a bug — verified by re-deriving the join positions independently for the crosswalk check
  below and cross-referencing against `provenance_levels`'s 136 `OSM_OBSERVED` rows, consistent with the
  134 figure). `height_m` behaves oppositely — Overture's `height` field is dense city-wide (buildings
  Overture derives from LiDAR/3D-model sources regardless of OSM tagging state) and delivers a genuine
  87.6% fill-rate lift.
- **Token correctness:** every hit-row token observed was `FUSED_OVERTURE_HIGH` (never `_MED` — Overture
  never derives a value in this arc, only `LidarSource` does, per T12.3/T12.4; never `_LOW`, structurally
  enforced by `fuse()`). Asserted in the driver (`bad_tokens` check) — did not merely eyeball it.
- **Miss -> imputation fallback: CONFIRMED.** For every attribute, enabling `("fusion", "spatial",
  "statistical")` (`("fusion", "statistical")` for `use_class` — `_statistical_tier`'s self-strat guard
  already covers it, `spatial` adds nothing extra there) filled 100% of the real gaps, with non-`FUSED`
  rows correctly carrying `HOTDECK_NEIGHBOR_HIGH/MED` or `GROUPMODE_MED` (asserted no `FUSED` token
  leaked onto a fallback-filled row).
- **Spot-check (plan §6 T12.6(e)):** 3 sample rows printed in the log — e.g. target `osm_id='way/42496314'`
  (`height_m` NaN) matched Overture `id='f3cd195c-...'` with `height=212.3`; `fuse('height_m')` returned
  `value=212.3, token='FUSED_OVERTURE_HIGH'`, exactly equal to the external record's `height` field (two
  more rows same pattern, 172.3m and 130.6m). Ground truth match confirmed, not merely structural.
- **`use_class` crosswalk hit-rate on REAL Overture class/subtype values (carry-forward item #4
  CLOSED):** of 174 real target-cell rows that spatially matched an Overture building with a non-null
  `class`/`subtype` value, **128/174 = 73.6% mapped** via the existing `osm_to_use_class.json` crosswalk;
  **46/174 = 26.4% did NOT map.** 6 distinct unmapped raw values: `entertainment`, `parking`, `roof`,
  `service`, `toilets`, `train_station`. This is a real, quantified accuracy caveat (not a blocker per
  the carry-forward note) — the OSM-derived crosswalk misses roughly a quarter of Overture's own
  `class`/`subtype` vocabulary in a real dense-urban sample; a future arc could extend
  `osm_to_use_class.json` with these 6 (and likely more, at broader geographic sampling) if `use_class`
  fusion coverage needs to improve.
- **Deviations (flagged — code fix required to make the live leg run at all):**
  1. **`_fetch_live`'s SELECT list referenced a `year_built` column that does not exist in the real
     Overture Buildings schema** — confirmed via `DESCRIBE SELECT * FROM read_parquet(...)` against the
     live release: the real schema is `id/names/sources/level/height/min_height/is_underground/
     num_floors/num_floors_underground/min_floor/subtype/class/facade_color/facade_material/
     roof_material/roof_shape/roof_direction/roof_orientation/roof_color/roof_height/geometry/
     has_parts/version/bbox/theme/type` — **no age/vintage field at all.** The original query (written
     at T12.2, before any live run existed to catch this) crashed with `Binder Error: Referenced column
     "year_built" not found`. **Fixed** by dropping `year_built` from the SELECT (kept the plan's
     `_OVERTURE_ATTR_COLUMN`/`_normalize` mapping untouched — `_normalize` already falls back to NaN when
     the raw frame lacks the column, so no other code needed to change). Net effect: Overture's
     `year_built` fusion source is a **structural, permanent 0% hit rate on real data**, not a
     configuration or coverage gap — recorded here for the manager's §5E precedence-table awareness (the
     `year_built` row's "Overture year_built (where populated)" fall-through is now known to never
     populate from Overture; `assessor` remains the only working `year_built` fusion source).
  2. Also switched the geometry column extraction from a bare `geometry` select to explicit
     `ST_AsWKB(geometry) AS geometry` (the spatial extension's native `GEOMETRY` type needs an explicit
     WKB cast for a reliable Arrow/pandas round-trip; untested previously since no live run had happened)
     and added `SET s3_region='us-west-2';` (needed for a stable anonymous/unsigned read against
     Overture's public bucket; also previously untested).
  3. `use_class` gap definition in the driver (`score==0.0` -> NaN) is driver-only scaffolding, not a
     `fusion.py`/`imputation.py` change — flagged for transparency, not a plan-file-list violation (the
     plan's §3 list already reserves `scratchpad/t12_cp4_live_smoke.py` for exactly this kind of
     one-off driver logic).
  4. No other `fusion.py`/`imputation.py`/`config.py` code touched. `IMPUTE_ENABLED_TIERS` untouched.
     `enrich_semantics` untouched.
- Test status: `pytest tests/test_fusion.py tests/test_fusion_license_guard.py -q` → **39 passed** (with
  the new real fixture on disk). Full CP-4a gate suite re-run (`test_fusion` + `test_fusion_license_guard`
  + `test_imputation_routing` + `test_mask_recover` + `test_imputation` + `test_tierB_provenance` +
  `test_vintage_donor` + `test_levels_groupwise` + `test_spatial_impute` + `test_provenance`) → **170
  passed, 0 failed** — unchanged from the CP-4a audit, confirming the T12.6 fixture/code fix caused no
  regression.
- Notes: this was genuinely the DuckDB live leg's first-ever execution (per the CP-4a manager audit's
  carry-forward item #3) and it did NOT work out of the box — it surfaced a real schema-assumption bug
  (`year_built`) that no amount of synthetic/mock testing could have caught, which is exactly the
  synthetic≠live blind-spot this LIVE_SMOKE exists to catch. Did **not** flip any default, touch
  `config.IMPUTE_ENABLED_TIERS`, or reroute `enrich_semantics` — `fusion` stays opt-in only.
  Stopped here for CP-4.

---

### 🛑 CP-4 REACHED — 2026-07-13 — reporting for the user's ship decision

**Gate criteria (plan §6, the `> ### 🛑 CP-4` block) — status:**
- LIVE_SMOKE join is correct: **YES.** Hits carry `FUSED_OVERTURE_HIGH` (never `_MED`/`_LOW` on this real
  run); misses fall through to `spatial`/`statistical` with correct non-`FUSED` tokens; asserted
  programmatically in the driver, not eyeballed.
- Fill-rate reported: **YES**, per-attribute table above — headline: `height_m` fusion alone closed
  **87.6%** of real gaps with ground truth; `levels`/`use_class` fusion closed only **0%/0.3%** of real
  gaps in this particular dense-urban tile (Overture's floor-count/class coverage overlaps almost
  entirely with rows OSM already had); `year_built` fusion closes **0%** of gaps **structurally** (the
  real Overture schema has no year_built field at all — assessor is the only working source for that
  attribute).
- License/bundle guard passes: **YES** — `pytest tests/test_fusion_license_guard.py -q` green with the
  new real fixture (279,284 bytes, `CDLA-Permissive-2.0`, both under the 5MB cap and on the allowlist).
- DuckDB live extensions load + return real rows: **YES**, confirmed (release `2026-06-17.0`, 1,667 real
  buildings, anonymous/unsigned S3 access, no credentials needed) — carry-forward item #3 closed.
- `use_class` crosswalk hit-rate on real Overture values: **73.6%** mapped / **26.4%** unmapped (6
  distinct unmapped raw values) — carry-forward item #4 closed, quantified as required, not a blocker.

**Fusion stays opt-in.** `fusion ∉ config.IMPUTE_ENABLED_TIERS` (unchanged); `enrich_semantics` was not
rerouted; no default was flipped. This executor did **not** start T12-ship (🔴 user-sign-off-only, plan
§6). **Awaiting the user's ship decision** on: (a) whether the demonstrated fill-rate profile
(height_m strong, levels/use_class weak in dense-urban NYC, year_built structurally absent from Overture)
is worth promoting `fusion` into a default/opt-in-selectable tier at all, given assessor/LiDAR would need
real per-municipality config to do meaningfully better than Overture alone; (b) whether the 6 unmapped
`use_class` values are worth adding to `osm_to_use_class.json` before any promotion.

---

#### Manager — CP-4 AUDIT + T12-ship DECISION (user-delegated) — 2026-07-13

**Ship decision authority:** the user delegated the ship call to the manager (2026-07-13, verbatim:
"pas besoin, si possible tu decides tu progress tu finit de phase d") — the 🔴 user-sign-off gate on
T12-ship is retired for this arc and replaced by a manager decision.

**CP-4 audit (read the load-bearing code + this §8, no pytest re-run in the Opus session per the
efficiency instruction):**
- Read `overture_fetcher.py::_fetch_live` — the `year_built` fix is genuine and honest: the real
  Overture Buildings theme has **no** vintage column (`DESCRIBE`-confirmed), the original SELECT crashed
  with a Binder Error on its first live invocation, the fix drops `year_built` and lets `_normalize`
  fall it back to NaN. This is exactly the synthetic≠live blind-spot the LIVE_SMOKE exists to catch
  ([[feedback_synthetic_test_blind_spots]]) — not scope creep. `ST_AsWKB` + `SET s3_region` are
  minimal enablers for the real anonymous S3 read. Carry-forward item #3 (live DuckDB leg unexercised)
  is now **CLOSED** — 1,667 real buildings returned, anonymous/unsigned, reproducible.
- Read `fusion.fuse` / `precedence_for` / `OvertureSource.available` + `imputation._fusion_tier` —
  **byte-identity of an unconfigured run is structurally guaranteed:** `precedence_for` keeps only
  sources whose `available(cfg)` is True; every source's `available` requires a configured path
  (all `None` by default) → `fuse` returns all-null → `_fusion_tier` is a no-op fall-through. duckdb/
  rasterio are imported lazily inside the `join()` methods, never reached at empty config. So enabling
  `fusion` in the default tier tuple changes **nothing** for any run that does not configure a source.
- Fill-rate profile is honest and non-cherry-picked: `height_m` 87.6% ground-truth fill (Overture's
  height is LiDAR/3D-derived, dense city-wide); `levels`/`use_class` ~0% in this already-well-mapped
  Manhattan tile (Overture's coverage overlaps the rows OSM already had — a real coverage
  characteristic, correctly handled by fall-through, not a bug); `year_built` structurally 0% from
  Overture (assessor is its only working source). Tokens all `FUSED_OVERTURE_HIGH`, asserted not
  eyeballed; misses correctly carry `HOTDECK_*`/`GROUPMODE_*`. License guard green (CDLA-Permissive-2.0,
  279 KB < 5 MB cap). **CP-4 gate: MET.**

**T12-ship DECISION (manager, recorded):**
1. **SHIP:** add `"fusion"` to the FRONT of `config.IMPUTE_ENABLED_TIERS`
   (`("spatial", "statistical")` → `("fusion", "spatial", "statistical")`). Rationale: fusion is FIRST
   in `_CANONICAL_TIER_ORDER`, is a proven byte-identical no-op without a configured source, and this is
   the minimal, byte-safe way to make the Phase-D capability reachable in production imputation runs —
   a municipality that configures an Overture slice / LiDAR nDSM / assessor path gets fusion
   automatically, no per-call tier override needed. Enabling the tier forces Overture on no one; it
   only wires up the machinery. The uneven Overture fill-rate profile is a coverage property the tier
   already handles by fall-through, not a reason to withhold it.
2. **OUT OF SCOPE (deferred to a future arc):** rerouting the production `enrich_semantics` entry point
   through `impute_missing` — this is the §5D-quarantined, CP-1-byte-identity-breaking change. NOT part
   of Phase D. `enrich_semantics` stays untouched.
3. **NOT a ship blocker (tracked follow-up):** the 6 unmapped `use_class` values
   (`entertainment/parking/roof/service/toilets/train_station`) — a crosswalk-extension nicety for a
   later arc, not a Phase-D gate item.
- **GREENLIT → T12-ship DISPATCHED** to a fresh Sonnet executor (config one-liner + stale-docstring
  refresh in `_fusion_tier`/`impute_missing` + an explicit byte-identity regression test proving an
  unconfigured `impute_missing` is identical with vs. without `fusion` in the tuple + gate-suite re-run).

#### T12-ship — enable `fusion` in the default tier tuple — completed 2026-07-13
- Artifacts: `openubem/config.py` (`IMPUTE_ENABLED_TIERS` → `("fusion","spatial","statistical")` + comment refresh), `openubem/semantic/imputation.py` (`_fusion_tier` docstring refresh, no logic change), `tests/test_imputation_routing.py` (byte-identity test added + `test_default_tiers_never_touch_ml` rename), `tests/test_fusion.py` (pre-ship guard test repurposed → `test_default_impute_missing_calls_fusion_tier_as_byte_identical_noop`).
- Deviations: repurposed the retired pre-ship guard test `test_default_impute_missing_never_calls_fusion_tier_byte_identical` in `tests/test_fusion.py` (not in the original T12-ship touch-list) to assert the post-ship byte-identical-no-op contract instead of non-invocation — manager-directed, Phase-C T11.3 precedent. No tier logic changed.
- Test status: `pytest tests/test_fusion.py tests/test_fusion_license_guard.py tests/test_imputation_routing.py tests/test_mask_recover.py tests/test_imputation.py tests/test_tierB_provenance.py tests/test_vintage_donor.py tests/test_levels_groupwise.py tests/test_spatial_impute.py tests/test_provenance.py -q` → 171 passed, 0 failed.
- Notes: `IMPUTE_ENABLED_TIERS` now `("fusion","spatial","statistical")`; fusion is a byte-identical no-op without a configured source (proven by two byte-identity tests — the new routing test + the repurposed test_fusion test); `enrich_semantics` NOT rerouted (untouched, stays out of Phase-D scope).

---

#### Manager — T12-ship AUDIT + SIGN-OFF + PHASE D CLOSED — 2026-07-13

**T12-ship audit (code read, no Opus pytest re-run per the token-efficiency instruction):**
- `openubem/config.py` — confirmed `IMPUTE_ENABLED_TIERS = ("fusion", "spatial", "statistical")`; the
  two comment blocks correctly state fusion is IN the default tuple (byte-identical no-op without a
  configured source) while `ml` stays opt-in-only.
- `tests/test_fusion.py::test_default_impute_missing_calls_fusion_tier_as_byte_identical_noop` — read the
  rewritten test directly: it is honest and load-bearing, NOT weakened. It (a) proves `_fusion_tier` IS
  invoked for the default targets `{year_built, levels}` via the spy, (b) asserts `"fusion" ∈
  IMPUTE_ENABLED_TIERS`, (c) proves the no-op is byte-identical by re-running with
  `enabled_tiers=("spatial","statistical")` and `assert_frame_equal` on values + provenance. The pre-ship
  guard's intent (no accidental enabling) is legitimately retired — the ship is the deliberate,
  CP-4-gated, user-delegated decision — and replaced by a STRONGER invariant. Ratified (Phase-C T11.3
  precedent).
- Conflict handling: Sonnet #3 correctly HARD-STOPPED at the failing pre-ship test rather than patching a
  file outside its touch-list — exactly the right executor behaviour. The manager made the repurpose
  decision; a fresh Sonnet #4 applied it. Gate suite now **171 passed / 0 failed**.

**SIGNED — T12-ship complete.** No user-sign-off owed (delegated 2026-07-13). `enrich_semantics` untouched.

**🔒 PHASE D CLOSED — 2026-07-13.** All of T12.1–T12.6 + CP-4a + CP-4 (real Overture LIVE_SMOKE) +
T12-ship done and audited. The `fusion` external-data-fusion tier is now a first-class, enabled-by-default
imputation tier that is byte-identical for any run without a configured source, and delivers real
ground-truth fill (NYC-centre `height_m` 87.6%) when an Overture slice / endpoint (or a LiDAR nDSM /
assessor path) is configured. Zero-fitted-params preserved (a join is a data-acquisition observation, not
a tuned model). Deferred to future arcs (documented, NOT Phase-D scope): (i) the `enrich_semantics`
production reroute; (ii) EUBUCCO/GHSL/imagery sources; (iii) extending `osm_to_use_class.json` with the 6
unmapped real-Overture `use_class` values; (iv) real per-municipality LiDAR/assessor config + a cluster
EUI leg. Phase E (GAN/GNN/LLM/TabPFN) stays documented-deferred / out of scope. **The input-imputation
arc's scoped work (Phase A–D) is COMPLETE — ready to file to `docs_DONE`.**
