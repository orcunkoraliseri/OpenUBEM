# EXECUTOR PROMPT — EU-04 / `S1-EXEC-01`, run the ruled `D-EU-04-H` (Option H1)

**Paste this whole file into a fresh executor session. Execute it top to bottom. Do not propose
alternatives. If anything here is ambiguous or contradicts the code you find, STOP and quote the
conflict rather than choosing.**

**Working directory:** `C:\Users\o_iseri\Desktop\OpenUBEM`
**Date opened:** 2026-08-25
**Authority:** `docs/docs_ACTIVE/europeanLocations/debugs/docs/DECISION_REQUEST_EU-04_H_S1_reachability_2026-08-25.md`
— status `RULED`, **Option H1 selected**: *"S1 ladder execution proceeds with 12 buildings
(3 per typology) selected by the established ladder rules, measuring real corpus yield and
classifying all failure modes fail-closed."*

**Ladder acceptance criterion** (`content/table_9_7_sample_group_ladder.csv`, row `S1`):
`12/12 accounted for; failures classified` — **not** `12/12 succeed`. A named, reproducible refusal
is a pass of this criterion. Never widen a threshold, swap a building, or drop a row to raise a
success count.

---

## 0. What is already true, and one correction you must carry

Already on disk, do not redo it:

- `openubem/outputs/eu_evidence/EU-04/s1_layout_reachability_census.csv` — 297 rows, the manager's
  measurement of which layout-ready French buildings can be laid out. **18 emit** a dwelling layout,
  23 fall back, 256 are refused by the layout contract.
- The 12 buildings of `S1` are **already selected** and frozen in §2 below. Do not re-select them.

**Correction to carry into your report.** The decision request estimated that "about 4" of the 12
would reach an EnergyPlus run with dwelling-level zones. The frozen selection was computed after
that sentence was written: **exactly 1 of the 12 emits a dwelling layout** (`AB`,
`BATIMENT0000000240879449_part0`). The other 11 do not. This is the ladder rule applied honestly —
it selects `2 irregular + 1 simple` per typology **by `building_id` order**, never by whether the
building works. Report the 1, not the 4.

---

## 1. Hard rules

1. **No network.** No WFS call, no re-acquisition, no ERA5, no EPW download. The manifest and the
   census on disk are the only inputs.
2. **No re-selection.** The 12 `building_id` values in §2 are frozen. If one is missing from the
   manifest, STOP and report which.
3. **Fail-closed, and never launder a fallback into a success.** A building whose dwelling layout is
   not emitted is simulated — if at all — through the repository's already-ruled
   `one_zone_per_floor` strategy, and its result is recorded in a **separate column** from the
   dwelling-layout status. `openubem/geometry/european_residential.py:89` states it directly: a
   fallback "may never be counted as successful dwelling-level geometry." Honour that in every
   artefact you write.
4. **S1 produces no energy number.** It is a geometry-to-EnergyPlus smoke: it proves the path runs.
   Do not compute, report, or write to disk any demand, EUI, or load figure. Design-day sizing only.
5. **Do not change the layout generator, its thresholds, `zoning.py`, or any test that currently
   passes.** If you believe the generator is wrong, STOP and say so; do not edit it.
6. Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` first.
   After solving any error, register it there before closing the task, in the house format.
7. Do not edit root `main.py`, OVERVIEW or DESIGN docs. No `.py` under `docs/`. Figures, if any, go
   flat in `openubem/outputs/`.
8. Create only the files §4 names. Append a progress-log entry per checkpoint (§5).

---

## 2. The frozen `S1` sample — 12 buildings

Neighbourhood `FR-LYO-HAUTCOEURPENTES`, manifest
`openubem/outputs/eu02/FR-LYO-HAUTCOEURPENTES/02_residential_manifest.gpkg`.
Selection rule, already applied: per typology, the **2 lowest-`building_id` irregular** footprints
(non-convex or courtyard) plus the **1 lowest-`building_id` simple** footprint (convex, no hole).

| # | type | building_id | archetype_id | year | dwellings | storeys | units/floor | area m2 | shape | expected layout status |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| 1 | SFH | `BATIMENT0000000240877122_part0` | `FR.N.SFH.01.Gen.ReEx.001.001` | 1800 | 1 | 1 | 1 | 36.54 | irregular | `REFUSED_BY_LAYOUT_CONTRACT` / `NON_CONVEX_FOOTPRINT` |
| 2 | SFH | `BATIMENT0000000240877182_part0` | `FR.N.SFH.01.Gen.ReEx.001.001` | 1860 | 1 | 2 | 1 | 107.88 | irregular | `REFUSED_BY_LAYOUT_CONTRACT` / `NON_CONVEX_FOOTPRINT` |
| 3 | SFH | `BATIMENT0000000240879451_part0` | `FR.N.SFH.01.Gen.ReEx.001.001` | 1805 | 1 | 1 | 1 | 69.11 | simple | `FALLBACK_PENDING_LAYOUT` / `NARROW_FOOTPRINT_LT_8M` |
| 4 | TH | `BATIMENT0000000240879618_part0` | `FR.N.TH.01.Gen.ReEx.001.001` | 1900 | 1 | 2 | 1 | 57.68 | irregular | `REFUSED_BY_LAYOUT_CONTRACT` / `NON_CONVEX_FOOTPRINT` |
| 5 | TH | `BATIMENT0000000240879754_part0` | `FR.N.TH.01.Gen.ReEx.001.001` | 1880 | 1 | 4 | 1 | 155.93 | irregular | `REFUSED_BY_LAYOUT_CONTRACT` / `NON_CONVEX_FOOTPRINT` |
| 6 | TH | `BATIMENT0000000240880050_part0` | `FR.N.TH.01.Gen.ReEx.001.001` | 1720 | 1 | 4 | 1 | 76.84 | simple | `FALLBACK_PENDING_LAYOUT` / `NARROW_FOOTPRINT_LT_8M` |
| 7 | MFH | `BATIMENT0000000240877101_part0` | `FR.N.MFH.01.Gen.ReEx.001.001` | 1860 | 10 | 4 | 3 | 221.98 | irregular | `REFUSED_BY_LAYOUT_CONTRACT` / `NON_CONVEX_FOOTPRINT` |
| 8 | MFH | `BATIMENT0000000240877183_part0` | `FR.N.MFH.01.Gen.ReEx.001.001` | 1890 | 5 | 4 | 2 | 132.13 | irregular | `REFUSED_BY_LAYOUT_CONTRACT` / `NON_CONVEX_FOOTPRINT` |
| 9 | MFH | `BATIMENT0000000013365727_part0` | `FR.N.MFH.07.Gen.ReEx.001.001` | 1998 | 2 | 3 | 1 | 49.03 | simple | `FALLBACK_PENDING_LAYOUT` / `NARROW_FOOTPRINT_LT_8M` |
| 10 | AB | `BATIMENT0000000240877151_part0` | `FR.N.AB.01.Gen.ReEx.001.001` | 1900 | 17 | 6 | 3 | 271.70 | irregular | `REFUSED_BY_LAYOUT_CONTRACT` / `NON_CONVEX_FOOTPRINT` |
| 11 | AB | `BATIMENT0000000240877527_part0` | `FR.N.AB.01.Gen.ReEx.001.001` | 1860 | 15 | 5 | 3 | 276.07 | irregular | `REFUSED_BY_LAYOUT_CONTRACT` / `NON_CONVEX_FOOTPRINT` |
| 12 | AB | `BATIMENT0000000240879449_part0` | `FR.N.AB.07.Gen.ReEx.001.001` | 1999 | 28 | 6 | 5 | 544.21 | simple | **`DWELLING_LAYOUT_EMITTED`** |

Every value in this table is copied from `s1_layout_reachability_census.csv`. **Your T01 must
reproduce the "expected layout status" column exactly, from the manifest, independently.** If any
row differs, STOP and report the row — do not adjust anything to match.

---

## 3. The two axes you are measuring — keep them apart

- **Axis A — dwelling-layout status.** Does `generate_european_dwelling_layout` emit dwelling
  polygons for this real footprint? Values: `DWELLING_LAYOUT_EMITTED`, `FALLBACK_PENDING_LAYOUT`
  (+ reason), `REFUSED_BY_LAYOUT_CONTRACT` (+ reason). **This is what the ruling asked to be
  classified.** Expected: 1 emitted, 3 fallback, 8 refused.
- **Axis B — design-day smoke outcome.** Does the building reach a completed EnergyPlus design-day
  run at all? Zones come from Axis A where it emitted, and from
  `openubem.geometry.zoning.build_zones(..., strategy="one_zone_per_floor")` where it did not.
  Values: `EPLUS_COMPLETED`, `EPLUS_SEVERE`, `EPLUS_FATAL`, `EPLUS_TIMEOUT`, `NOT_ATTEMPTED`
  (+ the first `** Severe **` / `** Fatal **` line, verbatim, truncated to 300 chars).

A row that is `REFUSED_BY_LAYOUT_CONTRACT` on Axis A and `EPLUS_COMPLETED` on Axis B is **a
whole-floor smoke success and a dwelling-layout failure**. Say exactly that. Never collapse the two
into one "passed" count.

---

## 4. Tasks

### T01 — build the runner and reproduce Axis A

**What.** Create `scripts/run_eu_s1_smoke.py` (a runner, not a test). It must read the 12 frozen
`building_id` values (hardcode the list from §2 — this is a frozen sample, not a query), load the
manifest in its **native `EPSG:32631`** (UTM 31N, metric, correct for Lyon) and do **not** reproject - CORRECTED 2026-08-25 after `S1-EXEC-01` CP-1 stopped on it: the earlier text said EPSG:2154, but `generate_european_dwelling_layout` rotates about the literal origin (`european_residential.py:504`, `origin=(0.0, 0.0)`) while `audit_european_floor_partition` uses an **absolute** `topology_tolerance_m2=1e-8` (`european_residential.py:643`), so Lambert-93's larger coordinates inject float noise that trips `AREA_GAP`/`OUTSIDE_FOOTPRINT` spuriously on row 12 at an `area_error_fraction` of 5.09e-12. The frozen table in section 2 and `s1_layout_reachability_census.csv` were both produced in the native CRS. This is recorded as a generator fragility, NOT fixed in this measurement task. For each row call
`allocate_european_dwellings` on the observed dwelling and storey counts to get `units_per_floor`,
then `generate_european_dwelling_layout(footprint, requested_dwelling_count=units_per_floor)`.

**Why.** Axis A must be re-derived by the code that will build the IDFs, not copied from the census,
or the census cannot be checked.

**How.** Refuse a footprint that is not a `Polygon` with the reason `MULTIPART_FOOTPRINT` rather
than taking its largest part. Read the courtyard flag from `footprint.interiors`, convexity from the
same predicate the census used. A `--dry-run` flag runs T01 only and writes nothing.

**How to test.** `python scripts/run_eu_s1_smoke.py --dry-run` prints 12 rows; the status column
must equal §2's last column for all 12. Report the 12 statuses.

### T02 — build one IDF per building and run the design-day smoke

**What.** For each of the 12, build an IDF and run EnergyPlus once.

**Why.** This is what `S1` exists to prove: an observed European footprint reaches a completed run.

**How.** Follow the proven recipe in `tests/test_eu_reciprocal_surface_audit.py:164-232` — the same
synthetic header (`Version,23.1` / `Timestep,4` / `SimulationControl,Yes,Yes,No,Yes,No,No,1` /
`Site:Location` / one `SizingPeriod:DesignDay` `WinterDesignDay` at -10 C /
`ScheduleTypeLimits,Any Number`), then `extrude_geometry`, then one `SIZING:ZONE` per zone, then
`add_european_heating_controls(idf, record, zone_name)`. Pinned differences from that test:

- `record` is the **French** TABULA record whose `archetype_id` matches the row, read from
  `openubem/data/construction/tabula_archetypes_fr.json` — not the ES S0 fixture.
- Zones: `european_layout_to_zone_specs` for row 12 only; for the other 11,
  `build_zones(building_id, footprint, archetype_id, num_floors=observed_storeys,
  strategy="one_zone_per_floor", floor_to_floor_m=3.0)`.
- **Floor-to-floor 3.0 m is a pinned geometry-smoke constant**, matching the S0 smoke; it is not a
  physical claim about Lyon. Record it as a stated assumption in the manifest and in the report.
- Row 12 is the only row that also runs `audit_reciprocal_interzone_wall_surfaces` — it is the only
  one with party walls to audit. Report `passed`, `party_face_count`, `reciprocal_pair_count`.
- `subprocess.run([...], timeout=180)`. Run outputs go to a per-building temp dir; keep only
  `eplusout.err`, copied to `openubem/outputs/eu_evidence/EU-04/s1_smoke/<building_id>.err`.
  **Do not keep the `.idf`, `.eso`, `.sql` or any other E+ artefact** — the arc does not need them
  and they are large.
- A courtyard footprint is extruded from its **exterior ring only**; the hole is filled. That is a
  known simplification of the existing pipeline, not a new decision — record it in the `notes`
  column for every row whose `has_courtyard` is true, and count those rows in the report.

**How to test.** Report the Axis B value for all 12, plus the verbatim first severe/fatal line for
any row that is not `EPLUS_COMPLETED`.

### T03 — write the S1 evidence manifest

**What.** Write `openubem/outputs/eu_evidence/EU-04/s1_smoke_manifest.csv`, exactly 12 rows, columns:
`building_id, building_type, archetype_id, year_built, observed_dwellings, observed_storeys,
units_per_floor, footprint_area_m2, is_convex, has_courtyard, shape_class, zone_source,
zone_count, layout_status, layout_reason, eplus_status, eplus_first_severe, runtime_s, notes`.

`zone_source` is `EUROPEAN_DWELLING_LAYOUT` or `FALLBACK_ONE_ZONE_PER_FLOOR`. `shape_class` is
`simple` or `irregular` as in §2.

**Why.** "12/12 accounted for" has to be a file someone can read, not a claim in a chat message.

**How to test.** `wc -l` is 13. No cell is empty except `eplus_first_severe` and `notes`. Assert in
the runner that the row count is 12 and that every `layout_status` is one of the three tokens.

### T04 — report

Report, in one message, and write nothing else:

1. The 12 Axis A statuses versus §2 — same or different, per row.
2. The 12 Axis B outcomes, with counts by `zone_source`.
3. The party-wall audit triple for row 12.
4. How many rows carry the courtyard-fill note.
5. Any error you hit and the `OpenUBEM_debug_References.md` entry you appended for it.
6. `pytest -q tests/test_eu_reciprocal_surface_audit.py tests/test_eu_box_generator.py` — counts and
   duration, to show you broke nothing.

---

## 5. Stop-and-report points

- **CP-1, after T01.** Report the 12 Axis A statuses against §2 **before** running EnergyPlus. If a
  single row differs, stop there and report it.
- **CP-2, after T03.** Report the full manifest summary and the test result.

At each checkpoint append one row to
`docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv` and the matching row to
Walkthrough Table 4 — nine fields, UTC timestamp, commit + `dirty` caveat. Append only; never
rewrite an existing row.

---

## 6. What this task does **not** do

- It does not extend the layout generator to concave or courtyard footprints. That is option H3 of
  the ruled decision and it was **not** selected; it remains an unopened work package.
- It does not touch `ES`, `GB` or `IT`, and it does not form `S2` or `S3`.
- It does not produce or quote an energy result.
- It does not fix the hardcoded `current_year = 2026` in `bdtopo_fetcher.py:82` — recorded, separate.
