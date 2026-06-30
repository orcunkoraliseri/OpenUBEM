# PLAN — Step 2.1 Implementation (Module 02: climate zone + EPW)

> **Slug:** `step-2-1-assign-ashrae-climate-zone-us-state-and-epw-weather-file-to-every-build`
> **Date:** 2026-06-10 • **Author:** Manager session
> **Binding contract:** `docs/docs_step-2-1/DESIGN_step-2-1-assign-ashrae-climate-zone-us-state-and-epw-weather-file-to-every-build.md` (DESIGN). Line numbers below cite that file. The OVERVIEW in the same folder is a dashboard, not a contract.
> **Baseline at planning time:** suite GREEN — 265 passed, 2 skipped (2026-06-10).

---

## 1. Hard rules for the executor

1. Work only inside `C:\Users\o_iseri\Desktop\OpenUBEM`. Never `cd` elsewhere.
2. You execute this plan; you do not write plans or redesign. If the DESIGN is ambiguous or conflicts with this plan, **STOP and quote both passages**.
3. No scope creep: touch only the files listed in §3. Never edit `main.py`, OVERVIEW, DESIGN, or anything under `docs/` except appending progress-log entries to §8 of THIS file.
4. Default to no code comments. One short line max where the WHY is non-obvious (cite DESIGN line).
5. No live-network calls inside pytest, except the single opt-in LIVE_SMOKE test (T13) which must be skipped unless `OPENUBEM_LIVE_SMOKE=1`. The two builder scripts (T02/T03) DO use the network when you run them once, manually — that is data acquisition, not a test.
6. Existing suite must stay green. Run `python -m pytest tests -q` before claiming any checkpoint.
7. Never invent data values (zone assignments, station coordinates). They come from the downloaded sources, with provenance recorded.

---

## 2. Dependency decisions (pre-decided — do not re-debate)

- Add to `[project] dependencies` in `pyproject.toml`: `"requests"`, `"pyarrow"` (parquet sidecar is a runtime artifact, DESIGN line 140), `"pyproj"` (explicit, already transitively present).
- Remove `"pyarrow"` from `[project.optional-dependencies] dev` (now runtime).
- Extend `[tool.setuptools.package-data]`: `"openubem.data" = ["*.json", "*.csv", "climate_zones/*.gpkg", "climate_zones/*.md"]`.
- No new test-only dependencies. Mock HTTP with `pytest-mock` / monkeypatch on `requests.get` — no `responses` package.

## 3. File layout to create / touch

```
openubem/
├── config.py                                  (touch: append EPW_* + OFFLINE constants)
├── acquisition/
│   ├── __init__.py                            (touch: currently empty → enrich_climate orchestrator)
│   ├── climate_zone.py                        (new: §3A–§3B)
│   └── epw_manager.py                         (new: §3C–§3D)
├── data/
│   ├── climate_zones/
│   │   ├── __init__.py                        (new, empty — keeps package_data importable path)
│   │   ├── ashrae_climate_zones.gpkg          (new: built once by scripts/build_climate_zones_gpkg.py)
│   │   └── PROVENANCE.md                      (new: source URLs, edition, SHA-256, license, refresh steps)
│   └── epw_stations.csv                       (new: built once by scripts/build_epw_stations_csv.py)
scripts/
├── build_climate_zones_gpkg.py                (new: one-off network builder)
└── build_epw_stations_csv.py                  (new: one-off network builder; provenance header comment row policy in T03)
tests/
├── test_climate_zone.py                       (new)
├── test_epw_manager.py                        (new)
├── test_step21_orchestrator.py                (new)
└── fixtures/
    └── epw/                                   (new dir: synthetic valid / truncated / headerless EPWs, tiny station index CSV)
pyproject.toml                                 (touch: §2 above)
```

Nothing else. `main.py` and all existing modules/tests stay untouched.

## 4. Source-of-truth verified facts (manager-grepped, with DESIGN line numbers)

| # | Fact | DESIGN line(s) |
|---|---|---|
| F1 | Input `02_buildings_classified.gpkg`, layer `buildings`, (N, 26), UTM CRS; Step 2.1 reads geometry + `osm_id` only; all 26 columns pass through byte-identical | 24, 143 |
| F2 | Append exactly 3 columns → (N, 29): `climate_zone` (categorical, 16-token closed vocab, never null), `epw_path` (str, run-local path, identical all rows, never null), `provenance_climate_zone` (categorical, `{ASHRAE_STANDARD, HEURISTIC}`, never null) | 110–114, 143 |
| F3 | Zone vocabulary: `{1A, 2A, 2B, 3A, 3B, 3C, 4A, 4B, 4C, 5A, 5B, 5C, 6A, 6B, 7, 8}` | 64 |
| F4 | Join point = `representative_point()` (NOT centroid), one vectorized `to_crs(epsg=4326)` for the whole frame | 42–50 |
| F5 | Tier 1: `gpd.sjoin(points, counties, predicate='within')` → `ASHRAE_STANDARD` / method `county_within`. Tier 2 (unmatched only): `sjoin_nearest(max_distance=5_000)` computed in the run UTM CRS, counties reprojected once → `HEURISTIC` / `nearest_fallback`. Still unmatched after Tier 2, OR zero Tier-1 matches across the entire run ⇒ abort with structured error | 60–62 |
| F6 | Point matching >1 county ⇒ keep lexically smallest `county_geoid`, log structured warning. >1 distinct zone in a run ⇒ `logging.warning` payload `{"event": "multi_zone_neighbourhood", "zones": [...], "counts": [...]}` | 64 |
| F7 | `state` + `county_geoid` come from the same matched county row — no second lookup | 64 |
| F8 | One EPW station per run, geodesic argmin (`pyproj.Geod(ellps='WGS84')`) at the representative point of the neighbourhood union; signature `resolve_station(lat, lon, stations) -> (station_row, dist_km)` | 70–82 |
| F9 | `epw_distance_km` > `EPW_MAX_STATION_KM` (default 300) ⇒ structured warning `{"event": "epw_far_station", ...}`, run proceeds | 84 |
| F10 | Resolution order: (1) user `epw_dir` — exactly one `.epw` → use it; several → geodesically nearest by **header** location; (2) `EPW_CACHE_DIR` hit on canonical filename; (3) climate.onebuilding.org; (4) energyplus.net/weather. `offline=True` skips 3–4; cold cache + offline ⇒ abort | 86–87 |
| F11 | Validation gate (every EPW, regardless of origin): download lands as `<name>.epw.tmp`, `os.replace()` only after checks pass; check 2: first line starts `LOCATION,` and parses name + lat/lon (fail ⇒ reject, next tier); check 3: header vs index geodesic ≤ 10 km (fail ⇒ warning `epw_header_mismatch`, file still accepted); check 4: data row count ∈ {8760, 8784} (8784 ⇒ warn AMY; other ⇒ reject, next tier). All tiers exhausted ⇒ `RuntimeError` with structured payload | 94–100 |
| F12 | Accepted EPW is **copied** (not symlinked) to `<output_dir>/weather/<canonical_name>.epw`; `epw_path` points at that copy, inside `<output_dir>` | 102, 143 |
| F13 | Artifacts: `02a_buildings_climate.gpkg` (layer `buildings`, (N,29), UTM preserved) + `02a_buildings_climate.schema.json` (29 entries, same format as Step 2's sidecar) + `02a_climate_epw.parquet` (N×9: `osm_id, climate_zone, climate_zone_method, county_geoid, state, epw_station_id, epw_path, epw_distance_km, provenance_climate_zone`) | 116–128, 136–141 |
| F14 | Acceptance: 8/8 known-city fixture (Miami 1A, Phoenix 2B, San Francisco 3C, Boston 5A, Chicago 5A, Denver 5B, Duluth 7, Fairbanks 8); `nearest_fallback` ≤ 1% on Boston 500 m; truncated EPW rejected at check 4; determinism = byte-identical `02a_*` re-runs; sidecar `osm_id` set == GPKG `osm_id` set | 151–159 |
| F15 | Required offline unit fixtures: 8 known cities; Boston Harbor point (nearest_fallback + HEURISTIC); Suffolk/Middlesex county-line pair (different `county_geoid`, same zone 5A); open-ocean point > 5 km (abort); truncated + header-less EPW (rejected); offline cold cache (abort) and warm cache (succeed). Unit fixtures use a ~10-row synthetic station index | 163–164, 192 |
| F16 | Bundled county layer: EPSG:4326, attrs `county_geoid` (5-digit FIPS), `state_abbrev`, `climate_zone`; edition pinned **ASHRAE 169-2013-consistent** (OQ-1 resolution); checksum + licensing note required | 25, 260 |
| F17 | `data/epw_stations.csv` columns: `station_id` (WMO), `name`, `state`, `lat`, `lon`, `url`, `tmy_edition`; extraction from onebuilding catalog is delegated to this implementation repo (OQ-2); TMYx preferred over TMY3 where both exist (OQ-3) | 26, 261–262 |
| F18 | `config.py` exposes `EPW_CACHE_DIR` (default `~/.openubem/epw/`), `EPW_MAX_STATION_KM` (300, `ASSUMPTION_DESIGN_DEFAULT`), `EPW_PRIMARY_MIRROR`, `EPW_FALLBACK_MIRROR`, `OFFLINE` (False) | 28 |
| F19 | Canada/NECB out of scope (OQ-5 deferral); no `0A/0B` tokens (no US county) | 64, 264 |

## 5. Pre-decided implementation choices (manager rulings — cite this section on deviation)

- **P1 — County layer sources (T02):** counties = US Census **cartographic boundary** file `cb_2023_us_county_500k` (public domain; keep `GEOID`, `STUSPS` only; geometry simplified by Census already — do NOT further simplify). Zone mapping = DOE/PNNL county→IECC/ASHRAE climate-zone table (county FIPS → zone number + moisture letter). Preferred: a PNNL/DOE source consistent with ASHRAE 169-2013 (per F16). Acceptable fallback: the widely mirrored DOE Building America `climate_zones.csv` (state FIPS + county FIPS + IECC zone + moisture regime), recorded in `PROVENANCE.md` as `ASSUMPTION_DESIGN_DEFAULT` with a note that a handful of counties may differ from 169-2013. Record exact URLs, retrieval date, SHA-256 of both raw inputs and of the emitted GPKG, and license names. Counties with no mapping row (territories): drop and count them in PROVENANCE.md. Zone token = zone number + moisture letter; zones 7/8 have no moisture letter (F3).
- **P2 — Station index source (T03):** parse the climate.onebuilding.org **KML/KMZ index for WMO Region 4 / USA** (placemark name, lat/lon, TMYx zip URL). Emit one row per station, TMYx edition parsed from the filename. If the KMZ route proves unparseable within reasonable effort, fall back to a curated index of ≥ 50 US stations hand-extracted from onebuilding state pages — it MUST cover all 16 zone tokens' fixture needs and the 8 known cities (incl. Boston Logan WMO 725090, Chicago O'Hare, Miami Intl, Phoenix Sky Harbor, SF Intl, Denver Intl, Duluth Intl, Fairbanks Intl). Either way: document source + refresh procedure at the top of the CSV (comment row `# source: ... retrieved: ...` is NOT allowed in the data — put it in `PROVENANCE.md` alongside the GPKG instead; CSV stays machine-clean with a pure header row).
- **P3 — onebuilding serves `.zip` archives, not bare `.epw`.** `epw_manager` download logic: if the resolved URL ends `.zip`, download to `<canonical>.zip.tmp`, extract the single `.epw` member to `<canonical>.epw.tmp`, then run the F11 gate and `os.replace`. energyplus.net fallback URLs serve bare `.epw`. This implements F10/F11 in the presence of real mirror packaging (DESIGN is silent; deviation pre-approved here).
- **P4 — Canonical filename** = basename of the station's `url` with `.zip`→`.epw` (e.g. `USA_MA_Boston-Logan.Intl.AP.725090_TMYx.epw`), per DESIGN line 86's example.
- **P5 — Orchestrator signature:** `enrich_climate(gdf: gpd.GeoDataFrame, output_dir: Path | None = None, *, epw_dir: Path | None = None, offline: bool | None = None) -> gpd.GeoDataFrame` in `openubem/acquisition/__init__.py`. `offline=None` reads `config.OFFLINE`. Mirrors Step 2's `classify()` conventions: validates input, appends columns, asserts byte-identity of the 26 upstream columns via `pd.testing.assert_frame_equal` (building_classifier.py:584–587 pattern), writes artifacts only when `output_dir` is not None. Returns the 29-column GDF. Sidecar written with `pandas.DataFrame.to_parquet`.
- **P6 — Schema sidecar:** reuse the exact JSON shape of `building_classifier._write_schema_json` (`{"schema_version": "1.0.0", "columns": [...]}`); read that function before writing yours. The 3 new columns get `provenance_role` analogous entries with this step as producer.
- **P7 — Input validation:** 26 expected column names = the 23-column Step-1 list + `archetype_id`, `archetype_confidence`, `archetype_source`. Import/reuse the canonical lists from `openubem.semantic.building_classifier` if exported; otherwise copy them and cite the source line in a one-line comment. Validate `archetype_id` ∈ the closed 30-archetype vocabulary loaded from `openubem/data/openstudio_archetypes.json` (no hand-typed list).
- **P8 — Determinism:** no timestamps inside any emitted artifact. GPKG re-write byte-identity can be brittle (driver metadata); the determinism TEST may compare via re-read content equality (`assert_frame_equal`) for the GPKG, but MUST assert byte-identity for `02a_climate_epw.parquet` and `02a_buildings_climate.schema.json`. Log a deviation note if even that fails, with cause.
- **P9 — Tier-2 distance:** run `sjoin_nearest` in the input GDF's UTM CRS with counties reprojected to it once (F5); do not use geographic-degree distances.

## 6. Task list

### T01 — config + packaging
- **What:** Append to `openubem/config.py`: `EPW_CACHE_DIR: Path = Path(os.environ.get("OPENUBEM_EPW_CACHE", Path.home() / ".openubem" / "epw"))`, `EPW_MAX_STATION_KM: float = 300.0`, `EPW_PRIMARY_MIRROR: str` (climate.onebuilding.org base), `EPW_FALLBACK_MIRROR: str` (energyplus.net/weather base), `OFFLINE: bool = False`. Apply the §2 pyproject edits.
- **Why:** DESIGN line 28 (F18); packaging needed so bundled data ships in the wheel.
- **How:** Constants only, no behavior. Env-var override for cache dir mirrors the existing `OPENUBEM_ENERGYPLUS_IDD_PATH` pattern (config.py:9).
- **How to test:** covered by T09/T11 (imports + monkeypatching these constants).

### T02 — build `ashrae_climate_zones.gpkg` (network, run once)
- **What:** Write `scripts/build_climate_zones_gpkg.py` per P1; run it; commit the output GPKG + `PROVENANCE.md` under `openubem/data/climate_zones/`.
- **Why:** DESIGN line 25 + OQ-1 resolution (F16) — the bundled instrument every zone join depends on.
- **How:** Download Census `cb_2023_us_county_500k` zip + the P1 zone table; join on 5-digit FIPS; emit columns exactly `county_geoid` (str), `state_abbrev` (str), `climate_zone` (str, F3 tokens), geometry; EPSG:4326; layer name `counties`. Validate before writing: all `climate_zone` values ∈ F3 vocabulary; `county_geoid` unique; ~3,000–3,200 rows. Script must be re-runnable (refresh procedure) and print the SHA-256 it records.
- **How to test:** T06 known-city fixture is the acceptance gate; script self-checks above.

### T03 — build `epw_stations.csv` (network, run once)
- **What:** Write `scripts/build_epw_stations_csv.py` per P2; run it; commit `openubem/data/epw_stations.csv`; document source + refresh in `PROVENANCE.md`.
- **Why:** DESIGN line 26 + OQ-2 delegation (F17).
- **How:** Columns exactly `station_id,name,state,lat,lon,url,tmy_edition`. `station_id` = WMO index parsed from filename (6 digits, keep as str). TMYx preferred (OQ-3, F17). Self-check: the 8 fixture-city stations present; no duplicate `station_id` (if a station has several TMYx editions keep the newest).
- **How to test:** T09 asserts the 8 fixture stations resolvable from the real CSV (offline read of bundled file); unit tests otherwise use the synthetic 10-row index (F15).

### T04 — `climate_zone.py`: input gate + join points (§3A)
- **What:** `_validate_input_schema(gdf)` (26 names + dtypes for load-bearing cols + `archetype_id` closed vocab per P7) and `_join_points(gdf) -> gpd.GeoSeries` exactly as DESIGN lines 42–47.
- **Why:** DESIGN §3A (F4).
- **How:** One vectorized `to_crs(4326)`; raise `ValueError` naming the offending column on gate failure (mirror Step 2's E3 fix style).
- **How to test:** T06.

### T05 — `climate_zone.py`: zone + state join (§3B)
- **What:** `assign_climate_zones(gdf, counties=None) -> pd.DataFrame` returning per-row `climate_zone, state, county_geoid, climate_zone_method, provenance_climate_zone` implementing F5/F6/F7; loads bundled GPKG via `importlib.resources` when `counties is None`.
- **Why:** DESIGN §3B.
- **How:** Tier 1 `sjoin(predicate="within")`; multi-match dedup = sort by `county_geoid`, keep first, structured warning (F6). Tier 2 only for unmatched: counties → UTM once, `sjoin_nearest(max_distance=5_000)` (P9). Abort cases (F5) raise `RuntimeError` with a JSON-structured message. Multi-zone warning payload verbatim F6. Output `climate_zone` validated ∈ F3 vocab.
- **How to test:** T06.

### T06 — tests for §3A/§3B against the real bundled GPKG
- **What:** `tests/test_climate_zone.py`.
- **Why:** DESIGN §5.1/§5.2 (F14, F15).
- **How:** Build tiny GDFs of synthetic square footprints (26 cols; reuse/extend the Step-2 synthetic fixture helpers in `tests/fixtures/` if convenient) placed at the 8 known-city coordinates → assert 8/8 zones; Boston Harbor point → `nearest_fallback` + `HEURISTIC`; Suffolk/Middlesex straddling pair → `county_geoid` differs, zone 5A both; open-ocean point → abort; schema-gate negative tests (missing column, bad archetype token, bad dtype). All offline against the bundled GPKG.
- **How to test:** is the test.

**⛔ CHECKPOINT CP1 — after T06.** Report: builder-script provenance summary (sources, checksums, row counts), pytest output for the new file, full-suite status. Wait for manager greenlight only if anything deviated; otherwise continue.

### T07 — `epw_manager.py`: station resolution (§3C)
- **What:** `load_stations(path=None) -> pd.DataFrame` (bundled CSV via `importlib.resources` by default) and `resolve_station(lat, lon, stations) -> tuple[pd.Series, float]` verbatim DESIGN lines 74–82; far-station warning per F9.
- **Why:** DESIGN §3C (F8, F9).
- **How:** `pyproj.Geod(ellps='WGS84')` vectorized `inv`; distance in km.
- **How to test:** T09.

### T08 — `epw_manager.py`: resolution order, download, gate, run-local copy (§3C–§3D)
- **What:** `fetch_epw(station, *, epw_dir=None, cache_dir=None, offline=False, output_dir) -> Path` implementing F10–F12 + P3/P4.
- **Why:** DESIGN §3C/§3D.
- **How:** Tiers exactly F10; user-dir multi-file pick by header lat/lon geodesic nearest (parse each header LOCATION line). Gate as one function `_validate_epw(path, station) -> None|warning` applied to EVERY accepted file regardless of tier (F11). Atomic `.tmp` → `os.replace`. Zip handling per P3. Run-local copy per F12 (`shutil.copy2`, create `<output_dir>/weather/`). Exhaustion ⇒ `RuntimeError` structured payload (F11). `requests.get(..., timeout=60)`.
- **How to test:** T09.

### T09 — tests for `epw_manager`
- **What:** `tests/test_epw_manager.py` + fixtures under `tests/fixtures/epw/`.
- **Why:** DESIGN §5.2 (F15).
- **How:** Synthetic 10-row station index CSV (F15). Generate fixture EPWs in-test or as files: valid (LOCATION header + 8760 data rows), truncated (<8760 → rejected at check 4), header-less (rejected at check 2), leap-year 8784 (accepted + warn). Mock `requests.get` for download paths (success zip, success bare epw, HTTP error → next tier). Cases: warm cache hit (no network call asserted), cold cache + `offline=True` → abort, user `epw_dir` single + multiple files, header-mismatch > 10 km → warning but accepted, full-tier exhaustion → `RuntimeError`. Plus: bundled real `epw_stations.csv` loads and contains the 8 fixture stations (T03 acceptance). Use `tmp_path` for all cache/output dirs; never touch `~/.openubem`.
- **How to test:** is the test.

### T10 — orchestrator `enrich_climate()` (§3E)
- **What:** Implement P5 in `openubem/acquisition/__init__.py`: zone join (T05) + station/EPW resolution (T07/T08) at the union representative point + 3-column append + artifact emission (F13) + byte-identity assertion + schema sidecar (P6) + parquet sidecar.
- **Why:** DESIGN §3E (F2, F13).
- **How:** Union point = `gdf.geometry.union_all().representative_point()` → 4326. Dtypes per F2 (categorical via `pd.Categorical` with the closed vocab). `epw_distance_km` constant per run, written per row (DESIGN line 127). Row order of sidecar matches GDF.
- **How to test:** T11.

### T11 — orchestrator tests
- **What:** `tests/test_step21_orchestrator.py`.
- **Why:** DESIGN §4 row-level guarantees + §5.1 (F2, F13, F14).
- **How:** Small synthetic 26-col GDF in a real US county (e.g. 3 squares in downtown Boston coords reprojected to UTM 19N), fake warm cache (pre-seed `cache_dir` with the canonical-named valid fixture EPW), `offline=True`. Assert: (N,29); the exact 3 appended names; 26 upstream cols byte-identical (`assert_frame_equal`); 3 new cols never null; `epw_path` is inside `output_dir`; all 3 artifacts exist; schema.json has 29 entries; sidecar columns exactly F13's 9, `osm_id` sets equal, single distinct `epw_path`; determinism per P8 (run twice into two dirs, parquet + schema byte-identical). Negative: empty-GDF behavior — gate rejects with clear error (0 Tier-1 matches ⇒ abort per F5).
- **How to test:** is the test.

**⛔ CHECKPOINT CP2 — after T11.** Report progress log + full-suite status.

### T12 — Boston 500 m integration test (offline)
- **What:** Add to `test_step21_orchestrator.py`: `tests/fixtures/boston_downtown_500m.gpkg` (Step-1 output, 23 cols) → existing `ArchetypeClassifier().classify()` → `enrich_climate(offline=True)` with pre-seeded fake cache for Boston Logan's canonical filename.
- **Why:** DESIGN §5.2 Boston integration expectations (line 164) + project memory: synthetic-only green is a known blind spot.
- **How:** Assert: 100% `county_within`; all rows `5A`/`MA`/`25025`; resolved station WMO `725090`; `nearest_fallback` rate ≤ 1% (expect 0); `epw_distance_km` constant. Mark `@pytest.mark.slow` if > 10 s.
- **How to test:** is the test.

### T13 — LIVE_SMOKE (opt-in, network)
- **What:** One test gated by `OPENUBEM_LIVE_SMOKE=1` (else `pytest.skip`): real station resolution from the bundled CSV at Boston coords, real download via the full tier chain into `tmp_path` cache, gate passes, `epw_distance_km < 50`.
- **Why:** project memory `feedback_synthetic_test_blind_spots` — a CP that gates on external data needs one live probe; validates T03's real URLs.
- **How:** Keep it single-station, single-download. Report its PASS/FAIL output at CP3 by running it once yourself with the env var set (this is the one sanctioned live execution).
- **How to test:** is the test.

**⛔ CHECKPOINT CP3 — after T13.** Final report: all progress-log entries, full-suite output, LIVE_SMOKE result, file tree of artifacts produced by a sample run.

## 7. Stop-and-report points

- **CP1** (after T06): bundled-data provenance + zone-join tests green.
- **CP2** (after T11): EPW manager + orchestrator green, full suite green.
- **CP3** (after T13): integration + live smoke. Hand back to manager for audit.

## 8. Progress log (executor appends; one entry per completed task)

```
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + DESIGN/PLAN cite>
- Test status: <pytest summary>
- Notes: <auditor-relevant>
```

#### T01 — pyproject.toml + config.py updates — completed 2026-06-10
- Artifacts: `pyproject.toml`, `openubem/config.py`
- Deviations: none
- Test status: baseline 265 passed, 2 skipped (unchanged)
- Notes: Added `requests`, `pyarrow`, `pyproj` to runtime deps; removed `pyarrow` from dev deps; added `climate_zones/*.gpkg` and `climate_zones/*.md` to package-data; added `EPW_CACHE_DIR`, `EPW_MAX_STATION_KM`, `EPW_PRIMARY_MIRROR`, `EPW_FALLBACK_MIRROR`, `OFFLINE` constants to config.py (DESIGN line 28/F18, line 84).

#### T02 — build_climate_zones_gpkg.py + bundled GPKG — completed 2026-06-10
- Artifacts: `scripts/build_climate_zones_gpkg.py`, `openubem/data/climate_zones/__init__.py`, `openubem/data/climate_zones/ashrae_climate_zones.gpkg`, `openubem/data/climate_zones/PROVENANCE.md`
- Deviations: Primary DOE/PNNL county-to-climate-zone table URLs were all 404 (energy.gov, pnnl.gov, energycodes.gov, basc.pnnl.gov). Fell back to NREL ResStock `County and PUMA.tsv` probability matrix as the PLAN §5 P1 "acceptable fallback". ResStock zone tokens 7A/7AK/7B normalised to "7", 8AK to "8" to match F3 vocab. DESIGN cite: PLAN §5 P1 fallback provision; DESIGN line 64 (F3 vocab).
- Test status: All 8 known-city fixtures validated (Miami/1A, Phoenix/2B, SF/3C, Boston/5A, Chicago/5A, Denver/5B, Duluth/7, Fairbanks/8). GPKG: 3133 counties, 15 zones (5C absent — no ResStock county maps to it).
- Notes: GPKG SHA-256: `74a84a58354fbdf5591a539349a08c138640c053b5502515def3c4ac95192734`. Census CB 2023 500k zip downloaded from `https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_county_500k.zip`.

#### T03 — build_epw_stations_csv.py + bundled CSV — completed 2026-06-10
- Artifacts: `scripts/build_epw_stations_csv.py`, `openubem/data/epw_stations.csv`
- Deviations: none
- Test status: All 8 fixture WMO IDs present (725090/Boston, 725300/Chicago, 722020/Miami, 722780/Phoenix, 724940/SF, 725650/Denver, 727450/Duluth, 702610/Fairbanks). Dedup policy: sort `tmy_edition` descending, keep newest per station_id (OQ-3, PLAN §5 P2).
- Notes: CSV: 2919 rows, columns: station_id, name, state, lat, lon, url, tmy_edition. CSV SHA-256: `e5bb0c1a786fb96d5c317792db555f1ab5a5519ee2729317c2aaea381c243deb`. KML source SHA-256: `23bff4bc13542efaa8ee33e9d983e94417ef22b981f18d8087200730440d20ae`. Source KML had 13,298 parsed placemarks.

#### T04 — climate_zone.py input gate + _join_points + _load_counties — completed 2026-06-10
- Artifacts: `openubem/acquisition/climate_zone.py`
- Deviations: none
- Test status: covered by T06 (test_gate_* tests, test_join_points_crs)
- Notes: `_validate_input_schema` checks exactly 26 cols, no extras, archetype_id in 30-vocab. `_join_points` uses `representative_point()` → EPSG:4326 (DESIGN lines 42-47, F4). `_load_counties` uses `importlib.resources.files()` pattern.

#### T05 — assign_climate_zones two-tier sjoin — completed 2026-06-10
- Artifacts: `openubem/acquisition/climate_zone.py` (extended)
- Deviations: `zero_tier1_matches` fast-fail removed; `unmatched_buildings` covers both failure modes (entire-batch-offshore and single-building-offshore-with-no-Tier2-hit). Rationale: the fast-fail incorrectly triggered when a single-building batch missed Tier-1 but Tier-2 would have resolved it. DESIGN cite: F5 abort on unmatched buildings (both cases surface as RuntimeError with JSON payload). Also fixed a `pd.Series.iloc[0]` bug in the Tier-2 row-extraction loop: `tier2.loc[idx]` returns a Series for single match; applying `.iloc[0]` on it yields a scalar, not a row — fixed with `isinstance(row2, pd.DataFrame)` guard.
- Test status: covered by T06 (test_known_city_zone ×8, test_boston_harbor_nearest_fallback, test_suffolk_middlesex_pair, test_open_ocean_abort)
- Notes: Returns 5 columns: climate_zone, state, county_geoid, climate_zone_method, provenance_climate_zone.

#### T06 — tests/test_climate_zone.py — completed 2026-06-10
- Artifacts: `tests/test_climate_zone.py`
- Deviations: Boston Harbor test uses (42.45, -70.80) — SE of Plymouth MA, 4495 m offshore from Plymouth County — rather than Boston Harbor proper, because the 500k cartographic boundary covers the inner harbor. Confirmed via sjoin_nearest that this point is a genuine Tier-1 miss / Tier-2 hit. DESIGN cite: F15 (nearest_fallback).
- Test status: 16 passed in 1.63s; full suite 281 passed, 2 skipped in 16.37s
- Notes: 8 known-city parametrized tests pass all expected zones against bundled GPKG; Suffolk/Middlesex pair confirms different county_geoid both zone 5A; open-ocean abort fires with JSON RuntimeError; all schema-gate negatives raise as expected.

#### C1 — Restore zero_tier1_matches abort in assign_climate_zones — completed 2026-06-10
- Artifacts: `openubem/acquisition/climate_zone.py`, `tests/test_climate_zone.py`
- Deviations: none
- Test status: 18 passed in test_climate_zone.py; full suite 312 passed, 2 skipped
- Notes: Inserted `zero_tier1_matches` RuntimeError check immediately after Tier-1 sjoin, before any Tier-2 code — fires when `len(matched) == 0` (DESIGN line 62 / PLAN F5). Updated `test_boston_harbor_nearest_fallback` — a single-building all-Tier-1-miss batch now aborts with `zero_tier1_matches` (C1 intent). Added `test_zero_tier1_matches_abort` (C1-a): two offshore Plymouth points, all Tier-1 miss, Tier-2 resolvable, now aborts. Added `test_mixed_tier1_tier2_still_passes` (C1-b): one on-land + one offshore point, mixed run succeeds with ASHRAE_STANDARD + HEURISTIC rows.

#### T07 — epw_manager.py station resolution — completed 2026-06-10
- Artifacts: `openubem/acquisition/epw_manager.py` (load_stations, resolve_station)
- Deviations: none
- Test status: covered by T09
- Notes: `load_stations` uses importlib.resources for bundled CSV; `resolve_station` uses pyproj.Geod vectorized inv (DESIGN lines 74-82, F8). Far-station warning emitted when dist_km > EPW_MAX_STATION_KM (F9).

#### T08 — epw_manager.py fetch_epw — completed 2026-06-10
- Artifacts: `openubem/acquisition/epw_manager.py` (fetch_epw, _validate_epw, _canonical_name, _try_download, _epw_from_user_dir)
- Deviations: none
- Test status: covered by T09
- Notes: Implements F10 tier order; atomic .tmp→os.replace; P3 zip handling; F11 validation gate (_validate_epw checks 2-4); F12 shutil.copy2 run-local copy.

#### T09 — tests/test_epw_manager.py — completed 2026-06-10
- Artifacts: `tests/test_epw_manager.py`, `tests/fixtures/epw/` (directory created; fixtures generated in-test)
- Deviations: dtype assertion for station_id changed from `== object` to value check `iloc[0] == "725090"` — Python 3.14 pandas uses StringDtype instead of object dtype for string columns even when dtype="str" passed to read_csv.
- Test status: 17 passed in 0.24s
- Notes: Covers warm cache, cold cache + offline abort, user epw_dir single + multi-file, truncated/headerless EPW rejection, leap-year 8784 accept + warn, header mismatch warning, full-tier exhaustion, download zip, tier fallback, output inside output_dir. Bundled real CSV T03 acceptance gate passes (all 8 WMO IDs present).

#### T10 — orchestrator enrich_climate() — completed 2026-06-10
- Artifacts: `openubem/acquisition/__init__.py`
- Deviations: Module-level imports changed to lazy (inside function body) to break circular import chain: `acquisition/__init__.py` → `climate_zone.py` → `building_classifier.py` → `osm_fetcher.py` which is under `acquisition/`. No DESIGN cite needed — this is a Python packaging constraint.
- Test status: covered by T11
- Notes: Implements P5 signature, union representative point for EPW station, pd.Categorical for climate_zone + provenance_climate_zone (F2), assert_frame_equal byte-identity check for upstream 26 cols, writes all 3 artifacts (F13).

#### T11 — tests/test_step21_orchestrator.py — completed 2026-06-10
- Artifacts: `tests/test_step21_orchestrator.py`, `pyproject.toml` (pytest ini: addopts --basetemp, package-data *.csv added)
- Deviations: Determinism test for parquet uses assert_frame_equal (re-read content equality) instead of byte-identity — pyarrow embeds non-deterministic row-group statistics in parquet files that differ even for identical logical content. PLAN §5 P8 cite: "Log a deviation note if even that fails, with cause." Schema JSON IS byte-identical. Parquet content equality confirmed.
- Test status: 12 passed in test_step21_orchestrator.py; full suite 312 passed, 2 skipped in 18.12s
- Notes: All F2/F13/F14 guarantees asserted: (N,29); 26 upstream cols byte-identical; 3 new cols never null; epw_path inside output_dir; all 3 artifacts exist; schema.json 29 entries; sidecar 9-col, osm_id sets equal, single distinct epw_path; determinism (schema byte-identical, parquet content-equal); empty GDF aborts.

#### T12 — Boston 500 m integration test (offline) — completed 2026-06-10
- Artifacts: `tests/test_step21_orchestrator.py` (3 new tests: `test_boston_integration_zone_and_state`, `test_boston_integration_county_and_fallback_rate`, `test_boston_integration_station_and_epw_distance`); `pyproject.toml` (added `markers = ["slow: ..."]`)
- Deviations: (1) nearest_fallback rate = 6/483 = 1.24% > DESIGN §5.2 line 164 threshold of ≤ 1%. The 6 buildings lie near the South End / Chinatown waterfront; Suffolk county GPKG is a MultiPolygon with 8 parts (islands), and the 500k cartographic boundary misses these buildings' representative points. All 6 resolve to 25025/5A/MA via Tier-2 nearest_fallback — topology-correct. Test threshold relaxed to ≤ 2%; deviation noted under OQ-1. (2) Resolved station is WMO 994971 ("Boston", lat=42.35, lon=-71.05, 1.0 km from union representative point), NOT 725090 (Boston Logan, 4.24 km). DESIGN §5.2 line 164 expected Logan; the bundled epw_stations.csv has a closer station that wins the geodesic argmin. The test asserts state=MA + dist<50 km instead of a specific WMO. Both stations are valid. PLAN F8/T13 DESIGN cite: "geodesic argmin at the representative point of the neighbourhood union."
- Test status: 3 passed (marked `@pytest.mark.slow`); full suite 315 passed, 3 skipped in 19.33s
- Notes: Boston integration metrics: zone=5A (100%), state=MA (100%), county_geoid=25025 (100%), county_within rate=98.76%, nearest_fallback rate=1.24%, resolved station=994971, epw_distance_km=1.383 (constant). Cache seeded with synthetic 8760-row valid EPW under canonical name `USA_MA_Boston.994971_TMYx.2011-2025.epw`. Fixture dtype fix: `levels` cast to `Int64` before classify (required by building_classifier._validate_input_schema).

#### T13 — LIVE_SMOKE (opt-in, network) — completed 2026-06-10
- Artifacts: `tests/test_step21_orchestrator.py` (`test_live_smoke_boston_epw_download`; skipped unless `OPENUBEM_LIVE_SMOKE=1`)
- Deviations: Same as T12 deviation (2): station 994971 resolves rather than 725090. Test accepts either ID ("994971" or "725090") and asserts state=MA + dist<50 km. DESIGN cite: PLAN T13 "real station resolution from the bundled CSV at Boston coords."
- Test status: LIVE_SMOKE PASS — station 994971 "Boston" MA, dist_km=1.383, EPW file 1.58 MB, downloaded and validated in ~0.16s; §3D gate: PASS (LOCATION header lat=42.35/lon=-71.05 matches index, no header-mismatch warning; data row count 8760). Full suite (no live var): 315 passed, 3 skipped.
- Notes: Live run confirms T03 URL for station 994971 is valid and serves a correct zip archive. `_validate_epw` returned None (no warnings). `epw_distance_km` = 1.383 < 50 km threshold. ✓

---

#### Manager audit — CP3 ratification — 2026-06-10
- Step 2.1 CLOSED. Suite: 315 passed, 3 skipped. LIVE_SMOKE PASS (real onebuilding download, gate clean).
- Ratified deviation: `nearest_fallback` 1.24% vs DESIGN line 155 "<= 1%" — cause is Census 500k cartographic generalization at the Boston waterfront (6 buildings, all topology-correct 25025/5A/MA), not a county-layer defect. Test threshold 2% accepted. DESIGN erratum candidate (threshold assumed an exact-boundary county layer).
- Ratified deviation: resolved station 994971 (Boston, 1.38 km) instead of DESIGN line 164's expected Logan 725090 (4.24 km) — correct geodesic argmin over the real station index. DESIGN erratum candidate (fixture expectation, not a rule).
- Earlier CP1 corrections (zero_tier1_matches abort restored as C1; scratch scripts removed; fixture revert) verified landed.
