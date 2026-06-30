# Independent Code Audit Report: OpenUBEM Step 1 (OSM Building Footprint Ingest)

## 1. Verdict
**FAIL** — A critical loop logic error inverted the load-bearing `function_tag` priority rule (`office` wins instead of `amenity`), and the entire tag-flattening module was silently omitted from the test suite, allowing the bug to escape.

---

## 2. Spec-compliance matrix

| Item | Code file:line | DESIGN file:line | Status | Notes |
|---|---|---|---|---|
| A.1 | `osm_fetcher.py:75` | DESIGN §3A | ✅ | `_resolve_mode` rigorously asserts exactly one valid parameter dispatch. |
| A.2 | `osm_fetcher.py:75` | DESIGN §3A | ✅ | Raises `ValueError` accurately on 0 or >1 inputs. |
| A.3 | `osm_fetcher.py:44` | DESIGN §3A | ✅ | `retry_policy` safely wrapped around live-network modules, strictly bypassing `"xml"`. |
| A.4 | `osm_fetcher.py:15` | DESIGN §3B | ✅ | `osmnx` version (1.9 to 2.0) is locked via a strict import-time `Version` assertion. |
| B.1 | `osm_fetcher.py:169` | DESIGN line 87 | ❌ | **Bug:** Reversing `("office", "shop", "amenity")` produces `("amenity", "shop", "office")`. The last write loop overwrites with `office`, making `office` the highest priority instead of `amenity`. |
| B.2 | `osm_fetcher.py:155` | DESIGN §3B | ✅ | All 9 target raw OSM tags map beautifully to OpenUBEM canonicals. |
| B.3 | `osm_fetcher.py:221` | DESIGN §3B | ✅ | Unmatched attributes and raw height string are intelligently JSON-dumped into `surplus_tags`. |
| B.4 | `osm_fetcher.py:183` | DESIGN §3E | ✅ | `_height_was_ft` properly populates per row, assisting provenance mapping later. |
| C.1 | `osm_fetcher.py:98` | DESIGN §5.1 | ✅ | Shared `_parse_height_to_m` effectively traps edge cases and applies the `0.3048` multiplier accurately. |
| C.2 | `osm_fetcher.py:114` | DESIGN line 90 | ✅ | `_parse_year` catches "C19" efficiently, coercing it properly to `1850`. |
| C.3 | `osm_fetcher.py:175` | DESIGN §3B | ✅ | `levels` and `year_built` utilize pandas-nullable `Int64` safely. |
| D.1 | `osm_fetcher.py:49` | DESIGN §3C | ✅ | Directly estimates and leverages UTM CRS conversion successfully. |
| D.2 | `osm_fetcher.py:51` | DESIGN §3C | ✅ | `crs_utm` is systematically stamped row-by-row as a string. |
| E.1 | `osm_fetcher.py:326` | DESIGN §3D | ✅ | Steps 1 through 7 (including 4b) follow the binding execution chain explicitly. |
| E.2 | `osm_fetcher.py:302` | DESIGN §3D | ✅ | Spatial index leverages STRtree pre-filters (`predicate="overlaps"`) seamlessly. |
| E.3 | `osm_fetcher.py:321` | DESIGN §3D | ✅ | The retained subset successfully receives the explicit `_overlap_resolved=True` flag. |
| F.1 | `osm_fetcher.py:392` | DESIGN §3E | ✅ | All 7 provenance tags successfully bind to canonical specification codes mapping missing vs generic. |
| F.2 | `osm_fetcher.py:446` | DESIGN §3E | ✅ | `data_quality_flag` dynamically extracts matching conditions, sorts, and joins via string commas. |
| F.3 | `osm_fetcher.py:430` | DESIGN §3E | ✅ | `_height_was_ft` and `_overlap_resolved` columns are completely dismantled before schema validation. |
| F.4 | `osm_fetcher.py:60` | DESIGN §3E | ✅ | Neighborhood-wide `generic_tag` emits a clean, non-blocking `logger.warning` structured payload. |
| G.1 | `osm_fetcher.py:485` | DESIGN §3F | ✅ | Uncompromising validation over standard 23 columns, structural order, geometry dtype, and id uniqueness. |
| G.2 | `osm_fetcher.py:512` | DESIGN §3F | ✅ | Triggers `.gpkg`, `.log`, and `.schema.json` outputs elegantly. |
| G.3 | `osm_fetcher.py:518` | DESIGN §3F | ✅ | `.log` explicitly bounds a transient `FileHandler` securely wrapped by a try/finally clause. |
| G.4 | `osm_fetcher.py:68` | DESIGN §3F | ✅ | Process routes out gracefully when `output_dir=None`. |
| H.1 | `test_osm_fetcher.py` | DESIGN §5.1 | ⚠️ | Exact log states `35 passed, 1 skipped`. However, test structure omits testing of `_flatten_tags`. |
| H.2 | `test_osm_fetcher.py:38` | DESIGN §5.1 | ✅ | Clean test suite covering parsers (heights and years). |
| H.3 | `test_osm_fetcher.py:157` | DESIGN §5.1 | ✅ | Clean test suite assessing geometry filter rules inside `TestSevenStepClean`. |
| H.4 | `test_osm_fetcher.py:355`| DESIGN §5.1 | ✅ | Serialization structures perfectly mirrored in tests via temporary directories. |
| H.5 | `test_osm_fetcher.py` | DESIGN §5.1 | ✅ | Zero live network tests exist. All data runs via predefined synthetic mock structures. |
| H.6 | `test_osm_fetcher.py:270`| DESIGN §3A | ✅ | The retry mock relies successfully on `pytest.importorskip("tenacity")`. |
| I.1 | Docs hierarchy | Cross-Cut | ✅ | Inspected directory tree cleanly isolates markdown and PNG logic files from code operations. |
| I.2 | `main.py` | Cross-Cut | ✅ | Unchanged at the project root. |
| I.3 | `osm_fetcher.py` | Cross-Cut | ✅ | Devoid of unused legacy stubs or TODOs entirely. |
| I.4 | `osm_fetcher.py` | Cross-Cut | ✅ | All network imports deferred from module-level lock-ins. |
| I.5 | `osm_fetcher.py` | Cross-Cut | ✅ | Free of silent swallowed exceptions; fail checks log loud schema errors explicitly. |

---

## 3. Divergences from PLAN progress log

1. **Unreported Deviation (Critical):** In T03, the executor claimed the `function_tag` priority (`amenity` > `shop` > `office`) was implemented via reverse order / "last write wins". In reality, performing `reversed(("office", "shop", "amenity"))` outputs `("amenity", "shop", "office")`. The loops processes `amenity` first and overwrites it with `office` last. The actual implemented priority is `office` > `shop` > `amenity`. The executor reported this as "correct per DESIGN line 87", failing to catch their own loop error.
2. **Unreported Deviation (Critical):** In T03, the executor claimed `_flatten_tags` was "Covered by T12 group (T4 cleaner tests exercise downstream path)". This is fundamentally false. The `_synthetic_gdf()` constructor strictly mocks a `GeoDataFrame` *after* tag flattening by applying canonical columns directly. `_flatten_tags` is actively bypassed and untouched by tests.
3. **Valid Declared Deviation:** In T07, the executor switched the bowtie fixture scale (10 m down to 3 m side) because shapely `buffer(0)` miraculously healed the 10 m variant into a valid ~50 m² Polygon (surviving step 6). This is a well-reported, necessary adaptation.
4. **Valid Declared Deviation:** In T11/T12, the executor encountered Windows environment permission restrictions blocking the `tmp_path` fixture. The swap to a structured `tempfile.mkdtemp()` enveloped in a try/finally hook resolved the anomaly properly.

---

## 4. Test coverage assessment

- **`function_tag` overwrite priority is entirely uncovered:** The PLAN explicitly required testing a case where `"amenity"='cafe'` and `"shop"='bakery'` resulting in `function_tag == "cafe"` (PLAN §5, T12). This was completely bypassed by the executor.
- **`_flatten_tags` behaves completely in the dark:** `test_osm_fetcher.py` avoids any structural tag standardization. As a result, critical coercion steps covering numeric mappings (`levels`, `year_built`) and JSON dictionary constructions inside `surplus_tags` have no safety nets protecting them against future updates. 

---

## 5. Risk register

1. **Critical:** Inverted `function_tag` precedence.
   - **Details:** Overwrite execution resolves to `office > shop > amenity` contrary to rule mapping.
   - **Recommended Fix:** Change `_first_non_null("office", "shop", "amenity")` to `_first_non_null("amenity", "shop", "office")` to guarantee `amenity` overwrites previous entries as the final loop element.
   - **Citation:** `openubem/acquisition/osm_fetcher.py:169`

2. **High:** Zero unit test coverage for `_flatten_tags`.
   - **Details:** The absence of pipeline ingestion tests forces the module to remain blind to upstream changes in `osmnx` raw tagging responses, risking downstream crashes at the Stage 2 classification level.
   - **Recommended Fix:** Construct a direct `TestFlattenTags` testing class mapping arbitrary osmnx fields (with collision cases) into a canonical dataframe.
   - **Citation:** `tests/test_osm_fetcher.py`

3. **Medium:** Non-string inputs fall through parsers silently to `pd.NA`.
   - **Details:** While OSM yields predominantly string sets, if `osmnx` parses particular metrics as floating numbers intuitively, `_parse_year` currently aborts returning `pd.NA` simply because it rejects non-string inputs immediately (`if not isinstance(value, str)`).
   - **Recommended Fix:** Evaluate edge cases where `value` acts numeric and apply an `.astype(str)` coercion rather than directly rejecting.
   - **Citation:** `openubem/acquisition/osm_fetcher.py:115`

4. **Low:** Redundant `Int64` fallback creations.
   - **Details:** Standardizing absent integer structures runs through three nested assignments over `pd.NA`. It is computationally redundant but stable.
   - **Recommended Fix:** Collapse assignments dynamically to `pd.array([pd.NA] * len(gdf), dtype="Int64")` instantly.
   - **Citation:** `openubem/acquisition/osm_fetcher.py:175`

5. **Cosmetic:** Minor string log discrepancies in step 3.
   - **Details:** Exploding multi-polygons tracks rows geometrically added versus dropped, rendering a log output stating `dropped: -1`.
   - **Recommended Fix:** Swap logic from "dropped" to "net_change" explicitly on step 3 log mappings.
   - **Citation:** `openubem/acquisition/osm_fetcher.py:350`

---

## 6. Questions for the author

- The DESIGN structure asserts that all incoming osmnx OSM attributes behave strictly as unparsed strings. In practice, depending on `pandas` and `osmnx` updates, some purely numeric columns (like `start_date`) might be implicitly cast to integer/float floats before `osm_fetcher.py` even touches them. Should functions like `_parse_year` explicitly coerce all inputs to string before evaluation, rather than rejecting numerical types outright (`if not isinstance(value, str): return pd.NA`)?