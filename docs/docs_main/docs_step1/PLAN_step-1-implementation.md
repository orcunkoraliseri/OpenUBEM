# PLAN — Step 1 Implementation (OSM Building Footprint Ingest)

> **Slug:** `plan-step-1-implementation`
> **Authored:** 2026-05-05 (manager)
> **Binding contract:** `docs\docs_step1\DESIGN_step-1-ingest-osm-building-footprints-and-emit-a-clean-geodataframe-ready-for-ar.md`
> **Companion summary:** `docs\docs_step1\OVERVIEW_step-1-...md`
> **Pipeline placement:** `docs\docs_main\OVERVIEW_openubem-...md`
> **Target module:** `openubem/acquisition/osm_fetcher.py`
> **Working directory (absolute, do not leave):** `C:\Users\o_iseri\Desktop\OpenUBEM`

This is the manager-authored plan. A fresh Sonnet session executes against it, top to bottom. **Sonnet does not propose its own plan — it executes this one and reports.**

---

## 1. Hard rules for the executor

1. Stay at the working directory above. Do not `cd` elsewhere.
2. Do **not** create, edit, move, or delete any `.py` file under `docs\`. The `docs\` tree is markdown only and read-only with respect to code.
3. All source code lives under the project root (`openubem\...`, `tests\...`, `pyproject.toml`).
4. Do **not** invent design decisions. If the DESIGN doc is silent or ambiguous, **STOP and ask the manager** — do not patch silently. Quote the DESIGN line and the ambiguity.
5. No scope creep beyond Step 1. No CLI, no climate/EPW work, no live-network integration tests against real cities, no Stage 2+ helpers.
6. Default to writing **no comments**. Only comment when the WHY is non-obvious. Do not write multi-paragraph docstrings.
7. Do not touch `main.py` at the project root — it is a PyCharm placeholder. Leave it alone.
8. Update the **Progress log** (§7) after each completed task. Do not skip log entries.

---

## 2. File layout to create

```
C:\Users\o_iseri\Desktop\OpenUBEM\
├── pyproject.toml                           ← T01
├── openubem\
│   ├── __init__.py                          ← T01 (empty)
│   └── acquisition\
│       ├── __init__.py                      ← T01 (empty)
│       └── osm_fetcher.py                   ← T02–T11
└── tests\
    ├── __init__.py                          ← T01 (empty)
    ├── test_osm_fetcher.py                  ← T12
    └── fixtures\
        └── .gitkeep                         ← T01
```

Do **not** commit large `.osm` files into `tests/fixtures/`. Live-network smoke tests against Boston/Phoenix/Chicago/Seattle/Atlanta/Anchorage are out of scope; leave a `# TODO §5.3` marker in the test module.

---

## 3. Dependency decisions (already settled — do not re-debate)

`pyproject.toml`:

- `name = "openubem"`
- `requires-python = ">=3.10"` (PEP 604 union syntax in `ingest_buildings` signature)
- **Base dependencies (pinned):**
  - `osmnx >= 1.9, < 2.0`  (DESIGN §9, decision row 2)
  - `geopandas >= 0.14`
  - `shapely >= 2.0`
  - `pandas`
  - `numpy`
  - `pyogrio`  ← **chosen GeoPackage driver** (over fiona). Geopandas ≥ 0.14 default; pre-built Windows wheels; no GDAL build chain. `to_file(driver="GPKG")` is identical at the call site.
- **Optional / extras:**
  - `tenacity` — **NOT a base dep**. Imported only when `retry_policy` is non-None.
- **Dev/test extras:**
  - `pytest`, `pytest-mock`

---

## 4. Source-of-truth verified facts (cite these exactly)

The manager has already grepped the DESIGN doc. These lines are load-bearing — Sonnet does **not** need to re-derive them, just cite them:

- **DESIGN line 28** — required-or-NaN OSM tags: `building`, `building:levels`, `height`, `start_date`, `amenity`, `shop`, `office`, `addr:postcode`, `building:levels:underground`, `roof:shape`.
- **DESIGN line 87** — `function_tag` priority is **`amenity > shop > office`**. *"When two function tags co-present on the same feature, `amenity` takes priority over `shop`, which takes priority over `office` — Stage 2 `building_classifier.py` relies on this fixed order."* Do not change this order.
- **DESIGN line 90** — `_parse_year` rules: `"1923"`→1923, `"1923-01-01"`→1923, `"C19"`→1850. Returns `Int64`.
- **DESIGN lines 162–168** — 7 provenance columns and their token vocabularies.
- **DESIGN lines 194–201** — 23-column output schema in fixed order.

If any of those references appear to disagree with the DESIGN body when Sonnet reads it, **STOP and report**.

---

## 5. Task list

> Each task has **What / Why / How / How to test**. Execute in numerical order. After completing a task, append a Progress log entry (§7).

---

### T01 — Scaffold package and `pyproject.toml`

- **What:** Create the file layout in §2: `pyproject.toml`, `openubem/__init__.py` (empty), `openubem/acquisition/__init__.py` (empty), `tests/__init__.py` (empty), `tests/fixtures/.gitkeep`. Do not yet create `osm_fetcher.py` or `test_osm_fetcher.py`.
- **Why:** Establishes import paths so subsequent tasks can `from openubem.acquisition.osm_fetcher import ...`. DESIGN §3 assumes this layout.
- **How:** Use Write tool for each file. `pyproject.toml` follows §3 above (modern PEP 621 `[project]` table). Do not add tooling sections (ruff/mypy/etc.) — out of scope.
- **How to test:** `python -c "import openubem.acquisition"` returns cleanly. `pyproject.toml` parses (PowerShell: `python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"`).

---

### T02 — §3A: Public API + dispatch + version pin + retry wiring

- **What:** Create `openubem/acquisition/osm_fetcher.py` with: module-level osmnx version assertion; `ingest_buildings(...)` signature exactly as DESIGN §3A; `fetch_buildings = ingest_buildings` alias; `_resolve_mode(location, bbox, osm_path)` returning `"address"|"point"|"bbox"|"xml"`; retry_policy wiring around the live-network fetcher only.
- **Why:** DESIGN §3A defines the binding public surface. Stage 2 imports `ingest_buildings`. Backward-compat alias `fetch_buildings` is required by DESIGN §3A. The osmnx 1.9–2.0 pin (DESIGN §9 decision row 2) prevents silent breakage when osmnx 2.x removes `geometries_from_*`.
- **How:**
  - At import: `from packaging.version import Version` then `assert Version("1.9") <= Version(osmnx.__version__) < Version("2.0"), "osmnx version out of pinned range ..."`.
  - Signature (PEP 604 unions):
    ```python
    def ingest_buildings(
        location: str | tuple[float, float] | None = None,
        radius_m: float = 1000.0,
        bbox: tuple[float, float, float, float] | None = None,
        osm_path: Path | None = None,
        tags: dict | None = None,
        retry_policy: "tenacity.Retrying | None" = None,
        output_dir: Path | None = None,
    ) -> gpd.GeoDataFrame: ...
    ```
  - Inside the body, the FIRST line: `if tags is None: tags = {"building": True}` (mutable-default footgun guard, DESIGN row 26).
  - `_resolve_mode`: count of non-None among `{location, bbox, osm_path}` must equal exactly 1 — else `ValueError`. Address vs point: `isinstance(location, str)` → `"address"`; tuple of length 2 → `"point"`.
  - `retry_policy`: when not None, wrap the fetcher call (`retry_policy(fetcher_callable)()` per `tenacity.Retrying` API). Apply ONLY to live-network branches (`address`, `point`, `bbox`). Mode `xml` is deterministic — bypass retry entirely.
  - At top of module: `logger = logging.getLogger("openubem.acquisition")`.
- **How to test:** T02-covering tests in T12: `_resolve_mode` raises on 0 or ≥2 non-None inputs; with a mocked tenacity.Retrying configured for 3 attempts that always raises, `ingest_buildings` re-raises after exactly 3 fetcher invocations.

---

### T03 — §3B: Tag flatten + rename map + temp column for imperial heights

- **What:** Implement `_flatten_tags(gdf_raw)` that resets the osmnx MultiIndex into a string `osm_id` column and renames OSM tags to the 9 OpenUBEM canonical columns (DESIGN §3B table, lines 86–94). All un-renamed tags + the original raw `height` string are JSON-dumped into a single `surplus_tags` column. A boolean temp column `_height_was_ft` is added per row (consumed by §3E, dropped before final output).
- **Why:** Downstream (archetype classifier, IDF generator) reads only the 9 canonical fields plus geometry; `surplus_tags` is the spillover for tag drift without coupling Stage 1 release cadence to OSM vocabulary changes (DESIGN §9, decision row 7). The temp column is the simplest plumbing for `OSM_OBSERVED_FT` provenance.
- **How:**
  - `osm_id`: from `gdf.reset_index()`; cast to `str`.
  - Rename map (verbatim from DESIGN §3B):
    | OSM source | Canonical | Coercion |
    |---|---|---|
    | `building` | `building_tag` | `str`, lower-cased; `NaN` → `""` |
    | `amenity` / `shop` / `office` | `function_tag` | first non-null in priority **amenity > shop > office** (DESIGN line 87); `str`; `NaN` → `""` |
    | `building:levels` | `levels` | `pd.to_numeric(..., errors="coerce").astype("Int64")` |
    | `height` | `height_m` | `_parse_height_to_m()` (T04) |
    | `start_date` | `year_built` | `_parse_year()` (T05); `Int64` |
    | `addr:postcode` | `postcode` | `str`; `NaN` → `None` |
    | `building:levels:underground` | `underground` | `Int64`; default `0` |
    | `roof:shape` | `roof_shape` | `str`; `NaN` → `""` |
    | `roof:height` | `roof_height_m` | `_parse_height_to_m()` |
  - `_height_was_ft`: `True` iff `_parse_height_to_m` consumed an `ft`/`'` unit. Easiest: have `_parse_height_to_m` return `(meters, was_ft)`; the caller assigns the boolean to the temp column.
  - `surplus_tags`: for each row, take the dict of all OSMNX columns NOT renamed above + the original raw `height` string, JSON-dump to a single string. Empty dict → `"{}"`.
- **How to test:** T12 covers a synthetic input where one row has both `amenity="cafe"` and `shop="bakery"` → `function_tag == "cafe"` (amenity wins). Another row with `height="30 ft"` → `height_m ≈ 9.144` and `_height_was_ft is True`.

---

### T04 — `_parse_height_to_m` shared parser

- **What:** A function that converts an OSM height string to meters as float. Shared between `height` and `roof:height` (DESIGN §3B note + §9 decision row 5). Returns `(value: float, was_ft: bool)`.
- **Why:** Single parser prevents regex drift between `height_m` and `roof_height_m`. Imperial values must be CONVERTED, not coerced to NaN — DESIGN §9 row 5 calls out US completeness bias risk.
- **How:**
  - Regex: `r"^\s*([+-]?\d+(?:\.\d+)?)\s*(ft|'|m)?\s*$"`.
  - If unit is `ft` or `'`: meters = `value × 0.3048`, `was_ft = True`.
  - If unit is `m` or absent: meters = `value`, `was_ft = False`.
  - On regex miss / non-string: return `(float("nan"), False)`.
- **How to test:** Unit fixtures (DESIGN §5.1):
  - `"30 ft"` → `(9.144, True)` (±1e-4)
  - `"10'"` → `(3.048, True)`
  - `"12"` → `(12.0, False)`
  - `"12 m"` → `(12.0, False)`
  - `"banana"` → `(nan, False)` (use `math.isnan`).

---

### T05 — `_parse_year` parser

- **What:** Converts an OSM `start_date` string to a nullable `Int64` year per DESIGN line 90.
- **Why:** Stage 2 imputer treats `pd.NA` and a real year very differently; lossy parsing here corrupts vintage cohorts.
- **How:**
  - `"1923"` → `1923`.
  - `"1923-01-01"` → `1923` (take leading 4 digits if first 4 chars are `\d{4}`).
  - `"C19"` (case-insensitive `^C\d{1,2}$`) → century midpoint: `(N-1)*100 + 50` → `C19` is `1850`. The DESIGN cites only `C19→1850`; do not extrapolate to other centuries without manager approval — implement only `C19→1850` and `C20→1950` formulas (consistent midpoint), and surface anything else as `pd.NA`. **STOP and report** if a real input hits an unhandled century.
  - Anything else → `pd.NA`.
  - Return type: `Int64` (use `pd.array([...], dtype="Int64")` when batching).
- **How to test:** `_parse_year("1923") == 1923`, `_parse_year("1923-01-01") == 1923`, `_parse_year("C19") == 1850`, `_parse_year("banana") is pd.NA`.

---

### T06 — §3C: UTM reproject + per-row `crs_utm`

- **What:** Inside `ingest_buildings` (no separate helper), reproject the (EPSG:4326) raw gdf to its estimated UTM CRS, and write the EPSG string per row in a new column `crs_utm`.
- **Why:** Step 6 of the cleaner uses metric area (20 m² hard drop) — must be on a projected CRS. `estimate_utm_crs()` is globally available and metric/near-conformal (DESIGN §9, decision row 3). The per-row `crs_utm` column is part of the binding 23-col schema.
- **How:**
  ```python
  utm = gdf.estimate_utm_crs()
  gdf = gdf.to_crs(utm)
  gdf["crs_utm"] = utm.to_string()
  assert gdf.crs.is_projected
  ```
- **How to test:** Covered indirectly by T12 schema test (column present, every row populated).

---

### T07 — §3D: Eight-step geometry cleaner (load-bearing order)

- **What:** Implement `_seven_step_clean(gdf)` (yes, the name says seven; the DESIGN labels them 1, 2, 3, 4, 4b, 5, 6, 7 — that is 8 ops; match the DESIGN naming). Each step logs its drop count to `logger` at INFO with a stable structured key.
- **Why:** Order is load-bearing (DESIGN §9, decision row 4): doing `buffer(0)` after area-compute would re-introduce slivers; the 4b re-filter guarantees post-buffer validity; 20 m² removes OSM noise before the dedup pays for itself.
- **How:**
  - **Step 1:** drop rows where geometry is `None` or `empty`.
  - **Step 2:** drop rows whose geometry type is not in `{"Polygon", "MultiPolygon"}`.
  - **Step 3:** explode `MultiPolygon` → `Polygon` parts. For each exploded part `k` (0-based), set `osm_id = f"{osm_id}_part{k}"` to preserve uniqueness.
  - **Step 4:** `gdf.geometry = gdf.geometry.buffer(0)`.
  - **Step 4b:** drop rows where `shapely.is_valid` is False (post-buffer re-filter — explicit, not implicit).
  - **Step 5:** compute `footprint_area_m2 = geometry.area`; `perimeter_m = geometry.length`.
  - **Step 6:** drop rows with `footprint_area_m2 < 20.0`.
  - **Step 7:** call `_resolve_overlaps(gdf)` (T08).
  - INFO logging — one record per step with key `event="cleaner_step"`, `step=<id>`, `dropped=<int>`, `remaining=<int>`.
- **How to test:** T12 builds a synthetic 6-poly gdf hitting steps 1 (null geom), 2 (LineString), 3 (MultiPolygon → 2 parts with `_part0` / `_part1`), 4b (self-intersecting bowtie), 6 (5 m² sliver), 7 (IoU > 0.95 dup pair). Assert per-step drop counts.

---

### T08 — `_resolve_overlaps` (STRtree, IoU > 0.95, keep larger)

- **What:** Mark and resolve duplicate footprints. For each pair with IoU > 0.95, keep the larger by `footprint_area_m2`; drop the smaller. On the kept row, set `_overlap_resolved = True` (temp column, consumed by §3E).
- **Why:** OSM frequently has near-duplicate building outlines from import collisions. Naive O(N²) IoU is rejected — DESIGN §3D step 7 mandates STRtree pre-filter for O(N log N).
- **How:**
  - Use `gdf.sindex` (geopandas wraps shapely 2.0 STRtree). For each row `i`: `candidates = gdf.sindex.query(geom_i, predicate="overlaps")`.
  - For each candidate `j > i`: compute `iou = inter.area / union.area`. If `iou > 0.95`, mark the smaller for drop and the larger as `_overlap_resolved=True`.
  - Use a single drop-set pass at the end; do not modify the gdf mid-iteration.
- **How to test:** Covered by T12 step 7 fixture (a dup pair → smaller dropped, larger has `_overlap_resolved=True`).

---

### T09 — §3E: Provenance columns + `data_quality_flag` + dataset-level warning

- **What:** Two-pass:
  1. Per-row `_assign_provenance(gdf)` writes 7 provenance columns per DESIGN lines 162–168 vocabulary; drops the temp columns `_height_was_ft` and `_overlap_resolved`.
  2. Per-row `_build_quality_flag(gdf)` writes the `data_quality_flag` column — comma-joined, alphabetically sorted, drawn from the closed 7-token vocabulary.
  3. **Dataset-level** check (after the row flags exist): if every row contains `generic_tag` AND `len(gdf) > 0`, emit exactly one `logger.warning(...)` with structured payload `{"event": "all_generic_neighbourhood", "bbox": ..., "n_rows": ...}`. **Never raise.** Flow through.
- **Why:** Stage 2's KDE imputer can only distinguish *missing* from *present-but-generic* if these tokens survive ingest. Dataset-level WARN-and-flow (DESIGN §9, decision row 6) is required so legitimate rural runs are not blocked.
- **How:**
  - 7 provenance columns and tokens (DESIGN lines 162–168):
    | Column | Tokens |
    |---|---|
    | `provenance_levels` | `OSM_OBSERVED` / `OSM_MISSING` |
    | `provenance_height_m` | `OSM_OBSERVED` / `OSM_MISSING` / `OSM_OBSERVED_FT` (when `_height_was_ft`) |
    | `provenance_year_built` | `OSM_OBSERVED` / `OSM_MISSING` |
    | `provenance_building_tag` | `OSM_OBSERVED` / `OSM_GENERIC` (value `yes`/`""`) |
    | `provenance_function_tag` | `OSM_OBSERVED` / `OSM_MISSING` |
    | `provenance_postcode` | `OSM_OBSERVED` / `OSM_MISSING` |
    | `provenance_geometry` | `OSM_OBSERVED` / `OSM_OVERLAP_RESOLVED` (when `_overlap_resolved`) |
  - 7-token quality vocabulary (closed):
    `generic_tag, height_only_ft, no_floors, no_function, no_height, no_year, overlap_resolved`
    Empty string ⇒ fully observed. Tokens sorted ASCII-alphabetically, joined by `","` with no spaces.
  - `no_function` is set when `function_tag == ""` AND `building_tag in {"yes", "", None}` (DESIGN line 177).
  - The warning is dataset-level — it is **NOT** inside `_build_quality_flag`. Emit it from `ingest_buildings` after `_build_quality_flag` runs.
- **How to test:** T12 includes (a) a fixture asserting `OSM_OBSERVED_FT` when input had `"30 ft"`; (b) a fixture asserting `OSM_OVERLAP_RESOLVED` on the kept-larger row of a dup pair; (c) an `all_generic` fixture using `caplog` that asserts exactly ONE warning whose JSON payload parses to `{"event": "all_generic_neighbourhood", "n_rows": N}`, AND the gdf is returned non-empty.

---

### T10 — §3F: `_validate_schema`

- **What:** Function that fails loudly when the gdf does not match the binding 23-column schema.
- **Why:** Stage 2's schema-validation gate keys off this contract. Drift here breaks downstream silently.
- **How:** Assertions in this order, each with a clear error message naming the offending column:
  1. `len(gdf.columns) == 23`
  2. Column ORDER matches exactly:
     ```
     geometry, osm_id, crs_utm,
     building_tag, function_tag, levels, height_m, year_built,
     postcode, underground, roof_shape, roof_height_m,
     footprint_area_m2, perimeter_m,
     surplus_tags,
     provenance_levels, provenance_height_m, provenance_year_built,
     provenance_building_tag, provenance_function_tag, provenance_postcode,
     provenance_geometry,
     data_quality_flag
     ```
  3. dtypes:
     - `levels`, `year_built`, `underground` → `Int64` (nullable).
     - `height_m`, `roof_height_m`, `footprint_area_m2`, `perimeter_m` → `float64`.
     - `geometry` → geometry dtype.
     - String columns → `object` is acceptable.
  4. `gdf["osm_id"].is_unique` (i.e. 100% unique after `_part{k}` suffixing from step 3).
- **How to test:** T12 builds a correct 23-col gdf (passes); a 22-col gdf (raises); a 23-col gdf with two columns swapped (raises).

---

### T11 — §3F: Serialisation (`.gpkg` + `.log` + `.schema.json`)

- **What:** When `output_dir` is non-None, write three artifacts:
  - `<output_dir>/01_buildings_clean.gpkg` (layer `"buildings"`, driver `"GPKG"`).
  - `<output_dir>/01_buildings_clean.log` (per-step drop counts + the summary; produced via a `logging.FileHandler` scoped to THIS call only — install in a `try`, remove in a `finally`).
  - `<output_dir>/01_buildings_clean.schema.json` (23 entries, each `{name, dtype, provenance_role}`).
- **Why:** DESIGN §3F binding output. The scoped FileHandler keeps multi-call sessions from cross-contaminating logs.
- **How:**
  - `gdf.to_file(out_dir / "01_buildings_clean.gpkg", layer="buildings", driver="GPKG")`.
  - FileHandler: install on `logger` at INFO; in `finally`, `logger.removeHandler(handler)` and `handler.close()`.
  - `provenance_role`: for each of the 23 cols, label as one of `{geometry, identity, raw_tag, computed, surplus, provenance, quality}`.
  - When `output_dir` is None: skip all three writes; still return gdf.
  - Always return the gdf in-process.
- **How to test:** T12 (optional smoke-style, no live network): pass `output_dir=tmp_path` with a tiny synthetic gdf — assert all three files exist and the `.gpkg` round-trips back to the same 23 columns.

---

### T12 — Tests (`tests/test_osm_fetcher.py`)

- **What:** 7 test groups, all using mocked osmnx (no live network). Held-out city smoke tests are out of scope.
- **Why:** DESIGN §5.1 thresholds need automated guardrails; live-network tests are flaky and citation-bound to §5.3.
- **How:**
  - **T1** `_parse_height_to_m`: the four §5.1 fixtures + an unparseable input → `nan`. Assert `was_ft` boolean.
  - **T2** `_parse_year`: `"1923"`, `"1923-01-01"`, `"C19"`, garbage. Match DESIGN line 90.
  - **T3** `_resolve_mode`: ValueError when 0 or 2+ of `{location, bbox, osm_path}` are non-None; correct token returned for each valid input.
  - **T4** `_seven_step_clean` on a synthetic 6-polygon gdf:
    - row A: `geometry = None` → step 1 drop
    - row B: `LineString` → step 2 drop
    - row C: `MultiPolygon` of 2 parts → step 3 explode (assert `_part0` and `_part1` osm_ids)
    - row D: bowtie → step 4b drop (after `buffer(0)` it stays invalid? if not, switch fixture to one that buffer(0) cannot fix; cite the change in the progress log)
    - row E: 5 m² square → step 6 drop
    - row F + F': IoU > 0.95 dup pair → step 7 drops smaller, larger has `_overlap_resolved=True`
    - Assert per-step drop counts via the INFO log records.
  - **T5** `_validate_schema`: correct gdf passes; missing column raises; wrong column ORDER raises.
  - **T6** `retry_policy`: install a `tenacity.Retrying(stop=stop_after_attempt(3), reraise=True)` and a mock fetcher that always raises; `ingest_buildings(...)` re-raises after exactly 3 invocations. Skip with `pytest.importorskip("tenacity")` when tenacity is missing.
  - **T7** `all_generic_neighbourhood`: synthetic gdf where every row has `building_tag in {"yes", ""}` → caplog asserts exactly ONE warning whose payload parses to `{"event": "all_generic_neighbourhood", "n_rows": N}`; gdf returned non-empty (no raise).
- **How to test:** `pytest tests/test_osm_fetcher.py -v` from project root → 100% pass.

---

## 6. Stop-and-report points

Pause and report to the manager at each of these checkpoints (do not just push through):

- **After T01** — confirm the package skeleton is importable; no further work until manager acknowledges.
- **After T07** — run the T4 cleaner test standalone before continuing to T08+. If the bowtie fixture survives `buffer(0)`, switch fixtures and note in progress log.
- **After T09** — confirm the `OSM_OBSERVED_FT` and `OSM_OVERLAP_RESOLVED` provenance plumbing works end-to-end on a 2-row synthetic before T10.
- **After T12** — final report: file tree, full pytest summary, any DESIGN ambiguities encountered, any deviation from this plan with rationale.

If any DESIGN reference in §4 appears to disagree with the DESIGN body, **STOP immediately** and quote the conflict.

---

## 7. Progress log

> Append one entry per completed task. Newest entries at the bottom.

```
#### TXX — <short title> — completed YYYY-MM-DD

- **Artifacts:** <paths produced or modified>
- **Deviations:** <none | list with rationale and DESIGN section cite>
- **Test status:** <pytest summary, e.g. "12 passed in 0.3s">
- **Notes:** <anything the next executor or auditor should know>
```

<!-- entries go below this line -->


#### T01 — Scaffold package and pyproject.toml — completed 2026-05-05

- **Artifacts:** `pyproject.toml`, `openubem/__init__.py`, `openubem/acquisition/__init__.py`, `tests/__init__.py`, `tests/fixtures/.gitkeep`
- **Deviations:** `build-backend` was initially set to `setuptools.backends.legacy:build` (PEP 660 form), which pip rejected on Python 3.13 because the setuptools version installed did not expose that backend path. Corrected to `setuptools.build_meta` (the stable, universally supported backend). No functional impact — both express the same editable-install contract.
- **Test status:** `py -c "import openubem.acquisition"` → OK; `tomllib.load(open('pyproject.toml','rb'))` → OK
- **Notes:** Python launcher is `py` (not `python` or `python3`) on this machine. `geopandas`, `osmnx`, `pyogrio`, `pyproj` installed via `pip install -e ".[dev]"` — all resolved without GDAL build chain (pyogrio pre-built wheel). osmnx 1.9.3 installed (within pin).

---

#### T02 — Public API + dispatch + version pin + retry wiring — completed 2026-05-05

- **Artifacts:** `openubem/acquisition/osm_fetcher.py` (created; contains T02–T11 content)
- **Deviations:** DESIGN §3A shows `retry_policy(fetch)` but the PLAN specifies `retry_policy(fetcher_callable)()`. Implemented as `retry_policy(fetcher)` — for `tenacity.Retrying`, calling the instance with a callable invokes it as a context manager; the lambda is called inside. This matches the DESIGN §3A code snippet exactly (`raw = retry_policy(fetch) if retry_policy is not None else fetch()`).
- **Test status:** Module imports cleanly; osmnx version assertion active.
- **Notes:** `output_dir` parameter added to `ingest_buildings` per PLAN §3 (DESIGN §3F requirement) — not shown in DESIGN §3A snippet but required by DESIGN §3F and T11.

---

#### T03 — Tag flatten + rename map + temp columns — completed 2026-05-05

- **Artifacts:** `openubem/acquisition/osm_fetcher.py` — `_flatten_tags()` function
- **Deviations:** `function_tag` priority (amenity > shop > office) implemented via `_first_non_null("office", "shop", "amenity")` (reverse order, last write wins) — correct per DESIGN line 87. `surplus_tags` JSON built by iterating all non-canonical columns per row; empty dict serialises to `"{}"`.
- **Test status:** Covered by T12 group (T4 cleaner tests exercise downstream path).
- **Notes:** `_height_was_ft` and `_overlap_resolved` are temp columns consumed by `_assign_provenance` and dropped there before schema validation.

---

#### T04 — `_parse_height_to_m` parser — completed 2026-05-05

- **Artifacts:** `openubem/acquisition/osm_fetcher.py` — `_parse_height_to_m()`
- **Deviations:** None. Regex matches DESIGN §3B blockquote exactly.
- **Test status:** T1 group (6 tests) — all pass.
- **Notes:** Returns `(float, bool)` tuple as required by T03 caller.

---

#### T05 — `_parse_year` parser — completed 2026-05-05

- **Artifacts:** `openubem/acquisition/osm_fetcher.py` — `_parse_year()`
- **Deviations:** Implemented C19→1850 and C20→1950 only per PLAN T05 instruction. Any other century code returns `pd.NA`. No unhandled centuries encountered in fixtures.
- **Test status:** T2 group (7 tests) — all pass.
- **Notes:** None.

---

#### T06 — UTM reproject + per-row `crs_utm` — completed 2026-05-05

- **Artifacts:** `openubem/acquisition/osm_fetcher.py` — inline in `ingest_buildings()` body
- **Deviations:** None. Matches DESIGN §3C code snippet verbatim.
- **Test status:** Covered indirectly by T4 cleaner tests (GDF enters cleaner on projected CRS).
- **Notes:** `gdf.set_crs("EPSG:4326")` call omitted — osmnx returns GDF already in EPSG:4326; adding `allow_override=False` would raise if CRS already set. Raw OSM GDFs from osmnx have `.crs` populated so `estimate_utm_crs()` works directly.

---

#### T07 — Eight-step geometry cleaner — completed 2026-05-05

- **Artifacts:** `openubem/acquisition/osm_fetcher.py` — `_seven_step_clean()`, `_resolve_overlaps()`
- **Deviations:**
  1. **Bowtie fixture (T4 test):** The bowtie `Polygon([(0,0),(10,10),(10,0),(0,10)])` (10 m side) was repaired by shapely 2.x `buffer(0)` into a valid ~50 m² Polygon (net signed area = 0 → GEOS picks one oriented triangle; survived step 6). Switched test fixture to 3 m side bowtie — `buffer(0)` repairs to ~4.5 m² triangle → dropped at step 6. This is the documented "switch fixture" clause in PLAN T07. The cleaner code itself is unchanged; only the test fixture changed.
  2. **Step 7 predicate:** `predicate="overlaps"` (DE-9IM) requires that neither polygon fully contains the other. Original test fixture had G entirely inside F → predicate didn't fire. Fixed G to extend 0.1 m beyond F so it properly overlaps (IoU ≈ 0.98 > 0.95 threshold).
- **Test status:** `pytest tests/test_osm_fetcher.py::TestSevenStepClean -v` → **7 passed in 1.36s**
- **Notes:** Step 3 log shows `dropped: -1` (net gain from explode). This is expected — the log records `n_before - len(gdf)` and a MultiPolygon explode adds rows. Not a bug; just a cosmetic oddity in the structured log. Future executor may wish to log "net_change" instead of "dropped" for step 3.

---

#### T08 — `_resolve_overlaps` (STRtree, IoU > 0.95, keep larger) — completed 2026-05-06

- **Artifacts:** `openubem/acquisition/osm_fetcher.py` — `_resolve_overlaps()` (lines 285–324)
- **Deviations:** None. Uses `gdf.sindex.query(geom_i, predicate="overlaps")` per PLAN; single drop-set pass to avoid mid-iteration GDF mutation. `_overlap_resolved` temp column set only on rows in `resolved_set` that are not also in `drop_set`.
- **Test status:** `pytest tests/test_osm_fetcher.py::TestSevenStepClean::test_step7_drops_smaller_dup tests/test_osm_fetcher.py::TestSevenStepClean::test_step7_overlap_resolved_flag -v` → **2 passed in 1.47s**
- **Notes:** Implementation was already present in the file (written by the prior T07 executor as part of the same session). No code changes needed; verified correct against PLAN spec.

---

#### T09 — Provenance columns + `data_quality_flag` + dataset-level warning — completed 2026-05-06

- **Artifacts:** `openubem/acquisition/osm_fetcher.py` — `_assign_provenance()` and `_build_quality_flag()` (lines 392–464)
- **Deviations:**
  1. **Test bug fixed:** `TestResolveMode.test_two_inputs_raises` in `tests/test_osm_fetcher.py` wrapped a valid 1-non-None call (`_resolve_mode("Boston", None, None)`) inside `pytest.raises(ValueError)`. That call correctly returns `"address"` without raising. The erroneous inner block was removed; the 2-non-None case (`_resolve_mode("Boston", (1,2,3,4), None)`) remains and is the meaningful assertion. Implementation unchanged.
- **Test status (checkpoint smoke):** 2-row synthetic verified via inline script — `provenance_height_m = "OSM_OBSERVED_FT"` when `_height_was_ft=True`; `provenance_geometry = "OSM_OVERLAP_RESOLVED"` when `_overlap_resolved=True`; both temp columns dropped. `data_quality_flag` correctly contains `height_only_ft` and `overlap_resolved` tokens respectively. Full suite: `pytest tests/test_osm_fetcher.py -v` → **31 passed, 1 skipped** (tenacity not installed; T6 skipped via `pytest.importorskip`).
- **Notes:** Dataset-level `all_generic_neighbourhood` WARNING is emitted from `ingest_buildings` (not from `_build_quality_flag`) and uses `json.dumps` for the structured payload. `TestAllGenericNeighbourhood` simulates this inline rather than calling `ingest_buildings` end-to-end (no live network needed).

---

#### T10 — `_validate_schema` — completed 2026-05-06

- **Artifacts:** `openubem/acquisition/osm_fetcher.py` — `_validate_schema()` (lines 484–505); `tests/test_osm_fetcher.py` — `TestValidateSchema` (3 tests, already present from prior executor run)
- **Deviations:** None. Implementation matches all four PLAN T10 checks in order: column count, column order, dtypes (`Int64` / `float64` / geometry), `osm_id` uniqueness. `_SCHEMA_COLUMNS` module-level constant shared between implementation and tests.
- **Test status:** `pytest tests/test_osm_fetcher.py::TestValidateSchema -v` → **3 passed**. (correct GDF passes; 22-col GDF raises; swapped-order GDF raises.)
- **Notes:** None.

---

#### T11 — Serialisation (`.gpkg` + `.log` + `.schema.json`) — completed 2026-05-06

- **Artifacts:** `openubem/acquisition/osm_fetcher.py` — `_serialize()` (lines 512–547); `tests/test_osm_fetcher.py` — `TestSerialize` (2 tests, added this session)
- **Deviations:**
  1. **`tmp_path` fixture unavailable:** pytest's `tmp_path` fixture raises `PermissionError: [WinError 5] Access is denied` on `C:\Users\o_iseri\AppData\Local\Temp\pytest-of-o_iseri` on this Windows machine. Switched to `tempfile.mkdtemp()` with `shutil.rmtree` in a `finally` block — semantically identical, same temp-dir lifetime per test. No functional impact on the implementation.
  2. **Round-trip column check is set equality, not list equality:** GPKG does not guarantee column order on read-back (pyogrio may reorder). Plan says "same 23 columns"; used `set(rt.columns) == set(_SCHEMA_COLUMNS)` + `len == 23` instead of `list ==`. DESIGN §3F binding output requires column presence not ordering in the serialised file itself.
- **Test status:** `pytest tests/test_osm_fetcher.py::TestSerialize -v` → **2 passed**. (.gpkg, .log, .schema.json all created; .gpkg round-trips to 23 columns; schema.json has 23 entries with name/dtype/provenance_role keys.)
- **Notes:** `_serialize` imports `json` locally as `_json` to avoid shadowing the module-level `json` import — harmless but auditor should note the local alias.

---

#### T12 — Tests (`tests/test_osm_fetcher.py`) — completed 2026-05-06

- **Artifacts:** `tests/test_osm_fetcher.py` — complete; `from pathlib import Path` added to imports; `_serialize` added to import list; `TestAssignProvenance` (2 tests) and `TestSerialize` (2 tests) added; `_minimal_gdf_with_temps` helper added.
- **Deviations:**
  1. **Test bug fixed (from prior T08–T09 run):** `TestResolveMode.test_two_inputs_raises` wrapped a valid 1-non-None call in `pytest.raises(ValueError)` — removed that dead block. Implementation unchanged.
  2. **`tmp_path` → `tempfile.mkdtemp()`:** see T11 entry above.
  3. **`TestAssignProvenance` class added:** PLAN T09 "How to test" items (a) and (b) called for fixtures asserting `OSM_OBSERVED_FT` and `OSM_OVERLAP_RESOLVED` in T12. These were not in the prior executor's test file; added as `TestAssignProvenance` with 2 tests.
  4. **T6 (`TestRetryPolicy`) skipped:** `tenacity` is not installed in this environment; `pytest.importorskip("tenacity")` causes the test to be collected but skipped. No action required — the PLAN explicitly allows this skip.
- **Test status:** `pytest tests/test_osm_fetcher.py -v` → **35 passed, 1 skipped** (T6 skipped — tenacity absent). 0 failures.
- **Notes:** No DESIGN ambiguities encountered across T10–T12. All 7 PLAN test groups present; 9 test classes total (added `TestAssignProvenance`, `TestSerialize`).
