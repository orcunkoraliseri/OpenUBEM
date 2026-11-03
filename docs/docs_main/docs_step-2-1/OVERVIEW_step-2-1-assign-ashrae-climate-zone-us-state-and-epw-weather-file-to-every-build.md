# OVERVIEW — Step 2.1 — Classified GeoDataFrame → ASHRAE Climate Zone, US State, and EPW Weather File
### OpenUBEM Stage 1 / Module 02 — append `climate_zone` + `epw_path` + `provenance_climate_zone` (26 → 29 columns), resolve one validated EPW per run, and emit the `02a_climate_epw.parquet` sidecar carrying `state` to Stage 5

> **Slug:** `step-2-1-assign-ashrae-climate-zone-us-state-and-epw-weather-file-to-every-build` &nbsp;•&nbsp; **Snapshot of:** `DESIGN_step-2-1-assign-ashrae-climate-zone-us-state-and-epw-weather-file-to-every-build.md` &nbsp;•&nbsp; **Generated:** `2026-06-09`
>
> Compact dashboard. For depth → read the DESIGN doc. For revision history → read DESIGN §11.

---

## AIM

Step 2.1 designs Module 02 — the recurring blocker named in Step 3 OQ-7, Step 4 OQ-5, and Step 5 OQ-5. For every classified building it answers the two questions the rest of the pipeline assumes are answered: *which ASHRAE climate zone* (the lookup key for every Module 04 construction table) and *which EPW weather file* (what Step 4 binds at launch with `-w`). It appends exactly three columns (26 → 29: `climate_zone`, `epw_path`, `provenance_climate_zone`), copies one validated EPW into the run directory, and emits a per-building sidecar that carries `state` + county FIPS to Stage 5's eGRID lookup — resolving Step 5 OQ-3 without widening the frozen 57-column Step 3 contract. Governing principles: per-building correctness at county/zone borders, closed vocabularies with canonical provenance tokens, fail-loud on weather (no per-building degradation path exists), and self-contained run directories.

---

## PIPELINE

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  3A — Input Gate & Representative Points (climate_zone.py)                   ║
║  Inputs:    02_buildings_classified.gpkg (N, 26) from Step 2                 ║
║  Operation: schema validation; representative_point() per building           ║
║             (guaranteed inside footprint); ONE vectorized UTM→EPSG:4326      ║
║  Output:    join-point GeoSeries                                             ║
║  Validation: 26-column schema + closed archetype vocabulary                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3B — ASHRAE Zone + State Spatial Join (climate_zone.py)                     ║
║  Inputs:    bundled ashrae_climate_zones.gpkg (~3,100 US county polygons)    ║
║  Operation: sjoin within → ASHRAE_STANDARD; unmatched → sjoin_nearest        ║
║             ≤ 5 km → HEURISTIC; zero coverage ⇒ ABORT RUN;                   ║
║             state + county_geoid from the same matched county                ║
║  Output:    climate_zone (16-token closed vocab) + state per building        ║
║  Validation: 8/8 known-city fixture; nearest_fallback ≤ 1% (Boston)          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3C — EPW Station Resolution (epw_manager.py)                                ║
║  Inputs:    bundled epw_stations.csv (WMO id, lat/lon, URL)                  ║
║  Operation: ONE station per run — pyproj.Geod geodesic argmin at the         ║
║             neighbourhood representative point; epw_distance_km recorded;    ║
║             > 300 km ⇒ epw_far_station warning (ASSUMPTION_DESIGN_DEFAULT);  ║
║             order: user epw_dir → ~/.openubem/epw cache → onebuilding →      ║
║             energyplus.net; offline=True skips network                       ║
║  Output:    resolved station + candidate EPW file                            ║
║  Validation: header–index distance ≤ 10 km                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3D — Download, Atomic Cache & EPW Validation (epw_manager.py)               ║
║  Inputs:    candidate EPW (downloaded / cached / user-provided)              ║
║  Operation: .tmp → os.replace atomic write; gate: LOCATION header parses,    ║
║             8760|8784 data rows, header lat/lon sanity; all tiers fail ⇒     ║
║             ABORT RUN (weather has no flag-don't-drop path);                 ║
║             accepted EPW COPIED to <output_dir>/weather/                     ║
║  Output:    run-local validated EPW                                          ║
║  Validation: truncated-EPW fixture rejected; cold-cache offline ⇒ abort      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3E — Column Append + Artifact Emission (acquisition/__init__.py)            ║
║  Inputs:    26-col GDF + zone/state frame + run-local epw_path               ║
║  Operation: append EXACTLY 3 columns → (N, 29); 26 upstream byte-identical;  ║
║             emit 02a_buildings_climate.gpkg + .schema.json (29 entries) +    ║
║             02a_climate_epw.parquet (N × 9, incl. state → Step 5 eGRID)      ║
║  Output:    Step 2.2's input + Step 5's state source                         ║
║  Validation: sidecar osm_id set == GDF osm_id set; determinism check         ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## KEY NUMBERS

| Quantity | Value | Source |
|---|---|---|
| Input → output schema             | (N, 26) → (N, 29): + `climate_zone`, `epw_path`, `provenance_climate_zone` | DESIGN §3E, §4 |
| Climate-zone vocabulary           | 16 closed US tokens {1A…3C, 4A…5C, 6A, 6B, 7, 8} | DESIGN §3B |
| Provenance vocabulary             | {ASHRAE_STANDARD (county join), HEURISTIC (nearest fallback)} | DESIGN §3B |
| Nearest-fallback search radius    | ≤ 5 km (metric, in run UTM CRS)            | DESIGN §3B |
| EPW stations resolved per run     | 1 (geodesic-nearest, pyproj.Geod)          | DESIGN §3C |
| Far-station warn threshold        | 300 km (`ASSUMPTION_DESIGN_DEFAULT`, OQ-4) | DESIGN §3C |
| EPW validation gate               | LOCATION header + 8760/8784 rows + ≤ 10 km header sanity | DESIGN §3D |
| Sidecar shape                     | (N, 9) — incl. `state`, `county_geoid`, `epw_distance_km` | DESIGN §3E |
| Wall-clock (Boston 500 m, warm)   | < 30 s                                     | DESIGN §6 |
| Network (warm cache / offline)    | 0 bytes; cold cache: one ~1.5–2 MB EPW     | DESIGN §6 |
| GPU hours                         | 0                                          | DESIGN §6 |
| Open Questions                    | 5                                          | DESIGN §7 |

---

## VALIDATION SUMMARY

- Zone/state coverage: **100%** non-null `climate_zone`, `state`, `county_geoid` — the fallback chain ends in a whole-run abort, never NaN
- Known-city fixture: **8/8** exact (Miami 1A, Phoenix 2B, San Francisco 3C, Boston 5A, Chicago 5A, Denver 5B, Duluth 7, Fairbanks 8)
- `nearest_fallback` rate: **≤ 1%** on the Boston 500 m fixture (higher ⇒ county-layer topology defects → OQ-1)
- EPW gate: **100%** of accepted files pass; the truncated-EPW fixture must be rejected at the row-count check
- Header–index consistency: station header lat/lon within **10 km** of the bundled index entry
- Determinism: identical inputs + warm cache ⇒ **byte-identical** `02a_*` artifacts
- Sidecar integrity: sidecar `osm_id` set **==** GeoPackage `osm_id` set; one `epw_path` per run
- True Future Test: n/a — deterministic lookup, nothing trained; generalization surface covered by the abort paths

---

## KEY DECISIONS

> Mirrors DESIGN §9 — same rows, one line each.

| Decision | Rationale (one line) |
|---|---|
| Column-accretion position after Step 2 (26 → 29) despite Module 02 being logically Stage-1 | Step 2's frozen 23 → 26 byte-identical contract fixes the artifact order; Module 02 needs nothing from `archetype_id`. |
| Per-building county `sjoin` on `representative_point()`, not the spec's single union-centroid zone | Vectorized join is near-free and correct when a bbox crosses a county/zone boundary. |
| Closed 16-token US vocabulary; nearest-fallback ≤ 5 km = HEURISTIC; zero coverage ⇒ abort | Local gaps degrade traceably; systemic coverage failure fails loudly. |
| One EPW station per run, geodesic-nearest; `epw_distance_km` recorded per building | Station spacing ≫ neighbourhood size; per-building stations buy nothing and cost a spurious EUI discontinuity. |
| Spec resolution order + atomic `.tmp → os.replace` + uniform validation gate; no EPW ⇒ abort | Weather has no per-building degradation path — a loud abort at minute 0 beats 400 `failed_crash` rows at minute 30. |
| `epw_path` points at a run-local copy under `<output_dir>/weather/` | Self-contained run dirs survive cache eviction and stage cleanly to HPC scratch; copies, not symlinks (Windows). |
| `state` rides in `02a_climate_epw.parquet`, not as a flowing column | Keeps the frozen 57/70-column contracts intact while resolving Step 5 OQ-3 with a designed owner. |

---

## OPEN QUESTIONS

- **OQ-1** — Pin edition + checksum of the bundled county climate-zone GPKG (169-2013-consistent vs IECC-2021 re-assignments). *(blocks §3B fixture sign-off)*
- **OQ-2** — One-time extraction of `data/epw_stations.csv` from the climate.onebuilding.org catalog, with refresh procedure + licensing note. *(blocks §3C on real networks)*
- **OQ-3** — TMY edition policy (TMYx 2007–2021 vs TMY3) — affects comparability with the CBECS 2018 validation anchor. *(blocks §3C canonical filename)*
- **OQ-4** — Calibrate `EPW_MAX_STATION_KM = 300` (`ASSUMPTION_DESIGN_DEFAULT`) from measured Phase-1 fixture distances. *(tunes observability only)*
- **OQ-5** — Phase-3 Canada: NECB HDD zones are a different vocabulary — union vocabulary + `zone_system` discriminator vs parallel column. *(blocks Phase 3 only)*
